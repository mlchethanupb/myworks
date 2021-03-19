import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.spaces import MultiDiscrete, Tuple, Box
import networkx as nx
import numpy as np
import random
import w_mac
from packet_MAC_RL import Packet_MAC_RL
import matplotlib.pyplot as plt
from IPython.display import clear_output
import time
from collections import defaultdict
import logging
from stable_baselines import PPO2
from Routing_Table import Routing_info
from Updated_RTable import Updated_Routing_info
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env


class MAC_RL(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, graph: nx.Graph):
        super(MAC_RL, self).__init__()
        self.graph = graph
        self.total_nodes = len(self.graph.nodes())
        # print(self.total_nodes)
        logging.basicConfig(
            filename='wmac.log',
            filemode='w',
            format='%(levelname)s:%(message)s',
            level=logging.DEBUG
        )

        logging.debug("___Init____")
        self.__initialize_rewards()
        self.__reset_stat_variables()
        # self.__reset_visualization_variables()

        """ Sequence of next function calls should not be changed """
        self.__reset_attack_nodes()
        self.__read_graph_data()
        self.__create_action_observation_space()
        self.create_routing_table(self.attack_nodes)
        self.__reset_queue()

    # --------------------------------------------------------------------------------------------

    def reset(self):

        logging.info(
            "------------------ resetting environment--------------------")

        self.__reset_stat_variables()
        # self.__reset_visualization_variables()

        """ Should be called in same order """
        self.__reset_attack_nodes()
        self.create_routing_table(self.attack_nodes)
        self.__reset_queue()
        state = self.__frame_next_state()
        logging.info("initial state in the reset: %s", state)
        arr = np.array(state)

        return(arr)

    # --------------------------------------------------------------------------------------------

    def step(self, rcvd_actions):
        logging.info("rcvd_actions: %s", rcvd_actions)

        reward = self.__perform_actions(rcvd_actions)

        next_state = self.__frame_next_state()
        nxt_state_arr = np.array(next_state)

        isdone = self.__isdone()
        info = {}

        actions_list = list(rcvd_actions)

        # punishing agent if allactions are wait and packets exist in queues
        if isdone == False and actions_list.count(1) == 0:
            reward = self.EMPTY_ACTION_REWARD

        if isdone == True:
            queue_empty = True
            for node in self.graph.nodes:
                if len(self.queues[node]) > 0:
                    reward = (-self.MAX_REWARD)*100*self.total_nodes

                    logging.info("Punishing when done even if packets remain")
                    queue_empty = False
                    break

            if queue_empty == True and self.packet_lost == 0:
                # print("Hurray !!! All packets transmitted successfully")
                logging.info("Hurray !!! All packets transmitted successfully")
                # reward = self.MAX_REWARD*self.total_nodes

        logging.info("nxt_state_arr: %s, reward: %s, isdone: %s",
                     nxt_state_arr, reward, isdone)
        return nxt_state_arr, reward, isdone, info
    # --------------------------------------------------------------------------------------------

    """ Create different constant variables used to reward the agent in different scenarios and queue-size """

    def __initialize_rewards(self):
        # Rewards
        self.MAX_REWARD = 1
        self.COLLISION_REWARD = -1
        self.QUEUE_SIZE = 5
        self.EMPTY_ACTION_REWARD = -1
    # --------------------------------------------------------------------------------------------

    """ Reset the variables used to measure the stats """

    def __reset_stat_variables(self):
        self.total_packets = self.QUEUE_SIZE * (self.total_nodes - 1)
        self.packet_delivered = 0
        self.packet_lost = 0
        self.counter = 0
        self.total_transmission = 0
        self.succ_transmission = 0
    # --------------------------------------------------------------------------------------------

    """
    Randomly assign nodes as attack nodes

    self.attack_nodes - "List" of attack nodes
    """

    def __reset_attack_nodes(self):

        self.attack_nodes = []

        for i in range(1):
            a_node = random.randrange(0, self.total_nodes)
            while (a_node in self.attack_nodes):
                a_node = random.randrange(0, self.total_nodes)

            self.attack_nodes.append(a_node)

        logging.info("self.attack_nodes: %s", self.attack_nodes)

    # --------------------------------------------------------------------------------------------
    """
    Read the network graph of the experiment and obtain the following values ###

    1. self.collision_domain_elems -- Different collosion domains and elements in the
      (type - Dictionary)            respective collision domain

    2. self.node_in_domains -- Each node as keys and in values the respective
      (type - Dictionary)     collision domain they belong to

    3. self.node_action_list -- Each node as keys and repective valid next hops as values.
      (type - Dictionary)      Used mainly to define action space and map the recieved actions
                               from agent to respective node.
    """

    def __read_graph_data(self):

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
        logging.debug("self.collision_domain_elems: %s",
                      self.collision_domain_elems)
        
        # Find all the domains a node belong too.
        self.node_in_domains = {}
        for key, value in self.collision_domain_elems.items():
            for i in range(len(value)):
                if value[i] not in self.node_in_domains:
                    self.node_in_domains[value[i]] = [key]
                else:
                    self.node_in_domains[value[i]].append(key)
        logging.debug("self.node_in_domains: %s", self.node_in_domains)
        # print("self.node_in_domains: %s", self.node_in_domains)

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

        logging.debug("self.node_action_list: %s", self.node_action_list)
        # print("self.node_action_list: %s", self.node_action_list)

    # -------------------------------------------------------------------------------------------

    """
    Create the action space and observation space variables for gym environment ###

    Preconditions -- Should be called only after
                  __reset_attack_nodes() and __read_graph_data()
    """
    # creating action space for wait or transmit action

    def __create_action_observation_space(self):
        action_space = []
        action_space = [2 for i in range(len(self.graph.nodes()))]
        self.action_space = spaces.MultiDiscrete(action_space)

    # creating observation space to have next_hop details from routing table
        observation_space = []
        for i in range(self.total_nodes):
            observation_space.append(self.total_nodes+1)

        for i in range(self.total_nodes):
            observation_space.append(self.QUEUE_SIZE * (self.total_nodes - 1))

        for i in range(len(self.attack_nodes)):
            observation_space.append(self.total_nodes)
        self.observation_space = MultiDiscrete(observation_space)

    # --------------------------------------------------------------------------------------------
    """
    Creating a routing table without defect node.
    Routing table at each node includes destination, next_hop and hop_counts for respective destination
    Defect node will not have any routing table.
    It should be called after __reset_attack_nodes()

    """

    def create_routing_table(self, attack_node):

        self.attack_nodes = attack_node
        # print("self.attack_nodes", self.attack_nodes)

        dic = {}
        for nodes in self.graph.nodes():
            dic[nodes] = {}
            self.routing_table = dic
        # print('Empty routing table\n', self.routing_table)

        # print('\n------------------------------------------------------\n')

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
                        if (nodes, n_nodes) in self.graph.edges:  # check for neighbors
                            hop_count += 1

                            nbr_dest.append(n_nodes)
                            nbr_nh.append(n_nodes)
                            nbr_hc.append(hop_count)

                            self.routing_table[nodes]['destination'] = nbr_dest
                            self.routing_table[nodes]['next_hop'] = nbr_nh
                            self.routing_table[nodes]['hop_count'] = nbr_hc
                            self.routing_table[nodes]['id_num'] = self_id

        self.Broadcast_NbrTable()  # broadcast the rputing table to neighbor nodes

        # print("Final Routing table", self.routing_table)

        return self.routing_table

    def Broadcast_NbrTable(self):
        
        

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

                # insert this routing table info into queue of neighbor nodes
                neighbor_nodes = [n for n in self.graph.neighbors(src_nodes)]
                for idx, nbr_node in enumerate(neighbor_nodes):
                    if nbr_node not in self.attack_nodes:
                        self.rtable_info_queue[nbr_node].insert(
                            0, rtable_to_bcast)

        # print("self.rtable_info_queue", self.rtable_info_queue)

        self.queue_length()

    # each node will update their routing table according to received routing table from enighbor node
    def update_table(self):

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

                            else:  # if all destinations are present check for the hop count with the less value and update
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

        if any(self.rtable_info_queue[node] for node in self.graph.nodes):

            self.update_table()
        else:
            # print("all queues are empty")
            # print("\n final routing table", self.routing_table)
            ...

    # -------------------------------------------------------------------------------------------

    """
    Create queue for each node and assign packets with different destination. ###

    Precondition -- Should be called only after __reset_attack_nodes()
    """

    def __reset_queue(self):

        # Creating queue for each node
        self.queues = {i: [] for i in self.graph.nodes}

        # Add packets to the queue.
        for node in self.graph.nodes:
            if node not in self.attack_nodes:  # If node is defect node, do not add packets.
                for count in range(self.QUEUE_SIZE):
                    self.src = node  # node is the source
                    self.dest = random.randrange(
                        0, self.total_nodes)  # find random destination
                    while self.src == self.dest or self.dest in self.attack_nodes:
                        self.dest = random.randrange(0, self.total_nodes)
                    # Add respective next-hop for the destination from routing table
                    self.nxt_hop_to_transmit = self.fetch_nh_from_RTable(
                        node, self.dest)

                    # create a packet with source, destination and next_hop details
                    packet = Packet_MAC_RL(
                        self.src, self.dest, self.nxt_hop_to_transmit)  # Create packet
                    # adding packet to the queue.
                    self.queues[self.src].insert(0, packet)

    # -------------------------------------------------------------------------------------------

    """
    Fetch the next-hop for the destination from routing table

    This will return next-hop for each packet's destination

    """

    def fetch_nh_from_RTable(self, node, dest):
        self.dest = dest
        
        dest_list_to_search = self.routing_table[node]['destination']
        nxt_hop_list_search = self.routing_table[node]['next_hop']
        if (self.dest in dest_list_to_search):
            dest_index = dest_list_to_search.index(self.dest)
            self.nh_to_transmit = nxt_hop_list_search[dest_index]
            

        return self.nh_to_transmit

    # -------------------------------------------------------------------------------------------

    """  
    Frame the "state/observation list" with next-hop of first packet in each node queue
    and the attack node

    Precondition -- Should be called after __reset_queue() and __reset_attack_nodes()
    Returns - "List"    
    """

    def __frame_next_state(self):
        # next state =  next-hop to send packet + attack nodes status
        next_state = []  # empty list for next_state

        # Add next-hop of first packet in the queue.
        for node in self.graph.nodes:
            if len(self.queues[node]):
                node_queue = self.queues[node]
                nxt_hop_of_packet = node_queue[len(node_queue)-1].nxt_hop
                next_state.append(nxt_hop_of_packet)
                # print("state", next_state)
            else:
                next_state.append(self.total_nodes)

        for node in self.graph.nodes:
            next_state.append(len(self.queues[node]))

        for node in self.attack_nodes:
            next_state.append(node)

        return (next_state)
    # --------------------------------------------------------------------------------------------

    """
    Checks if all the queues are empty or if the counter has exceeded value (avoid loops). ###

    Returns "True" or "False"
    """

    def __isdone(self):
        queue_empty = True
        # Execution is completed if packet queue in all the nodes are empty.

        if any(self.queues[node] for node in self.graph.nodes):
            queue_empty = False

        counter_exceeded = True
        # Condition to avoid loops.
        if self.counter > 100*self.total_nodes:
            counter_exceeded = True
            logging.error("Max counter exceeded")
        else:
            counter_exceeded = False
            self.counter += 1

        isdone = False
        if queue_empty or counter_exceeded:
            isdone = True
            logging.info('packets delivered %s ', self.packet_delivered)
            logging.info('packet_lost %s', self.packet_lost)

        return isdone
    # --------------------------------------------------------------------------------------------
    """
    Find the index of the node in the action list.

    As the node positions is not in sorted order, it is necessary to find the right index to determine
    the repective action in action list.

    Returns - Integer
    """

    def __get_index(self, node):

        node_list = list(self.graph.nodes)
        index = node_list.index(node)

        return index

    # --------------------------------------------------------------------------------------------

    """
    Function to retrieve the number of packets lost stat.

    Returns - Integer

    """

    def get_packet_lost(self):
        return self.packet_lost
    # --------------------------------------------------------------------------------------------

    """
    Function to retrieve total number of transmission stat.

    Returns - Integer

    """

    def get_total_transmission(self):
        return self.total_transmission

    # --------------------------------------------------------------------------------------------

    """
    Function to retrieve total number of successfull transmission stat.

    Returns - Integer

    """

    def get_succ_transmission(self):
        return self.succ_transmission

    # --------------------------------------------------------------------------------------------

    """
    Function to retrieve the number of packets delivered stat.

    Returns - Integer

    """

    def get_packet_delivered(self):
        return self.packet_delivered

    # --------------------------------------------------------------------------------------------
    """
    Function to retrieve the total number of packets sent stat.

    Returns - Integer

    """

    def get_total_packet_sent(self):
        return self.total_packets
    # --------------------------------------------------------------------------------------------
    """
    Retrun list of queue sizes of each node.
    """

    def get_queue_sizes(self):

        queue_size_list = []
        for node in self.graph.nodes:
            queue_size_list.append(len(self.queues[node]))

        return queue_size_list

    # --------------------------------------------------------------------------------------------

    """
    Receives the action_list to wait/transmit and transfers packet from one node to next-hop based on the wireless 
    transmission rules. 

    -- Negative reward are given for packet loss with following scenarios 

      1. Two nodes transmitting in same collision domain results in packet loss
      2. Two nodes of different collision domain transferring to intermediate nodes 
         results in packet loss (Hidden terminal problem)
      

    -- Positive reward is given when packet reachs the destination
    -- Positive reward is also reduced with factor of hopcount taken to reach destination.

    """

    def __perform_actions(self, actions):
        reward = 0
        state_info = self.__frame_next_state()
        for nodes in self.graph.nodes:
            index_of_nodes = self.__get_index(nodes)
            action_of_node = actions[index_of_nodes]
            logging.debug('nodes: %s', nodes)
            logging.debug('index of node %s', index_of_nodes)
            logging.debug('action_of_node: %s', action_of_node)

            if(action_of_node == 1):
                queue = self.queues[nodes]
                
                if(len(queue)):
                    qs_list = self.get_queue_sizes()
                    packet_to_send = queue.pop()
                    self.total_transmission += 1
                    domain_list = self.node_in_domains[nodes]
                    logging.debug('domain_list %s', domain_list)
                    
                    num_nodes_transmitting = 0
                    for domain in domain_list:
                        
                        collision_domain_elements = self.collision_domain_elems[domain]
                        logging.debug('collision_domain_elems %s',
                                      collision_domain_elements)
                        domain_key = domain
                        

                        for elems in collision_domain_elements:
                            logging.debug(
                                'elems in collision domain list %s', elems)
                            if elems != nodes:
                                elems_action = []
                                index_of_elems = self.__get_index(elems)
                                elems_action.append(actions[index_of_elems])
                                logging.debug('elems_action %s', elems_action)
                                for ele_action in elems_action:
                                    if ele_action == 1 and elems not in self.attack_nodes and (self.queues[elems]):
                                        
                                        num_nodes_transmitting += 1
                                        break

                    logging.debug('num_nodes_transmitting %s',
                                  num_nodes_transmitting)

                    if num_nodes_transmitting >= 1:
                        self.packet_lost += 1
                    
                        reward = self.COLLISION_REWARD
                        
                        logging.debug("collision occurred")
                        self.collision_occured = True
                        break
                    elif (self.__hidden_terminal_problem(actions, nodes, domain_key, qs_list, packet_to_send, state_info)):
                        reward = self.COLLISION_REWARD
                        self.packet_lost += 1
                        logging.debug("Hidden terminal problem")
                        self.collision_occured = True
                        break

                    else:
                        next_hop_for_source = packet_to_send.nxt_hop
                        destination_for_source = packet_to_send.dest
                        if(next_hop_for_source == destination_for_source):
                            logging.debug(
                                "Succesfull transmission to destination")
                            self.packet_delivered += 1
                            reward += (self.MAX_REWARD)
                            self.succ_transmission += 1
                        else:
                            reward -= (packet_to_send.get_hop_count())*0.1
                            packet_to_send.update_hop_count()
                            # update next hop and add into queue
                            destination_for_source = packet_to_send.dest
                            self.nh_to_deliver = self.fetch_nh_from_RTable(
                                nodes, destination_for_source)
                            packet_to_send.update_nxt_hop(self.nh_to_deliver)
                            self.queues[next_hop_for_source].insert(
                                0, packet_to_send)
                            
                            logging.debug(
                                "Successfull transmission to nexthop")
                            self.succ_transmission += 1


        return reward

    # --------------------------------------------------------------------------------------------

    def __hidden_terminal_problem(self, actions, source, domain_key, qs_list, packet_to_send, state_info):

        ret_val = False
        index = self.__get_index(source)
        domain_list_of_source = self.node_in_domains[source]

        src_nxt_hop = packet_to_send.nxt_hop
        domain_list_of_nxtHop = self.node_in_domains[src_nxt_hop]
        for domain_of_source in domain_list_of_source:
            for domain_of_nh in domain_list_of_nxtHop:
                if (domain_of_source != domain_of_nh):
                    for h_key, h_values in self.collision_domain_elems.items():
                        if (h_key == domain_of_nh):

                            h_action = []
                            for node_val in h_values:
                                node_val_index = self.__get_index(node_val)
                                h_action.append(actions[node_val_index])
                                

                            num_nodes_transmitting = 0
                            for itr in range(len(h_action)):
                                if(h_action[itr] == 1):

                                    other_queue = self.queues[h_values[itr]]
                                    node_to_check = h_values[itr]
                                    node_to_check_index = self.__get_index(
                                        node_to_check)
                                    if len(other_queue):
                                        if(source != h_values[itr] and state_info[node_to_check_index] == src_nxt_hop):
                                            
                                            num_nodes_transmitting += 1

                            if num_nodes_transmitting > 0:
                                ret_val = True
        return ret_val
    # --------------------------------------------------------------------------------------------
    """ 
    Find the index of the node in the action list. 

    As the node positions is not in sorted order, it is necessary to find the right index to determine 
    the repective action in action list. 

    Returns - Integer
    """

    def __get_index(self, node):

        node_list = list(self.graph.nodes)
        index = node_list.index(node)

        return index
