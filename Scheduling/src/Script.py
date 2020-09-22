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

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height, '%.2f' % height, ha='center', va='bottom')

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
    models = [pa.A2C_Slowdown, pa.A2C_Ctime, pa.random, pa.PPO2]
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                        job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=4)

    episodes = []
    rewards = []
    slowdowns = []
    ctimes = []
    
    for i in range(len(models)):
        pa.objective = models[i]
        save_path = models[i]['save_path']
        model = None
        if save_path != None:
            model = models[i]['agent'].load(save_path, env1)
        episode, reward, slowdown, completion_time = run_episodes(model, pa, env, job_sequence_len)
        episodes.append(episode)
        rewards.append(reward)
        slowdowns.append(slowdown)
        ctimes.append(completion_time)

    # data to plot
    n_groups = 2
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.1
    opacity = 0.8
    agent_plots = []

    for i in range(len(models)):
        mean_values = (mean(slowdowns[i]), mean(ctimes[i]))
        deviation = (np.std(slowdowns[i]), np.std(ctimes[i]))
        agent_plot = plt.bar(index + i*bar_width, mean_values, bar_width, yerr=deviation, ecolor='black', capsize=10,
         alpha=opacity, color=models[i]['color'], label=models[i]['title'])
        agent_plots.append(agent_plot)

    for agent_plot in agent_plots:
        autolabel(agent_plot)

    plt.xlabel('Performance metrics')
    plt.ylabel('Average Job Slowdown')
    plt.title('Performance for different objectives')
    plt.xticks(index + bar_width, ('Slowdown', 'Completion time'))
    plt.legend()
    ax2 = ax.twinx()
    plt.ylabel('Average Job Completion Time')
    ax2.set_ylim(ax.get_ylim())
    plt.tight_layout()
    plt.show()
    fig.savefig('Performance.png')
