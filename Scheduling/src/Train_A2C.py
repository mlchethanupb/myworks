import tensorflow
import pandas as pd
from gym import spaces
from stable_baselines.common.env_checker import check_env
from stable_baselines.common import make_vec_env
from stable_baselines import DQN
from stable_baselines import PPO2
from stable_baselines import A2C
from stable_baselines.deepq.policies import MlpPolicy
import gym
import os
from random import sample
import argparse
import job_distribution
import parameters
import matplotlib.pyplot as plt
import math
import numpy as np
import operator
import Deeprm1
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

if __name__ == '__main__':
    print("------------------------------------------------------------------")
    override_misprediction = False
    pa = parameters.Parameters()
    pa.objective = pa.objective_slowdown
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len,
                        job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=1)

    # Training the A2C agent
    env.reset()
    model1 = A2C("MlpPolicy", env1, verbose=1,
                 tensorboard_log='/home/aicon/kunalS/workspace/tensor_A2C/')
    model1.learn(total_timesteps=25000)
    model1.save("job_scheduling_A2C_Slowdown")

    pa.objective = pa.objective_Ctime
    env.reset()
    model2 = A2C("MlpPolicy", env1, verbose=1,
                 tensorboard_log='/home/aicon/kunalS/workspace/tensor_A2C/')
    model2.learn(total_timesteps=25000)
    model2.save("job_scheduling_A2C_Ctime")
    print("Done training using A2C")
