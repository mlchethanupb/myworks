import argparse
from random import sample
import os
from networkx import nx
import gym
import math
import random
import numpy as np
import time

from gym import spaces

class Network(gym.Env):

    def __init__(self, configuration: dict, graph: nx.Graph):

        super(Network, self).__init__()
        #action_space = [6 for i in range(2)]
        #print(action_space,"AC N")
        #observe_space = [100 for i in range(len(graph.nodes()))]
        state_space = [nodes for nodes in graph.nodes()]
        #print("TTT",state_space,len(state_space))
        self.action_space = spaces.Discrete(len(state_space))
        #print(self.action_space,"sP")
        self.observation_space = spaces.Discrete(len(state_space))
        # self.arrival_time = config['arrival_time']
        self.maxsteps = config['maxsteps']
        # self.packet_size = config['packet_size'] 
        self.graph = graph
        self.current_timestep = 0
        self.sink,self.source,self.current,self.hop = None,None,None,None
        self.packet_per_node=[0 for i in range(len(self.graph.nodes()))]
        self.packet_pass = [0 for i in range(len(self.graph.nodes()))]


    def step(self, action):
        reward = 0
        done = False
        info=dict()
        #print("AC",action)
        i=self.current
        j=action[0]
        self.current_timestep+=1
        #print(i,j,"current nd new action")
        if (i,j) in self.graph.edges():
           
            """if current node contains a packet it will tranfer to the next node
            next node will be the current node for next action otherwise current node will be unchanged"""
            if  self.packet_per_node[i] > 0:
                
                reward+= 10
                self.packet_per_node[j]=1
                self.packet_per_node[i]=0
                self.current=j
                self.path.append(j)
                #print("current",self.current)
                self.hop+=1
                self.packet_pass[j]=self.hop
                #print("dukcy",done)
                if self.sink==j:
                    self.packet_per_node[j]=0
                    reward+= 1000
                    done = True
                    
            else:
                reward=-99

        else:
            reward=-99

        if self.hop >=100:
            self.hop=0
            reward =-99
            done = True

        if self.current_timestep >= self.maxsteps : done=True
        #print(np.array(self.packet_pass),"R:",reward)
        return self.current, reward, done, info

    def reset(self):

        self.packet_per_node = [0 for i in range(len(self.graph.nodes()))]
        self.path = []
        nodes = list(self.graph.nodes())
        node1 = np.random.choice(self.graph.nodes)
        node2= np.random.choice(self.graph.nodes)
        while (node1==node2):
            node2= np.random.choice(self.graph.nodes)
        self.sink=node1
        self.source=node2
        print("source =",node2, "and destination =",node1)
        self.current=self.source
        self.packet_per_node[self.current]=1
        self.hop=0
        return self.current
        #return np.array(self.packet_per_node)


    def render(self, mode='human', close=False):
        pass



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')

    config = {}
    config['maxsteps'] = 20000
    # config['arrival_time'] = 2
    # config['packet_size'] = 4.0

    G = nx.Graph()
    G.add_node(0)
    G.add_node(1)
    G.add_node(2)
    G.add_node(3)
    G.add_node(4)
    G.add_node(5)

    #declaring edges

    G.add_edge(0,1)
    G.add_edge(1,2)
    G.add_edge(4,5)
    G.add_edge(3,4)
    G.add_edge(2,3)
    G.add_edge(5,0)
    G.add_edge(1,4)
    G.add_edge(1,5)
    G.add_edge(2,4)
    G.add_edge(5,3)
    G.add_edge(4,0)
    
    
    network = Network(config,graph=G)
    # network.reset()
    # print(network.step([4]))
    # print(network.step([0]))
    # print(network.step([5]))
    # print(network.step([1]))
    # print(network.step([2]))
    # print(network.step([3]))
    

    # print(network.step([5]))
    # print(network.step([4]))
    # network.reset()
    # print(network.step([0]))
    # print(network.step([3]))
    
    # print("done",network.action_space,network.observation_space)

    q_table = np.zeros([network.observation_space.n,network.action_space.n])
    #print(q_table)
    num_episodes = 2000
    max_steps_per_episode = 100

    learning_rate = 0.1
    discount_rate = 0.99

    exploration_rate = 1
    max_exploration_rate = 1
    min_exploration_rate = 0.01
    exploration_decay_rate = 0.001
    rewards_all_episodes = []

    #Q-Learning algorithm
    for episode in range(num_episodes):
        
        state = network.reset()
        done = False
        rewards_current_episodes = 0
        c=0
        #for step in range(max_steps_per_episode):
        for step in range(max_steps_per_episode):
            
            #exploration exploiatation trade-off
            exploration_rate_threshold = random.uniform(0,1)
            if exploration_rate_threshold > exploration_rate:
                #print("state for action : ", state)
                action = np.argmax(q_table[state,:])
                
            else:
                action =random.randrange(0,6)
        
            n_action=[]
            n_action.append(action)
            new_state, reward, done, info = network.step(n_action)
            
            q_table[state,action] = q_table[state,action] * (1 - learning_rate) + \
                                    learning_rate * (reward + discount_rate*np.max(q_table[new_state,:]))
            
            state = new_state
            rewards_current_episodes += reward

            if done == True:
                break
                
        exploration_rate = min_exploration_rate + \
                          (max_exploration_rate - min_exploration_rate) * \
                          np.exp(-exploration_decay_rate*episode)

    print("\n")
    # print(q_table[0])


    for episode in range(5):
        print("\n Episode : ",episode+1)
        state = network.reset()
        path=[]
        path.append(state)
        done = False
        it=0
        for step in range(100):
            
            it=it+1
            action =np.argmax(q_table[state])
            ar=[]
            ar.append(action)
            path.append(action)
            #print("action",action)
            new_state, reward , done, info = network.step(ar)
            state = new_state
            #print("new state",state,done)
            if done:
                print(" hop count",it,"\n path",path)
                
                
                break;
    
    network.close()

   