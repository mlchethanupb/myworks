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
import json
from statistics import mean
import other_agents
# import Otheragents
# import Other_agent_II as newOther
# import other_agents_original as og
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
        # for _ in range(episode_max_length):
        while not done:

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

    def accumulate_results(test_types, jobs_slow_down, work_complete):
        slowdown = []
        ctime = []
        for i in range(len(test_types)):
            mean_slowdown = []
            mean_ctime = []

            value_sl = jobs_slow_down.get(test_types[i])
            value_ct = work_complete.get(test_types[i])
            for val in range(len(value_sl)):
                mean_slowdown.append(np.mean(value_sl[val]))
                mean_ctime.append(np.mean(value_ct[val]))
            slowdown.append(np.mean(mean_slowdown))
            ctime.append(np.mean(mean_ctime))
        return slowdown, ctime

    test_types = ['PG']
    collection = []
    dict = {}
    dict['new_job_rate']= []
    # test_types = ['SJF', 'Packer', 'Random']
    render = False
    pa = parameters.Parameters()
    pa.simu_len = 50
    pa.episode_max_length = 100
    pa.num_ex = 10
    pa.num_nw = 10
    pa.num_seq_per_batch = 20
    all_discount_rews = {}
    jobs_slow_down = {}
    work_complete = {}
    work_remain = {}
    job_len_remain = {}
    num_job_remain = {}
    job_remain_delay = {}

    # for [[DeepRM], [SJF], [Packer], [Random]]
    job_slowdown = [[], [], [], []]
    job_completion_time = [[], [], [], []]
    for new_job_rate in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] :
        for test_type in test_types:
            all_discount_rews[test_type] = []
            jobs_slow_down[test_type] = []
            work_complete[test_type] = []
            work_remain[test_type] = []
            job_len_remain[test_type] = []
            num_job_remain[test_type] = []
            job_remain_delay[test_type] = []

        pa.new_job_rate = new_job_rate
        pg_resume = 'data/pg_re_rate_' + str(new_job_rate) + '_simu_len_' + str(
            pa.simu_len) + '_num_seq_per_batch_' + str(pa.num_seq_per_batch) + '_ex_10' + '_nw_' + str(pa.num_nw) + '_950.pkl'
        env = environment.Env(
            pa, render=False, repre='image', end='all_done')
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
                work_complete[test_type].append(
                    np.sum(job_len[finished_idx] *
                           job_total_size[finished_idx])
                )
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

        slowdown, ctime = accumulate_results(
            test_types, jobs_slow_down, work_complete)
        # Done for the specified job arrival rate
        for i in range(len(test_types)):
            job_slowdown[i].append(slowdown[i])
            job_completion_time[i].append(ctime[i])
            if test_types[i] == 'PG':
                dict['new_job_rate'].append(pa.new_job_rate)

    # Plot figure
    fig = plt.figure()
    load = [10, 30, 50, 70, 90, 110, 130, 150, 170, 190] 
    colors = ['r', 'g', 'b', 'c']
    markers = ["o", "1", "s", "x"]
    for i in range(len(test_types)):
        plt.plot(load, job_slowdown[i],
                 color=colors[i], label=test_types[i],
                 marker=markers[i])
        if test_types[i] == 'PG':
            dict['job_slowdown'] = job_slowdown[i]
            dict['job_completion_time'] = job_completion_time[i]
            #collection.append(dict)
    plt.xlabel("Cluster Load(Percentage)")
    plt.ylabel("Average Job Slowdown")
    plt.title("Job Slowdown at different levels of load")
    plt.legend()
    plt.grid()
    plt.show()
    fig.savefig("LoadVariation.png")
    data_json = json.dumps(dict)
    with open('loadresults.json', 'w') as f:
        json.dump(data_json, f)
    # f = open("loadresults.txt", "w")
    # f.write(collection)
    # f.close()
    print("Done")
