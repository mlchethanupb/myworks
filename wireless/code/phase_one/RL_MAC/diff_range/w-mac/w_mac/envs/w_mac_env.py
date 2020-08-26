import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.spaces import MultiDiscrete, Tuple, Box
import networkx as nx
import numpy as np
import random
import w_mac
from w_mac.envs.packet import Packet



class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
   #print("init")

    #Create the graph
    self.graph = nx.Graph()
    self.graph.add_nodes_from([0, 1, 2, 3, 4])
    self.graph.add_edges_from([(0, 1), (0, 2), (1, 2), (2, 3), (2, 4), (3, 4)])
    nx.draw(self.graph, with_labels=True, font_weight='bold')
    self.packet_delivered = 0
    self.packet_lost = 0
    #Each node can do 2 actions {Transmit, Wait}
    action_space = [2 for i in range(len(self.graph.nodes()))]
    # print(action_space)
    self.action_space = spaces.MultiDiscrete(action_space)
    #creating the collision domains
    self.collision_domain = {0:[0,1,2],1:[2,3,4]}  
    self.common_domain = [2] #nodes common in both range trying to work on this still

    self.node_in_domains = {}

    for key, value in self.collision_domain.items():
      for i in range(len(value)):
        if value[i] not in self.node_in_domains: 
          self.node_in_domains[value[i]] = [key]
        else:
          self.node_in_domains[value[i]].append(key)
    print("self.node_in_domains : ",self.node_in_domains)
    
    observation_space = [5 for i in range(len(self.graph.nodes()))] #next hops are the observation space
    for i in range(5):
      observation_space.append(10)
    self.observation_space = spaces.MultiDiscrete(observation_space)
    #print(self.observation_space)
    #print(self.observation_space.sample())

    self.wait_counter = [0 for i in range(len(self.graph.nodes()))]
    self.__reset_queue()

    # #todo - next hop : only if it has a direct connection | Queue size #doubt why giving 5 as a next hop options, when 1 has only 2 options, 3 has 4 options to select net nodes
    # self.state_space = MultiDiscrete([5,5,5,5,5])#Tuple([MultiDiscrete([5,5,5,5,5]),MultiDiscrete([3,3,3,3,3])])
    # self.observation_space = MultiDiscrete([5,5,5,5,5])
    # #print(self.state_space.sample())

    """self.num_nodes = len(self.graph.nodes())
    self.num_links = len(self.graph.edges())
    self.observation_space = [Box(low=0, high=5, shape=(
             self.num_nodes,), dtype=np.int8), 
             Box(low=0, high=5, shape=(
             self.num_nodes,), dtype=np.int8)]
    print(self.observation_space)"""

    self.__reset_queue()

  #new reset queue function
  def __reset_queue(self):
    self.queues = {i: [] for i in self.graph.nodes(data=False)}  #{1: [], 2: [], 3: [], 4: [], 5: []} create a empty list for all nodes
    print(self.queues)

    for i in self.graph.nodes(data=False):
      print("-----------------------------")
      print("Adding packets for node : ",i)  
      #Add 8 packets for each node
      for count in range(8):
        src = i
        dest = random.randrange(0,5)
        while src == dest:
          dest = random.randrange(0,5)
            
        #To fetch the domain of source and destination node
        for key,values in self.collision_domain.items():
          #print("key, values, src, dest", key, values, src, dest)
          if (src in values):  
            source_key = key
          if (dest in values):
            dest_key = key
            break #destination key not present in the same collision domain
        
        #print("src_key, dest_key",source_key,dest_key)
          #w  hen source and destination belong to same domain, compared with key value of source and destination then next hop = destination      
        if source_key == dest_key:
          next_hop = dest
          print("1. src,dest,next_hop",src,dest,next_hop)
          packet = Packet(src,dest,next_hop)
          self.queues[src].insert(0, packet)
          #break #break and add next packet
          
        else:
          """
              when source and destination are in different range then find the common node of both range 
              and assign as a next hop    
          """
          source_nodes = self.collision_domain[source_key]
          dest_nodes = self.collision_domain[dest_key]
          for node in source_nodes:
              if node in dest_nodes:
                next_hop = node
          print("2. src,dest,next_hop",src,dest,next_hop)
          packet= Packet(src,dest,next_hop)
          self.queues[src].insert(0, packet)
    
    self.queue_length_list = []
    for i in self.graph.nodes(data=False):
      self.queue_length_list.append(len(self.queues[i]))
    #print("self.queue_length_list",self.queue_length_list)

  def reset(self):
    #reset the queue
    self.__reset_queue()
    self.packet_delivered = 0
    self.packet_lost = 0
    #Frame the state - Next hop of all first packets in queue.

    state = [] #empty list for state

    for node in self.queues.values():
      if len(node):
        state.append(node[len(node)-1].nxt_hop)
    
    for node in self.queues.values():
      state.append(len(node))

      """
      #for packet in node:
      while (len(node)):
        packet = node.pop()
        print('id :',packet.id)
        print('src :',packet.src)
        print('dest :',packet.dest)
        print('nxt_hop :',packet.nxt_hop)
        print('------------------------')
      """
    print(state)
    arr = np.array(state)
    #todo : add ques lenght to state space
    #return the state
    return(arr)

  def step(self, actions):
    print("received action",actions)

    #for node, action in enumerate(actions):
      #print(node, action)

    reward = self.perform_actions(actions)
    
    next_state = [] #empty list for next_state
    for node in self.queues.values():
      if len(node):
        next_state.append(node[len(node)-1].nxt_hop)
      else:
        next_state.append(0)
    
    for node in self.queues.values():
      next_state.append(len(node))
    
    nxt_state_arr = np.array(next_state)
    isdone = self.isdone()
    info = {}

    actions_list = list(actions)
    if isdone == False and actions_list.count(1) == 0 :
      reward -= 500


    print("nxt_state_arr, reward, isdone", nxt_state_arr, reward, isdone)
    return nxt_state_arr, reward, isdone, info



  def isdone(self):
    isdone = True

    #Execution is completed if packet queue in all the nodes are empty.
    for node in self.queues.values():
      if len(node):
        isdone = False
    return isdone




  def perform_actions(self, actions):

    reward = 0

    for id, action in enumerate(actions):
      """
      1. Get the list of domains the node is associated with.
      2. If it belongs to only one domain (else part)
          - Check all the actions of that node and decide accordingly
      3. If node belongs to multiple domains (if part)
          - find the value of packet next_hop and check for colloiion with that nodes  
      """
      if (actions[id] == 1):
        queue = self.queues[id]
        
        if len(queue):

          packet_2_send = queue.pop()
          domain_list = self.node_in_domains[id]
          len_domain_list = len(domain_list) 
          if  len_domain_list > 1 :
            
            nxt_hop = packet_2_send.nxt_hop
            for itr in range(len_domain_list):
              if nxt_hop in self.collision_domain[domain_list[itr]]:
                node_list = self.collision_domain[domain_list[itr]]
                break
            #print("nxt_hop, node_list",nxt_hop, node_list)
            
            action_sublist = [actions[i] for i in node_list]
            #print("a_sublist", action_sublist)
            
            if(action_sublist.count(1) > 1):
              print("node ", id," transmission collision")
              self.packet_lost += 1
              reward -= 500
            #elif (self.hidden_terminal_problem(actions, id, domain_list[0] )):
              #print("node ", id," transmission collision because of hidden terminal problem")
            else:
              print("node ", id," transmission SUCCESS")
              reward += 500
              self.packet_delivered += 1

              packet_2_send.update_hop_count()
              if (packet_2_send.nxt_hop == packet_2_send.dest):
                print("Packet reached destination")
              else:
                rcvd_node = packet_2_send.nxt_hop
                packet_2_send.update_nxt_hop(packet_2_send.dest)
                print("Adding packet to the queue of ", rcvd_node)
                self.queues[rcvd_node].insert(0, packet_2_send)

          else:
            node_list = self.collision_domain[domain_list[0]]
            action_sublist = [actions[i] for i in node_list]
            #print("a_sublist", action_sublist)
            if (actions[id] == 1):
              if(action_sublist.count(1) > 1):
                print("node ", id," transmission collision")
                reward -= 500
                self.packet_lost += 1
              elif (self.hidden_terminal_problem(actions, id, domain_list[0], packet_2_send )):
                print("node ", id," transmission collision because of hidden terminal problem")
                reward -= 500
                self.packet_lost += 1
              else:
                print("node ", id," transmission SUCCESS")
                self.packet_delivered += 1
                reward += 500

                packet_2_send.update_hop_count()
                if (packet_2_send.nxt_hop == packet_2_send.dest):
                  print("Packet reached destination")
                else:
                  rcvd_node = packet_2_send.nxt_hop
                  packet_2_send.update_nxt_hop(packet_2_send.dest)
                  print("Adding packet to the queue of ", rcvd_node)
                  self.queues[rcvd_node].insert(0, packet_2_send)

        else:
          print("Action taken on empty queue")
          reward -= 500
      else:
            #print("node", id , "waiting to send")
            ...
    """
    for id, count_val in enumerate(self.wait_counter):
      if count_val > 4 and actions[id] != 1 :
        reward -= 300
    
    for id, act_val in enumerate(actions):
      if act_val == 1:
        self.wait_counter[id] = 0
      else:
        self.wait_counter[id] += 1
    """
    """
    for id, item in enumerate(self.queue_length_list):
      if item > len(self.queues[id]):
        reward += 100
        item = len(self.queues[id])
      elif self.wait_counter[id] > 4 and item == len(self.queues[id]):
        reward -= 100

    """


    #print("self.wait_counter",self.wait_counter) 
    print('final reward', reward)
    print('packets delivered ',self.packet_delivered)
    print('packet_lost ', self.packet_lost)
    print ('test')

    return reward



  def hidden_terminal_problem(self, actions, id, domain_key, packet_2_send):
    #special case - Hidden terminal problem
    ret_val = False

    #print("id : ", id )
    src_nxt_hop = packet_2_send.nxt_hop
    #print("src_nxt_hop", src_nxt_hop)
    for h_key,h_values in self.collision_domain.items():
      if( src_nxt_hop in h_values):
        if(domain_key != h_key):
          h_action = [actions[i] for i in h_values]
          #print("h_values : ",h_values)
          #print("h_action : ",h_action)
          for itr in range(len(h_action)):
            if(h_action[itr] == 1):
              other_queue = self.queues[h_values[itr]]
              if len(other_queue):
                if(id != h_values[itr] and other_queue[len(other_queue)-1].nxt_hop == src_nxt_hop):
                  ret_val = True

    return ret_val


  def render(self, mode='human', close=False):
    print('render')


