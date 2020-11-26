#!/usr/bin/env python
# coding: utf-8

import os
import argparse
import networkx as nx
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines import A2C,PPO2
from stable_baselines.common.env_checker import check_env
from IPython.display import clear_output
import time
from copy import deepcopy
# from ray import tune
from stable_baselines.common.callbacks import BaseCallback
import tensorflow as tf
import gym
import w_mac
from collections import defaultdict
import matplotlib as plt



if __name__ == '__main__':
    d = defaultdict(list)
    """Larger network"""
    #data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10),(4,10)]#(4,6),(5,10),(6,10),(9,6),(8,10)]
    """Smaller netowrk"""
    data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]
    # defaultdict(<type 'list'>, {})
    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)
    nx.draw_networkx(G)


    env = gym.make('wmac-graph-v0',graph=G)
    check_env(env)

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
                    tf.summary.scalar('packet_lost', tf.reduce_mean(env.get_packet_lost()))
                    self.model.summary = tf.compat.v1.summary.merge_all()
                self.is_tb_set = True
            # Log scalar value (here a random variable)
            value = env.get_packet_lost()
            summary = tf.Summary(value=[tf.Summary.Value(tag='packet_lost', simple_value=value)])
            self.locals['writer'].add_summary(summary, self.num_timesteps)
            return True


    model = A2C(MlpPolicy, env, verbose=1,tensorboard_log="./a2c_tensorboard/")
    model.learn(total_timesteps=600000, callback=TensorboardCallback())
    model.save("a2c_wmac")



