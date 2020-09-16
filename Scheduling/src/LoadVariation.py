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
    Job_arrival_rate_slowdown_sd = []
    Job_arrival_rate_slowdown_ct = []
    Job_arrival_rate_reward_sd = []
    Job_arrival_rate_reward_ct = []
    Job_arrival_rate_completion_time_sd = []
    Job_arrival_rate_completion_time_ct = []
    Job_arrival_rate = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
    objectives = [pa.objective_slowdown, pa.objective_random]
    for objective in objectives:
        pa.objective = objective
        Job_arrival_rate_slowdown = []
        Job_arrival_rate_reward = []
        Job_arrival_rate_completion_time = []
        for rate in Job_arrival_rate:
            pa.new_job_rate = rate / 100
            job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
            env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                                job_sequence_size=job_sequence_size)
            env1 = make_vec_env(lambda: env, n_envs=1)
            model = None
            if pa.objective == pa.objective_slowdown:
                model1 = A2C.load("job_scheduling_A2C_Slowdown", env1)
                model = model1
            elif pa.objective == pa.objective_Ctime:
                model2 = A2C.load("job_scheduling_A2C_Ctime", env1)
                model = model2
            elif pa.objective == pa.objective_random: 
                model = None
            episode_a2c, reward_a2c, slowdown_a2c, completion_time_a2c = Script.run_episodes(model, pa, env, job_sequence_len)

            mean_slowdown = mean(slowdown_a2c)
            mean_reward = mean(reward_a2c)
            mean_completion_time = mean(completion_time_a2c)
            Job_arrival_rate_slowdown.append(mean_slowdown)
            Job_arrival_rate_reward.append(mean_reward)
            Job_arrival_rate_completion_time.append(mean_completion_time)

        if pa.objective == pa.objective_slowdown:
            Job_arrival_rate_slowdown_sd = Job_arrival_rate_slowdown
            Job_arrival_rate_reward_sd = Job_arrival_rate_reward
            Job_arrival_rate_completion_time_sd = Job_arrival_rate_completion_time

        elif pa.objective == pa.objective_Ctime:
            Job_arrival_rate_slowdown_ct = Job_arrival_rate_slowdown
            Job_arrival_rate_reward_ct = Job_arrival_rate_reward
            Job_arrival_rate_completion_time_ct = Job_arrival_rate_completion_time

        elif pa.objective == pa.objective_random:
            Job_arrival_rate_slowdown_random = Job_arrival_rate_slowdown
            Job_arrival_rate_reward_random = Job_arrival_rate_reward
            Job_arrival_rate_completion_time_random = Job_arrival_rate_completion_time

    fig = plt.figure()
    plt.plot(Job_arrival_rate, Job_arrival_rate_slowdown_sd, color='blue', label='A2C Slowdown agent')
    plt.plot(Job_arrival_rate, Job_arrival_rate_slowdown_random, color='yellow', label='Random agent')
    plt.xlabel("Cluster Load(Percentage)")
    plt.ylabel("Average Slowdown")
    plt.title("Job_arrival_rate_slowdown")
    plt.legend()
    plt.grid()
    plt.show()
    fig.savefig('Job_arrival_rate_Slowdown.png')