import os
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
import w_mac
from collections import defaultdict
import matplotlib as plt
import networkx as nx
import tensorflow as tf
import argparse
from DSDV_Agent import dsdv
from w_mac.envs.w_mac_env import W_MAC_Env
import ast

if __name__ == '__main__':

    d = defaultdict(list)
    """Larger network"""
    # data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10),(4,10)]#(4,6),(5,10),(6,10),(9,6),(8,10)]
    """Smaller netowrk"""
    # data = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]
    # defaultdict(<type 'list'>, {})

    parser = argparse.ArgumentParser(
        description='FlowSim experiment specification.')
    parser.add_argument('--agent', type=str, nargs='?', const=1,
                        default='A2C', help='Whether to use A2C, PPO, DSDV')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?',
                        const=1, default=10, help='Number of training steps for the agent')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=1000,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--graph', type=str, nargs='?', const=1,
                        default='[(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

    args = parser.parse_args()

    data = args.graph
    data = ast.literal_eval(data)
    print("data of graph", data)

    total_train_timesteps = args.total_train_timesteps
    eval_episodes = args.eval_episodes

    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k, v in d.items():
        for vv in v:
            G.add_edge(k, vv)
    nx.draw_networkx(G)

    env = gym.make('wmac-graphpavitratest-v0', graph=G)
    # check_env(env)
    env2 = dsdv(env, G)

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

    if args.agent == 'A2C' or args.agent == 'PPO2':

        if args.agent == 'A2C':
            model = A2C(MlpPolicy, env, verbose=1,
                        tensorboard_log="./a2c_tensorboard/")
            model.learn(total_timesteps=total_train_timesteps,
                        callback=TensorboardCallback())
            model.save("a2c_wmac")

            model = A2C.load("a2c_wmac")

        else:
            model = PPO2(MlpPolicy, env, verbose=1,
                         tensorboard_log="./PPO2_tensorboard/")
            model.learn(total_timesteps=total_train_timesteps,
                        callback=TensorboardCallback())

            model.save("PPO2_wmac")

            model = PPO2.load("PPO2_wmac")

        print("entering into reset")

        obs = env.reset()

        count = 0
        while count < eval_episodes:
            action, _states = model.predict(obs)
            obs, rewards, done, info = env.step(action)
            env.render()
            count = count + 1
            time.sleep(3)
            clear_output(wait=True)
            if done:
                env.render()
                break

    elif args.agent == 'dsdv':
        # model = dsdv(env, G)
        # model.learn(total_timesteps=total_train_timesteps,
        #             callback=TensorboardCallback())

        obs = env.reset()
        # print("initial observatin")
        # create new queuesize function
        # attack_nodes = env.__reset_attack_nodes()

        count = 0
        while count < eval_episodes:

            queue_size = env.get_queue_size()
            # print("queue_size", queue_size)
            # print("later obs", obs)
            action = env2.predict(obs, queue_size)
            obs, rewards, done, info = env.step(action)
            env.render()
            count = count + 1
            time.sleep(3)
            clear_output(wait=True)
            if done:
                env.render()
                break

    else:
        raise ValueError('Unknown agent.')
