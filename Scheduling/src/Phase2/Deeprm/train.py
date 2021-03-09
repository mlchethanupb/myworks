from datetime import datetime
import tensorflow
import pandas as pd
from gym import spaces
from stable_baselines.common.env_checker import check_env
from stable_baselines.common import make_vec_env
from stable_baselines.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines import DQN
from stable_baselines import PPO2
from stable_baselines import A2C
from stable_baselines import HER
from stable_baselines import TRPO
from stable_baselines import GAIL
from stable_baselines import ACKTR
from stable_baselines.gail import ExpertDataset, generate_expert_traj
from stable_baselines.her import GoalSelectionStrategy, HERGoalEnvWrapper
from stable_baselines.common.bit_flipping_env import BitFlippingEnv
from stable_baselines.deepq.policies import MlpPolicy
import gym
import os
from matplotlib.cbook import flatten
from stable_baselines.common.policies import FeedForwardPolicy, register_policy
from stable_baselines.common.noise import AdaptiveParamNoiseSpec
from stable_baselines.common.callbacks import BaseCallback
from random import sample
import argparse
import job_distribution
import parameters
import matplotlib.pyplot as plt
import math
import numpy as np
import operator
import environment
import warnings
import random
import other_agents
from statistics import mean
import tensorflow as tf
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)


def plot_slowdown_curve(pa, iterations, env_slowdowns, models):
    fig = plt.figure()
    for i in range(len(models)):
        plt.plot(iterations[i], env_slowdowns[i],
                 color=models[i]['color'], label=models[i]['title'])
    plt.xlabel("Iterations")
    plt.ylabel("Slowdown")
    plt.title('Learning curve')
    plt.legend()
    plt.grid()
    plt.show()
    print("Output plotted at", pa.train_path,
          ' with name ', 'Learningcurve_Slowdown', str(datetime.today()), str(datetime.time(datetime.now())))
    fig.savefig(pa.train_path + 'Learningcurve_Slowdown' + str(datetime.today()) +
                str(datetime.time(datetime.now())) + pa.figure_extension)


def plot_learning_curve(pa, iterations, env_max_rewards, env_rewards, models):
    fig = plt.figure()
    for i in range(len(models)):
        if models[i]['agent'] == 'A2C':
            plt.plot(iterations[i], env_max_rewards[i],
                     color='plum', label=models[i]['agent'] + 'slowdown Max reward')
            plt.plot(iterations[i], env_rewards[i], color=models[i]['color'],
                     label=models[i]['agent']+'slowdown Mean reward')
        elif models[i]['agent'] == 'PPO2':
            plt.plot(iterations[i], env_max_rewards[i],
                     color='crimson', label=models[i]['agent'] + 'slowdown Max reward')
            plt.plot(iterations[i], env_rewards[i], color=models[i]['color'],
                     label=models[i]['agent'] + 'slowdown Mean reward')
        elif models[i]['agent'] == 'ACKTR':
            plt.plot(iterations[i], env_max_rewards[i],
                     color='deeppink', label=models[i]['agent'] + 'slowdown Max reward')
            plt.plot(iterations[i], env_rewards[i], color=models[i]['color'],
                     label=models[i]['agent'] + 'slowdown Mean reward')
        elif models[i]['agent'] == 'TRPO':
            plt.plot(iterations[i], env_max_rewards[i],
                     color='darkmagenta', label=models[i]['agent'] + 'slowdown Max reward')
            plt.plot(iterations[i], env_rewards[i], color=models[i]['color'],
                     label=models[i]['agent'] + 'slowdown Mean reward')
        elif models[i]['agent'] == 'DQN':
            plt.plot(iterations[i], env_max_rewards[i],
                     color='chartreuse', label=models[i]['agent'] + 'slowdown Max reward')
            plt.plot(iterations[i], env_rewards[i], color=models[i]['color'],
                     label=models[i]['agent']+'slowdown Mean reward')
    plt.xlabel("Iterations")
    plt.ylabel("Rewards")
    plt.title('Learning curve')
    plt.legend()
    plt.grid()
    plt.show()
    print("Output plotted at", pa.train_path,
          ' with name ', 'Learningcurve_Reward', str(datetime.today()), str(datetime.time(datetime.now())))
    fig.savefig(pa.train_path +
                'Learningcurve_Reward'+str(datetime.today())+str(datetime.time(datetime.now())) + pa.figure_extension)


def run_episodes(model, pa, env, agent, vec=False):
    job_slowdown = []
    job_comption_time = []
    job_reward = []
    episode_list = []
    for episode in range(pa.num_episode):
        cumulated_job_slowdown = []
        cumulated_reward = 0
        cumulated_completion_time = []
        action_list = []
        done = False
        obs = env.reset()
        # obs = env.observe()
        info = {}
        while not done:
            if agent == 'Random':
                action = other_agents.get_random_action(env.job_slot)
            elif agent == 'SJF':
                action = other_agents.get_sjf_action(
                    env.machine, env.job_slot)
            elif agent == 'Packer':
                action = other_agents.get_packer_action(
                    env.machine, env.job_slot)
            else:
                action, _states = model.predict(
                    obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            if isinstance(info, list):
                info = info[0]
            if 'Job Slowdown' in info.keys() and 'Completion Time' in info.keys():
                cumulated_job_slowdown.append(info['Job Slowdown'])
                cumulated_completion_time.append(
                    info['Completion Time'])
            if reward != 0:
                cumulated_reward += reward
                action_list.append(action)
                action_list = []
            elif reward == 0 and done != True:
                action_list.append(action)
            if done == True:
                break
        episode_list.append(episode+1)
        job_slowdown.append(mean(cumulated_job_slowdown))
        job_comption_time.append(mean(cumulated_completion_time))
        job_reward.append(cumulated_reward)
    return job_reward, job_slowdown, job_comption_time, episode_list


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
        self.agent = agent

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            iter = int((self.n_calls / self.check_freq))
            # print("Started Iteration", iter)
            env1.reset()
            env1.envs[0].env.seq_no = 0
            vec = True
            reward_lst, slowdown_lst, completion_time, episode = run_episodes(model,
                                                                              pa, env1, agent, vec)
            # save or update saved model only for best training results. Max possible iterations is time_steps/check_freq.
            mean_reward = np.mean(reward_lst)
            max_reward = max(reward_lst)
            slowdown = np.mean(slowdown_lst)
            model_slowdowns.append(slowdown)
            model_rewards.append(mean_reward)
            model_max_rewards.append(max_reward)
            model_iterations.append(iter)
            env.reset()
            print("Mean reward for agent", agent,
                  ' in iteration', iter, 'is', mean_reward, 'with slowdown', slowdown)
            if mean_reward >= self.best_mean_reward:
                self.best_mean_reward = mean_reward
                # if self.verbose > 0:
                #     print("Saving new best model to {}".format(self.save_path))
                self.model.save(self.save_path)

            return True


if __name__ == '__main__':
    print("------------------------------------------------------------------")

    pa = parameters.Parameters()
    parser = argparse.ArgumentParser(description='Tune Agent')
    parser.add_argument('--objective', type=str, nargs='?', const=1, default="Job_Slowdown",
                        help='Job_Slowdown or Job_Completion_Time')
    args = parser.parse_args()
    pa.objective_disc = args.objective
    env_slowdowns = []
    env_rewards = []
    env_max_rewards = []
    iterations = []
    check_freq = 10000
    time_steps = 10000000
    models = [pa.random_disc, pa.SJF_disc,
              pa.A2C_SL, pa.DQN_SL, pa.PPO2_SL, pa.TRPO_SL]

    for i in range(len(models)):
        agent = models[i]['agent']
        log_dir = models[i]['log_dir']
        # print("Started for agent", agent)
        model_slowdowns = []
        model_rewards = []
        model_max_rewards = []
        model_iterations = []
        env = environment.Env(pa, render=False, repre='image', end='all_done')
        env1 = make_vec_env(lambda: env, n_envs=1)
        obs = env1.reset()

        # Custom policy with 20 neurons in the hidden layer
        # pa.network_input_width*pa.network_input_height 4480, 20, 11
        # pa.network_output_dim
        class CustomPolicy(FeedForwardPolicy):
            def __init__(self, *args, **kwargs):
                super(CustomPolicy, self).__init__(*args, **kwargs,
                                                   net_arch=[dict(pi=[pa.network_input_width*pa.network_input_height, 20, pa.network_output_dim],
                                                                  vf=[pa.network_input_width*pa.network_input_height, 20, pa.network_output_dim])],
                                                   feature_extraction="mlp")
        if log_dir != None:
            save_path = models[i]['save_path']
            os.makedirs(log_dir, exist_ok=True)
            # Add some param noise for exploration
            param_noise = AdaptiveParamNoiseSpec(
                initial_stddev=0.1, desired_action_stddev=0.1)
            if agent == 'DQN':
                model = models[i]['load'](
                    "MlpPolicy", env, verbose=0,
                    learning_rate=1e-3)
            elif agent == 'GAIL':
                model = DQN("MlpPolicy", env, verbose=0)
                generate_expert_traj(
                    model, 'A2C_expert', n_timesteps=100, n_episodes=10)
                # Load the expert dataset
                dataset = ExpertDataset(expert_path='A2C_expert.npz',
                                        traj_limitation=10, verbose=1)
                model = GAIL("MlpPolicy", env, dataset)

            elif agent == 'HER':
                model_class = DQN
                goal_selection_strategy = 'future'
                # model = HER(CustomPolicy, model_class, env1, verbose=0)
                model = HER('MlpPolicy', env, model_class, n_sampled_goal=4, goal_selection_strategy=goal_selection_strategy,
                            verbose=1)
            elif agent == 'PPO2':
                model = models[i]['load'](
                    "MlpPolicy", env1, verbose=0)
            elif agent == 'TRPO':
                model = TRPO(CustomPolicy, env, verbose=1)
            elif agent == 'A2C':
                model = models[i]['load'](
                    CustomPolicy, env1, verbose=0,  # "MlpPolicy", env1, verbose=0,
                    learning_rate=1e-3,
                    _init_setup_model=True, policy_kwargs=None, seed=None)
            callback = SaveOnBestTrainingRewardCallback(
                check_freq=check_freq, log_dir=log_dir, save_path=save_path)
            model.learn(total_timesteps=int(time_steps), callback=callback)
        else:
            model = models[i]
            reward_lst, slowdown_lst, completion_time, episode = run_episodes(
                model, pa, env, agent)
            print("The mean slowdown for",
                  model['title'], 'is', np.mean(slowdown_lst), 'with mean reward', mean(reward_lst))
            for i in range(int(time_steps/check_freq)):
                model_slowdowns.append(np.mean(slowdown_lst))
                model_rewards.append(np.mean(reward_lst))
                model_iterations.append(i+1)

        env_slowdowns.append(model_slowdowns)
        env_rewards.append(model_rewards)
        env_max_rewards.append(model_max_rewards)
        iterations.append(model_iterations)

    plot_slowdown_curve(pa, iterations, env_slowdowns, models)
    plot_learning_curve(pa, iterations, env_max_rewards, env_rewards, models)

    # Done execution
    fig = plt.figure()
    fig.savefig(pa.train_path+'Done_training' + str(datetime.today()) +
                str(datetime.time(datetime.now())) + pa.figure_extension)
    print("Done")
