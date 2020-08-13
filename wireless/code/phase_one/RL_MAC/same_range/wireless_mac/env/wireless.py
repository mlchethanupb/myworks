import argparse
from random import sample
import tensorflow as tf
import os
from networkx import nx
import gym
import math
import numpy as np
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines.common.env_checker import check_env
from gym import spaces
from collections import Counter

class Wireless(gym.Env):
    def __init__(self, configuration: dict):
        self.num_nodes = 5
        action_space = []
        action_space = [2 for _ in range(self.num_nodes)]
        self.action_space = spaces.MultiDiscrete(action_space)
        print(self.action_space)
        self.dest = dict([(0, 1), (1, 4), (2, 3), (3, 1), (4, 2)])
        state_space = [5 for _ in range(self.num_nodes)]
        self.state_space = spaces.MultiDiscrete(state_space)
        print(self.state_space)
        
        # print(dest[0])
        
        
    
# for each of the key we need to fetch value, and then transmit packet to that node.
#             for all the keys in dict we need to choose an action
# randomly generate action for each key
# then perform transmit


    def step(self,action):
        
        
        # calculate number of 1's in array
        c = Counter(action)
        print ("printing c",c)
        print(c[1],c[0])
        self.reward= []
        if(c[1]<2):
    
            print("TRANSMIT ACTION")
    
    
            self.index = action.index(1)
            print("printing INDEX of the list",self.index)
    
            self.d = self.dest[self.index] #to fetch the vaue from dict
            self.num_packets[self.dest[self.index]] = self.num_packets[self.dest[self.index]] + self.num_packets[self.index]
            print("destination",self.d)
            print("count packet now",self.num_packets[self.dest[self.index]])
            self.num_packets[self.index]= self.num_packets[self.index] - 1
    
            self.reward.insert(self.index,1)
    
    
    
        else:
            print("WAIT ACTION to avoid collision")
            self.index = action.index(0)
            reward.insert(self.index,-1)



        print(self.num_packets) #printing the number of packets after transmission
        self.new_state = self.num_packets # take this as a obs
        print(self.new_state)
        print("obtained reward",self.reward)
        rew = sum(self.reward)
        print(rew)

        if max(self.num_packets) == 5 : done=True

        return self.new_state, rew, done, info



        
                      
              
            
            


    
    
    def reset(self):
        self.num_packets = [1 for i in range(self.num_nodes)]
        return self.num_packets
        
    
    
    def render(self, mode='human', close=False):
        pass
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')

    config = {}
    config['maxsteps'] = 10
    env = Wireless(config)
    # env = Wireless(config)
    # print(wireless.step([1, 0, 0, 0, 0]))
    model = A2C("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=25)
   
    obs = env.reset()
    print(obs)
    rew=[]
    
    for i in range(10):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, dones, info = env.step(action)
    
        print("Reward : ", reward)
        
        
