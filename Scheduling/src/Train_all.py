import os
import gym
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines.common.noise import AdaptiveParamNoiseSpec
from stable_baselines.common.callbacks import BaseCallback
import tensorflow
from gym import spaces
from stable_baselines.common.env_checker import check_env
from stable_baselines.common import make_vec_env
from stable_baselines import PPO2, A2C
import argparse
import job_distribution
import parameters
import matplotlib.pyplot as plt
import math
import numpy as np
import operator
import Deeprm1
import Script
import warnings
import random
from statistics import mean 
import tensorflow as tf
import pathlib
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).
    :param check_freq: (int)
    :param log_dir: (str) Path to the folder where the model will be saved.
    :param verbose: (int)
    """
    def __init__(self, check_freq: int, log_dir: str, save_path: str, verbose=1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.save_path = save_path
        self.best_mean_reward = -np.inf

    def _on_step(self)-> bool:
      if self.n_calls % self.check_freq == 0:
        iter = int((self.n_calls/self.check_freq)) + 1
        episode, reward_lst, slowdown_lst, completion_time, withheld_jobs, allocated_jobs = Script.run_episodes(model, pa, env, job_sequence_len)
        mean_reward = mean(reward_lst)
        # save or update saved model only for best training results. 
        # Max possible iterations is time_steps/check_freq.
        if mean_reward > self.best_mean_reward:
          slowdown = mean(slowdown_lst)
          model_slowdowns.append(slowdown)
          model_rewards.append(mean_reward)
          model_max_rewards.append(max(reward_lst))
          model_iterations.append(iter)
          self.best_mean_reward = mean_reward
          if self.verbose > 0:
            print("Saving new best model to {}".format(self.save_path))
          self.model.save(self.save_path)

        return True

if __name__ == '__main__':
  pa = parameters.Parameters()
  # models to be trained
  models = [pa.A2C_Slowdown, pa.A2C_Ctime, pa.PPO2]
  env_slowdowns = []
  env_rewards = []
  env_max_rewards = []
  check_freq = pa.check_freq
  time_steps = pa.training_time
  iterations = []

  for i in range(len(models)):
    pa.objective = models[i]
    log_dir = models[i]['log_dir']
    save_path = log_dir + models[i]['save_path']
    model_slowdowns = []
    model_rewards = []
    model_max_rewards = []
    model_iterations = []
    os.makedirs(log_dir, exist_ok=True)

    # Create and wrap the environment
    job_sequence_len, job_sequence_size = job_distribution.generate_sequence_work(pa)
    env = Deeprm1.Env(pa, job_sequence_len=job_sequence_len, job_sequence_size=job_sequence_size)
    env1 = make_vec_env(lambda: env, n_envs=1)

    # Add some param noise for exploration
    param_noise = AdaptiveParamNoiseSpec(initial_stddev=0.1, desired_action_stddev=0.1)
    # Because we use parameter noise, we should use a MlpPolicy with layer normalization
    model = models[i]['agent']("MlpPolicy", env1, verbose=1, tensorboard_log=log_dir)

    # Create the callback: check every 100 steps
    callback = SaveOnBestTrainingRewardCallback(check_freq=check_freq, log_dir=log_dir, save_path=save_path)
    
    # Train the agent
    model.learn(total_timesteps=int(time_steps), callback=callback)
    env_slowdowns.append(model_slowdowns)
    env_rewards.append(model_rewards)
    env_max_rewards.append(model_max_rewards)
    iterations.append(model_iterations)

  fig2 = plt.figure()
  for i in range(len(models)):
    plt.plot(iterations[i], env_slowdowns[i], color=models[i]['color'], label=models[i]['title'])
  plt.xlabel("Iterations")
  plt.ylabel("Slowdown")
  plt.title('Learning curve')
  plt.legend()
  plt.grid()
  plt.show()
  fig2.savefig('workspace/Learningcurve_Slowdown')

  fig3 = plt.figure()
  for i in range(len(models)):
    if models[i]['save_path'] == 'job_scheduling_A2C_Slowdown':
      plt.plot(iterations[i], env_max_rewards[i],  color='black', label='A2C slowdown Max reward')
      plt.plot(iterations[i], env_rewards[i], color=models[i]['color'], label='A2C slowdown Mean reward')
  plt.xlabel("Iterations")
  plt.ylabel("Rewards")
  plt.title('Learning curve')
  plt.legend()
  plt.grid()
  plt.show()
  fig3.savefig('workspace/Learningcurve_Reward')