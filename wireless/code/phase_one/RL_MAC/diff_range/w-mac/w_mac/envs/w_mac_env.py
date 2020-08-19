import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.spaces import MultiDiscrete, Tuple, Box
import networkx as nx
import numpy as np
import random
from w_mac.envs.packet import Packet


class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
   #print("init")

    #Create the graph
    self.graph = nx.Graph()
    self.graph.add_nodes_from([1, 2, 3, 4, 5])
    self.graph.add_edges_from([(1, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 5)])
    nx.draw(self.graph, with_labels=True, font_weight='bold')
    self.packet_delivered = 0
    self.packet_lost = 0
    #Each node can do 2 actions {Transmit, Wait}
    action_space = [2 for i in range(len(self.graph.nodes()))]
    # print(action_space)
    self.action_space = spaces.MultiDiscrete(action_space)
    #creating the collision domains
    self.collision_domain  = {0:[0,1,2],1:[2,3,4]}  
    self.common_domain = [2] #nodes common in both range trying to work on this still

    observation_space = [5 for i in range(len(self.graph.nodes()))] #next hops are the observation space
    self.observation_space = spaces.MultiDiscrete(observation_space)
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
    
#commented entire old reset queue function
  # def __reset_queue(self):
  #   self.queues = {i: [] for i in self.graph.nodes(data=False)}  #{1: [], 2: [], 3: [], 4: [], 5: []} create a empty list for all nodes
  #   print(self.queues)

  #   for i in self.graph.nodes(data=False):
      
  #     #Assumption : same destination for all the queued packets in the node
  #     """src = i
  #     dest = random.randrange(1,5)
  #     while (False == (self.graph.has_edge(src,dest))):
  #       dest = random.randrange(1,5)
  #     print(src,dest)"""

  #     for count in range(8):
  #       src = i
  #       dest = random.randrange(1,5)
  #       while (False == (self.graph.has_edge(src,dest))):
  #         dest = random.randrange(1,5)
  #       #print(src,dest)
  #       # create packet and register process
  #       packet = Packet(src,dest,dest) #for now consider single hop. Hence dest = nxt_hop
  #       self.queues[src].insert(0, packet)

  #   # Print the number of elements in queue.
  #   # print(len(self.queues[1]))

  #   #Frame the state - Next hop of all first packets in queue.



  #new reset queue function
  def __reset_queue(self):
    self.queues = {i: [] for i in self.graph.nodes(data=False)}  #{1: [], 2: [], 3: [], 4: [], 5: []} create a empty list for all nodes
    print(self.queues)

    for i in self.graph.nodes(data=False):
    
        for q_len in range(1):
            hop_count =0
            src = i
            dest = random.randrange(0,4)
            print("Source",src,"destination",dest)
            #source and destination should not be same, if same generate new destination
            while src == dest:
                dest = random.randrange(0,4)
                print('when src and dest were same select random dest again', dest)
            
            #To fetch the domain of source and destination node
            for key,values in self.collision_domain.items():
                if (src in values):  #doubt -- while selecting the range for common node what should i do?
                    source_key = key
                    print('source_key',source_key)
                if dest in values:
                    
                    dest_key = key
                    print('dest_key',dest_key)
            #when source and destination belong to same domain, compared with key value of source and destination
            #then next hop = destination      
            if source_key == dest_key:
                print('same domain')
                next_hop = dest
                packet = Packet(src,dest,next_hop)
                self.queues[src].insert(0, packet)
                print("Packet Q",self.queues)
            #when source and destination are in different range
            #then find the common node of both range and assign as a next hop    
            else:
                print('diff domain')
                source_nodes = self.collision_domain[source_key]
                dest_nodes = self.collision_domain[dest_key]
                for node in source_nodes:
                    if node in dest_nodes:
                        print('Common Node', node)
                        next_hop = node
                print(next_hop)
                packet= Packet(src,dest,next_hop)
                self.queues[src].insert(0, packet)
                print("Packet Q",self.queues)

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

    reward = self.find_reward(actions)
    
    next_state = [] #empty list for next_state
    for node in self.queues.values():
      if len(node):
        next_state.append(node[len(node)-1].nxt_hop)
      else:
        next_state.append(0)
    nxt_state_arr = np.array(next_state)
    isdone = self.isdone()
    info = {}

    return nxt_state_arr, reward, isdone, info



  def isdone(self):
    isdone = True

    #Execution is completed if packet queue in all the nodes are empty.
    for node in self.queues.values():
      if len(node):
        isdone = False
    return isdone


  def find_reward(self, actions):

    reward = 0
    #next hop list
    nxt_hop_list = [] #empty list for state
    for node in self.queues.values():
      if len(node):
        nxt_hop_list.append(node[len(node)-1].nxt_hop)
      else:
         nxt_hop_list.append(0)
         
    print('next hop',nxt_hop_list)
    
    #Check for Hidden terminal problem
    htp_exists = self.hidden_terminal_problem(actions, nxt_hop_list)


    if (actions[0] == 1):
      #print('one sending')
      n1_queue = self.queues[1]
      if len(n1_queue):
        packet = n1_queue.pop()
        if ((actions[1] == 1) or (actions[2] == 1) or htp_exists):
          print('n1 collision')
          self.packet_lost += 1
          reward =  reward - 100
        else:
          reward = reward + 100
          self.packet_delivered += 1
          print('one transmit success')
    
    if (actions[1] == 1):
      #print('two sending')
      n2_queue = self.queues[2]
      if len(n2_queue):
        packet = n2_queue.pop()
        if ((actions[0] == 1) or (actions[2] == 1) or htp_exists):
          print('n2 collision')
          self.packet_lost += 1
          reward = reward - 100
        else:
          reward = reward + 100
          self.packet_delivered += 1
          print('two transmit success')

    if (actions[2] == 1):
      #print('three sending')
      n3_queue = self.queues[3]
      if len(n3_queue):
        packet = n3_queue.pop()
      
        #check for next hop
        """n3_queue = self.queues[3]
        n3_first_packet = n3_queue[len(n3_queue)-1]"""
        n3_nxt_hop =  nxt_hop_list[2]
        print('n3_nxt_hop', n3_nxt_hop)

        if (n3_nxt_hop == 1) or (n3_nxt_hop == 2): 
          if (actions[0] == 1) or (actions[1] == 1):
            print('n3 collision')
            self.packet_lost += 1
            reward = reward - 100
          else:
            reward = reward + 100
            self.packet_delivered += 1
            print('three transmit success')
        elif (n3_nxt_hop == 4) or (n3_nxt_hop == 5):
          if (actions[3] == 1) or (actions[4] == 1):
            print('n3 collision')
            self.packet_lost += 1
            reward = reward - 100
          else:
            reward = reward + 100
            self.packet_delivered += 1
            print('three transmit success')

    if (actions[3] == 1):
      #print('four sending')

      n4_queue = self.queues[4]
      if len(n4_queue):
        packet = n4_queue.pop()
        if ((actions[2] == 1) or (actions[4] == 1) or htp_exists):
          print('n4 collision')
          self.packet_lost += 1
          reward = reward - 100
        else:
          reward = reward + 100
          self.packet_delivered += 1
          print('four transmit success')

    if (actions[4] == 1):
      #print('five sending')
      n5_queue = self.queues[5]
      if len(n5_queue):
        packet = n5_queue.pop()
        if ((actions[2] == 1) or (actions[3] == 1) or htp_exists) :
          print('n5 collision')
          self.packet_lost += 1
          reward = reward - 100
        else:
          print('five transmit success')
          self.packet_delivered += 1
          reward = reward + 100
    
    print('final reward', reward)
    print('packets delivered ',self.packet_delivered)
    print('packet_lost ', self.packet_lost)
    return reward



  def hidden_terminal_problem(self, actions, nxt_hop_list):
    #special case - Hidden terminal problem
    ret_val = False
    if (((nxt_hop_list[0] == 3 ) and (actions[0] == 1 ) or 
        (nxt_hop_list[1] == 3 ) and (actions[1] == 1 )) and 
       ((nxt_hop_list[3] == 3 ) and (actions[3] == 1 ) or 
        (nxt_hop_list[4] == 3 ) and (actions[4] == 1 ))):
        print('hidden terminal problem exists')
        ret_val = True
    
    return ret_val


  def render(self, mode='human', close=False):
    print('render')
