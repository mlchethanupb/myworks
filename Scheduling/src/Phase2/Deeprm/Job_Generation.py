from DeepRM.envs.DeepRMEnv import DeepEnv
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
import randomAgent
import SJF
import packer
import warnings
import random
from statistics import mean
import Otheragents
from datetime import datetime
import matplotlib.cm as cm
# warnings.simplefilter(action='ignore', category=FutureWarning)
# warnings.simplefilter(action='ignore', category=Warning)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

if __name__ == '__main__':
    # Test Sjf authors code
    pa = parameters.Parameters()
    pa.simu_len = 50
    pa.num_ex = 10
    pa.num_nw = 10
    pa.num_seq_per_batch = 20
    for new_job_rate in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]:
        pa.new_job_rate = new_job_rate
        job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(
            pa, 42)
        print('The number of nonzero elements for arrival rate',
              pa.new_job_rate, 'is :', np.count_nonzero(job_sequence_len[0]))

        fig = plt.figure()
        job_sequence_len_plot = []
        jobs = [i for i in range(pa.simu_len * pa.num_ex)]
        index_start = 0
        index_finish = pa.simu_len

        non_zero_list = []
        count_index = [l for l in range(pa.num_ex)]
        colors = cm.rainbow(np.linspace(0, 1, pa.num_ex))
        for j in range(pa.num_ex):
            jobs = [index for index in range(index_start, index_finish)]
            plt.bar(jobs, job_sequence_len[j], color=colors[j], width=5)
            index_start = index_finish
            index_finish = index_finish + pa.simu_len
            non_zero_list.append(np.count_nonzero(job_sequence_len[j]))

            # job_sequence_len_plot.extend(job_sequence_len[j])
            # jobs = [i for i in range(len(job_sequence_len[j]))]

        # plt.bar(jobs, job_sequence_len_plot)
        # plt.title('Mean load ' + np.mean(workload))
        plt.xlabel('Jobs')
        plt.ylabel('Job Length')
        plt.title('Job Distribution')
        fig.savefig('workspace/Discrete/output/Job_distribution/script_jobs_' + str(pa.new_job_rate)+'_' + str(pa.simu_len)+'_' + str(datetime.today()) + '_' + str(datetime.time(datetime.now())) +
                    pa.figure_extension)
        print("Figure plotted: workspace/Discrete/output/Job_distribution/script_jobs_",
              str(pa.new_job_rate), '_', str(pa.simu_len), '_', str(datetime.time(datetime.now())))

        fig = plt.figure()
        plt.bar(count_index, non_zero_list)
        plt.xlabel('Sequence')
        plt.ylabel('Non zero length jobs')
        plt.title('Number of non zero length jobs in each sequence')
        fig.savefig('workspace/Discrete/output/Job_distribution/script_nonzero_' + str(pa.new_job_rate)+'_' + str(pa.simu_len)+'_' + str(datetime.today()) + '_' + str(datetime.time(datetime.now())) +
                    pa.figure_extension)
        print("Figure plotted: workspace/Discrete/output/Job_distribution/script_nonzero_",
              str(pa.new_job_rate), '_', str(pa.simu_len), '_', str(datetime.time(datetime.now())))

        env = gym.make('deeprm-v0', pa=pa, job_sequence_len=job_sequence_len,
                       job_sequence_size=job_sequence_size)
        done = False

        models = ['SJF', 'Packer']

        job_slowdown = []
        job_comption_time = []
        job_reward = []
        episode_list = []
        for model in models:
            cumulated_job_slowdown = []
            cumulated_reward = 0
            cumulated_completion_time = []
            ob = env.reset()
            done = False
            info = {}
            while not done:
                if model == 'SJF':
                    action = Otheragents.get_sjf_action(
                        env.machine, env.job_slot)
                else:
                    action = Otheragents.get_packer_action(
                        env.machine, env.job_slot)
                ob, reward, done, info = env.step(action)
                if 'Job Slowdown' in info.keys() and 'Completion Time' in info.keys():
                    cumulated_job_slowdown.append(info['Job Slowdown'])
                    cumulated_completion_time.append(info['Completion Time'])
                if reward != 0:
                    cumulated_reward += reward

            job_slowdown.append(np.mean(cumulated_job_slowdown))
            job_comption_time.append(np.mean(cumulated_completion_time))
            job_reward.append(cumulated_reward)

        fig = plt.figure()
        plt.bar(models, job_slowdown, color=['r', 'y'])
        plt.xlabel('Heuristics')
        plt.ylabel('Average job slowdown')
        plt.title('Job Slowdown')
        fig.savefig('workspace/Discrete/output/Job_distribution/script_slowdown_' + str(pa.new_job_rate)+'_' + str(pa.simu_len)+'_' + str(pa.simu_len)+'_' + str(datetime.time(datetime.now())) +
                    pa.figure_extension)
        print("Figure plotted: workspace/Discrete/output/Job_distribution/script_slowdown_",
              str(pa.new_job_rate), '_', str(pa.simu_len), '_', str(datetime.time(datetime.now())))
    print("Done")
