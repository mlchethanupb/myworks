import gym
import logging
import networkx as nx
import numpy as np
import random

from gym.spaces import Discrete, MultiDiscrete, Tuple, Box
from packet import Packet
from ray.rllib.env.multi_agent_env import MultiAgentEnv

class WirelessEnv(MultiAgentEnv):
    def __init__(self, graph: nx.Graph, train_env, return_agent_actions = False, part=False):

        self.train_env_flag = train_env
        self.graph = graph
        self.total_nodes = len(self.graph.nodes())

        logging.basicConfig(
            filename='wmac.log',
            filemode='w', 
            format='%(levelname)s:%(message)s', 
            level=logging.DEBUG
        )

        logging.debug("___Init____")
        
        self.num_agents = self.total_nodes
        logging.debug("num_agents: %s ",self.num_agents)

        self.__initialize_rewards()
        self.__reset_stat_variables()
        self.__reset_visualization_variables()

        self.__reset_attack_nodes()
        self.__read_graph_data()
        self.__reset_queue()
        self.__create_action_observation_space()
        

        #self.observation_space = gym.spaces.Box(low=0, high=800, shape=(1,))
        #self.action_space = gym.spaces.Box(low=0, high=1, shape=(1,))

    def reset(self):
        
        self.dones = set()


        logging.info("------------------ resetting environment--------------------")

        self.__reset_stat_variables()
        self.__reset_visualization_variables()

        """ Should be called in same order """
        self.__reset_attack_nodes()
        self.__reset_queue() 

        obs =  self.__get_obs_dict()
        #logging.info("Observation : %s", obs)
        return obs


    def step(self, action_dict):
        obs, rew, done, info = {}, {}, {}, {}
        #logging.debug("received action: %s",action_dict)

        action_list = self.__action_dict_to_list(action_dict)

        actions = self.__map_to_valid_actions(action_list)
        logging.info("mapped actions: %s",actions)

        reward = self.__perform_actions(actions)

        obs =  self.__get_obs_dict()

        alldone = self.__allagentsdone()

        no_transmit = True
        for status in actions:
            if status != self.total_nodes:
                no_transmit = False
        
        if alldone == False and no_transmit == True:
            reward = self.OTHER_REWARD
            ...

        if alldone == True and self.end_episode == False:
            queue_empty = True
            for node in self.graph.nodes:
                if len(self.queues[node]) > 0:
                    reward = (-self.MAX_REWARD)*100*self.total_nodes
                    #print("Punishing when done even if packets remain")
                    logging.info("Punishing when done even if packets remain")
                    queue_empty = False
                    break
            
            if queue_empty == True and self.packet_lost == 0:
                #print("Hurray !!! All packets transmitted successfully")
                logging.info("Hurray !!! All packets transmitted successfully")
                #reward += self.MAX_REWARD*self.total_nodes
        
        self.reward = reward #testing - remove later
        for agnt_i in range(self.num_agents):
            rew[agnt_i], done[agnt_i], info[agnt_i] =  reward, self.__is_agent_done(agnt_i), {}

        done["__all__"] = alldone

        logging.info("Observation : %s", obs[0])
        logging.info("reward : %s", reward)
        logging.info("done : %s", done)


        return obs, rew, done, info

    #--------------------------------------------------------------------------------------------

    def __get_obs_dict(self):
        
        obs = {}
        state = self.__frame_next_state()
        state_arr = np.array(state)

        for i in range(self.num_agents):
            obs[i] = state_arr
        
        return obs


    #--------------------------------------------------------------------------------------------
    def __action_dict_to_list(self, action_dict):
        
        action_list = [self.total_nodes for agnt in range(self.num_agents)]
        #logging.debug("__action_dict_to_list: action_dict - %s, action_list - %s ", action_dict, action_list)
        
        for agnt in range(self.num_agents):
            index = self.__get_index(agnt)
            if agnt in action_dict:
                action_list[index] = action_dict[agnt]
            else:
                action_list[index] = self.node_action_list[agnt].index(agnt)

        #logging.debug("__action_dict_to_list: action_dict - %s, action_list - %s ", action_dict, action_list)

        return action_list
    #--------------------------------------------------------------------------------------------

    """ Create different constant variables used to reward the agent in different scenarios """
    
    def __initialize_rewards(self):
        self.QUEUE_SIZE = 5
        ### Rewards
        self.MAX_REWARD = 1 
        self.COLLISION_REWARD = -1 
        self.ATTACK_NODE_REWARD = -1
        self.OTHER_REWARD = -0.1

    #--------------------------------------------------------------------------------------------

    """ Reset the variables used to measure the stats """

    def __reset_stat_variables(self):
        
        self.packet_delivered = 0
        self.packet_lost = 0
        self.counter = 0
        self.end_episode = False
        self.succ_transmission = 0
        self.total_transmission = 0
        self.total_packets = self.QUEUE_SIZE * (self.total_nodes-1)
        #for testing
        self.reward = 0

    #--------------------------------------------------------------------------------------------

    """ Reset the lists used for visualization """

    def __reset_visualization_variables(self):
        self.vis_src_node_list = []
        self.vis_nxt_hop_node_list = []
        self.vis_dest_list = []

    #--------------------------------------------------------------------------------------------

    """  
        Randomly assign nodes as attack nodes

        self.attack_nodes - "List" of attack nodes
    """
    def __reset_attack_nodes(self):
        
        self.attack_nodes = []
        
        for i in range(1):
            a_node = random.randrange(0,self.total_nodes)
            while (a_node in self.attack_nodes):
                a_node = random.randrange(0,self.total_nodes)
            
            self.attack_nodes.append(a_node)
        
        #self.attack_nodes = []
        logging.info("self.attack_nodes: %s", self.attack_nodes)


    #--------------------------------------------------------------------------------------------

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
                if(self.graph.has_edge(i,j) == True):
                    
                    if i not in domain_list1:
                        domain_list1.append(i)
            
                    connected = True
                    for node in domain_list1:
                        if(self.graph.has_edge(node,j) == False):
                            connected = False
                
                    if connected == True:
                        if j not in domain_list1:
                            domain_list1.append(j)
                    else:

                        for index,values in collision_domain.items():
                    
                            connected = True
                            for node in values:
                                if(self.graph.has_edge(node,j) == False):
                                    connected = False
                            
                            if connected == True:
                                if j not in values:
                                    collision_domain[index].append(j)
                            else:
                                domain_list2 = [i,j]
                        
                            
            if len(domain_list1):
                dict_index += 1
                collision_domain[dict_index] = domain_list1
                
            if len(domain_list2):
                dict_index += 1
                collision_domain[dict_index] = domain_list2
                
        fullrange_wo_dupli = {}
        sorted_list = []
        for key,value in collision_domain.items():
            sorted_list = sorted(value) ## to arrange values in ascending order in dict
            fullrange_wo_dupli[key] = sorted_list

        d2 = {tuple(v): k for k, v in fullrange_wo_dupli.items()}  # exchange keys, values
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
            fullrange_wo_dupli.pop(key,None)
        
        ### creating the collision domains
        self.collision_domain_elems = fullrange_wo_dupli
        logging.debug("self.collision_domain_elems: %s",self.collision_domain_elems)
        
        ### Find all the domains a node belong too.  
        self.node_in_domains = {}
        for key, value in self.collision_domain_elems.items():
            for i in range(len(value)):
                if value[i] not in self.node_in_domains: 
                    self.node_in_domains[value[i]] = [key]
                else:
                    self.node_in_domains[value[i]].append(key)
        logging.debug("self.node_in_domains: %s", self.node_in_domains)

        """Create list of all the valid actions for each node"""
        self.node_action_list = {i: [] for i in self.graph.nodes(data=False)}

        for node in self.graph.nodes:
            coll_domain_list = self.node_in_domains[node]
            for id in coll_domain_list:
                for this_node in self.collision_domain_elems[id]:
                    if this_node not in self.node_action_list[node]:
                            self.node_action_list[node].append(this_node)

        sorted_list = []
        for key,value in self.node_action_list.items():
            sorted_list = sorted(value) ## to arrange values in ascending order in dict 
            self.node_action_list[key] = sorted_list
        
        logging.debug("self.node_action_list: %s", self.node_action_list)

    #--------------------------------------------------------------------------------------------

    """  
    Create the action space and observation space variables for gym environment ###

    Preconditions -- Should be called only after 
                    __reset_attack_nodes() and __read_graph_data()
    """
    
    def __create_action_observation_space(self):

        ## Creating Action space
        action_space = []
        for node in self.graph.nodes:
            action_space.append(len(self.node_action_list[node]))
        self.action_space = MultiDiscrete(action_space)

        ## Creating observation space 
        observation_space = []
        for i in range(self.total_nodes):
            observation_space.append(self.total_nodes + 1)
        for i in range(self.total_nodes):
            observation_space.append(self.QUEUE_SIZE * self.num_agents)        
        for i in range(len(self.attack_nodes)):
            observation_space.append(self.total_nodes)
        self.observation_space = MultiDiscrete(observation_space)

        logging.info("self.action_space: %s",self.action_space) 
        logging.info("self.observation_space: %s",self.observation_space)


    #--------------------------------------------------------------------------------------------

    """  
        With given agent id, return the action space

    """

    def get_agent_action_space(self, agent_id):
        
        # If agent_id is not foumd, return action_space as 0
        action_space = 0

        if agent_id < self.num_agents:
            for node in self.graph.nodes:
                if node == agent_id:
                    action_space = len(self.node_action_list[node])
        
        return Discrete(action_space)

    #--------------------------------------------------------------------------------------------

    """
    Create queue for each node and assign packets with different destination. ###

    Precondition -- Should be called only after __reset_attack_nodes() 
    """

    def __reset_queue(self):
        
        ### Creating queue for each node
        self.queues = {i: [] for i in self.graph.nodes} 

        ### Add packets to the queue. 
        for node in self.graph.nodes:
            if node not in self.attack_nodes: ## If node is defect node, do not add packets.
                    for count in range(self.QUEUE_SIZE):
                        self.src = node   ## node is the source
                        self.dest = random.randrange(0,self.total_nodes)  ## find random destination
                        while self.src == self.dest or self.dest in self.attack_nodes:
                                self.dest = random.randrange(0,self.total_nodes)
                        #print("src: ",self.src,"dest: ",self.dest) 
                        packet = Packet(self.src,self.dest)   ## Create packet
                        self.queues[self.src].insert(0, packet)   ## adding packet to the queue.

  #--------------------------------------------------------------------------------------------

    """  
    Frame the "state/observation list" with destination of first packet in each node queue
    and the attack node

    Precondition -- Should be called after __reset_queue() and __reset_attack_nodes()
    Returns - "List"    
    """
    def __frame_next_state(self):
        ### next state =  dest of next packet to send + attack nodes status
        next_state = [] #empty list for next_state

        ### Add destination of first packet in the queue. 
        for node in self.graph.nodes:
            if len(self.queues[node]):
                node_queue = self.queues[node]
                next_state.append(node_queue[len(node_queue)-1].dest)
            else:
                next_state.append(self.total_nodes)
        
        for node in self.graph.nodes:
            next_state.append(len(self.queues[node]))

        for node in self.attack_nodes:
            next_state.append(node)

        #logging.info("next_state : %s", next_state)
        return (next_state)

    #-------------------------------------------------------------------------------------------- 

    """ 
    Checks if all the queues are empty or if the counter has exceeded value (avoid loops). ###

    Returns "True" or "False"
    """

    def __allagentsdone(self):
        queue_empty = True
        #Execution is completed if packet queue in all the nodes are empty.
        for node in self.graph.nodes:
            if len(self.queues[node]):
                    queue_empty = False

        counter_exceeded = True
        ### Condition to avoid loops.
        if self.counter > 100*self.total_nodes:
            counter_exceeded = True
            logging.error("Max counter exceeded")
        else:
            counter_exceeded = False
            self.counter += 1
                    
        isdone = False
        done_condition = True
        if self.train_env_flag:
            done_condition = queue_empty or counter_exceeded or self.end_episode
        else:
            done_condition = queue_empty or counter_exceeded

        if done_condition:
            isdone = True
            logging.info('packets delivered %s ',self.packet_delivered)
            logging.info('packet_lost %s', self.packet_lost)
            logging.info("Successfull transmission %s",self.succ_transmission)
            #print('packets delivered',self.packet_delivered)
            #print('packet_lost', self.packet_lost)
        return isdone

    #-------------------------------------------------------------------------------------------- 

    """ 
    Checks if all the queues are empty or if the counter has exceeded value (avoid loops). ###

    Returns "True" or "False"
    """

    def __is_agent_done(self, agent_id):
        ret_val = False

        if 0 == len(self.queues[agent_id]):
            ret_val =  True

        return ret_val



    #--------------------------------------------------------------------------------------------
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
    
    #--------------------------------------------------------------------------------------------
    
    """
        Function to retrieve the number of packets lost stat.

        Returns - Integer

    """
    def get_packet_lost(self):
            return self.packet_lost

    """
        Function to retrieve the episode reward.

        Returns - Integer

    """
    def get_reward(self):
            return self.reward

    """
        Function to retrieve the number of successful transmission.

        Returns - Integer

    """
    def get_succ_transmissions(self):
            return self.succ_transmission

    """
        Function to retrieve the total transmission.

        Returns - Integer

    """
    def get_total_transmissions(self):
            return self.total_transmission

    """
        Function to retrieve the total packet.

        Returns - Integer

    """
    def get_total_packets(self):
            return self.total_packets
    #--------------------------------------------------------------------------------------------
    
    """
        Function to retrieve the number of packets delivered stat.

        Returns - Integer

    """
    def get_packet_delivered_count(self):
            return self.packet_delivered

    #--------------------------------------------------------------------------------------------

    """
        Retrun list of queue sizes of each node.  
    """
    def __get_queue_sizes(self):
            
        queue_size_list = []
        for node in self.graph.nodes:
            queue_size_list.append(len(self.queues[node]))

        return queue_size_list

    #--------------------------------------------------------------------------------------------
    
    """
        Store the source and next hop information for visualization 
    """
    def __vis_update_src_nxthop(self, src, nxthop):
        
        if src not in self.vis_src_node_list:
            self.vis_src_node_list.append(src)
        
        if nxthop not in self.vis_nxt_hop_node_list:
            self.vis_nxt_hop_node_list.append(nxthop)
        
    #--------------------------------------------------------------------------------------------
    """
        Store the source and destination information for visualization 
    """
    def __vis_update_src_dest(self, src, dest):

        if src not in self.vis_src_node_list:
            self.vis_src_node_list.append(src)
        
        if dest not in self.vis_dest_list:
            self.vis_dest_list.append(dest)


    #--------------------------------------------------------------------------------------------


    """
        Receives the action_list and transfers packet from one node to other based on the wireless 
        transmission rules. 

        -- Negative reward are given for packet loss with following scenarios 

        1. Two nodes transmitting in same collision domain results in packet loss
        2. Two nodes of different collision domain transferring to intermediate nodes 
            results in packet loss (Hidden terminal problem)
        3. Packet transmitted to the defect node is also lost. 

        -- Positive reward is given when packet reachs the destination
        -- Positive reward is also reduced with factor of hopcount taken to reach destination.

    """

    def __perform_actions(self, actions):

        reward = 0

        ## Reset visualization variables  
        self.__reset_visualization_variables()

        """ Reward for attacked node as a next hop """
        ### Next hop in same domain is valid_next_hop
        for node in self.graph.nodes:

            index = self.__get_index(node)
            nxt_hop = actions[index]
            
            domain_list = self.node_in_domains[node]

            valid_next_hop = True
            
            ### Check if next hop defect/attack node
            if nxt_hop in self.attack_nodes:

                reward = self.ATTACK_NODE_REWARD
                valid_next_hop = False

                if(len(self.queues[node])):
                    logging.debug("Packet lost due to passing to defect node: %s, index: %s, actions: %s",node,index,actions)
                    self.packet_lost += 1
                    self.end_episode = True
                    packet_to_send = self.queues[node].pop()
                    self.total_transmission += 1

                break       
                
            ### Transmit when node is not defect node
            if (actions[index] in range(self.total_nodes)) and valid_next_hop == True:
                
                queue = self.queues[node]

                if(len(queue)):
                
                    qs_list = self.__get_queue_sizes()
                    ### Pop the packet from the queue
                    packet_to_send = queue.pop()
                    self.total_transmission += 1

                    self.__vis_update_src_nxthop(node,nxt_hop)  

                    ### Find which domain the next hop belongs, so that interference can be checked in that collision domain. 
                    for domain in domain_list:
                        if nxt_hop in self.collision_domain_elems[domain]:
                            node_list = self.collision_domain_elems[domain]
                            domain_key = domain ## domain_key is used to check the hidden terminal problem
                            break

                    ### get valid actions for nodes in the nexthop collision domain
                    valid_act_sublist = self.__get_valid_action_sublist(actions, node_list, qs_list)

                    num_nodes_transmitting = 0
                    for tmp_action in valid_act_sublist:
                        if (tmp_action == 1):
                            num_nodes_transmitting += 1

                    if num_nodes_transmitting > 1:
                        logging.debug('Packet loss due to collision')
                        self.packet_lost += 1
                        self.end_episode = True
                        reward = self.COLLISION_REWARD


                        logging.debug("node: %s, index: %s ,next_hop: %s, domain_list: %s, nexthop in domain: %s, next_hop_node_list: %s",
                                node, index, nxt_hop, domain_list, domain_key, node_list)
                        logging.debug("actions: %s, valid_action_sublist: %s", actions, valid_act_sublist)

                        break

                    elif (self.__hidden_terminal_problem(actions, node, domain_key, qs_list)):
                        logging.debug('Packet loss due to hidden terminal problem')
                        reward = self.COLLISION_REWARD
                        self.packet_lost += 1
                        self.end_episode = True


                        logging.debug("node: %s, index: %s ,next_hop: %s, domain_list: %s, nexthop in domain: %s, next_hop_node_list: %s",
                                node, index, nxt_hop, domain_list, domain_key, node_list)
                        logging.debug("actions: %s, valid_action_sublist: %s", actions, valid_act_sublist)
                    
                        break
                    
                    else:
                        self.succ_transmission += 1

                        if (nxt_hop == packet_to_send.dest):
                            logging.debug("Packet reached destination node from source: %s, to destination: %s, with hopcount %s",packet_to_send.src, packet_to_send.dest, packet_to_send.get_hop_count()+1)
                            
                            self.__vis_update_src_dest(node,packet_to_send.dest)
                            
                            self.packet_delivered +=1
                            reward += (self.MAX_REWARD)

                        else:

                            reward -= (packet_to_send.get_hop_count())*0.01

                            #logging.debug("Packet added to queue of next_hop: %s",nxt_hop)
                            ### successful transmission, add the packet to the queue.
                            packet_to_send.update_hop_count()
                            self.queues[nxt_hop].insert(0, packet_to_send)
                else:
                    ## Queue length 0. Agent should not take action.
                    #reward2 -= self.OTHER_REWARD
                    ...
            
            elif(actions[index] == self.total_nodes):
                #logging.info("wait")
                #reward2 -= self.WAIT_REWARD 
                ...
        

        return reward

    #--------------------------------------------------------------------------------------------

    """
        Checks whether the packet transmitted by the "source" is lost due to hidden terminal problem.
        
        Retruns "True" or "False"

    """
    def __hidden_terminal_problem(self, actions, source, domain_key, qs_list):
        #special case - Hidden terminal problem
        ret_val = False
        
        index = self.__get_index(source)
        nxt_hop = actions[index]

        for h_key,h_values in self.collision_domain_elems.items():
            if( nxt_hop in h_values): ## Next hop is in other collision domain. 
                if(domain_key != h_key): ## Its not same as the source collision domain

                    h_action = self.__get_valid_action_sublist(actions,h_values,qs_list)
                    num_nodes_transmitting = 0

                    for tmp_action in h_action:
                        if (tmp_action == 1) and (index != self.__get_index(h_values[h_action.index(tmp_action)])):
                            num_nodes_transmitting += 1

                    # num_nodes_transmitting should be greater than 0(not 1) as we are
                    # have to check if any node is transmitting in the neighbouring collision domain
                    # when a node is transmitting to common intermediate node.
                    if num_nodes_transmitting > 0:
                            ret_val = True
                        
        return ret_val

    #--------------------------------------------------------------------------------------------

    """
        Maps the valid actions for the repective nodes from the recieved actions of the agent. 

        For example: If the collision domain as elements [3,4,5,9]; interpretation for agent
                    will be[0,1,2,3]. 

            With node "5" as source. The respective mapping is as follows:
                    0: Next hop is 3 
                    1: Next hop is 4
                    2: Wait 
                    3: Next hop is 9
    """

    def __map_to_valid_actions(self, actions):
            valid_actions = []
            
            for node in self.graph.nodes:
                action_list = self.node_action_list[node]
                index = self.__get_index(node)

                mapped_action = action_list[actions[index]]
                #logging.debug("Node: %s, index: %s, Action: %s, action_list: %s, mapped action:%s",node,index,actions[index],action_list,mapped_action)

                if node == mapped_action:
                        ### if action is hopping to itself then consider it as "wait" state.
                        valid_actions.append(self.total_nodes)
                elif node in self.attack_nodes:
                        ### If node is defect node, ignore the action.
                        valid_actions.append(self.total_nodes)
                else:
                        valid_actions.append(mapped_action)
                #logging.debug("Node: %s, index: %s, Action: %s, action_list: %s, mapped action:%s",node,index,actions[index],action_list,valid_actions)

            return valid_actions

    #--------------------------------------------------------------------------------------------

    """ Check actions in the given node list and return boolean value for each node
            1 - not wait and node has packet to send. 
            0 - wait or node queue is empty
    """
    def __get_valid_action_sublist(self, actions, node_list, qs_list):
            
            valid_act_sublist = []
            for i_node in node_list:
                i_index = self.__get_index(i_node)
                if (actions[i_index] in range(self.total_nodes)) and (qs_list[i_index] > 0):
                    valid_act_sublist.append(1)
                else:
                    valid_act_sublist.append(0)

            return valid_act_sublist