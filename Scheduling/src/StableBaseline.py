import Deeprm
from Deeprm import Env
import numpy as np
import math
import matplotlib.pyplot as plt
import parameters
import argparse
from random import sample
import os
from networkx import nx
import gym
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines import PPO2
from stable_baselines.common.env_checker import check_env
from gym import spaces

if __name__ == '__main__' :
    print("Stable baseline main method")
    pa = parameters.Parameters()
    pa.job_wait_queue = 5
    pa.simu_len = 50 
    pa.num_ex = 10
    pa.new_job_rate = 1
    job_sequence_len = []
    job_sequence_size = []
    # for i in range(1000) :
    #     job_sequence_len.append(np.random.randint(1 , pa.time_horizon))
   
    # # Creating the resource requirement for jobs
    # for i in range(1000):
    #     cpu_req = np.random.randint(1, pa.max_job_size)
    #     mem_req = np.random.randint(1, pa.max_job_size)
    #     job_sequence_size.append([cpu_req,mem_req])
    job_sequence_len = [1, 15, 6, 18, 14, 3, 12, 15, 1, 15, 7, 2, 2, 1, 16, 7, 9, 16, 15, 4, 17, 15, 11, 8, 1, 7, 1, 8, 1, 12, 1, 11, 13, 15, 9, 16, 16, 9, 4, 4, 11, 19, 13, 12, 2, 18, 5, 9, 15, 19, 5, 16, 7, 2, 18, 14, 10, 12, 14, 13, 7, 9, 17, 1, 2, 9, 3, 13, 9, 17, 8, 15, 6, 1, 7, 12, 1, 16, 11, 13, 19, 15, 15, 8, 6, 13, 7, 1, 1, 5, 5, 15, 13, 5, 14, 17, 1, 8, 3, 5]
    job_sequence_size = [[3, 9], [5, 8], [4, 9], [9, 2], [2, 4], [7, 6], [6, 2], [8, 9], [5, 9], [2, 8], [8, 1], [7, 9], [3, 2], [5, 6], [6, 7], [9, 8], [3, 8], [6, 3], [7, 7], [7, 4], [3, 8], [1, 6], [6, 7], [2, 2], [7, 8], [5, 8], [6, 2], [4, 7], [5, 9], [5, 8], [7, 5], [1, 7], [8, 7], [6, 5], [9, 5], [7, 1], [7, 7], [1, 3], [1, 1], [7, 1], [5, 2], [9, 2], [8, 2], [2, 1], [2, 8], [9, 3], [9, 4], [4, 7], [2, 1], [3, 5], [8, 4], [4, 9], [8, 4], [4, 8], [7, 2], [9, 2], [6, 6], [7, 5], [6, 5], [9, 8], [8, 3], [7, 1], [4, 7], [9, 4], [8, 2], [7, 9], [9, 4], [4, 3], [4, 3], [5, 6], [4, 6], [1, 2], [6, 1], [6, 1], [4, 7], [6, 9], [2, 3], [4, 8], [1, 3], [6, 3], [1, 4], [9, 4], [2, 1], [7, 7], [6, 8], [3, 1], [2, 1], [8, 1], [5, 1], [7, 3], [2, 7], [5, 4], [9, 3], [1, 5], [6, 1], [3, 6], [1, 6], [9, 2], [4, 2], [4, 7]]
    env = Env(pa , job_sequence_len, job_sequence_size)
    model = PPO2("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=100)
    obs = env.reset()
    for i in range(100):
        action, _states = model.predict(obs[0], deterministic=True)
        obs , reward , done , info = env.step(action)
        print("Iteration :",i, ",Action :", action,",Reward : ", reward)

