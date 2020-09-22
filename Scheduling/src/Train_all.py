import os

import gym
import numpy as np
import matplotlib.pyplot as plt

from stable_baselines import DDPG
from stable_baselines.ddpg.policies import LnMlpPolicy
from stable_baselines import results_plotter
from stable_baselines.bench import Monitor
from stable_baselines.results_plotter import load_results, ts2xy
from stable_baselines.common.noise import AdaptiveParamNoiseSpec
from stable_baselines.common.callbacks import BaseCallback
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
import random
import tensorflow as tf
import pathlib
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).

    :param check_freq: (int)
    :param log_dir: (str) Path to the folder where the model will be saved.
      It must contains the file created by the ``Monitor`` wrapper.
    :param verbose: (int)
    """
    def __init__(self, check_freq: int, log_dir: str, save_path: str, verbose=1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.save_path = save_path
        self.best_mean_reward = -np.inf

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:

          # Retrieve training reward
          x, y = ts2xy(load_results(self.log_dir), 'timesteps')
          if len(x) > 0:
              # Mean training reward over the last 100 episodes
              mean_reward = np.mean(y[-100:])
              if self.verbose > 0:
                print("Num timesteps: {}".format(self.num_timesteps))
                print("Best mean reward: {:.2f} - Last mean reward per episode: {:.2f}".format(self.best_mean_reward, mean_reward))

              # New best model, you could save the agent here
              if mean_reward > self.best_mean_reward:
                  self.best_mean_reward = mean_reward
                  # Example for saving best model
                  if self.verbose > 0:
                    print("Saving new best model to {}".format(self.save_path))
                  self.model.save(self.save_path)

        return True

if __name__ == '__main__':
  # Create log dir
  pa = parameters.Parameters()
  models = [pa.A2C_Ctime, pa.A2C_Slowdown, pa.PPO2]
  x_readings = []
  y_readings = []

  for i in range(len(models)):
    pa.objective = models[i]
    save_path = models[i]['save_path']
    log_dir = models[i]['log_dir']
    os.makedirs(log_dir, exist_ok=True)

    # Create and wrap the environment
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len, job_sequence_size=job_sequence_size)
    env = Monitor(env, log_dir)
    env1 = make_vec_env(lambda: env, n_envs=4)

    # Add some param noise for exploration
    param_noise = AdaptiveParamNoiseSpec(initial_stddev=0.1, desired_action_stddev=0.1)
    # Because we use parameter noise, we should use a MlpPolicy with layer normalization
    model = models[i]['agent']("MlpPolicy", env1, verbose=1, tensorboard_log=log_dir, learning_rate=0.001)

    # Create the callback: check every 1000 steps
    callback = SaveOnBestTrainingRewardCallback(check_freq=1000, log_dir=log_dir, save_path=save_path)
    # Train the agent
    time_steps = 1e5
    model.learn(total_timesteps=int(time_steps), callback=callback)

    results_plotter.plot_results([log_dir], time_steps, results_plotter.X_TIMESTEPS, models[i]['title'])
    print([log_dir], time_steps, results_plotter.X_TIMESTEPS)
    x, y = ts2xy(load_results(log_dir), 'timesteps')
    x_readings.append(x)
    y_readings.append(y)

  fig = plt.figure()
  for i in range(len(models)):
    plt.plot(x_readings[i], y_readings[i], color=models[i]['color'], label=models[i]['title'])
  plt.xlabel("Time Steps")
  plt.ylabel("Rewards")
  plt.title('Learning curve')
  plt.legend()
  plt.grid()
  plt.show()
  fig.savefig('learning_curve')