import gym
import numpy as np


class HotPotatoRouting(object):
    def __init__(self, env:gym.Env):
        self.env = env
        
    def predict(self, state, **kwargs):
        # randomly sample action from multidiscrete action space
        return self.env.action_space.sample(), None