import argparse
from random import sample
import os
from networkx import nx
import gym
import math
import numpy as np
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines.common.env_checker import check_env
from gym import spaces

# network_delay = {10,12,11
class Network(gym.Env):

    def __init__(self, configuration: dict, graph: nx.Graph):

        super(Network, self).__init__()
        action_space = [len(graph.nodes()) for i in range(len(graph.nodes()))]
        observe_space = [100 for i in range(len(graph.nodes()))]

        self.action_space = spaces.MultiDiscrete(action_space)
        self.observation_space = spaces.MultiDiscrete(observe_space)
        self.arrival_time = config['arrival_time']
        self.maxsteps = config['maxsteps']
        self.packet_size = config['packet_size'] 
        self.graph = graph
        self.current_timestep = 0
        self.sink,self.source = None,None
        self.packet_per_node=[0 for i in range(len(self.graph.nodes()))]
        self.packet_pass = [0 for i in range(len(self.graph.nodes()))]

        #randomly choose sink and source 

        nodes = list(self.graph.nodes())
        node1 = np.random.choice(self.graph.nodes)
        node2= np.random.choice(self.graph.nodes)
        self.sink=node1
        self.source=node2

        print(node1,node2,"source and sink")


    def step(self, action):

        reward = 0
        delay=0
        edge_bandwidth=0
        rew=0
        previous_timestep=0

        for i,j in enumerate(action):
        
            count = self.packet_per_node[i]
            limit_val= count * self.packet_size  

            #check if there is an edge between two nodes & calculate reward based on bandwidth and delay

            if (i,j) in self.graph.edges():
                edge_bandwidth = self.graph[i][j]['weight']
                if  self.packet_per_node[i] > 0:
                    if limit_val<=edge_bandwidth:
                        delay = delay + (1/edge_bandwidth)
                    elif limit_val>edge_bandwidth:
                        #previous_timestep=self.current_timestep
                        increase_val= math.ceil(limit_val/edge_bandwidth)
                        self.current_timestep = self.current_timestep + increase_val - 1
                        delay = delay + (.01*limit_val)
                        
                    reward += count+delay 
            
                self.packet_pass[j] += self.packet_per_node[i]
                self.packet_per_node[i] = 0

            #setting negative reward  if edge doesn't exist
            else:
                reward = -99999   
                
        for i in range(len(self.packet_per_node)):
            self.packet_per_node[i] += self.packet_pass[i]
            #negative reward if observation limits is over
            if self.packet_per_node[i] >=100:
                self.packet_per_node[i]=100
                reward -=99999

        self.packet_pass = [0 for i in range(len(self.graph.nodes()))]
        self.packet_per_node[self.sink]=0
        self.current_timestep+=1
        if(self.current_timestep % self.arrival_time==0):
            #arrival of new packet 
            self.packet_per_node[self.source]+=1

        info=dict()
        state = self.packet_per_node 
        done = False
        if self.current_timestep >= self.maxsteps: done=True
        return np.array(state), reward, done, info

   
    def reset(self):

        self.packet_per_node = [0 for i in range(len(self.graph.nodes()))]
        self.packet_pass = [0 for i in range(len(self.graph.nodes()))]
        self.packet_per_node[self.source]=1
        return np.array(self.packet_per_node)


    def render(self, mode='human', close=False):
        pass



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')

    config = {}
    config['maxsteps'] = 20000
    config['arrival_time'] = 2
    config['packet_size'] = 4.0

    G = nx.Graph()
    G.add_node(0, sink=False, source=True)
    G.add_node(1, sink=False, source=False)
    G.add_node(2, sink=False, source=False)
    G.add_node(3, sink=False, source=False)
    G.add_node(4, sink=True, source=False)
    G.add_node(5, sink=False, source=False)

    #declaring bandwidth as weight

    G.add_edge(0,1, weight=10)
    G.add_edge(0,2,weight=8)
    G.add_edge(1,5,weight=9)
    G.add_edge(4,5,weight=5)
    G.add_edge(3,4,weight=6)
    G.add_edge(2,3,weight=7)
    G.add_edge(0,3,weight=5)
    G.add_edge(0,5,weight=17)
    G.add_edge(2,1,weight=20)
    G.add_edge(2,5,weight=15)
    G.add_edge(2,4,weight=18)
    
    env = Network(config,graph=G)
    model = A2C("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=2500)

    obs = env.reset()
    for i in range(50):
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, dones, info = env.step(action)
        print("Reward : ", reward, "Observation : ",obs)

   

  
    