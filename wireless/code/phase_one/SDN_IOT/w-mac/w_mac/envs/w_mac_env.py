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
import logging
from w_mac.baseline.Routing_Table import Routing_info
from w_mac.baseline.Updated_RTable import Updated_Routing_info
from w_mac.baseline.DSDV_Agent import dsdv


class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, graph: nx.Graph):
    super(W_MAC_Env, self).__init__()
    
    self.graph = graph
    self.total_nodes = len(self.graph.nodes())
    

    #Each node can do 2 actions {Transmit, Wait}
    action_space = [2 for i in range(len(self.graph.nodes()))]
    self.action_space = spaces.MultiDiscrete(action_space)
    #nx.draw_networkx(self.graph)
    self.routing_table = {}
    

   
    logging.basicConfig(
        filename='wmac.log',
        filemode='w', 
        format='%(levelname)s:%(message)s', 
        level=logging.DEBUG
      )

    logging.debug("___Init____")
    self.__initialize_rewards()
    self.__reset_stat_variables()
    self.__reset_visualization_variables()

    """ Sequence of next function calls should not be changed """
    self.__reset_attack_nodes()
    self.__read_graph_data()
    self.__create_action_observation_space()
    self.__reset_queue()
    self.create_routing_table(self.attack_nodes)
    self.Broadcast_NbrTable()
    #self.update_table()
  
  #--------------------------------------------------------------------------------------------

  def reset(self):
        
    logging.info("------------------ resetting environment--------------------")

    self.__reset_stat_variables()
    self.__reset_visualization_variables()

    """ Should be called in same order """
    self.__reset_attack_nodes()
    self.__reset_queue() 
    state = self.__frame_next_state()
    arr = np.array(state)

    return(arr)

  #--------------------------------------------------------------------------------------------
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
            dsdv.update_table(self)
        else:
            print("all queues are empty")
            # print("\n final routing table", self.routing_table)
        # return self.queue_empty
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

  def step(self, actions):
    #logging.debug("received action: %s",rcvd_actions)
    #actions = self.actions
    #logging.debug("mapped actions: %s",actions)

    reward = self.__perform_actions(actions)

    
    print("calling predict function - 1")
    self.destinations_list_with_anode = []
    self.queue_size = []
    self.destinations_list_with_anode = self.__frame_next_state()
    self.queue_size = self.__get_queue_sizes()
    # last number is attack node info
    self.attack_node = ([self.destinations_list_with_anode[-1]])
    self.destinations_list = self.destinations_list_with_anode[:-1]
    print("self.destinations_list", self.destinations_list)

    
    #predict = dsdv.predict(self.destinations_list_with_anode, self.queue_size)
    
    
    ### next state =  dest of next packet to send + attack nodes status
    next_state = [] #empty list for next_state

    ### Add destination of first packet in the queue. 
    for node in self.graph.nodes:
      if len(self.queues[node]):
        node_queue = self.queues[node]
        next_state.append(node_queue[len(node_queue)-1].dest)
      else:
        next_state.append(self.total_nodes)
    
    for node in self.attack_nodes:
      next_state.append(node)

    nxt_state_arr = np.array(next_state)


    isdone = self.__isdone()
    info = {}

    # no_transmit = True
    # for status in actions:
    #   if status != self.total_nodes:
    #     no_transmit = False
    
    # if isdone == False and no_transmit == True:
    #   reward -= self.COLLISION_REWARD / 20

    # if isdone == True:
    #     queue_empty = True
    #     for node in self.graph.nodes:
    #         if len(self.queues[node]) > 0:
    #             reward -= self.MAX_REWARD*self.total_nodes
    #             #print("Punishing when done even if packets remain")
    #             logging.info("Punishing when done even if packets remain")
    #             queue_empty = False
    #             break
        
    #     if queue_empty == True and self.packet_lost == 0:
    #       #print("Hurray !!! All packets transmitted successfully")
    #       logging.info("Hurray !!! All packets transmitted successfully")
    #       reward += self.MAX_REWARD*self.total_nodes

    actions_list = list(actions)
    if isdone == False and actions_list.count(1) == 0 :
      reward -= 1000


    print("nxt_state_arr, reward, isdone", nxt_state_arr, reward, isdone)

    #logging.info("nxt_state_arr: %s, reward: %s, isdone: %s", nxt_state_arr, reward, isdone)
    return nxt_state_arr, reward, isdone, info


  #--------------------------------------------------------------------------------------------

  def render(self, mode='human'):

    ## @todo: Check for correctness - list is required
    nodes = self.node_in_domains

    for i in self.graph.nodes:
          queue = self.queues[i]
          print("number of packets at node",i,"=",len(queue),)


    fixed_pos = {0:[0,2],1:[0,4],2:[2,2],3:[2,4],4:[4,2],5:[4,4]}
    fixed_nodes = fixed_pos.keys()

    pos = nx.spring_layout(self.graph, pos=fixed_pos, fixed = fixed_nodes, scale=3)
    nx.draw(self.graph, pos , with_labels=True, font_weight='bold')
    nx.draw_networkx_nodes(self.graph , pos ,  nodelist = nodes , node_color = 'white',label='inactive')
    nx.draw_networkx_nodes(self.graph , pos , nodelist = self.vis_src_node_list, node_color = 'orange', label='source')
    nx.draw_networkx_nodes(self.graph , pos ,  nodelist = self.vis_nxt_hop_node_list , node_color = 'blue',label='next hop')
    nx.draw_networkx_nodes(self.graph , pos , nodelist = self.attack_nodes, node_color = 'red' , label='defect node')
    nx.draw_networkx_nodes(self.graph , pos , nodelist = self.vis_dest_list, node_color = 'green' , label='destination')


    edges1 =list(zip(self.vis_src_node_list,self.vis_nxt_hop_node_list))
        
    # for source, destination      
    nx.draw_networkx_edges(self.graph , pos , edge_color = 'gray')
    nx.draw_networkx_edges(self.graph , pos , edgelist= edges1, edge_color = 'blue')

    plt.legend(scatterpoints = 1) 
    plt.axis('off')
    plt.show()
    plt.pause(2)
    plt.close('all')


  #--------------------------------------------------------------------------------------------

  """ Create different constant variables used to reward the agent in different scenarios """
  
  def __initialize_rewards(self):
    ### Rewards
    self.MAX_REWARD = (self.total_nodes)
    self.COLLISION_REWARD = 10*self.total_nodes
    self.ATTACK_NODE_REWARD = 15 * self.total_nodes

  #--------------------------------------------------------------------------------------------

  """ Reset the variables used to measure the stats """

  def __reset_stat_variables(self):
    self.packet_delivered = 0
    self.packet_lost = 0
    self.counter = 0

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
    # action_space = []
    # for node in self.graph.nodes:
    #   action_space.append(len(self.node_action_list[node]))
    # self.action_space = spaces.MultiDiscrete(action_space)

    #Each node can do 2 actions {Transmit, Wait}
    action_space = [2 for i in range(len(self.graph.nodes()))]
    
    self.action_space = spaces.MultiDiscrete(action_space)

    ## Creating observation space 
    observation_space = []
    for i in range(self.total_nodes):
      observation_space.append(self.total_nodes+1)
    for i in range(len(self.attack_nodes)):
      observation_space.append(self.total_nodes)
    self.observation_space = MultiDiscrete(observation_space)

    logging.info("self.action_space: %s",self.action_space) 
    logging.info("self.observation_space: %s",self.observation_space)
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
                for count in range(5):
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
    
    for node in self.attack_nodes:
      next_state.append(node)
    
    return (next_state)

  #-------------------------------------------------------------------------------------------- 

  """ 
  Checks if all the queues are empty or if the counter has exceeded value (avoid loops). ###

  Returns "True" or "False"
  """

  def __isdone(self):
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
    if queue_empty or counter_exceeded:
          isdone = True
          logging.info('packets delivered %s ',self.packet_delivered)
          logging.info('packet_lost %s', self.packet_lost)
          #print('packets delivered',self.packet_delivered)
          #print('packet_lost', self.packet_lost)
    return isdone

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
    Retrun list of queue sizes of each node.  
  """
  def __get_queue_sizes(self):
        
        queue_size_list = []
        for node in self.graph.nodes:
              queue_size_list.append(len(self.queues[node]))

        return queue_size_list


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

    for id, action in enumerate(actions):
    
      """
      1. Get the list of domains the node is associated with.
      2. If it belongs to only one domain (else part)
          - Check all the actions of that node and decide accordingly
      3. If node belongs to multiple domains (if part)
          - find the value of packet next_hop and check for collosion with that nodes  
      """
   
      if (actions[id] == 1):
        queue = self.queues[id]
        qs_list = self.__get_queue_sizes()
        
        if len(queue):

          packet_2_send = queue.pop()
          domain_list = self.node_in_domains[id]
          len_domain_list = len(domain_list) 
          if  len_domain_list > 1 :
            for key in self.routing_table:
                    dest = self.routing_table[key]['destination']
                    nxt_hop = self.routing_table[key]['next_hop']
                    hop_count = self.routing_table[key]['hop_count']

            # for itr in range(len_domain_list):
            #   if nxt_hop in self.collision_domain[domain_list[itr]]:
            #     node_list = self.collision_domain[domain_list[itr]]
            #     break
            node_list = list(self.graph.nodes)
            action_sublist = [actions[i] for i in node_list]
            
            if(action_sublist.count(1) > 1):
              print("node ", id," transmission collision")
              self.packet_lost += 1
              reward -= 1000
            elif (self.hidden_terminal_problem(actions, id, domain_list[0], qs_list )):
              print("node ", id," transmission collision because of hidden terminal problem")
            else:
              print("node ", id," transmission SUCCESS")
              reward += 1000
              self.packet_delivered += 1

              # packet_2_send.update_hop_count()
              if (nxt_hop == dest):
                print("Packet reached destination")
              # else:
              #   rcvd_node = nxt_hop
              #   packet_2_send.update_nxt_hop(dest)
              #   print("Adding packet to the queue of ", rcvd_node)
              #   self.queues[rcvd_node].insert(0, packet_2_send)
          
          #Node belongs to single domain.
          else:
            node_list = list(self.graph.nodes)
            action_sublist = self.__get_valid_action_sublist(actions, node_list, qs_list)
            for key in self.routing_table:
                    dest = self.routing_table[key]['destination']
                    nxt_hop = self.routing_table[key]['next_hop']
                    hop_count = self.routing_table[key]['hop_count']
            # node_list = self.collision_domain[domain_list[0]]
            # action_sublist = [actions[i] for i in node_list]

            if (actions[id] == 1):
              if(action_sublist.count(1) > 1):
                print("node ", id," transmission collision")
                reward -= 1000
                self.packet_lost += 1
              elif (self.hidden_terminal_problem(actions, id, domain_list[0], qs_list )):
                print("node ", id," transmission collision because of hidden terminal problem")
                reward -= 1000
                self.packet_lost += 1
              else:
                print("node ", id," transmission SUCCESS")
                self.packet_delivered += 1
                reward += 1000

                packet_2_send.update_hop_count()
                if (nxt_hop == packet_2_send.dest):
                  print("Packet reached destination")
                #else:
                  # rcvd_node = nxt_hop
                  # packet_2_send.update_nxt_hop(packet_2_send.dest)
                  # print("Adding packet to the queue of ", rcvd_node)
                  # self.queues[rcvd_node].insert(0, packet_2_send)

        else:
          print("Action taken on empty queue")
          reward -= 1000
      else:
            print("node", id , "waiting to send")
            ...
    print('final reward', reward)
    print('packets delivered ',self.packet_delivered)
    print('packet_lost ', self.packet_lost)

    return reward
  #--------------------------------------------------------------------------------------------

  """
    Checks whether the packet transmitted by the "source" is lost due to hidden terminal problem.
    
    Retruns "True" or "False"

  """
  def hidden_terminal_problem(self, actions, source, domain_key, qs_list):
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
                if ( tmp_action == 1 ):
                    num_nodes_transmitting += 1 

          if num_nodes_transmitting > 1:
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
        #self.node_action_list = self.__read_graph_data()
        node_list = list(self.graph.nodes)
        for i_node in node_list:
            i_index = self.__get_index(i_node)
            if (actions[i_index] in range(self.total_nodes)) and (qs_list[i_index] > 0):
                valid_act_sublist.append(1)
            else:
                valid_act_sublist.append(0)

        return valid_act_sublist

