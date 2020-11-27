import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.spaces import MultiDiscrete, Tuple, Box
import networkx as nx
import numpy as np
import random
import w_mac
from w_mac.envs.packet import Packet
import matplotlib.pyplot as plt
from IPython.display import clear_output
import time
from collections import defaultdict


class DSDV():
    metadata = {'render.modes': ['human']}

    # get the graph from the outside
    # Create a empty routing table to all nodes initially
    # Insert routing table headings to each node's routing table

    def __init__(self, graph: nx.Graph):
        super(DSDV, self).__init__()
        self.graph = graph
        nx.draw_networkx(self.graph)
        self.total_nodes = len(self.graph.nodes())

        # attack node details, avoid attack nodes in the routing table
        self.attack_nodes = []

        for i in range(1):
            attack_node = random.randrange(0, self.total_nodes)
            # while (attack_node in self.attack_nodes):
            #     attack_node = random.randrange(0, self.total_nodes)

            self.attack_nodes.append(attack_node)
        print('Attack node', self.attack_nodes)

        # Construct new graph without attack node
        for i in self.attack_nodes:
            self.graph.remove_node(i)
        nx.draw_networkx(self.graph)

        print("Nodes after attack node removal", G.nodes)

        print('\n------------------------------------------------------\n')

        dic = {}
        for nodes in self.graph.nodes():
            dic[nodes] = {}
            self.routing_table = dic
        print('Empty routing table\n', self.routing_table)

        print('\n------------------------------------------------------\n')

        for i in self.routing_table.keys():
            self.routing_table[i].update({'destination': [], 'hop_count': [
            ], 'next_hop': []})  # 'timestamp': [] , 'seq_num': [],is optional
        # print('Routing table after column insertion\n', self.routing_table)

        # if we are constructing the routing table in the firat stage without exchanging the packets, we dont need sequence
        # number column name

        # Now for each node in the network construct the routing table
        # Fetch the list of destinations for each node and store in dictionary

        for key, value in self.routing_table.items():
            self.destinations_list = []
            for nodes in self.graph.nodes:
                if nodes not in self.attack_nodes:
                    if nodes != key:
                        self.destinations_list.append(nodes)
                self.routing_table[key]['destination'] = self.destinations_list
        print("routing table with destination details", self.routing_table)


if __name__ == '__main__':

    # parser = argparse.ArgumentParser(
    # description='FlowSim experiment specification.')
    config = {}
    # data = [(0,2),(0,1),(1,2),(2,3),(2,4),(3,4)]
    data = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),
            (2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]
    d = defaultdict(list)

# defaultdict(<type 'list'>, {})
    for node, dest in data:
        d[node].append(dest)
    print(d)

    G = nx.Graph()
    for k, v in d.items():
        for vv in v:
            G.add_edge(k, vv)
    nx.draw(G)

    env = DSDV(graph=G)
