import os
import matplotlib as plt
import networkx as nx
import tensorflow as tf
import argparse
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines import A2C, PPO2
from stable_baselines.common.env_checker import check_env
from IPython.display import clear_output
import time
from copy import deepcopy
from ray import tune
from stable_baselines.common.callbacks import BaseCallback
import gym
import ast
import numpy as np
from collections import defaultdict
from MAC_RL_env import MAC_RL
import w_mac


if __name__ == '__main__':

    d = defaultdict(list)
    """Larger network"""
    # data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10),(4,10)]#(4,6),(5,10),(6,10),(9,6),(8,10)]
    """Smaller netowrk"""
    # data = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]
    # defaultdict(<type 'list'>, {})
    """ Experiment details"""
    parser = argparse.ArgumentParser(
        description='Transmitting packets in wireless network.')
    parser.add_argument('--agent', type=str, nargs='?', const=1,
                        default='RL_MAC', help='To train RL_MAC Agent')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?',
                        const=1, default=1000000, help='Number of training steps for the agent')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=5000,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--graph', type=str, nargs='?', const=1,
                        default='[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

    args = parser.parse_args()
    agent = args.agent
    data = args.graph
    data = ast.literal_eval(data)
    print("data of graph", data)
    # testing_agent(data, agent, eval_episode)

    total_train_timesteps = args.total_train_timesteps
    eval_episodes = args.eval_episodes

    # Create a network graph
    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k, v in d.items():
        for vv in v:
            G.add_edge(k, vv)
    nx.draw_networkx(G)

    env = MAC_RL(G)

    class TensorboardCallback(BaseCallback):
        """
        Custom callback for plotting additional values in tensorboard.
        """

        def __init__(self, verbose=0):
            self.is_tb_set = False
            super(TensorboardCallback, self).__init__(verbose)

        def _on_step(self) -> bool:
            # Log additional tensor
            if not self.is_tb_set:
                with self.model.graph.as_default():
                    tf.summary.scalar(
                        'packet_lost', tf.reduce_mean(env.get_packet_lost()))
                    self.model.summary = tf.compat.v1.summary.merge_all()
                self.is_tb_set = True
            # Log scalar value (here a random variable)
            value = env.get_packet_lost()
            summary = tf.Summary(value=[tf.Summary.Value(
                tag='packet_lost', simple_value=value)])
            self.locals['writer'].add_summary(summary, self.num_timesteps)
            return True

    # Different agent's training and evaluation
    # Default agent is PPO2. To try new agents ->Ex: python agent_script.py --agent A2C
    if args.agent == 'RL_MAC':

        model = PPO2(MlpPolicy, env, verbose=1, gamma=0.99, n_steps=2048, nminibatches=32, learning_rate=2.5e-4, lam=0.95, noptepochs=10, ent_coef=0.01, cliprange=0.2,
                     tensorboard_log="./PPO2_RL_MAC_withQ_newreward_last_test/", seed=8, n_cpu_tf_sess=1)
        model.learn(total_timesteps=total_train_timesteps,
                    callback=TensorboardCallback())

        model.save("PPO2_RL_MAC_withQ_newreward_last_test")
    obs = env.reset()
    print("initial obs", obs)

    for i in range(20):
        action, _states = model.predict(obs, deterministic=True)
        print("action returned by agent", action)
        obs, rewards, dones, info = env.step(action)
        print("observation", obs)
        print("reward", rewards)
