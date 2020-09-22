import Deeprm
import Deeprm1
import operator
import numpy as np
import math
import matplotlib.pyplot as plt
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
import Script
from statistics import mean 

if __name__ == '__main__':
    pa = parameters.Parameters()
    models = [pa.A2C_Slowdown, pa.A2C_Ctime, pa.random, pa.PPO2]
    y_slowdown_readings = []
    Job_arrival_rate = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
    for i in range(len(models)):
        pa.objective = models[i]
        save_path = models[i]['save_path']
        Job_arrival_rate_slowdown = []
        Job_arrival_rate_reward = []
        Job_arrival_rate_completion_time = []
        for rate in Job_arrival_rate:
            pa.new_job_rate = rate / 100
            job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
            env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                                job_sequence_size=job_sequence_size)
            env1 = make_vec_env(lambda: env, n_envs=4)
            model = None
            if save_path != None:
                model = models[i]['agent'].load(save_path, env1)
            episode, reward, slowdown, completion_time = Script.run_episodes(model, pa, env, job_sequence_len)

            mean_slowdown = mean(slowdown)
            mean_reward = mean(reward)
            mean_completion_time = mean(completion_time)
            Job_arrival_rate_slowdown.append(mean_slowdown)
            Job_arrival_rate_reward.append(mean_reward)
            Job_arrival_rate_completion_time.append(mean_completion_time)

        y_slowdown_readings.append(Job_arrival_rate_slowdown)

    fig = plt.figure()
    for i in range(len(models)):
        plt.plot(Job_arrival_rate, y_slowdown_readings[i], color=models[i]['color'], label=models[i]['title'])
    plt.xlabel("Cluster Load(Percentage)")
    plt.ylabel("Average Slowdown")
    plt.title("Job_arrival_rate_slowdown")
    plt.legend()
    plt.grid()
    plt.show()
    fig.savefig('Job_arrival_rate_Slowdown.png')