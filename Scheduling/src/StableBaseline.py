import Deeprm
import operator
from Deeprm import Env
import numpy as np
import math
import matplotlib.pyplot as plt
import parameters
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

if __name__ == '__main__' :
    print("Stable baseline main method")
    #dataframe = pd.read_csv("/home/aicon/kunalS/workspace/csvTest/container_usage.csv")
    #print(dataframe.head(10)) 
    #np_array = dataframe.to_numpy()
    #np_array1 = np.asarray(np_array, dtype=int)

    pa = parameters.Parameters()
    pa.job_wait_queue = 5
    pa.simu_len = 10
    pa.num_ex = 10
    pa.new_job_rate = 1
    env = Env(pa , job_sequence_len = [3 , 1 , 1 , 1 , 3 , 1 , 2 , 3 , 4 , 5] ,
	          job_sequence_size = [[9 , 2] , [9 , 1] , [2 , 8] , [8 , 2] , [7 , 1] , [2 , 10] , [1 , 10] , [2 , 7] ,
	                               [4 , 8] , [2 , 9]])
    check_env(env,warn=True)
    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=25000)
    model.save("job_scheduling")
    del model # remove to demonstrate saving and loading
    model = DQN.load("job_scheduling")
    obs = env.reset()
    Rew = 0
    iterations = 0
    done = False
    action_list = []

    while not done:
        action, _states = model.predict(obs, deterministic=True)
        obs , reward , done , info = env.step(action)
        if action not in action_list:
            action_list.append(action)
        iterations = iterations + 1
        print("Iteration or Time step :",iterations, ",Action :",action,",Reward : ",reward)

        if iterations == 1000:
            done = True
        Rew = Rew + reward

    print("Average Reward:",Rew / iterations)
    for i in env.job_slot.slot :
        if i is not None:
            print("job pending",i,i.len, i.resorce_requirement)
  
    print("actions taken:",action_list)
