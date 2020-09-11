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
import random


class Wireless2(gym.Env):
    def __init__(self, configuration: dict):
        self.num_nodes = [0,1,2,3,4]

        action_space = [2 for i in self.num_nodes]
        self.action_space = spaces.MultiDiscrete(action_space)

        observation_space = [5 for i in self.num_nodes]
        self.observation_space = spaces.MultiDiscrete(observation_space)

        self.dest = random.sample(range(0, 5), 5)

        self.num_packets = [1 for i in self.num_nodes]



    # In same range, 2 nodes can't transmit at a same time
    # if action =1 transmit, action = 0 then wait
    # Give reward when number of 1's occured once in a action list
    # give penalty if number of 1's are more that one time, i.e collision

    def step(self,action1):
        print("Action",action1)
        action = list(action1)
        c = Counter(action)
        print ("printing c",c) # Printing c Counter({0: 3, 1: 2}) number of 1's and 0's

        reward= 0 # to check accumulation of rewards

        if(len(c) == 1 and c[0] == 5):
            reward = -100

        elif(c[1]<2): #if no of 1's are > 1 ex:[0,1,1,1,0] collision will happen

            print("TRANSMIT ACTION")
            index = action.index(1) # Fetching index of 1, to get the node which is permitted to transfer
            print("printiting INDEX of the list",index) #ex: [1,0,0,0,0] node 0 can transmit now
            if(self.num_packets[index]>0 and action[index]==1):

            #Fetch the destination to transmit from random list
                destination =  self.dest[index]
                print("Destinatio", destination)
                self.num_packets[destination] = self.num_packets[destination] + self.num_packets[index]

                print("After transmission", self.num_packets[destination])

                self.num_packets[index] = self.num_packets[index] - 1
                reward = 100

        else:
            print("WAIT ACTION to avoid collision")
            # index = action.index(0)
            reward = -100


        print(self.num_packets)
        state = self.num_packets
        reward += reward
        done = False
        info=dict()

        if max(self.num_packets) >= 5:  done=True

        print("New_state",np.array(state))
        print("Reward",reward)


        return np.array(state), reward, done, info











    def reset(self):
        self.num_packets = [1 for i in self.num_nodes]
        return np.array(self.num_packets)

    def render(self, mode='human', close=False):
        pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    config = {}
    env = Wireless2(config)
    # print(wireless.step([1, 0, 0, 0, 0]))
    model = A2C("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=25000)



    new_state = env.reset()
    print(new_state)
    # rew=[]

    for i in range(10):
        action, _states = model.predict(new_state, deterministic=True)
        new_state, reward, dones, info = env.step(action)
    
        print("Reward : ", reward,"Observation : ",new_state)
