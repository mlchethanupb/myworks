import Deeprm
import operator
from Deeprm import Env
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

if __name__ == '__main__' :
    print("Stable baseline main method")
    override_misprediction = True
    pa = parameters.Parameters()
    job_sequence_len , job_sequence_size = job_distribution.generate_sequence_work(pa, seed=42)
    env = Env(pa , job_sequence_len = job_sequence_len, job_sequence_size = job_sequence_size)
    Job_len = Rew = timesteps = misprediction_counter = 0
    for i in range(len(job_sequence_len)):
        Job_len = Job_len + job_sequence_len[i]
    print("job_sequence_len", job_sequence_len,"job_sequence_size", job_sequence_size)
    model = DQN("MlpPolicy", env, verbose=1)
    #model.learn(total_timesteps = 25000)
    model.save("job_scheduling")
    del model # remove to demonstrate saving and loading
    model = DQN.load("job_scheduling",env)
    obs = env.reset()
    done = False
    action_list = []
    while not done:
        action, _states = model.predict(obs, deterministic=True)
        # logic for handling job starvation and mispredicted action overriding
        if override_misprediction and ((action != 5 and all(s.all() == 0 for s in obs[action+1]))\
           or (action == 5 and all(s.all() == 10 for s in obs[0]))):
            for i in range(env.pa.job_wait_queue) :
                if env.job_slot.slot[i] is not None:
                    action = i
                    misprediction_counter = misprediction_counter + 1
                    break
        obs , reward , done , info = env.step(action)

        if action not in action_list:
            action_list.append(action)
        timesteps = timesteps + 1
        print("Time step :",timesteps, ",Action :",action,",Reward : ",reward)

        if timesteps == pa.episode_max_length:
            done = True
        Rew = Rew + reward

    Job_slow_down = timesteps / Job_len
    AverageReward = Rew / timesteps
    misprediction_percentage = misprediction_counter / timesteps
    print("Job_len :", Job_len,",Average Reward :", AverageReward,",Job_slow_down :", Job_slow_down,",misprediction_percentage :",misprediction_percentage)
    for i in env.job_slot.slot :
        if i is not None:
            print("job pending",i,i.len, i.resorce_requirement)
  
    print("actions taken:", action_list)
