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
    pa = parameters.Parameters()
    job_sequence_len , job_sequence_size = job_distribution.generate_sequence_work(pa, seed=42)
    env = Env(pa , job_sequence_len, job_sequence_size)
    print("job_sequence_len", job_sequence_len,"job_sequence_size", job_sequence_size)
    model = DQN("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=25000)
    model.save("job_scheduling")
    del model # remove to demonstrate saving and loading
    model = DQN.load("job_scheduling",env)
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

        if iterations == pa.episode_max_length:
            done = True
        Rew = Rew + reward

    print("Average Reward:",Rew / iterations)
    for i in env.job_slot.slot :
        if i is not None:
            print("job pending",i,i.len, i.resorce_requirement)
  
    print("actions taken:",action_list)
