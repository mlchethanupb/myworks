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
        print('init hgthghghghg')
        self.graph = nx.random_regular_graph(2,8,3)
        self.DG = nx.to_directed(self.graph)
        
        for n,p in self.DG.nodes(data=True):
            self.DG.nodes[n]['pos'] =(random.randrange(0,100000),random.randrange(0,100000))
            
        for u,v,d in self.DG.edges(data=True):
            d['weight']= random.randrange(0,20)

        pos=nx.get_node_attributes(self.DG,'pos')
        nx.draw(self.DG, pos, with_labels=True, font_weight='bold')
        labels = nx.get_edge_attributes(self.DG,'weight')
        nx.draw_networkx_edge_labels(self.DG,pos,edge_labels=labels)
        
        self.source = random.randrange(0,7)
        print("source = ",self.source)
        self.dest = random.randrange(0,7)
        while self.source == self.dest:
            self.dest = random.randrange(0,7)
        print("destination = ", self.dest)

        self.curr_state = self.encode(self.source,self.dest)
        print("curr_state = ", self.curr_state)
        
        self.Delay = d['weight']

        self.num_states = 56 # 8 current_node; 7 destinations
        self.num_actions = len(self.DG) #Number of nodes a packet can hop too

        self.observation_space = spaces.Discrete(self.num_states)
        self.action_space = spaces.Discrete(self.num_actions)
        self.state_space = [nodes for nodes in self.DG]
        
        self.P = {state: {action: [] for action in range(self.num_actions)} for state in range(self.num_states)}
        
        
        for c_node in range(len(self.DG)):
            for d_node in range(len(self.DG)):
                state = self.encode(c_node,d_node)
                
                for action in range(self.num_actions):
                    #next node is the current node by default, changes if there a valid edge
                    #is present between current node and the action_node 
                    next_node, dest_node = c_node , d_node 
                    reward = 0
                     #default reward for each edge
                    done = False

                    """
                    Action space includes the weight of the next edge. Check whether the next edge is destination
                    to give positive reward or if its completly random with out any associated path 
                    penalize the action 
                    """
                    
                             
                    if((action == dest_node) and (True == self.DG.has_edge(c_node, dest_node))): 
                        reward = +100
                        done = True
                        print("destination reached")
                        next_node = action
                        
                    elif(True == self.DG.has_edge(c_node, action)):
                        #has a edge so Hop to the next node
                        #print("Connected hopping")
                        for u,v,d in self.DG.edges(data=True):
                            if u == c_node and v == action :
                                edge_weight= d['weight']
                                reward = reward - edge_weight
                                next_node = action
                         
                        
                        #for better training of agent give some postive hopes when there is a path
                        #if (True == self.graph.has_edge(action,dest_node)):
                            #print("next hop has edge")
                            #reward += 5
                        #elif (True == nx.has_path(self.DG,action,dest_node)):
                            #print("has path")
                            #reward += 5
                        #else: 
                            #reward += -100
                            #print("No edge, no path")
                        #else:
                             #reward = -100
                             #print("NO CONNECTION reward", reward)
                    
                        new_state = self.encode(next_node, dest_node)
                        print("new_state",new_state)
                        #self.P[state][action].append(new_state,reward,done,1)
                    
                    
                    #print("p = ",self.P)

                       
    def encode(self, current_node, destination):
        # (8), 8
        i = current_node
        i *= 8
        i += destination
        return i

    def decode(self, state):
        # (8), 8
        destination = state % 8
        state = state // 8
        current_node = state
        return current_node, destination

    def step(self,action):
        #print(self.P[self.curr_state][action])
        #print("self.curr_state, action",self.curr_state,action)
        r_list = self.P[self.curr_state][action]
        l = list(r_list[0])
        next_state , reward, done, info =  l[0],l[1],l[2],l[3]
        self.curr_state = next_state
        curr_node , dest = self.decode(self.curr_state)
        # For rendering
        unwanted_num = {curr_node, dest}
        self.remaining_nodes = [ elem for elem in self.state_space if elem not in unwanted_num]

        print(next_state, reward, done, _)
        return next_state, reward , done , _


    def reset(self):
        #print("called function reset")
        self.source = random.randrange(0,7)
        print("================================")
        print("Source = ",self.source)
        self.dest = random.randrange(0,7)
        while self.source == self.dest:
            self.dest = random.randrange(0,7)
        print("Destination = ", self.dest)
        print("--------------------------------")
        self.curr_state = self.encode(self.source,self.dest)
        print("reset curr_state = ", self.curr_state)

        unwanted_num = {self.source , self.dest}
        self.remaining_nodes = [ elem for elem in self.state_space if elem not in unwanted_num]

        return self.curr_state

    def render(self,mode="human",close=False):
        curr_node, dest = self.decode(self.curr_state)
        list_current = [curr_node]
        list_sink = [self.dest]
        list_nodes =  self.remaining_nodes
        labels = {}
        labels[0] = '$0$'
        labels[1] = '$1$'
        labels[2] = '$2$'
        labels[3] = '$3$'
        labels[4] = '$4$'
        labels[5] = '$5$'
        labels[6] = '$6$'
        labels[7] = '$7$'
        labels = nx.get_edge_attributes(self.DG,'weight')
        pos=nx.get_node_attributes(self.DG,'pos')
        nx.draw_networkx_nodes(self.DG , pos , with_labels = True , nodelist = list_current, node_color = 'red')
        nx.draw_networkx_nodes(self.DG , pos , with_labels = True , nodelist = list_sink , node_color = 'green')
        nx.draw_networkx_nodes(self.DG , pos , with_labels = True , nodelist = list_nodes , node_color = 'blue')
        nx.draw_networkx_edges(self.DG , pos ,
                               edgelist =[e for e in self.DG.edges],
                               alpha = 0.5 , edge_color = 'black')
        plt.axis('off')
        plt.show(block = False)
        plt.pause(5)
        plt.close('all')
