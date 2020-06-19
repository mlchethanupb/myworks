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

        super(Routing, self).__init__()

        config = {}
        config['maxsteps'] = 200000
        config['arrival_time'] = 2
        config['packet_size'] = 4.0

        #graph = nx.Graph()
        #graph.add_node(1, sink=False, source=False)
        #graph.add_node(2, sink=False, source=False)
        #graph.add_node(3, sink=False, source=False)
        #graph.add_node(0, sink=False, source=True)
        #graph.add_node(4, sink=True, source=False)
        #graph.add_edges_from([(0,1),(1,2),(1,3),(2,4)])
        graph = nx.random_regular_graph(3,8,3)
        self.actionspace = [len(graph.nodes()) for _ in range(len(graph.nodes()))]
        self.obsspace = [5 for _ in range(len(graph.nodes()))]
        #print(actionspace)
        #print(obsspace)
        self.action_space = spaces.MultiDiscrete(self.actionspace)
        self.observation_space = spaces.MultiDiscrete(self.obsspace)
        print(self.action_space)
        print(self.observation_space)


        self.arrival_time = config['arrival_time']
        self.maxsteps = config['maxsteps']
        # self.packet_size =config['packet_size']
        self.graph = graph
        self.current_timestep = 0
        self.sink,self.source = None,None

        #number of packets at each node
        self.packet_count_per_node=[0 for _ in range(len(self.graph.nodes()))]
        self.sending = [0 for _ in range(len(self.graph.nodes()))]

        #extract the sink and the source node from the graph
        self.sink=1
        self.source=5
        """
        for node,data in self.graph.nodes.data():
            if data['sink']: self.sink=node
            if data['source']: self.source=node
        if self.sink is None or self.source is None:
            print('no sink or no source defined')
            return
        """
    def step(self, action):
        """the action is a list of -num_Nodes- length. action[i]=j means that a packet 
        is sent from node i to node j if possible"""

        reward = 0
        print(action)
        for i,j in enumerate(action):
            #print(i,j)
            #transmitting packets with respect to the actions
            reward  -= self.transmit(i,j)

        #update the nodes according to the packets that has been sent
        for i in range(len(self.packet_count_per_node)):
            self.packet_count_per_node[i] += self.sending[i]
            if self.packet_count_per_node[i] >=128:
                print('dropping packet')
                self.packet_count_per_node[i]=127
                reward -=999999999
        self.sending = [0 for _ in range(len(self.graph.nodes()))]

        #handle packets that were routet successfully to the sink
        reward += self.packet_count_per_node[self.sink]*len(self.graph.nodes())
        self.packet_count_per_node[self.sink]=0

        self.current_timestep+=1
        if(self.current_timestep % self.arrival_time==0):
            #new packet arrives at source node
            self.packet_count_per_node[self.source]+=1

        info=dict()
        state = self.packet_count_per_node
        done = False
        if self.current_timestep >= self.maxsteps: done=True

        return np.array(state), reward, done, info

    def transmit(self,i,j):
        """transmit all packets from node i to node j
        returns the number of packets that were tried to sent"""

        #number of packets that will be tried to sent
        count = self.packet_count_per_node[i]

        #send packets if possible
        if (i,j) in self.graph.edges():
            self.sending[j] += self.packet_count_per_node[i]
            self.packet_count_per_node[i] = 0

        return count

    def reset(self):

        self.packet_count_per_node = [0 for _ in range(len(self.graph.nodes()))]
        self.sending = [0 for _ in range(len(self.graph.nodes()))]

        #the first packet already arrived at the source
        self.packet_count_per_node[self.source]=1
        return np.array(self.packet_count_per_node)

    def render(self, mode='human', close=False):
        pass

"""
    def __init__(self):
        print('init 1')
        self.graph = nx.random_regular_graph(3,8,3)
        self.DG = nx.to_directed(self.graph)
        nx.draw(self.DG, with_labels=True, font_weight='bold')
        #actionspace = [len(graph.nodes()) for _ in range(len(graph.nodes()))]
        #obsspace = [128 for _ in range(len(graph.nodes()))]
        #print(actionspace)
        #print(obsspace)
        self.num_nodes = len(self.DG.nodes())
        self.num_links = len(self.DG.edges())
        self.source = 1 #next(node_id for node_id, data in self.DG.nodes(data=True) if data['source'])
        self.sink = 6 #next(node_id for node_id, data in self.DG.nodes(data=True) if data['sink'])
        #self.action_space = []
       # for node in range(1, self.num_nodes):
            #(if node != self.sink):
        #    self.action_space.append(self.DG.out_degree(node))
        self.action_space = Tuple(Discrete(self.DG.out_degree(node))
                                  for node in range(1, self.num_nodes) if node != self.sink)
        self.observation_space = Box(low=0.0, high=1.0, shape=(self.num_nodes + self.num_links,), dtype=np.float16)
        print(self.action_space)
        print(self.observation_space)


    def step(self,action):
        pass
    def reset(self):
        print("called function reset")
    def render(self,mode="human",close=False):
        pass
"""