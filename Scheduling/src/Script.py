import Deeprm
import Deeprm1
import operator
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.cbook import flatten
import parameters
import job_distribution
import argparse
from random import sample
import os
import gym
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines import PPO2
from stable_baselines import DQN
from stable_baselines.common.env_checker import check_env
from gym import spaces
import pandas as pd
from stable_baselines.common import make_vec_env
import Randomscheduler
from statistics import mean 

def run_episodes(model, pa, env, job_sequence_len):
    episode_list = []
    reward_list = []
    slowdown_list = []
    completion_time_list = []
    for episode in range(pa.num_episode):
        cumulated_episode_reward = 0
        cumulated_job_slowdown = []
        cumulated_job_completion_time = []
        obs = env.reset()
        done = False
        while not done:
            if model != None:
                action, _states = model.predict(obs, deterministic=False)
            else:
                action = Randomscheduler.rand_key(pa.job_wait_queue)

            obs, reward, done, info = env.step(action)

            if 'Completion Time' in info.keys() and  info['Completion Time'] != None:
                cumulated_job_completion_time.append(info['Completion Time'])
            if 'Job Slowdown' in info.keys() and info['Job Slowdown'] != None:
                cumulated_job_slowdown.append(info['Job Slowdown'])

            if done == True:
                break

            if reward != 0:
                print("Timestep: ", env.curr_time, "Action: ",action, "Reward: ", reward)
                cumulated_episode_reward += reward
                if env.curr_time == pa.episode_max_length:
                    done = True
        cumulated_job_completion_time = list(flatten(cumulated_job_completion_time))
        cumulated_job_slowdown = list(flatten(cumulated_job_slowdown))
        episode_list.append(episode+1)
        reward_list.append(cumulated_episode_reward)
        completion_time_list.append(mean(cumulated_job_completion_time))
        slowdown_list.append(mean(cumulated_job_slowdown))

    return episode_list, reward_list, slowdown_list, completion_time_list

if __name__ == '__main__':
    pa = parameters.Parameters()
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                        job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=1)

    ################################################################################################

    pa.objective = pa.objective_slowdown
    model1 = A2C.load("job_scheduling_A2C_Slowdown", env1)
    obs = env.reset()
    done = False
    print("-------------------------------------------------------------------")
    print("Scheduling using trained A2C agent for slowdown")
    episode_a2c_sd, reward_a2c_sd, slowdown_a2c_sd, completion_time_a2c_sd = run_episodes(model1, pa, env, job_sequence_len)

    ################################################################################################
    
    pa.objective = pa.objective_Ctime
    model2 = A2C.load("job_scheduling_A2C_Ctime", env1)
    obs = env.reset()
    done = False
    print("-------------------------------------------------------------------")
    print("Scheduling using trained A2C agent for Ctime")
    episode_a2c_ct, reward_a2c_ct, slowdown_a2c_ct, completion_time_a2c_ct = run_episodes(model2, pa, env, job_sequence_len)

    ################################################################################################

    model3 = None
    obs = env.reset()
    done = False
    print("-------------------------------------------------------------------")
    print("Scheduling using Random agent")
    episode_random, reward_random, slowdown_random, completion_time_random = run_episodes(model3, pa, env, job_sequence_len)
    
    ################################################################################################
    
    # data to plot
    n_groups = 2
    a2c_sd = (mean(slowdown_a2c_sd), mean(completion_time_a2c_sd))
    a2c_ct = (mean(slowdown_a2c_ct), mean(completion_time_a2c_ct))
    random = (mean(slowdown_random), mean(completion_time_random))

    # create plot
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.1
    opacity = 0.8

    rects1 = plt.bar(index, a2c_sd, bar_width,
    alpha=opacity,
    color='blue',
    label='A2C Slowdown agent')

    rects2 = plt.bar(index + bar_width, a2c_ct, bar_width,
    alpha=opacity,
    color='red',
    label='A2C CTime agent')

    rects3 = plt.bar(index + 2*bar_width, random, bar_width,
    alpha=opacity,
    color='yellow',
    label='Random agent')

    plt.xlabel('Performance metrics')
    plt.ylabel('Time')
    plt.title('Performance for different objectives')
    plt.xticks(index + bar_width, ('Slowdown', 'Completion time'))
    plt.legend((rects1[0], rects2[0], rects3[0]), ('A2C Slowdown agent', 'A2C CTime agent', 'Random agent'))
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width()/2., height, '%.2f' % height, ha='center', va='bottom')

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    plt.tight_layout()
    plt.show()
    fig.savefig('Performance.png')

    print(a2c_sd,a2c_ct)