import environment
import gym
import tensorflow as tf
import operator
import numpy as np
import math
import matplotlib.pyplot as plt
import parameters
import job_distribution
import argparse
from random import sample
import os
import pickle5
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines import PPO2
from stable_baselines import DQN
from stable_baselines import TRPO
from stable_baselines import ACKTR
from stable_baselines.common.env_checker import check_env
from matplotlib.cbook import flatten
from stable_baselines.common.policies import FeedForwardPolicy, register_policy
from stable_baselines.common.noise import AdaptiveParamNoiseSpec
from stable_baselines.common.callbacks import BaseCallback
from gym import spaces
import pandas as pd
from stable_baselines.common import make_vec_env
# import randomAgent
import SJF
import packer
import warnings
import random
from statistics import mean
from collections import defaultdict
import other_agents
# import Otheragents
# import Other_agent_II as newOther
# import other_agents_original as og
from datetime import datetime
# warnings.simplefilter(action='ignore', category=FutureWarning)
# warnings.simplefilter(action='ignore', category=Warning)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

if __name__ == '__main__':
    def plot_load_variation(load_occupied, slowdown):
        fig = plt.figure()
        res = defaultdict(list)
        {res[key].append(sub[key]) for sub in load_occupied for key in sub}
        for i in range(len(models)):
            plt.plot(res['cluster_load'], slowdown[i],
                     color=models[i]['color'], label=models[i]['title'])
        plt.xlabel("Cluster Load(Percentage)")
        plt.ylabel("Average Job Slowdown")
        plt.title("Job Slowdown at different levels of load")
        plt.legend()
        plt.grid()
        plt.show()
        print("Output plotted at", pa.run_path,
              ' with name ', 'LoadVariation', str(datetime.today()), str(datetime.time(datetime.now())))
        fig.savefig(pa.loadVariation_path +
                    "LoadVariation"+str(datetime.today()) + str(datetime.time(datetime.now())) + pa.figure_extension)

    def run_episodes(model, pa, env, agent):
        agent = model['agent']
        if agent == 'DQN':
            model = model['load'].load(model['save_path'], env)
        elif agent == 'A2C' or agent == 'PPO2' or agent == 'ACKTR' or agent == 'TRPO':
            class CustomPolicy(FeedForwardPolicy):
                def __init__(self, *args, **kwargs):
                    super(CustomPolicy, self).__init__(*args, **kwargs,
                                                       net_arch=[dict(pi=[4480, 20, 11],
                                                                      vf=[4480, 20, 11])],
                                                       feature_extraction="mlp")

            env = make_vec_env(lambda: env, n_envs=1)
            # model = model['load'].load(
            #     model['save_path'], env, policy=CustomPolicy)
            model = model['load'].load(
                model['save_path'], env)

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
            while not done:
                if agent == 'Random':
                    action = other_agents.get_random_action(env.job_slot)
                elif agent == 'SJF':
                    action = other_agents.get_sjf_action(
                        env.machine, env.job_slot)
                elif agent == 'Packer':
                    action = other_agents.get_packer_action(
                        env.machine, env.job_slot)
                elif agent == 'SJF AICON':
                    action = SJF.agent(
                        env.machine, env.job_slot)
                elif agent == 'Packer AICON':
                    action = packer.agent(
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
            job_slowdown.append(np.mean(cumulated_job_slowdown))
            job_comption_time.append(np.mean(cumulated_completion_time))
            job_reward.append(cumulated_reward)
        return job_reward, job_slowdown, job_comption_time, episode_list

    # Reward list , slowdown list and Completion time list for all models
    reward = [[], [], [], [], [], [], [], [], []]
    slowdown = [[], [], [], [], [], [], [], [], []]
    completionTime = [[], [], [], [], [], [], [], [], []]

    parser = argparse.ArgumentParser(
        description='Load variation')
    parser.add_argument('--num_episodes', type=int, nargs='?', const=1,
                        default=1, help='Maximum number of episodes')
    parser.add_argument('--objective', type=str, nargs='?', const=1, default='Job Slowdown',
                        help='Objective (Job Slowdown or Completion time)')
    args = parser.parse_args()

    pa = parameters.Parameters()
    pa.num_episode = args.num_episodes
    if args.objective == 'Job Slowdown':
        pa.objective_disc = pa.objective_slowdown
    elif args.objective == 'Job Completion Time':
        pa.objective_disc = pa.objective_Ctime

    episodes = [n for n in range(pa.num_episode)]

    models = [pa.random_disc, pa.SJF_disc,
              pa.Packer_disc, pa.A2C_SL, pa.PPO2_Tuned_SL, pa.DQN_SL, pa.TRPO_Tuned_SL]
    models = [pa.random_disc, pa.SJF_disc,
              pa.Packer_disc, pa.DQN_SL, pa.A2C_SL, pa.PPO2_SL, pa.TRPO_SL]

    cluster_load = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    cluster_load_percentage = [10, 30, 50, 70, 90, 110, 130, 150, 170, 190]

    slowdown_ep = []
    reward_ep = []
    ct_ep = []
    for i in range(len(cluster_load)):
        list1 = []
        list2 = []
        list3 = []
        for j in range(len(models)):
            list1.append([])
            list2.append([])
            list3.append([])
        slowdown_ep.append(list1)
        reward_ep.append(list2)
        ct_ep.append(list3)

    load_occupied = []
    for i in range(len(cluster_load)):
        pa.new_job_rate = cluster_load[i]
        cluster_values = {}
        cluster_values['simu_len'] = pa.simu_len
        cluster_values['new_job_rate'] = pa.new_job_rate
        cluster_values['cluster_load'] = cluster_load_percentage[i]
        load_occupied.append(cluster_values)
        # env = DeepRMEnv.Env(pa, job_sequence_len=job_sequence_len,
        #                     job_sequence_size=job_sequence_size)

        # Generating an unseen job set
        seed = 42

        env = environment.Env(
            pa, seed=seed, render=False, repre='image', end='all_done')
        for j in range(len(models)):
            rw, sl, ct, ep = run_episodes(
                models[j], pa, env, models[j]['agent'])
            slowdown_ep[i][j].append(np.mean(sl))
            reward_ep[i][j].append(np.mean(rw))
            ct_ep[i][j].append(np.mean(ct))
            print("Done for model",  models[j]['agent'],
                  "with load", pa.new_job_rate * 100)

    for j in range(len(models)):
        for i in range(len(cluster_load)):
            slowdown[j].append(mean(slowdown_ep[i][j]))

    plot_load_variation(load_occupied, slowdown)
    print("Graph ploted for load variation.")
