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
        self.source = random.randrange(0,8)
        print("source = ",self.source)
        self.dest = random.randrange(0,8)
        while self.source == self.dest:
            self.dest = random.randrange(0,8)
        print("destination = ", self.dest)

        self.curr_state = self.encode(self.source,self.dest)
        print("curr_state = ", self.curr_state)

        self.num_states = 64 # 8 current_node; 8 destinations
        self.num_actions = len(self.graph) #Number of nodes a packet can hop too

        self.observation_space = spaces.Discrete(self.num_states)
        self.action_space = spaces.Discrete(self.num_actions)
        self.state_space = [nodes for nodes in self.graph.nodes]

        self.P = {state: {action: [] for action in range(self.num_actions)} for state in range(self.num_states)}
        
        for c_node in range(len(self.graph)):
            for d_node in range(len(self.graph)):
                state = self.encode(c_node,d_node)

                for action in range(self.num_actions):
                    #next node is the current node by default, changes if there a valid edge
                    #is present between current node and the action_node
                    next_node, dest_node = c_node , d_node 
                    reward = -1 #default reward for one hop
                    done = False

                    """
                    Action space includes the next hop address. Check whether the next hop is destination
                    to give positive reward or if its completly random with out any associated path 
                    penalize the action 
                    """
                    if((action == dest_node) and (True == self.graph.has_edge(c_node,action))):
                        reward += 100
                        done = True
                        next_node = action
                        #print("destination reached")
                    elif (True == self.graph.has_edge(c_node,action)):
                        #has a edge so Hop to the next node
                        #print("Connected hopping")
                        reward = -1
                        next_node = action
                        
                        """for better training of agent give some postive hopes when there is a path"""
                        #if (True == self.graph.has_edge(action,dest_node)):
                            #print("next hop has edge")
                            #reward += 5
                        #elif (True == nx.has_path(self.graph,action,dest_node)):
                            #print("has path")
                            #reward += 5
                        #else: 
                            #reward += -100
                            #print("No edge, no path")

                    else: 
                        reward = -100
                        #print("No connection")

                    new_state = self.encode(next_node, dest_node)
                    self.P[state][action].append((new_state,reward,done,1))

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
        next_state , reward, done, _ =  l[0],l[1],l[2],l[3]
        self.curr_state = next_state
        curr_node , dest = self.decode(self.curr_state)
        # For rendering
        unwanted_num = {curr_node, dest}
        self.remaining_nodes = [ elem for elem in self.state_space if elem not in unwanted_num]

        print(next_state, reward, done, _)
        return next_state, reward , done , _


    def reset(self):
        #print("called function reset")
        self.source = random.randrange(0,8)
        print("================================")
        print("Source = ",self.source)
        self.dest = random.randrange(0,8)
        while self.source == self.dest:
            self.dest = random.randrange(0,8)
        print("Destination = ", self.dest)
        print("--------------------------------")
        self.curr_state = self.encode(self.source,self.dest)
        #print("reset curr_state = ", self.curr_state)

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
        pos = nx.spring_layout(self.graph)
        nx.draw_networkx_nodes(self.graph , pos , with_labels = True , nodelist = list_current, node_color = 'red')
        nx.draw_networkx_nodes(self.graph , pos , with_labels = True , nodelist = list_sink , node_color = 'green')
        nx.draw_networkx_nodes(self.graph , pos , with_labels = True , nodelist = list_nodes , node_color = 'blue')
        nx.draw_networkx_edges(self.graph , pos ,
                               edgelist =[e for e in self.graph.edges],
                               alpha = 0.5 , edge_color = 'black')
        nx.draw_networkx_labels(self.graph , pos , labels , font_size = 10)
        plt.axis('off')
        plt.show(block = False)
        plt.pause(5)
        plt.close('all')

                

        
        
