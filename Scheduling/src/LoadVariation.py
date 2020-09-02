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
from statistics import mean 


if __name__ == '__main__':
    pa = parameters.Parameters()
    Job_arrival_rate = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
    Job_arrival_rate_slowdown = []
    Job_arrival_rate_reward = []
    for rate in Job_arrival_rate:
        pa.new_job_rate = rate
        job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
        env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                            job_sequence_size=job_sequence_size)
        env1 = make_vec_env(lambda: env, n_envs=1)
        model3 = A2C.load("job_scheduling_A2C", env1)
        obs = env.reset()
        done = False
        action_list = []
        episode_a2c = []
        reward_a2c = []
        slowdown_a2c = []
        print("-------------------------------------------------------------------")
        print("Scheduling using trained A2C agent")
        for episode in range(pa.num_episode):
            cumulated_episode_reward = 0
            cumulated_job_slowdown = 0
            obs = env.reset()
            done = False
            while not done:
                action, _states = model3.predict(obs, deterministic=False)
                obs, reward, done, info = env.step(action)
                if bool(info) == True:
                    cumulated_job_slowdown += info['Job Slowdown']
                if done == True:
                    # print("All jobs scheduled")
                    break
                
                if reward != 0:
                    action_list.append(action)
                    # action_list = []
                    print("Timestep: ", env.curr_time, "Action: ",
                        action, "Reward: ", reward)
                    cumulated_episode_reward += reward
                    if env.curr_time == pa.episode_max_length:
                        done = True
                # elif reward == 0 and done != True:
                #     action_list.append(action)
            episode_a2c.append(episode+1)
            reward_a2c.append(cumulated_episode_reward)
            slowdown_a2c.append(cumulated_job_slowdown / len(job_sequence_len))

        mean_slowdown = mean(slowdown_a2c)
        mean_reward = mean(reward_a2c)
        Job_arrival_rate_slowdown.append(mean_slowdown)
        Job_arrival_rate_reward.append(mean_reward)



fig = plt.figure()
# plt.plot(episode_dqn, reward_dqn, color='skyblue', label='DQN agent')
# plt.plot(episode_ppo2, reward_ppo2,  color='red', label='PPO2 agent')
plt.plot(Job_arrival_rate, Job_arrival_rate_reward, color='olive', label='A2C agent')
plt.xlabel("Job_arrival_rate")
plt.ylabel("Job_arrival_rate_reward")
plt.legend()
plt.grid()
plt.show()
plt.savefig('Job_arrival_rate_reward.png')

fig2 = plt.figure()
# plt.plot(episode_dqn, slowdown_dqn, color='skyblue', label='DQN agent')
# plt.plot(episode_ppo2, slowdown_ppo2,  color='red', label='PPO2 agent')
plt.plot(Job_arrival_rate, Job_arrival_rate_slowdown, color='olive', label='A2C agent')
plt.xlabel("Job_arrival_rate")
plt.ylabel("Job_arrival_rate_slowdown")
plt.title("Job_arrival_rate_slowdown")
plt.legend()
plt.grid()
plt.show()
fig2.savefig('Job_arrival_rate_slowdown.png')