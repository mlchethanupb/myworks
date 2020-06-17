import gym
from gym import error, spaces, utils
from gym.utils import seeding

import random
import numpy as np
import matplotlib.pyplot as plt
from gym.spaces import Tuple, Discrete, Box
import networkx as nx

class Routing(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self):
        print('init 1')
        self.graph = nx.random_regular_graph(3,8,3)
        self.DG = nx.to_directed(self.graph)
        nx.draw(self.DG, with_labels=True, font_weight='bold')
        
    def step(self,action):
        pass
    def reset(self):
        print("called function reset")
    def render(self,mode="human",close=False):
        pass
