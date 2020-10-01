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
    self.total_nodes = len(self.graph.nodes())


    self.packet_delivered = 0
    self.packet_lost = 0

    """
    range_domain = {} ## to get the range of each node for each iteration it will get {0:{0,1,2}}
    full_range={} ## to get the range of all nodes merging it with range_domain the total domain will have is {0:{0,1,2},1:{0,1,2}etc}
    for i in self.graph.nodes: 
      domain = [] ## to get the domain of each node
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
          sorted_list = sorted(value) ## to arrange values in ascending order in dict and removes duplicate values of the single key
          # print('With dupli',sorted_list)

          sorted_wo_dupli = []
          for i in sorted_list:
            if i not in sorted_wo_dupli:
              sorted_wo_dupli.append(i)
          print('sorted list wo dupli',sorted_wo_dupli)
          fullrange_wo_dupli[key] = sorted_wo_dupli
    print('fullrange_wo_dupli' ,fullrange_wo_dupli)
    """
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
            
    #print("collision_domain",collision_domain)

    fullrange_wo_dupli = {}
    sorted_list = []
    for key,value in collision_domain.items():
        sorted_list = sorted(value) ## to arrange values in ascending order in dict and removes duplicate values of the single key
        # print('With dupli',sorted_list)
        fullrange_wo_dupli[key] = sorted_list
    #print('fullrange_wo_dupli' ,fullrange_wo_dupli)

    d2 = {tuple(v): k for k, v in fullrange_wo_dupli.items()}  # exchange keys, values
    fullrange_wo_dupli = {v: list(k) for k, v in d2.items()}
    #print('fullrange_wo_dupli' ,fullrange_wo_dupli)

    to_remove_index = []
    for index, values in fullrange_wo_dupli.items():
      #print(index, values)
      is_subset = False
      for test_values in fullrange_wo_dupli.values():
        #print("test_values",test_values)
        if values != test_values:
          if(set(values).issubset(set(test_values))):
            is_subset = True
            #print("subset_values",values)
            break
      if is_subset:
        to_remove_index.append(index)

    #print("to_remove_index", to_remove_index)

    for key in to_remove_index:
        fullrange_wo_dupli.pop(key,None)

    #print('fullrange_wo_dupli' ,fullrange_wo_dupli)
    
    ### Finding the intermediate nodes in multi domain network
    """
    intermediate_nodes = []
    for ranges, nodes in fullrange_wo_dupli.items():
      for ranges1, nodes1 in fullrange_wo_dupli.items():
        if set(nodes) < set(nodes1):  ## check whether values are subset of values1, if values are subset
          intermediate_nodes.append(ranges1)
    intermediate_nodes_wo_dupli = set(intermediate_nodes) ## removing the duplicate intermediate nodes


    ### Removing the range of intermediate nodes, to avoid problem with collision

    for nodes in intermediate_nodes_wo_dupli:
      print('Intermediate nodes',nodes)
      del fullrange_wo_dupli[nodes]
    print('Fullrange after intermediate node deletion',fullrange_wo_dupli)
    ### Removing the duplicate domains in the network

    d2 = {tuple(v): k for k, v in fullrange_wo_dupli.items()}  # exchange keys, values
    fullrange_wo_dupli = {v: list(k) for k, v in d2.items()} 
    #print('Multiple Collision Domains',fullrange_wo_dupli)
    """

     ### creating the collision domains
    self.collision_domain = fullrange_wo_dupli
    print("self.collision_domain",self.collision_domain)
     
    ### Find all the domains a node belong too.  
    self.node_in_domains = {}
    for key, value in self.collision_domain.items():
      for i in range(len(value)):
        if value[i] not in self.node_in_domains: 
          self.node_in_domains[value[i]] = [key]
        else:
          self.node_in_domains[value[i]].append(key)
    print("self.node_in_domains : ", self.node_in_domains)

    self.attack_nodes = [3]
    for i in range(3):
      a_node = random.randrange(0,self.total_nodes)
      #while (a_node not in self.attack_nodes):
        #a_node = random.randrange(0,self.total_nodes)
      #self.attack_nodes.append(a_node)


    print("self.attack_nodes", self.attack_nodes)

    """ Creating Action space """
    ### Action space will have 2 actions [ Nexthop list of all nodes + transmitwait list of nodes ]
    ### 1. All the nexthops that a node can take (@todo-limit the actions spaces | possible extension for multipacket transmission)
    ### 2. Each node can do 2 actions {Transmit, Wait}
    
    action_space = []
    for i in range(self.total_nodes):
      action_space.append(self.total_nodes)
    for i in range(self.total_nodes):
      action_space.append(2)
    self.action_space = spaces.MultiDiscrete(action_space)
    #print(self.action_space)
    #print(self.action_space.sample())
    
    """
    ### finding the low and high array
    lower_bound = []
    higher_bound = []

    for node in range(self.total_nodes):
      domain_list = self.node_in_domains[node]
      min_value = min(self.collision_domain[domain_list[0]])
      max_value = max(self.collision_domain[domain_list[len(domain_list)-1]])
      #print("min_value", min_value, "max_value", max_value)
      lower_bound.append(min_value)
      higher_bound.append(max_value)

    for node in range(self.total_nodes):
      lower_bound.append(0)
      higher_bound.append(1)
    print("lower_bound", lower_bound, "higher_bound",higher_bound)
    self.action_space = Box(low=np.array(lower_bound), high=np.array(higher_bound), dtype=np.uint8)
    print(self.action_space)
    print(self.action_space.sample())  
    """

    """ Creating observation space """
    ### observation_space = [ [ list of all destination nodes ], [ list of flowtable status @ each node] ]

    observation_space = []
    for i in range(self.total_nodes):
      observation_space.append(self.total_nodes+1)
    for i in range(self.total_nodes):
      observation_space.append(2)
    self.observation_space = MultiDiscrete(observation_space)
    #print(self.observation_space)
    #print(self.observation_space.sample())
    


    # | not_needed |  self.wait_counter = [0 for i in range(len(self.graph.nodes()))]
    self.__reset_queue()

  """-------------------------------------------------------------------------------------------- """


  def __reset_queue(self):
    
    ### Create queue for each node  || @todo = possible extenstion for multiple packet transmition || 
    ### Create a packet, fix source and destination for now - choose randomly later (but fixed for one episode)
    ### Add packet to that queue of source. 

    self.queues = {i: [] for i in self.graph.nodes(data=False)} 
    #print(self.queues)

    for i in self.graph.nodes(data=False):
      #print("-----------------------------")
      #print("Adding packets for node : ",i)  
      #Add 2 packets for each node
      for count in range(5):

        ### Find source and destination
        self.src = i
        self.dest = random.randrange(0,self.total_nodes)
        while self.src == self.dest or self.dest in self.attack_nodes:
          self.dest = random.randrange(0,self.total_nodes)
        #print("src: ",self.src,"dest: ",self.dest) 
        packet = Packet(self.src,self.dest)
        self.queues[self.src].insert(0, packet)

  def reset(self):
    ## reset the queue
    self.attack_nodes = [3]
    for i in range(3):
      a_node = random.randrange(0,self.total_nodes)
      #while (a_node not in self.attack_nodes):
      #  a_node = random.randrange(0,self.total_nodes)
     # self.attack_nodes.append(a_node)

    print("self.attack_nodes", self.attack_nodes)

    self.__reset_queue()
    self.packet_delivered = 0
    self.packet_lost = 0
    
    ## Frame the state - Next hop of all first packets in queue.
    """ initial state - destination of first packet and attacked nodes status """
    state = [] #empty list for state

    for node_queue in self.queues.values():
      if len(node_queue):
        state.append(node_queue[len(node_queue)-1].dest)
    
    for i in range(self.total_nodes):
      if i in self.attack_nodes:
        state.append(1)
      else:
        state.append(0)

    print(state)
    arr = np.array(state)
    #todo : add ques lenght to state space
    #return the state
    return(arr)

  """--------------------------------------------------------------------------------------------"""

  def step(self, actions):
    print("received action",actions)
    self.nxt_hop_list = []#actions[0]
    self.tw_status_list = []#actions[1]
    for id, value in enumerate(actions):
      if (id >= self.total_nodes):
        self.tw_status_list.append(value)
      else:
        self.nxt_hop_list.append(value)

    #print("nxt_hop_list: ",self.nxt_hop_list)
    #print("tw_status_list", self.tw_status_list)
    
    reward = 0
    
    reward = self.perform_actions()
    
    ### next state = curr_node + dest + flow_table_status
    next_state = [] #empty list for next_state

    for node_queue in self.queues.values():
      if len(node_queue):
        next_state.append(node_queue[len(node_queue)-1].dest)
      else:
        next_state.append(self.total_nodes)

    for i in range(self.total_nodes):
      if i in self.attack_nodes:
        next_state.append(1)
      else:
        next_state.append(0)

    nxt_state_arr = np.array(next_state)
    
    isdone = self.isdone()
    info = {}
    
    if isdone == False and self.tw_status_list.count(1) == 0 :
      reward -= 100

    print("nxt_state_arr, reward, isdone", nxt_state_arr, reward, isdone)
    return nxt_state_arr, reward, isdone, info

  """-------------------------------------------------------------------------------------------- """

  def isdone(self):
    isdone = True
    #Execution is completed if packet queue in all the nodes are empty.
    for node_queue in self.queues.values():
      if len(node_queue):
        isdone = False
    return isdone

  """-------------------------------------------------------------------------------------------- """

  def perform_actions(self):

    reward1 = 0
    reward2 = 0
    """ Reward for attacked node as a next hop """
    for id in self.graph.nodes:
      nxt_hop = self.nxt_hop_list[id]
      
      ### Verify for the valid next hop
      valid_next_hop = False
      domain_list = self.node_in_domains[id]
      for domain_id in range(len(domain_list)):
        if nxt_hop in self.collision_domain[domain_list[domain_id]] and nxt_hop != id:
          valid_next_hop = True
      
      if valid_next_hop == False:
        #print("Invalid next hop")
        reward1 -= 100
      else:
        reward1 -= 10    
      
      if nxt_hop in self.attack_nodes:
        reward1 -= 200
        if valid_next_hop and self.tw_status_list[id] == 1:
          self.packet_lost += 1

      #for tw in self.tw_status_list:
      
      if (self.tw_status_list[id] == 1) and (valid_next_hop == True):
        queue = self.queues[id]
        if len(queue):
          packet_2_send = queue.pop()
          domain_list = self.node_in_domains[id]
          len_domain_list = len(domain_list) 
          if  len_domain_list > 1 :
            # nxt_hop = packet_2_send.nxt_hop
            for itr in range(len_domain_list):
              if nxt_hop in self.collision_domain[domain_list[itr]]:
                node_list = self.collision_domain[domain_list[itr]]
                break

            action_sublist = [self.tw_status_list[i] for i in node_list]

            if(action_sublist.count(1) > 1):
              #print("node ", id," transmission collision")
              self.packet_lost += 1
              reward2 -= 100
                
            else:
              #print("node ", id, " transmission SUCCESS")
              reward2 -= 10
              # packet_2_send.update_hop_count()

              if (nxt_hop == packet_2_send.dest):
                #print("Packet reached destination")
                self.packet_delivered +=1
                reward2 += 1000
              else:
                #print("Adding packet to the queue of ", nxt_hop)
                self.queues[nxt_hop].insert(0, packet_2_send)

          #Node belongs to single domain.
          else:
            node_list = self.collision_domain[domain_list[0]]
            action_sublist = [self.tw_status_list[i] for i in node_list]
            if ((self.tw_status_list[id]) == 1):
              if(action_sublist.count(1) > 1):
                #print("node ",id, " transmission collision")
                self.packet_lost += 1
                reward2 -= 100

              elif (self.hidden_terminal_problem(self.tw_status_list, id, domain_list[0], nxt_hop)):
                #print("node ", id," transmission collision because of hidden terminal problem")
                reward2 -= 100
                self.packet_lost += 1

              else:
                #print("node ", id," transmission SUCCESS")
                reward2 -= 10

                # packet_2_send.update_hop_count()
                if (nxt_hop == packet_2_send.dest):
                  #print("Packet reached destination")
                  self.packet_delivered += 1
                  reward2 += 1000
                else:
                  #print("Adding packet to the queue of ", nxt_hop)
                  self.queues[nxt_hop].insert(0, packet_2_send)
        else:
          #print("Action taken on empty queue")
          reward2 -= 100



    # for id, action in enumerate(actions):

    #   """
    #   1. Get the list of domains the node is associated with.
    #   2. If it belongs to only one domain (else part)
    #       - Check all the actions of that node and decide accordingly
    #   3. If node belongs to multiple domains (if part)
    #       - find the value of packet next_hop and check for colloiion with that nodes  
    #   """
   
    #   if (actions[id] == 1):
    #     queue = self.queues[id]
        
    #     if len(queue):

    #       packet_2_send = queue.pop()
    #       domain_list = self.node_in_domains[id]
    #       len_domain_list = len(domain_list) 
    #       if  len_domain_list > 1 :
            
    #         nxt_hop = packet_2_send.nxt_hop
    #         for itr in range(len_domain_list):
    #           if nxt_hop in self.collision_domain[domain_list[itr]]:
    #             node_list = self.collision_domain[domain_list[itr]]
    #             break
            
    #         action_sublist = [actions[i] for i in node_list]
            
    #         if(action_sublist.count(1) > 1):
    #           print("node ", id," transmission collision")
    #           self.packet_lost += 1
    #           reward -= 1000
    #         #elif (self.hidden_terminal_problem(actions, id, domain_list[0] )):
    #           #print("node ", id," transmission collision because of hidden terminal problem")
    #         else:
    #           print("node ", id," transmission SUCCESS")
    #           reward += 1000
    #           self.packet_delivered += 1

    #           packet_2_send.update_hop_count()
    #           if (packet_2_send.nxt_hop == packet_2_send.dest):
    #             print("Packet reached destination")
    #           else:
    #             rcvd_node = packet_2_send.nxt_hop
    #             packet_2_send.update_nxt_hop(packet_2_send.dest)
    #             print("Adding packet to the queue of ", rcvd_node)
    #             self.queues[rcvd_node].insert(0, packet_2_send)
          
    #       #Node belongs to single domain.
    #       else:
    #         node_list = self.collision_domain[domain_list[0]]
    #         action_sublist = [actions[i] for i in node_list]

    #         if (actions[id] == 1):
    #           if(action_sublist.count(1) > 1):
    #             print("node ", id," transmission collision")
    #             reward -= 1000
    #             self.packet_lost += 1
    #           elif (self.hidden_terminal_problem(actions, id, domain_list[0], packet_2_send )):
    #             print("node ", id," transmission collision because of hidden terminal problem")
    #             reward -= 1000
    #             self.packet_lost += 1
    #           else:
    #             print("node ", id," transmission SUCCESS")
    #             self.packet_delivered += 1
    #             reward += 1000

    #             packet_2_send.update_hop_count()
    #             if (packet_2_send.nxt_hop == packet_2_send.dest):
    #               print("Packet reached destination")
    #             else:
    #               rcvd_node = packet_2_send.nxt_hop
    #               packet_2_send.update_nxt_hop(packet_2_send.dest)
    #               print("Adding packet to the queue of ", rcvd_node)
    #               self.queues[rcvd_node].insert(0, packet_2_send)

    #     else:
    #       print("Action taken on empty queue")
    #       reward -= 1000
    #   else:
    #         #print("node", id , "waiting to send")
    #         ...

    """
    for id, count_val in enumerate(self.wait_counter):
      if count_val > 4 and actions[id] != 1 :
        reward -= 100 * self.wait_counter[id]
    """

    # for id, act_val in enumerate(actions):
    #   if act_val == 0:
    #     self.wait_counter[id] = 0
    #   else:
    #     self.wait_counter[id] += 1
      
    #   if self.wait_counter[id] > 2 :
    #     reward -= 100 * self.wait_counter[id] 
    #     print("id :", id , "wait counter reward :", -1*100*self.wait_counter[id])

    #print("reward1", reward1, "reward2", reward2)
    reward = (0.5) * reward1 + (0.5) * reward2
    #print('final reward', reward)
    print('packets delivered ',self.packet_delivered)
    print('packet_lost ', self.packet_lost)
    #print ('test')

    return reward

  """-------------------------------------------------------------------------------------------- """

  def hidden_terminal_problem(self, tw_status_lis, id, domain_key, nxt_hop):
    #special case - Hidden terminal problem
    ret_val = False

    #print("id : ", id )
    # src_nxt_hop = packet_2_send.nxt_hop
    #print("src_nxt_hop", src_nxt_hop)
    for h_key,h_values in self.collision_domain.items():
      if( nxt_hop in h_values):
        if(domain_key != h_key):
          h_action = [self.tw_status_list[i] for i in h_values]
          #print("h_values : ",h_values)
          #print("h_action : ",h_action)
          for itr in range(len(h_action)):
            if(h_action[itr] == 1):
              #other_queue = self.queues[h_values[itr]]
              #if len(other_queue):
              if(id != h_values[itr] and self.nxt_hop_list[itr] == nxt_hop):
                ret_val = True

    return ret_val


  def render(self, mode='human'):
        queue0 = self.queues[0]
        source_node0 = []
        dest_node0 = []
        source_node1 = []
        dest_node1 = []

        if len(queue0):
          packet0 = queue0[len(queue0)-1]
          source_node0= [packet0.src]
          dest_node0 =[packet0.dest]
          
        queue1 = self.queues[1]
        if len(queue1):
          packet1 = queue1[len(queue1)-1]
          source_node1= [packet1.src]
          dest_node1 =[packet1.dest]

        

        nodes = self.node_in_domains
        # next_hop = self.nxt_hop_list


        # Assigning labels to the nodes
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos , with_labels=True, font_weight='bold')
        nx.draw_networkx_nodes(self.graph , pos ,  nodelist = nodes , node_color = 'white')
        nx.draw_networkx_nodes(self.graph , pos , nodelist = source_node0, node_color = 'red')
        nx.draw_networkx_nodes(self.graph , pos ,  nodelist = dest_node0 , node_color = 'green')
        nx.draw_networkx_nodes(self.graph , pos , nodelist = source_node1, node_color = 'orange')
        nx.draw_networkx_nodes(self.graph , pos ,  nodelist = dest_node1 , node_color = 'blue')
        nx.draw_networkx_edges(self.graph , pos , edge_color = 'black')

        plt.axis('off')
        plt.show(block = False)
        plt.pause(3)
        plt.close('all')

