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


if __name__ == '__main__':
    pa = parameters.Parameters()
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)

    ################################################################################################
    # Prediction using trained DQN model
    # env = DeepRMEnv.Env(pa, job_sequence_len=job_sequence_len,
    #                     job_sequence_size=job_sequence_size)
    # model1 = DQN.load("job_scheduling_DQN", env)
    # action_list = []
    # episode_dqn = []
    # reward_dqn = []
    # print("-------------------------------------------------------------------")
    # print("Scheduling using trained DQN agent")
    # for episode in range(pa.num_episode):
    #     cumulated_episode_reward = 0
    #     obs = env.reset()
    #     done = False
    #     while not done:
    #         action, _states = model1.predict(obs, deterministic=False)
    #         obs, reward, done, info = env.step(action)
    #         if done == True:
    #             # print("All jobs scheduled")
    #             break
    #         if reward != 0:
    #             action_list.append(action)
    #             # print("Timestep: ", env.curr_time, "Action: ",
    #             #       action_list, "Reward: ", reward)
    #             action_list = []
    #             cumulated_episode_reward += reward
    #             if env.curr_time == pa.episode_max_length:
    #                 done = True
    #         elif reward == 0 and done != True:
    #             action_list.append(action)
    #     episode_dqn.append(episode+1)
    #     reward_dqn.append(cumulated_episode_reward)
    ################################################################################################
    # env = Deeprm.Env(pa, job_sequence_len=job_sequence_len,
    #                     job_sequence_size=job_sequence_size)
    # env1 = make_vec_env(lambda: env, n_envs=1)
    # model2 = PPO2.load("job_scheduling_PPO2", env1)
    # action_list = []
    # episode_ppo2 = []
    # reward_ppo2 = []
    # print("-------------------------------------------------------------------")
    # print("Scheduling using trained PPO2 agent")
    # for episode in range(pa.num_episode):
    #     cumulated_episode_reward = 0
    #     obs = env.reset()
    #     done = False
    #     while not done:
    #         action, _states = model2.predict(obs, deterministic=False)
    #         obs, reward, done, info = env.step(action)
            
    #         if done == True:
    #             # print("All jobs scheduled")
    #             break
    #         if reward != 0:
    #             # for i in range(len(action)):
    #             #     if action[i] !=0:
    #             action_list.append(action)
    #             print("Timestep: ", env.curr_time, "Action: ",
    #                   action, "Reward: ", reward)
    #             action_list = []
    #             cumulated_episode_reward += reward
    #             if env.curr_time == pa.episode_max_length:
    #                 done = True
    #         elif reward == 0 and done != True:
    #             action_list.append(action)
    #     episode_ppo2.append(episode+1)
    #     reward_ppo2.append(cumulated_episode_reward)
    #    print(obs)
    ################################################################################################

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

    ################################################################################################

    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                        job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=1)
    obs = env.reset()
    done = False
    action_list = []
    episode_random = []
    reward_random = []
    slowdown_random = []
    print("-------------------------------------------------------------------")
    print("Scheduling using trained Random agent")
    for episode in range(pa.num_episode):
        cumulated_episode_reward = 0
        cumulated_job_slowdown = 0
        obs = env.reset()
        done = False
        while not done:
            action = Randomscheduler.rand_key(len(env.job_slot.slot))
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
        episode_random.append(episode+1)
        reward_random.append(cumulated_episode_reward)
        slowdown_random.append(cumulated_job_slowdown / len(job_sequence_len))

fig = plt.figure()
# plt.plot(episode_dqn, reward_dqn, color='skyblue', label='DQN agent')
# plt.plot(episode_ppo2, reward_ppo2,  color='red', label='PPO2 agent')
plt.plot(episode_a2c, reward_a2c, color='olive', label='A2C agent')
plt.plot(episode_random, reward_random, color='black', label='Random agent')
plt.xlabel("Number of episodes")
plt.ylabel("Reward per episodes")
plt.legend()
plt.grid()
plt.show()
plt.savefig('Reward.png')

fig2 = plt.figure()
# plt.plot(episode_dqn, slowdown_dqn, color='skyblue', label='DQN agent')
# plt.plot(episode_ppo2, slowdown_ppo2,  color='red', label='PPO2 agent')
plt.plot(episode_a2c, slowdown_a2c, color='olive', label='A2C agent')
plt.plot(episode_random, slowdown_random, color='black', label='Random agent')
plt.xlabel("Number of episodes")
plt.ylabel("Average Job Slowdown per episodes")
plt.title("Average Job Slowdown per episodes for Stable Baselines")
plt.legend()
plt.grid()
plt.show()
fig2.savefig('slowdown.png')