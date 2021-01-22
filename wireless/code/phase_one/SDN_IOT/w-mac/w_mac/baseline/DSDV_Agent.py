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
#from Routing_Table import Routing_info
#from Updated_RTable import Updated_Routing_info
from w_mac.baseline.Routing_Table import Routing_info
from w_mac.baseline.Updated_RTable import Updated_Routing_info

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

        print("calling predict function - 1")
        self.destinations_list_with_anode = []
        self.queue_size = []

        self.destinations_list_with_anode = state

        self.queue_size = queue_size
        # last number is attack node info
        self.attack_node = [self.destinations_list_with_anode[-1]]
        self.destinations_list = self.destinations_list_with_anode[:-1]
        print("self.destinations_list", self.destinations_list)

        self.create_routing_table(self.attack_node)
        self.actions = self.tdma()
        self.valid_action_list = self.map_actions()

        return self.valid_action_list

    def create_routing_table(self, attack_node):
        print("calling create routing table function - 2")
        self.attack_nodes = attack_node
        print("self.attack_nodes", self.attack_nodes)

        print('\n------------------------------------------------------\n')

        dic = {}
        for nodes in self.graph.nodes():
            dic[nodes] = {}
            self.routing_table = dic
        # print('Empty routing table\n', self.routing_table)

        print('\n------------------------------------------------------\n')

        for i in self.routing_table.keys():
            self.routing_table[i].update({'destination': [], 'hop_count': [],
                                          'next_hop': [], 'id_num': []})
        # print("self.routing_table after column insertion", self.routing_table)

        for nodes in self.graph.nodes():
            if nodes not in self.attack_nodes:
                nbr_dest = self.routing_table[nodes]['destination']
                nbr_nh = self.routing_table[nodes]['next_hop']
                nbr_hc = self.routing_table[nodes]['hop_count']
                self_id = self.routing_table[nodes]['id_num']
                self_id.append(nodes)

                for n_nodes in self.graph.nodes():
                    hop_count = 0
                    if n_nodes not in self.attack_nodes:
                        if (nodes, n_nodes) in self.graph.edges:
                            hop_count += 1

                            nbr_dest.append(n_nodes)
                            nbr_nh.append(n_nodes)
                            nbr_hc.append(hop_count)

                            self.routing_table[nodes]['destination'] = nbr_dest
                            self.routing_table[nodes]['next_hop'] = nbr_nh
                            self.routing_table[nodes]['hop_count'] = nbr_hc
                            self.routing_table[nodes]['id_num'] = self_id

        self.Broadcast_NbrTable()

        print("Final Routing table", self.routing_table)

        return self.routing_table

    def Broadcast_NbrTable(self):
        print("calling broadcast nbr table function - 3")
        # self.r_table = r_table

        self.rtable_info_queue = {i: []
                                  for i in self.graph.nodes}

        for src_nodes in self.graph.nodes():
            if src_nodes not in self.attack_nodes:
                rtable_dest = self.routing_table[src_nodes]['destination']
                rtable_nh = self.routing_table[src_nodes]['next_hop']
                rtable_hc = self.routing_table[src_nodes]['hop_count']
                rtable_id = self.routing_table[src_nodes]['id_num']
                rtable_info = Routing_info(
                    rtable_dest, rtable_nh, rtable_hc, rtable_id)
                rtable_to_bcast = rtable_info

                # insert this object into queue of neighbor nodes
                neighbor_nodes = [n for n in self.graph.neighbors(src_nodes)]
                for idx, nbr_node in enumerate(neighbor_nodes):
                    if nbr_node not in self.attack_nodes:
                        self.rtable_info_queue[nbr_node].insert(
                            0, rtable_to_bcast)

        # print("self.rtable_info_queue", self.rtable_info_queue)

        self.queue_length()

    def update_table(self):
        # print("if any of the  not empty calling update table function - 5")

        # while (self.queue_empty):
        # print("queues are not empty")
        
        for self.src_node in self.graph.nodes():
            if self.src_node not in self.attack_nodes:
                if (len(self.rtable_info_queue[self.src_node]) != 0):
                    rtable_pkt = self.rtable_info_queue[self.src_node].pop(
                    )
                    src_dest_list = rtable_pkt.dest
                    src_nh_list = rtable_pkt.nh
                    src_hc_list = rtable_pkt.hc
                    src_id_list = rtable_pkt.id_num

                    original_src_dest = self.routing_table[self.src_node]['destination']
                    original_src_nh = self.routing_table[self.src_node]['next_hop']
                    original_src_hc = self.routing_table[self.src_node]['hop_count']

                    for idx, node_to_add in enumerate(src_dest_list):
                        if node_to_add != self.src_node:
                            if node_to_add not in original_src_dest:
                                idx_node_to_add = src_dest_list.index(
                                    node_to_add)
                                for index_nh, nh_node in enumerate(src_id_list):
                                    nh_to_add = nh_node
                                    hc_to_add = src_hc_list[idx_node_to_add]
                                    original_src_dest.append(node_to_add)
                                    original_src_nh.append(nh_to_add)
                                    original_src_hc.append(hc_to_add + 1)
                                    self.routing_table[self.src_node]['destination'] = original_src_dest
                                    self.routing_table[self.src_node]['next_hop'] = original_src_nh
                                    self.routing_table[self.src_node]['hop_count'] = original_src_hc
                                    self.broadcast_update()

                            else:  # if all are present check for the hop count
                                idx_node_to_add = src_dest_list.index(
                                    node_to_add)
                                hc_to_add = src_hc_list[idx_node_to_add]
                                for index_nh, nh_node in enumerate(src_id_list):

                                    nh_to_add = nh_node
                                    idx_node_to_check = original_src_dest.index(
                                        node_to_add)
                                    hc_to_check = original_src_hc[idx_node_to_check]

                                    if (hc_to_add < hc_to_check):
                                        hc_to_add += 1
                                        if (hc_to_add < hc_to_check):
                                            original_src_hc[idx_node_to_check] = hc_to_add
                                            original_src_nh[idx_node_to_check] = nh_to_add
                                            self.routing_table[self.src_node]['destination'] = original_src_dest
                                            self.routing_table[self.src_node]['next_hop'] = original_src_nh
                                            self.routing_table[self.src_node]['hop_count'] = original_src_hc
                                            self.broadcast_update()
        self.queue_length()

    def broadcast_update(self):
        # print("calling broadcast update - 6")
        self.updated_dest = self.routing_table[self.src_node]['destination']
        self.updated_nh = self.routing_table[self.src_node]['next_hop']
        self.updated_hc = self.routing_table[self.src_node]['hop_count']
        self.updated_id = self.routing_table[self.src_node]['id_num']
        updated_rtable = Updated_Routing_info(
            self.updated_dest, self.updated_nh, self.updated_hc, self.updated_id)
        n_nodes_to_bcast = [n for n in self.graph.neighbors(self.src_node)]

        for index_nnode, n_nodes_to_bcast in enumerate(n_nodes_to_bcast):
            if n_nodes_to_bcast not in self.attack_nodes:
                self.rtable_info_queue[n_nodes_to_bcast].insert(
                    0, updated_rtable)

    def queue_length(self):
        # print("calling q length function - 4")

        # self.queue_empty = False
        if any(self.rtable_info_queue[node] for node in self.graph.nodes):

            # self.queue_empty = True
            self.update_table()
        else:
            print("all queues are empty")
            # print("\n final routing table", self.routing_table)
        # return self.queue_empty

    """Allocating timeslot to each node to transmit based on the queue size. The larger the queue size, higher the priority"""
    """Find the next hop for the respective destination"""
    """Ex - Routing table of 0 = {destinations = [1,2,3,4,5], next_hop = [1,2,3,2/3,2/3]
        if destination of packet in 0 node is 1, then respective next hop is 1 """

    def tdma(self):

        # print("calling tdma - 7")
        self.actions = list(self.graph.nodes)
        # print("actions before returning", self.actions)
        self.max_queue_size = max(self.queue_size)

        if self.max_queue_size > 0:
            index_of_large_queue = np.argmax(self.queue_size)
            # print("index_of_large_queue", index_of_large_queue)
            node_with_max_queue = self.actions[index_of_large_queue]
            # print("node_with_max_queue", node_with_max_queue)

        # now fetch the destination information for this node from state info

            for src, dest in enumerate(self.destinations_list):
                if index_of_large_queue == src:
                    dest_to_transmit = dest

        # fetch the routing table of index_of_large_queue

                    for key in self.routing_table:
                        if key == node_with_max_queue:

                            dest_list_to_search = self.routing_table[key]['destination']
                            next_hop_to_send = self.routing_table[key]['next_hop']
                            if dest_to_transmit in dest_list_to_search:
                                index_of_dest = dest_list_to_search.index(
                                    dest_to_transmit)
                                for nodes, next_hop in enumerate(next_hop_to_send):
                                    if nodes == index_of_dest:
                                        next_hop_found = next_hop_to_send[nodes]

                                        self.actions[index_of_large_queue] = next_hop_found
                                        break

        # else:
        #     print("send wait condition to all nodes")
        #     self.actions

        print("actions returned by dsdv", self.actions)

        return self.actions

    def read_graph(self):
        # print("read graph - 9")
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
        # print("self.collision_domain_elems", self.collision_domain_elems)

        # Find all the domains a node belong too.
        self.node_in_domains = {}
        for key, value in self.collision_domain_elems.items():
            for i in range(len(value)):
                if value[i] not in self.node_in_domains:
                    self.node_in_domains[value[i]] = [key]
                else:
                    self.node_in_domains[value[i]].append(key)
        # print("self.node_in_domains : ", self.node_in_domains)

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

        # print("self.node_action_list", self.node_action_list)

        # self.map_actions(node_action_list)

        return self.node_action_list

    def map_actions(self):
        # print("mapp actions - 8")
        valid_action_list = []
        self.node_action_list = self.read_graph()

        for node in self.graph.nodes:
            # print("action rcvd from tdma", self.actions)
            action_list = self.node_action_list[node]
            # print("action_list of a node", action_list, node)
            index = self.__get_index(node)
            # print("index of node", index, node)
            # print("self.actions", self.actions)
            next_hop = self.actions[index]
            # print("next_hop", next_hop)
            mapped_action = action_list.index(next_hop)
            # print("mapped_action", mapped_action)
            valid_action_list.append(mapped_action)
            print("valid_action_list aftr mapping", valid_action_list)
        return valid_action_list

    def __get_index(self, node):

        node_list = list(self.graph.nodes)
        index = node_list.index(node)

        return index
