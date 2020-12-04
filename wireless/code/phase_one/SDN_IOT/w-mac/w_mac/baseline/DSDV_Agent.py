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

"""Baseline routing protocol DSDV"""


class dsdv():

    def __init__(self, env: gym.Env, graph: nx.Graph):
        # super(dsdv, self).__init__(env)
        self.graph = graph

        nx.draw_networkx(self.graph)
        self.total_nodes = len(self.graph.nodes())

    """ This will return the action required for the W_MAC_Env"""
    """Ex - actions = [2,1,2,3,4,5] nodes = [0,1,2,3,4,5] - only 0th node will be transmitting the packet"""

    def predict(self, state, queue_size):
        self.destinations_list_with_anode = []
        self.queue_size = []

        self.destinations_list_with_anode = state
        self.queue_size = queue_size
        # last number is attack node info
        self.attack_node = [self.destinations_list_with_anode[-1]]
        self.destinations_list = self.destinations_list_with_anode[:-1]

        self.create_routing_table(self.attack_node)
        self.actions = self.tdma()
        self.valid_actions = self.map_actions()
        # self.node_action_list = self.read_graph()
        self.valid_action_list = self.map_actions()

        return self.valid_action_list

    """Routing table creation steps"""
    "1. Creating a empty routing table with columns - destinations, next_hop for particular destination"
    "2. Each node will gather the info about neighbour nodes except attack node"
    "3. Now each node will broadcast their routing table to it's neighbors, indirectly connected nodes will be added"

    def create_routing_table(self, attack_node):

        self.attack_node = attack_node
        # for i in self.attack_node:

        #     self.graph.remove_node(i)
        # nx.draw_networkx(self.graph)
        # self.total_nodes = len(self.graph.nodes())

        # print("Graph after removing attack nodes", self.graph.nodes)

        dic = {}
        for nodes in self.graph.nodes():
            dic[nodes] = {}
            self.routing_table = dic
        print('Empty routing table\n', self.routing_table)

        for i in self.routing_table.keys():
            self.routing_table[i].update({'destination': [], 'hop_count': [
            ], 'next_hop': []})

        for i in self.graph.nodes:
            if i not in self.attack_node:
                self.destinations_list = []
                self.next_hop_list = []
                self.hop_count_list = []
                hop_count = 0
                for j in self.graph.nodes:
                    if j not in self.attack_node:
                        if (i, j) in self.graph.edges:
                            hop_count = 1

                            self.destinations_list.append(j)
                            self.next_hop_list.append(j)
                            self.hop_count_list.append(hop_count)
                            for key in self.routing_table:
                                if key == i:
                                    self.routing_table[key]['destination'] = self.destinations_list
                                    self.routing_table[key]['next_hop'] = self.next_hop_list
                                    self.routing_table[key]['hop_count'] = self.hop_count_list

        print("routing table with destination and next_hop details",
              self.routing_table)

        # once the neighbor details are available at each node, each node will transmit their table to neighbor node

        for src_node in self.graph.nodes:
            if src_node not in self.attack_node:

                self.neighbor_nodes = [
                    n for n in self.graph.neighbors(src_node)]
                print("self.neighbor_nodes of ", src_node, self.neighbor_nodes)

                # fetch the dict of node i
                for key in self.routing_table:
                    if key == src_node:
                        dest_of_source = self.routing_table[key]['destination']
                        print("destination list of source node ",
                              src_node, dest_of_source)
                        for n_node in self.neighbor_nodes:
                            if n_node not in self.attack_node:
                                for key in self.routing_table:
                                    if n_node == key:
                                        dest_of_neighbor = self.routing_table[key]['destination']
                                        print("destination list of neighbor nodes",
                                              dest_of_neighbor)

                                        # compare the destination list of neighbor node
                                        # insert the new destination into destination list of dictionary.
                                        for i in dest_of_source:
                                            if i in dest_of_neighbor:
                                                print(
                                                    "all destinations are present no need of table update")
                                            else:
                                                if i != n_node:
                                                    dest_to_add = self.routing_table[key]['destination']
                                                    dest_to_add.append(i)
                                                    self.routing_table[key]['destination'] = dest_to_add
                                                    next_hop_add = self.routing_table[key]['next_hop']
                                                    next_hop_add.append(
                                                        src_node)
                                                    self.routing_table[key]['next_hop'] = next_hop_add

        print("routing table after inserting new destination details",
              self.routing_table)

    """Allocating timeslot to each node to transmit based on the queue size. The larger the queue size, higher the priority"""
    """Find the next hop for the respective destination"""
    """Ex - Routing table of 0 = {destinations = [1,2,3,4,5], next_hop = [1,2,3,2/3,2/3]
        if destination of packet in 0 node is 1, then respective next hop is 1 """

    def tdma(self):

        self.actions = [n for n in range(len(self.graph.nodes))]
        self.max_queue_size = max(self.queue_size)
        if self.max_queue_size > 0:
            self.index_of_large_queue = np.argmax(self.queue_size)

        # now fetch the destination information for this node from state info

            for src, dest in enumerate(self.destinations_list):
                if self.index_of_large_queue == src:
                    self.dest_to_transmit = dest

        # fetch the routing table of self.index_of_large_queue

                    for key in self.routing_table:
                        if key == self.index_of_large_queue:
                            self.dest_list_to_search = self.routing_table[key]['destination']
                            self.next_hop_to_send = self.routing_table[key]['next_hop']
                            if self.dest_to_transmit in self.dest_list_to_search:
                                self.index_of_dest = self.dest_list_to_search.index(
                                    self.dest_to_transmit)
                                for nodes, next_hop in enumerate(self.next_hop_to_send):
                                    if nodes == self.index_of_dest:
                                        self.next_hop_found = self.next_hop_to_send[nodes]
                                        self.actions[self.index_of_large_queue] = self.next_hop_found

        else:
            print("send wait condition to all nodes")
            self.actions

        print("actions returned by dsdv", self.actions)

        return self.actions

    def read_graph(self):
        collision_domain = {}

        dict_index = 0
        for i in self.graph.nodes:
            domain_list1 = []
            domain_list2 = []
            for j in self.graph.nodes:
                if(self.graph.has_edge(i, j) == True):
                    if i not in domain_list1:
                        domain_list1.append(i)

                    connected = True
                    for node in domain_list1:
                        if(self.graph.has_edge(node, j) == False):
                            connected = False

                    if connected == True:
                        if j not in domain_list1:
                            domain_list1.append(j)
                    else:
                        for index, values in collision_domain.items():

                            connected = True
                            for node in values:
                                if(self.graph.has_edge(node, j) == False):
                                    connected = False

                            if connected == True:
                                if j not in values:
                                    collision_domain[index].append(j)
                            else:
                                domain_list2 = [i, j]

            # print("domain_list1",domain_list1)
            # print("domain_list2",domain_list2)
            if len(domain_list1):
                dict_index += 1
                collision_domain[dict_index] = domain_list1

            if len(domain_list2):
                dict_index += 1
                collision_domain[dict_index] = domain_list2

        fullrange_wo_dupli = {}
        sorted_list = []
        for key, value in collision_domain.items():
            # to arrange values in ascending order in dict
            sorted_list = sorted(value)
            fullrange_wo_dupli[key] = sorted_list

        # exchange keys, values
        d2 = {tuple(v): k for k, v in fullrange_wo_dupli.items()}
        fullrange_wo_dupli = {v: list(k) for k, v in d2.items()}

        to_remove_index = []
        for index, values in fullrange_wo_dupli.items():
            is_subset = False
            for test_values in fullrange_wo_dupli.values():
                if values != test_values:
                    if(set(values).issubset(set(test_values))):
                        is_subset = True
                        break
            if is_subset:
                to_remove_index.append(index)

        for key in to_remove_index:
            fullrange_wo_dupli.pop(key, None)

        # creating the collision domains
        self.collision_domain_elems = fullrange_wo_dupli
        print("self.collision_domain_elems", self.collision_domain_elems)

        # Find all the domains a node belong too.
        self.node_in_domains = {}
        for key, value in self.collision_domain_elems.items():
            for i in range(len(value)):
                if value[i] not in self.node_in_domains:
                    self.node_in_domains[value[i]] = [key]
                else:
                    self.node_in_domains[value[i]].append(key)
        print("self.node_in_domains : ", self.node_in_domains)

        """Create list of all the valid actions for each node"""
        self.node_action_list = {i: [] for i in self.graph.nodes(data=False)}

        for node in self.graph.nodes:
            coll_domain_list = self.node_in_domains[node]
            for id in coll_domain_list:
                for this_node in self.collision_domain_elems[id]:
                    if this_node not in self.node_action_list[node]:
                        self.node_action_list[node].append(this_node)

        sorted_list = []
        for key, value in self.node_action_list.items():
            # to arrange values in ascending order in dict
            sorted_list = sorted(value)
            self.node_action_list[key] = sorted_list

        print("self.node_action_list", self.node_action_list)

        # self.map_actions(node_action_list)

        return self.node_action_list

    def map_actions(self):
        valid_action_list = []
        self.node_action_list = self.read_graph()

        for node in self.graph.nodes:
            action_list = self.node_action_list[node]
            print("action_list", action_list)
            index = self.__get_index(node)
            print("index", "node", index, node)
            print("self.actions", self.actions)
            next_hop = self.actions[index]
            mapped_action = action_list.index(next_hop)
            print("mapped_action", mapped_action)
            valid_action_list.append(mapped_action)
            print("valid_action_list", valid_action_list)
        return valid_action_list

    def __get_index(self, node):

        node_list = list(self.graph.nodes)
        index = node_list.index(node)

        return index
