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


class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self, graph: nx.Graph):
    super(W_MAC_Env, self).__init__()
   #print("init")

    #Create the graph
    self.graph = graph

    nx.draw(self.graph, with_labels=True, font_weight='bold')

    self.packet_delivered = 0
    self.packet_lost = 0



    """
    Commenting out previous intermediate node detection in multiple collision domain

    """




    range_domain = {} #to get the range of each node for each iteration it will get {0:{0,1,2}}
    full_range={} #to get the range of all nodes merging it with range_domain the total domain will have is {0:{0,1,2},1:{0,1,2}etc}
    for i in self.graph.nodes: 
      domain = [] #to get the domain of each node
      for j in self.graph.nodes:
        if (i,j) in self.graph.edges:      
          domain.append(i)
          domain.append(j)
      range_domain[i] = domain
    
     
    full_range.update(range_domain)
    print('Full Range with duplicates',full_range)


    fullrange_wo_dupli = {}
    sorted_list = []
    for key,value in full_range.items():
          sorted_list = sorted(value) #to arrange values in ascending order in dict and removes duplicate values of the single key
          # print('With dupli',sorted_list)

          sorted_wo_dupli = []
          for i in sorted_list:
            if i not in sorted_wo_dupli:
              sorted_wo_dupli.append(i)
          # print('sorted list wo dupli',sorted_wo_dupli)
          fullrange_wo_dupli[key] = sorted_wo_dupli
    print('fullrange_wo_dupli' ,fullrange_wo_dupli)


    """
    Finding the intermediate nodes in multi domain network

    """ 

    intermediate_nodes = []
    for ranges, nodes in fullrange_wo_dupli.items():
      for ranges1, nodes1 in fullrange_wo_dupli.items():
        if set(nodes) < set(nodes1):      #check whether values are subset of values1, if values are subset
          intermediate_nodes.append(ranges1)
    intermediate_nodes_wo_dupli = set(intermediate_nodes) #removing the duplicate intermediate nodes


    """
    Removing the range of intermediate nodes, to avoid problem with collision

    """

    for nodes in intermediate_nodes_wo_dupli:
      print('Intermediate nodes',nodes)
      del fullrange_wo_dupli[nodes]
    print('Fullrange after intermediate node deletion',fullrange_wo_dupli)



    """
    Removing the duplicate domains in the network

    """
    d2 = {tuple(v): k for k, v in fullrange_wo_dupli.items()}  # exchange keys, values
    fullrange_wo_dupli = {v: list(k) for k, v in d2.items()} 
    print('Multiple Collision Domains',fullrange_wo_dupli)
 



    #Each node can do 2 actions {Transmit, Wait}
    action_space = [2 for i in range(len(self.graph.nodes()))]
    
    self.action_space = spaces.MultiDiscrete(action_space)
    #creating the collision domains
    self.collision_domain = fullrange_wo_dupli
     
    self.common_domain = [2] #nodes common in both range trying to work on this still

    self.node_in_domains = {}

    for key, value in self.collision_domain.items():
      for i in range(len(value)):
        if value[i] not in self.node_in_domains: 
          self.node_in_domains[value[i]] = [key]
        else:
          self.node_in_domains[value[i]].append(key)
    #print("self.node_in_domains : ",self.node_in_domains)
    
    observation_space = [5 for i in range(len(self.graph.nodes()))] #next hops are the observation space
    for i in range(len(self.graph.nodes())):
      observation_space.append(10)
    self.observation_space = spaces.MultiDiscrete(observation_space)
    #print(self.observation_space)
    #print(self.observation_space.sample())

    self.wait_counter = [0 for i in range(len(self.graph.nodes()))]
    self.__reset_queue()
  """ Observation space for SDN """
    # self.observation_space = Tuple((Discrete(6),Discrete(6),Box(0, 1, shape=(1, 5))))

  """-------------------------------------------------------------------------------------------- """


  #new reset queue function
  def __reset_queue(self):
    self.queues = {i: [] for i in self.graph.nodes(data=False)}  #{1: [], 2: [], 3: [], 4: [], 5: []} create a empty list for all nodes
    #print(self.queues)

    for i in self.graph.nodes(data=False):
      #print("-----------------------------")
      #print("Adding packets for node : ",i)  
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
        

          #when source and destination belong to same domain, compared with key value of source and destination then next hop = destination      
        if source_key == dest_key:
          next_hop = dest
          print("1. src,dest,next_hop",src,dest,next_hop)
          packet = Packet(src,dest,next_hop)
          self.queues[src].insert(0, packet)
          
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
    for node in self.queues.values():
      state.append(len(node))
    """
    for i in self.wait_counter:
      state.append(i)

    print(state)
    arr = np.array(state)
    #todo : add ques lenght to state space
    #return the state
    return(arr)

  """-------------------------------------------------------------------------------------------- """

  def step(self, actions):
    print("received action",actions)

  """ Pavitra's code for Flowtable implementation """

    # next_hop = actions[0][src]
    # flowtable = collections.defautdict(list)
    # flowentry = []
    # flowentry = next_hop, dest
    # flowtable[src].append(flowentry)
    # if (len(flowtable[src] == 5)):
    #   attacked_node = src

    # flowtable_status = [0] * len(self.graph.nodes)
    # flowtable_ratio = len(flowtable[src])/5
      
    # for index,item in enumerate(flowtable_status):
    #   if index == src:
    #     flowtable_status[index] = flowtable_ratio
    #   if flowtable_status[index] == 1:
    #      attacked_node = src
    #       print('attacked_node',attacked_node)
    # print('Flow table status',flowtable_status)

    # next_state = []
    # next_state.append(flowentry)
    # next_state.append(flowtable_status)

    # reward = self.perform_actions(actions)

    #for node, action in enumerate(actions):
      #print(node, action)

    reward = self.perform_actions(actions)
    
    """ Form the next state by adding next jop of all nodes and values of wait counter"""
    next_state = [] #empty list for next_state
    for node in self.queues.values():
      if len(node):
        next_state.append(node[len(node)-1].nxt_hop)
      else:
        #invalid value
        next_state.append(999)
    
    for i in self.wait_counter:
          next_state.append(i)
    
    nxt_state_arr = np.array(next_state)


    isdone = self.isdone()
    info = {}

    actions_list = list(actions)
    if isdone == False and actions_list.count(1) == 0 :
      reward -= 1000


    print("nxt_state_arr, reward, isdone", nxt_state_arr, reward, isdone)
    return nxt_state_arr, reward, isdone, info

  """-------------------------------------------------------------------------------------------- """

  def isdone(self):
    isdone = True

    #Execution is completed if packet queue in all the nodes are empty.
    for node in self.queues.values():
      if len(node):
        isdone = False
    return isdone

  """-------------------------------------------------------------------------------------------- """

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
            
            action_sublist = [actions[i] for i in node_list]
            
            if(action_sublist.count(1) > 1):
              print("node ", id," transmission collision")
              self.packet_lost += 1
              reward -= 1000
            #elif (self.hidden_terminal_problem(actions, id, domain_list[0] )):
              #print("node ", id," transmission collision because of hidden terminal problem")
            else:
              print("node ", id," transmission SUCCESS")
              reward += 1000
              self.packet_delivered += 1

              packet_2_send.update_hop_count()
              if (packet_2_send.nxt_hop == packet_2_send.dest):
                print("Packet reached destination")
              else:
                rcvd_node = packet_2_send.nxt_hop
                packet_2_send.update_nxt_hop(packet_2_send.dest)
                print("Adding packet to the queue of ", rcvd_node)
                self.queues[rcvd_node].insert(0, packet_2_send)
          
          #Node belongs to single domain.
          else:
            node_list = self.collision_domain[domain_list[0]]
            action_sublist = [actions[i] for i in node_list]

            if (actions[id] == 1):
              if(action_sublist.count(1) > 1):
                print("node ", id," transmission collision")
                reward -= 1000
                self.packet_lost += 1
              elif (self.hidden_terminal_problem(actions, id, domain_list[0], packet_2_send )):
                print("node ", id," transmission collision because of hidden terminal problem")
                reward -= 1000
                self.packet_lost += 1
              else:
                print("node ", id," transmission SUCCESS")
                self.packet_delivered += 1
                reward += 1000

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
          reward -= 1000
      else:
            #print("node", id , "waiting to send")
            ...

    """
    for id, count_val in enumerate(self.wait_counter):
      if count_val > 4 and actions[id] != 1 :
        reward -= 100 * self.wait_counter[id]
    """

    for id, act_val in enumerate(actions):
      if act_val == 0:
        self.wait_counter[id] = 0
      else:
        self.wait_counter[id] += 1
      
      if self.wait_counter[id] > 2 :
        reward -= 100 * self.wait_counter[id] 
        print("id :", id , "wait counter reward :", -1*100*self.wait_counter[id])


    print('final reward', reward)
    print('packets delivered ',self.packet_delivered)
    print('packet_lost ', self.packet_lost)
    #print ('test')

    return reward

  """-------------------------------------------------------------------------------------------- """

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


   #def render(self, mode='human', close=False):
  #   print('render')


  def render(self, mode='human'):
          
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

        for i in self.graph.nodes(data=False):
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
        

        source_nodes = self.collision_domain[source_key]
        dest_nodes = self.collision_domain[dest_key]
        for node in source_nodes:
          if node in dest_nodes:
            next_hop = node
        packet= Packet(src,dest,next_hop)


        # Assigning labels to the nodes
        labels = {}
        labels[0] = '$0$'
        labels[1] = '$1$'
        labels[2] = '$2$'
        labels[3] = '$3$'
        labels[4] = '$4$'
        pos = nx.spring_layout(self.graph)
        nx.draw_networkx_nodes(self.graph , pos , with_labels = True , nodelist = source_nodes, node_color = 'red')
        nx.draw_networkx_nodes(self.graph , pos , with_labels = True , nodelist = dest_nodes , node_color = 'green')
        nx.draw_networkx_nodes(self.graph , pos , with_labels = True , nodelist = packet , node_color = 'blue')
        nx.draw_networkx_edges(self.graph , pos , edgelist =[(0 , 1) , (1 , 3) , (3 , 4) , (0 , 2) , (1 , 4) , (4,0) ], alpha = 0.5 , edge_color = 'black')
        nx.draw_networkx_labels(self.graph , pos , labels , font_size = 10)
        plt.axis('off')
        plt.show(block = False)
        plt.pause(3)
        plt.close('all')

