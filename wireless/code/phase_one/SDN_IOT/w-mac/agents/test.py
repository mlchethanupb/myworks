#!/usr/bin/env python
# coding: utf-8


from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines import A2C
from stable_baselines.common.env_checker import check_env
from IPython.display import clear_output
import time
from copy import deepcopy
from stable_baselines.common.callbacks import BaseCallback
import gym
import w_mac
from collections import defaultdict
import matplotlib as plt
import networkx as nx


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


model = A2C.load("a2c_wmac")

obs = env.reset()
count = 0
while count < 5000:
    action, _states = model.predict(obs)
    obs, rewards, done, info = env.step(action)
    print("------ Iteration------")
    env.render()
    count = count + 1
    time.sleep(3)
    clear_output(wait = True)
    if done:
        env.render()
        print("---------end--------")
        break

