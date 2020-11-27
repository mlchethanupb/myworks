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

  
class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, graph: nx.Graph):
    super(W_MAC_Env, self).__init__()
    
    self.graph = graph
    self.total_nodes = len(self.graph.nodes())
    #nx.draw_networkx(self.graph)
   
    self.__initialize_rewards()
    self.__reset_stat_variables()
    self.__reset_visualization_variables()

    """ Sequence of next function calls should not be changed """
    self.__reset_attack_nodes()
    self.__read_graph_data()
    self.__create_action_observation_space()
    self.__reset_queue()

  #--------------------------------------------------------------------------------------------

  def reset(self):
        
    print("------------------ resetting environment--------------------")

    self.__reset_stat_variables()
    self.__reset_visualization_variables()

    """ Should be called in same order """
    self.__reset_attack_nodes()
    self.__reset_queue() 
    state = self.__frame_next_state()
    arr = np.array(state)

    return(arr)

  #--------------------------------------------------------------------------------------------

  def step(self, rcvd_actions):
    #print("received action",rcvd_actions)

    actions = self.__map_to_valid_actions(rcvd_actions)
    reward = 0

    reward = self.__perform_actions(actions)
    
    next_state = self.__frame_next_state()
    nxt_state_arr = np.array(next_state)
    
    isdone = self.__isdone()
    info = {}

    no_transmit = True
    for status in actions:
      if status != self.total_nodes:
        no_transmit = False
    
    if isdone == False and no_transmit == True:
      reward -= self.COLLISION_REWARD / 2

    if isdone == True:
        queue_empty = True
        for node in self.graph.nodes:
            if len(self.queues[node]) > 0:
                reward -= self.MAX_REWARD*10*self.total_nodes
                print("Punishing when done if packets remain")
                queue_empty = False
                break
        
        if queue_empty == True and self.packet_lost == 0:
          print("Hurray !!! All packets transmitted successfully")
          reward += self.MAX_REWARD*self.total_nodes


    #print("nxt_state_arr, reward, isdone", nxt_state_arr, reward, isdone)
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


    edges1 =list(zip(src,self.vis_nxt_hop_node_list))
        
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
    self.MAX_REWARD = 20*(self.total_nodes + 1)
    self.COLLISION_REWARD = 1*self.total_nodes
    self.PATH_REWARD = 0.1 * self.total_nodes
    self.ATTACK_NODE_REWARD = 5 * self.total_nodes
    self.HOP_COUNT_MULT = 1

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

    #print("self.attack_nodes", self.attack_nodes)

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
                    
                        
      #print("domain_list1",domain_list1)
      #print("domain_list2",domain_list2)
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
    print("self.collision_domain_elems",self.collision_domain_elems)
     
    ### Find all the domains a node belong too.  
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
    for key,value in self.node_action_list.items():
      sorted_list = sorted(value) ## to arrange values in ascending order in dict 
      self.node_action_list[key] = sorted_list
    
    print("self.node_action_list", self.node_action_list)

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
    self.action_space = spaces.MultiDiscrete(action_space)

    ## Creating observation space 
    observation_space = []
    for i in range(self.total_nodes):
      observation_space.append(self.total_nodes+1)
    for i in range(len(self.attack_nodes)):
      observation_space.append(self.total_nodes)
    self.observation_space = MultiDiscrete(observation_space) 
        
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
    if self.counter > 20000:
          counter_exceeded = True
          print("Max counter exceeded")
    else:
          counter_exceeded = False
          self.counter += 1
                
    isdone = False
    if queue_empty or counter_exceeded:
          isdone = True
          print('packets delivered ',self.packet_delivered)
          print('packet_lost ', self.packet_lost)
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

    reward1 = 0
    reward2 = 0

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

          reward1 -= self.ATTACK_NODE_REWARD
          valid_next_hop = False

          if(len(self.queues[node])):
              #print("Packet lost due to passing to defect node",node,"index",index, actions, valid_next_hops_list)
              self.packet_lost += 1
              packet_to_send = self.queues[node].pop()
        
      ### Transmit when node is not defect node
      if (actions[index] in range(self.total_nodes)) and valid_next_hop == True:

        queue = self.queues[node]

        if(len(queue)):
          
            ### Pop the packet from the queue
            packet_to_send = queue.pop()

            self.__vis_update_src_nxthop(node,nxt_hop)

            ### Find which domain the next hop belongs, so that interference can be checked in that collision domain. 
            for domain in domain_list:
                if nxt_hop in self.collision_domain_elems[domain]:
                    node_list = self.collision_domain_elems[domain]
                    domain_key = domain ## domain_key is used to check the hidden terminal problem
                    break

            ### actions for other nodes in the nexthop collision domain
            action_sublist = []
            for i_node in node_list:
                i_index = self.__get_index(i_node)
                action_sublist.append(actions[i_index])

            num_nodes_transmitting = 0
            for tmp_action in action_sublist:
                if (tmp_action in range(self.total_nodes)):
                    num_nodes_transmitting += 1

            if num_nodes_transmitting > 1:
                #print('intermediate; Packet loss due to collision',node, index, actions)
                self.packet_lost += 1
                reward2 -= self.COLLISION_REWARD

            elif (self.__hidden_terminal_problem(actions, node, domain_key)):
                #print("intermediate; Hidden terminal problem, packet lost",node,actions, valid_next_hops_list)
                reward2 -= self.COLLISION_REWARD
                self.packet_lost += 1
              
            else:
              

              if (nxt_hop == packet_to_send.dest):
                  #print("Packet reached destination node from source:",packet_to_send.src,"to destination",packet_to_send.dest," with hopcount",packet_to_send.get_hop_count()+1)
                
                  self.__vis_update_src_dest(node,packet_to_send.dest)
                
                  self.packet_delivered +=1
                  hopcount_reward = self.HOP_COUNT_MULT * packet_to_send.get_hop_count()
                  reward2 += (self.MAX_REWARD) - hopcount_reward

              else:

                  reward2 += self.COLLISION_REWARD/10
  
                  path_reward = 0 #self.__is_in_shortest_path(node, packet_to_send, nxt_hop)
                  reward2 += path_reward ## path reward is in negative
                
                  ### successful transmission, add the packet to the queue.
                  packet_to_send.update_hop_count()
                  self.queues[nxt_hop].insert(0, packet_to_send)
                                               
        else:
          ## Queue length 0. Agent should not take action.
          reward2 -= self.COLLISION_REWARD / 2
    
    #print("reward1", reward1, "reward2", reward2)
    reward = (1) * reward1 + (1) * reward2

    #print('packets delivered ',self.packet_delivered)
    #print('packet_lost ', self.packet_lost)

    return reward

  #--------------------------------------------------------------------------------------------

  """
    Checks whether the packet transmitted by the "source" is lost due to hidden terminal problem.
    
    Retruns "True" or "False"

  """
  def __hidden_terminal_problem(self, actions, source, domain_key):
    #special case - Hidden terminal problem
    ret_val = False
    
    index = self.__get_index(source)
    nxt_hop = actions[index]

    for h_key,h_values in self.collision_domain_elems.items():
      if( nxt_hop in h_values): ## Next hop is in other collision domain. 
        if(domain_key != h_key): ## Its not same as the source collision domain
         
          h_action = []
          for i_node in h_values:
                h_action.append(actions[self.__get_index(i_node)])
          #print("h_values : ",h_values)
          #print("h_action : ",h_action)

          num_nodes_transmitting = 0
          for tmp_action in h_action:
                if (tmp_action in range(self.total_nodes)):
                    num_nodes_transmitting += 1

          if num_nodes_transmitting > 0:
                ret_val = True
                  
    return ret_val

  #--------------------------------------------------------------------------------------------

  def __is_in_shortest_path(self, src, packet_to_send, nxt_hop):
    
    path_reward = 0

    src_in_domains = self.node_in_domains[src]
    #print("src_in_domains", src_in_domains)

    dest = packet_to_send.dest
    dest_in_domains = self.node_in_domains[dest]
    #print("dest_in_domains", dest_in_domains)

    nxthop_in_domains = self.node_in_domains[nxt_hop]
    #print("nxthop_in_domains", nxthop_in_domains)

    ### source and destination are in same collision domain, but agent did not choose the destination. 
    if src_in_domains == dest_in_domains:
      path_reward -= self.PATH_REWARD
    ### destination in different domain but the next hop is in same domain as that of source
    ### (looping in same domain) punish the agent
    elif src_in_domains == nxthop_in_domains:
      path_reward -= self.PATH_REWARD

    else:

      ### destination domain is part of next hop domains. 
      ### i.e nexthop is the intermediate node between destination and source
      ### example: src = [1] dest = [2] nxthop = [1, 2]
      ### positive reward to agent
      for dmn_id in dest_in_domains:
          if dmn_id in nxthop_in_domains:
                #print("Four")
                path_reward += self.PATH_REWARD
                break
    
      ### destination is part of source domain but next hop is not
      ### ex: src = [1,2] dest = [1], next_hop = [2]
      ### Program Logic: 
      ### if dest_domain is part of src_domain, then nxthop_domain should be part of dest_domain
      ### else, agent is choosing the wrong path. 
      """
      for dmn_id in dest_in_domains:
          if dmn_id in src_in_domains:
              for nh_dmn_id in nxthop_in_domains:
                    if nh_dmn_id not in dest_in_domains:
                      path_reward -= self.PATH_REWARD
                      break
      """                     
    #print("path_reward:",path_reward)
    return path_reward

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
              #print("action_list",action_list)
              index = self.__get_index(node)
              mapped_action = action_list[actions[index]]
              #print("Node",node,"index",index,"Action: ",actions[index],"action_list",action_list ,"mapped action:",mapped_action)

              if node == mapped_action:
                    ### if action is hopping to itself then consider it as "wait" state.
                    valid_actions.append(self.total_nodes)
              elif node in self.attack_nodes:
                    ### If node is defect node, ignore the action.
                    valid_actions.append(self.total_nodes)
              else:
                    valid_actions.append(mapped_action)
              #print("Node",node,"index",index,"Action: ",actions[index],"action_list",action_list ,"mapped action:",valid_actions)

        #print("valid_actions",valid_actions)
        return valid_actions

