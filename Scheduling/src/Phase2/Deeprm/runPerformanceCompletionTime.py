# from DeepRM.envs.DeepRMEnv import DeepEnv
import environment
import gym
import tensorflow as tf
import operator
import numpy as np
import math
import matplotlib.pyplot as plt
import parameters
import job_distribution
import argparse
from random import sample
import os
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines import PPO2
from stable_baselines import DQN
from stable_baselines.common.env_checker import check_env
from gym import spaces
import pandas as pd
from stable_baselines.common import make_vec_env
import numpy as np
import _pickle as cPickle
import matplotlib.pyplot as plt
import numpy as np
import environment
import parameters
import pg_network
import other_agents
from datetime import datetime
# import randomAgent

import warnings

from statistics import mean
import other_agents
from datetime import datetime
# warnings.simplefilter(action='ignore', category=FutureWarning)
# warnings.simplefilter(action='ignore', category=Warning)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

if __name__ == '__main__':
    def get_traj(test_type, pa, env, episode_max_length, pg_resume=None, render=False):
        """
        Run agent-environment loop for one whole episode (trajectory)
        Return dictionary of results
        """

        if test_type == 'PG':  # load trained parameters

            pg_learner = pg_network.PGLearner(pa)

            net_handle = open(pg_resume, 'rb')
            net_params = cPickle.load(net_handle)
            pg_learner.set_net_params(net_params)

        env.reset()
        rews = []
        done = False

        ob = env.observe()

        # Issue here
        for _ in range(episode_max_length):
            # while not done:

            if test_type == 'PG':
                a = pg_learner.choose_action(ob)
            elif test_type == 'Tetris':
                a = other_agents.get_packer_sjf_action(
                    env.machine, env.job_slot, 1)
            elif test_type == 'Packer':
                a = other_agents.get_packer_action(env.machine, env.job_slot)

            elif test_type == 'SJF':
                a = other_agents.get_sjf_action(env.machine, env.job_slot)

            elif test_type == 'Random':
                a = other_agents.get_random_action(env.job_slot)

            ob, rew, done, info = env.step(a, repeat=True)

            rews.append(rew)

            if done:
                break
            if render:
                env.render()
            # env.render()

        return np.array(rews), info

    def discount(x, gamma):
        """
        Given vector x, computes a vector y such that
        y[i] = x[i] + gamma * x[i+1] + gamma^2 x[i+2] + ...
        """
        out = np.zeros(len(x))
        out[-1] = x[-1]
        for i in reversed(range(len(x)-1)):
            out[i] = x[i] + gamma*out[i+1]
        assert x.ndim >= 1
        # More efficient version:
        # scipy.signal.lfilter([1],[1,-gamma],x[::-1], axis=0)[::-1]
        return out

    # Test types
    test_types = ['PG', 'SJF',  'Packer', 'Random']
    # test_types = ['SJF',  'Packer']

    render = False
    # pg_resume = 'data/pg_re_rate_0.7_simu_len_50_num_seq_per_batch_20_ex_10_nw_10_950.pkl'
    pg_resume = 'data/pg_re_rate_0.7_simu_len_NewCtime_10Jan50_num_seq_per_batch_20_ex_10_nw_10_950.pkl'
    pa = parameters.Parameters()
    pa.new_job_rate = 0.7
    pa.num_seq_per_batch = 20
    pa.num_ex = 10
    pa.num_nw = 10
    pa.simu_len = simu_len = 50
    # pa.simu_len = simu_len = 200
    pa.episode_max_length = 100
    # Environment
    env = environment.Env(pa, render=False, repre='image', end='all_done')
    all_discount_rews = {}
    jobs_slow_down = {}
    work_complete = {}
    work_remain = {}
    job_len_remain = {}
    num_job_remain = {}
    job_remain_delay = {}
    for test_type in test_types:

        all_discount_rews[test_type] = []
        jobs_slow_down[test_type] = []
        work_complete[test_type] = []
        work_remain[test_type] = []
        job_len_remain[test_type] = []
        num_job_remain[test_type] = []
        job_remain_delay[test_type] = []

    for seq_idx in range(pa.num_ex):
        # print('\n\n')
        print("=============== " + str(seq_idx) + " ===============")
        for test_type in test_types:
            rews, info = get_traj(test_type, pa, env,
                                  pa.episode_max_length, pg_resume)
            # print("---------- " + test_type + " -----------")

            # print("total discount reward : \t %s" %
            #       (discount(rews, pa.discount)[0]))

            all_discount_rews[test_type].append(
                discount(rews, pa.discount)[0]
            )

            # ------------------------
            # ---- per job stat ----
            # ------------------------

            enter_time = np.array(
                [info.record[i].enter_time for i in range(len(info.record))])
            finish_time = np.array(
                [info.record[i].finish_time for i in range(len(info.record))])
            job_len = np.array(
                [info.record[i].len for i in range(len(info.record))])
            job_total_size = np.array(
                [np.sum(info.record[i].res_vec) for i in range(len(info.record))])

            finished_idx = (finish_time >= 0)
            unfinished_idx = (finish_time < 0)

            jobs_slow_down[test_type].append(
                (finish_time[finished_idx] -
                 enter_time[finished_idx]) / job_len[finished_idx]
            )
            # work_complete[test_type].append(
            #     np.sum(job_len[finished_idx] *
            #            job_total_size[finished_idx])
            # )
            work_complete[test_type].append(
                (finish_time[finished_idx] -
                 enter_time[finished_idx])
            )
            print("bhai printing the value for work complete")
            print("work_complete -> ",work_complete)
            work_remain[test_type].append(
                np.sum(job_len[unfinished_idx] *
                       job_total_size[unfinished_idx])
            )
            job_len_remain[test_type].append(
                np.sum(job_len[unfinished_idx])
            )
            num_job_remain[test_type].append(
                len(job_len[unfinished_idx])
            )
            job_remain_delay[test_type].append(
                np.sum(pa.episode_max_length -
                       enter_time[unfinished_idx])
            )
        env.seq_no = (env.seq_no + 1) % env.pa.num_ex

    # Plot the values
    def autolabel(rects, ax):
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2., height,
                    '%.1f' % height, ha='center', va='bottom')

    fig = plt.figure()
    n_groups = 1
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    index = np.arange(n_groups)
    bar_width = 0.9
    opacity = 0.8
    agent_plots = []
    colors = ['r',  'c', 'm', 'y']
    title = ['DeepRM',  'SJF',  'Packer', 'Random']
    for i in range(len(test_types)):
        # mean_slowdown = []
        mean_ctime = []
        print(test_types[i])
        # value_sl = jobs_slow_down.get(test_types[i])
        value_ct = work_complete.get(test_types[i])
        for val in range(len(value_ct)):
            # mean_slowdown.append(np.mean(value_sl[val]))
            mean_ctime.append(np.mean(value_ct[val]))
    
        mean_values = (np.mean(mean_ctime))
        print("mean values -> ",mean_values)
        deviation = (np.std(mean_ctime))
        print("deviation values -> ",deviation)
        agent_plot = plt.bar(index + i * bar_width, mean_values, bar_width,
                             yerr=deviation,
                             ecolor='k',
                             capsize=12,
                             alpha=opacity,
                             color=colors[i],
                             label=title[i])
        # agent_plot = plt.bar( mean_values, bar_width,
        #                      yerr=deviation,
        #                      ecolor='k',
        #                      capsize=12,
        #                      alpha=opacity,
        #                      color=colors[i],
        #                      label=title[i])
        agent_plots.append(agent_plot)
    for agent_plot in agent_plots:
        autolabel(agent_plot, ax)
    plt.xlabel('Objective - Average job completion time')
    plt.ylabel('Average job completion time')
    plt.title('Performance for objective minimize Average Job Completion')
    plt.xticks(index + 4 * bar_width, ('Average job slowdown',
                                       'Average job completion time'))
    plt.legend()
    # ax2 = ax.twinx()
    # plt.ylabel("Average job completion time")
    # ax2.set_ylim(ax.get_ylim())
    plt.tight_layout()

    plt.tight_layout()
    fig.savefig("TestPerformance" +
                str(datetime.time(datetime.now()))+".png")
