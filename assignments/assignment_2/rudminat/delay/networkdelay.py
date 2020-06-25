import argparse
from random import sample
import os
from networkx import nx
import gym
import math
import random
import numpy as np
import time
import matplotlib.pyplot as plt
from gym import spaces

#from stable_baselines.common.env_checker import check_env
from gym import spaces

class Network(gym.Env):

    def __init__(self, nodeTravarsal, configuration: dict, graph: nx.Graph):

        super(Network, self).__init__()
        self.nodeTravarsal = nodeTravarsal
        self.action_space = spaces.Discrete(6)
        self.arrival_time = config["arrival_time"]
        self.maxsteps = config["maxsteps"]
        self.packet_size = config["packet_size"]
        self.graph = graph
        self.current_timestep = 0
        self.sink,self.source,self.current = None,None,None 
        nodes = list(self.graph.nodes())
        node1 = np.random.choice(self.graph.nodes)
        node2= np.random.choice(self.graph.nodes)
        while (node1==node2):
            node2= np.random.choice(self.graph.nodes)
        self.sink=node1
        self.source=node2


    def step(self, action):
        reward = 0
        edge_bandwidth=0
        self.nodeTravarsal[self.source]+=1
        done=False
        i= self.source
        j= action

        
        if(i,j) in self.graph.edges():
            count=self.nodeTravarsal.get(self.source)
            limit_val= count * self.packet_size
            if(self.nodeTravarsal.get(self.source)>0):
                edge_bandwidth = self.graph[i][j]['weight']
                print("Limit val........",limit_val)
                print("Weightage of the connecting edge",edge_bandwidth)
                if limit_val< edge_bandwidth:
                    reward-=self.nodeTravarsal.get(action)
                    self.nodeTravarsal[j]+=count
                    self.nodeTravarsal[i]-=count
                elif limit_val> edge_bandwidth:
                    reward-=self.nodeTravarsal.get(action)
                    self.nodeTravarsal[j]+=count
                    self.nodeTravarsal[i]-=count
                self.action=j
                if j==self.sink :
                    self.nodeTravarsal[j]=0
                    reward=1000
                    self.action=self.source
                    done=True
                
                elif self.nodeTravarsal.get(j)>100 or self.nodeTravarsal.get(i)>100 :
                    done=True    
            else:
                reward=-99
        else:
            reward=-99
        info=dict()
        return action, reward, done, info

    def resetSourceDestination(self):  
        self.source=random.randrange(0,6)
        self.sink=random.randrange(0,6)  
        while self.source==self.sink:
            self.source= random.randrange(0,6)
        for i in range(len(self.nodeTravarsal)):
            if i==self.source:
                continue
            self.nodeTravarsal[i]=0   
        print("Source is now",self.source)
        print("Destination is now",self.sink)
        return self.source

   
    def reset(self):
        self.current=self.source
        self.nodeTravarsal[self.source]=1
        return self.source


    def render(self, mode='human', close=False):
        pass



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')

    config = {}
    config['maxsteps'] = 6
    config['arrival_time'] = 2
    config['packet_size'] = 4.0

    G = nx.Graph()
    G.add_node(0)
    G.add_node(1)
    G.add_node(2)
    G.add_node(3)
    G.add_node(4)
    G.add_node(5)

    #declaring bandwidth as weight

    G.add_edge(0,1, weight=32)
    G.add_edge(0,2,weight=36)
    G.add_edge(0,5,weight=28)
    G.add_edge(1,5,weight=40)
    G.add_edge(4,5,weight=32)
    G.add_edge(3,4,weight=16)
    G.add_edge(2,3,weight=24)
    G.add_edge(0,3,weight=16)
    G.add_edge(4,0, weight=24)
    G.add_edge(1,2,weight=44)
    G.add_edge(1,4,weight=40)
    G.add_edge(1,3,weight=24)
    G.add_edge(3,5,weight=24)
    G.add_edge(2,5,weight=32)
    G.add_edge(2,4,weight=16)
    nodeTravarsal = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0,5: 0}
    env = Network(nodeTravarsal,config,graph=G)
    env.reset()
    q_table = np.zeros([len(env.nodeTravarsal),env.action_space.n])
    print(q_table)
    num_episodes = 22000
    max_steps_per_episode = 1000
    learning_rate = 0.1
    discount_rate = 0.99
    exploration_rate = 1
    max_exploration_rate = 1
    min_exploration_rate = 0.01
    exploration_decay_rate = 0.001
    rewards_all_episodes = []


    #Q-Learning algorithm
    
    for episode in range(2000):  
        
        state = len(env.nodeTravarsal)-1
        done = False
        rewards_current_episodes = 0
        c=0
        #for step in range(max_steps_per_episode):
        for step in range(100):
            loopChecking=[]
            exploration_rate_threshold = random.uniform(0,1)
            if exploration_rate_threshold > exploration_rate:
                action = np.argmax(q_table[state,:])
                loopChecking.append(action)
                while action in loopChecking:
                    action =random.randrange(0,6)
            else:
                action =random.randrange(0,6)#choose any node from 0 to 6
            n_action=[]
            n_action.append(action)
            new_state, reward, done, info = env.step(action)
            
            q_table[state,action] = q_table[state,action] * (1 - learning_rate) + \
                                    learning_rate * (reward + discount_rate*np.max(q_table[new_state,:]))
           
            if done == True:
                break
            state = new_state
            rewards_current_episodes += reward     
        exploration_rate = min_exploration_rate + \
                          (max_exploration_rate - min_exploration_rate) * \
                          np.exp(-exploration_decay_rate*episode)
        plt.plot(q_table)
        plt.show()
        print("With updated value",q_table)
    for episode in range(5):
        tempDuplicationChecking=[]
        state = env.resetSourceDestination()
        s=state
        tempDuplicationChecking.append(state)
        path=[]
        path.append(state)
        done = False
        it=0
        for step in range(100):
            it=it+1
            action =np.argmax(q_table[state])
            while action in tempDuplicationChecking:
                action=np.argmax(q_table[state])
            ar=[]
            ar.append(action)
            path.append(action)
            new_state, reward , done, info = env.step(action)
            state = new_state
            tempDuplicationChecking.append(action)
            if done:
                if s not in path:
                    path.append(s)
                print("Optimal path-",path,"  Reward-",reward)
                
                
                break;
    
    

    
 

   

  
    