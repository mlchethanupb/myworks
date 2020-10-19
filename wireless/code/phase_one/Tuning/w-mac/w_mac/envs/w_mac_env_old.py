import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.spaces import MultiDiscrete, Tuple, Box
import networkx as nx
import numpy as np
import random
import w_mac
# import w_mac_tune
from w_mac.envs.packet import Packet
import matplotlib.pyplot as plt
from collections import defaultdict


class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
    super(W_MAC_Env, self).__init__()
   #print("init")

    #Create the graph
    # data = [(0,2),(0,1),(1,2),(2,3),(2,4),(3,4)]
    #data = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),(2,4),(2,5),(3,4),(3,5),(4,5),(4,10),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10)]
    d = defaultdict(list)
    data = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]
    # defaultdict(<type 'list'>, {})
    for node, dest in data:
        d[node].append(dest)
    print(d)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)
    nx.draw(G)


    # self.graph = nx.Graph()
    self.graph = G
    self.total_nodes = len(self.graph.nodes())


    self.packet_delivered = 0
    self.packet_lost = 0

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

    ### Attack node generation.
    self.attack_nodes = []
    # for i in range(3):
    a_node = 2
      # a_node = random.randrange(0,self.total_nodes)
      #while (a_node not in self.attack_nodes):
        #a_node = random.randrange(0,self.total_nodes)
    self.attack_nodes.append(a_node)
    print("self.attack_nodes", self.attack_nodes)

    """ Creating Action space """
    ### Action space will have 2 actions [ Nexthop list of all nodes + 1 ]
    ### Transmit action if values < Total_nodes
    ### Wait action if action is Total_nodes
    
    action_space = []
    for i in range(self.total_nodes):
      action_space.append(self.total_nodes+1)
    self.action_space = spaces.MultiDiscrete(action_space)
    print(self.action_space)
    print(self.action_space.sample())
    #print(self.action_space)
    #print(self.action_space.sample())
    
    """ Creating observation space """
    ### observation_space = [ list of all destination nodes, attacked node status for each node ]

    observation_space = []
    for i in range(self.total_nodes):
      observation_space.append(self.total_nodes+1)
    for i in range(self.total_nodes):
      observation_space.append(2)
    self.observation_space = MultiDiscrete(observation_space)
    #print(self.observation_space)
    #print(self.observation_space.sample())

    self.__reset_queue()

  """-------------------------------------------------------------------------------------------- """


  def __reset_queue(self):
    
    ### Create queue for each node  || @todo = possible extenstion for multiple packet transmition || 
    ### Create a packet, fix source and destination for now - choose randomly later (but fixed for one episode)
    ### Add packet to that queue of source. 
    ### No packets added to attacked node

    self.queues = {i: [] for i in self.graph.nodes(data=False)} 

    for i in self.graph.nodes(data=False):
      #print("-----------------------------")
      #print("Adding packets for node : ",i)  
      #Add 2 packets for each node
      if i not in self.attack_nodes:
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
        
    print("------------------ resetting environment--------------------")
    ## reset the queue
    self.attack_nodes = []
    # for i in range(3):
      # a_node = random.randrange(0,self.total_nodes)
    a_node = 2
      #while (a_node not in self.attack_nodes):
      #  a_node = random.randrange(0,self.total_nodes)
    self.attack_nodes.append(a_node)

    print("self.attack_nodes", self.attack_nodes)

    self.__reset_queue()
    self.packet_delivered = 0
    self.packet_lost = 0
    
    ### Frame the state - Next hop of all first packets in queue.
    """ initial state - destination of first packet and attacked nodes status """
    state = [] #empty list for state

    for node_queue in self.queues.values():
      if len(node_queue):
        state.append(node_queue[len(node_queue)-1].dest)
      else:
        state.append(self.total_nodes)
    
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
    reward = 0
    valid_next_hops_list =[]
    ### call an API to check validity of each action, this shud be in the form of list (0 - invalid,1 - valid) for all nodes.
    ### pass validity list into perform actions
    valid_next_hops_list  = self.check_valid_nxt_hop(actions)
    reward = self.perform_actions(actions, valid_next_hops_list)
    
    ### next state =  dest + attack nodes status
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

    no_transmit = True
    for status in actions:
      if status != self.total_nodes:
        no_transmit = False
    
    if isdone == False and no_transmit == True:
      reward -= 100

    print("nxt_state_arr, reward, isdone", nxt_state_arr, reward, isdone)
    return nxt_state_arr, reward, isdone, info
  """--------------------------------------------------------------------------------------------"""

  def check_valid_nxt_hop(self,actions):
    valid_next_hops_list = []
    
    for src_id in self.graph.nodes:

      next_hop = actions[src_id]

      if src_id in self.attack_nodes:
        valid_next_hops_list.append(0) ## invalid action for attack node
        #print("append 1")
      elif (next_hop == self.total_nodes):
        #print("append 1.1")
        valid_next_hops_list.append(0) ## wait case
      else:
         ### doubt : if src and next hop are same, do we need to punish here along with giving invalid state
      #find the collision domain of src id
        if next_hop != src_id:
              
          src_domain_list = self.node_in_domains[src_id]
          src_domain_list_count = len(src_domain_list)
          if src_domain_list_count > 1:
            for src_domain_id in range(len(src_domain_list)):
              if next_hop in self.collision_domain[src_domain_list[src_domain_id]]:
                valid_next_hops_list.append(1)
                #print("append 2")
                break
          else:
              
            if next_hop in self.collision_domain[src_domain_list[0]]:
              #print("append 4")
              valid_next_hops_list.append(1)
            else:
              #print("append 5")
              valid_next_hops_list.append(0)              
        else:
          # print('source and destination are same')
          #print("append 6")
          valid_next_hops_list.append(0)

    print('valid_next_hops_list',valid_next_hops_list)

    return valid_next_hops_list

  """-------------------------------------------------------------------------------------------- """

  def isdone(self):
    isdone = True
    #Execution is completed if packet queue in all the nodes are empty.
    for node_queue in self.queues.values():
      if len(node_queue):
        isdone = False
    return isdone

  """-------------------------------------------------------------------------------------------- """

  def perform_actions(self, actions, valid_next_hops_list):

    reward1 = 0
    reward2 = 0
    """ Reward for attacked node as a next hop """
    ### Next hop in same domain is valid_next_hop
    for id in self.graph.nodes:
      nxt_hop = actions[id]
      #print("id: ", id, "nxt_hop",nxt_hop)
    #   # print( 'source', id , 'next hop', nxt_hop)
    
      domain_list = self.node_in_domains[id]
      #print("id: ", id, "domain_list",domain_list)
    #   # for domain_id in range(len(domain_list)):
    #   #   if nxt_hop in self.collision_domain[domain_list[domain_id]] and nxt_hop != id:
    #       valid_next_hop = True

      valid_next_hop = False

      if valid_next_hops_list[id] == 1:
        valid_next_hop = True #valid next hop
        reward1 -= 1
      elif nxt_hop == self.total_nodes: ## When the action is for waiting.
        reward1 -= 1  
      else:
        valid_next_hop == False
        reward1 -= 1000

      
      ### Check if next hop defect/attack node
      if nxt_hop in self.attack_nodes:
        reward1 -= 1000
        ### Cross check this logic
        if valid_next_hop and actions[id] in range(self.total_nodes): ## next hop validity + not waiting
          if(len(self.queues[id])):
            self.packet_lost += 1
            packet_to_send = self.queues[id].pop()
          valid_next_hop = False 
          
      ### Transmit when node is not defect node
      if (actions[id] in range(self.total_nodes)) and valid_next_hop == True: 
        queue = self.queues[id]

        if(len(queue)):
          packet_to_send = queue.pop()
          domain_list_of_id = self.node_in_domains[id]
          #print("id: ", id, "domain_list_of_id",domain_list_of_id)
          len_domain_list = len(domain_list_of_id)

          ### intermediate node
          if len_domain_list > 1: 
            for domains in range(len_domain_list):
              if nxt_hop in self.collision_domain[domain_list_of_id[domains]]:
                node_list = self.collision_domain[domain_list_of_id[domains]]
                #print("intermediate id: ", id, "node_list",node_list)
                break
            ### actions for other nodes in the destination's domain
            action_validity_sublist = [valid_next_hops_list[i] for i in node_list] #valid action sublist, check for num of 1's,
            #print("intermediate id: ", id, "action_sublist",action_validity_sublist)
            #if node is attack node, give invalid state. 
            count = 0
            for validity_check_item in action_validity_sublist:
              if validity_check_item == 1:
                count += 1
            #print("count ", count)
            if count > 1:
              print('Packet collision, id:', id)
              self.packet_lost += 1
              reward2 -= 100
              
            else:
              #print('transmission success')
              reward2 -= 1

              if (nxt_hop == packet_to_send.dest):
                print("Packet reached destination node with hopcount",packet_to_send.get_hop_count() )
                self.packet_delivered +=1
                hopcount_reward = 50 * packet_to_send.get_hop_count()
                reward2 += (1000 - hopcount_reward)

              else:
                    
                path_reward = self.__is_in_shortest_path(id, packet_to_send, nxt_hop)
                reward2 += path_reward ## path reward is in negative
                #print("reward2 after path", reward2)
                print("Adding packet to the queue of ", nxt_hop)
                packet_to_send.update_hop_count()
                self.queues[nxt_hop].insert(0, packet_to_send)

          ### for single domain node
          else:
            node_list = self.collision_domain[domain_list[0]]
            #print("single domain id: ", id, "node_list",node_list)
            ### check if any node in the same domain is transmitting
            action_validity_sublist = [valid_next_hops_list[i] for i in node_list]
            #print("single domain id: ", id, "action_validity_sublist",action_validity_sublist)

            count = 0
            for validity_check_item in action_validity_sublist:
              if validity_check_item == 1:
                count += 1
            #print("count ", count)  
            if count > 1:
              self.packet_lost += 1
              print('Packet collision, id :', id)
              reward2 -= 100
              
            elif (self.hidden_terminal_problem(actions, valid_next_hops_list, id, domain_list[0])):
              reward2 -= 100
              self.packet_lost += 1
              
            else:
              #print('transmission success')
              reward2 -= 1

              if (nxt_hop == packet_to_send.dest):
                print("Packet reached destination node with hopcount",packet_to_send.get_hop_count())
                self.packet_delivered +=1
                hopcount_reward = 50 * packet_to_send.get_hop_count()
                reward2 += (1000 - hopcount_reward)
                
              else:

                path_reward = self.__is_in_shortest_path(id,packet_to_send,nxt_hop)
                reward2 += path_reward ## path reward is in negative
                #print("reward2 after path", reward2)

                print("Adding packet to the queue of single node range", nxt_hop)
                packet_to_send.update_hop_count()
                self.queues[nxt_hop].insert(0, packet_to_send)

        else:
          ## Queue length 0. Agent should not take action.
          reward2 -= 100
      else:
        if(actions[id] == self.total_nodes):
          ...
          #print('wait to transmit')
        else:
          ...
          #print('invalid next hop')
          # reward1 -=100
    

    print("reward1", reward1, "reward2", reward2)
    reward = (1) * reward1 + (1) * reward2
    #print('final reward', reward)
    print('packets delivered ',self.packet_delivered)
    print('packet_lost ', self.packet_lost)

    return reward

  """-------------------------------------------------------------------------------------------- """

  def hidden_terminal_problem(self, actions, valid_next_hops_list, src, domain_key):
    #special case - Hidden terminal problem
    ret_val = False
    nxt_hop = actions[src]
    #print("id : ", id )
    # src_nxt_hop = packet_2_send.nxt_hop
    #print("src_nxt_hop", src_nxt_hop)
    for h_key,h_values in self.collision_domain.items():
      if( nxt_hop in h_values):
        if(domain_key != h_key):
          h_action = [actions[i] for i in h_values]
          h_action_validity = [valid_next_hops_list[i] for i in h_values]
          #print("h_values : ",h_values)
          #print("h_action : ",h_action)
          #print("h_action_validity : ",h_action_validity)
          
          
          for itr in range(len(h_action)):
            if(h_action_validity[itr] == 1):
              #print("src:",src)
              #print("h_values[itr]", h_values[itr])
              if(src != h_values[itr] and h_action[itr] == nxt_hop): 
                ret_val = True

    return ret_val

  """-------------------------------------------------------------------------------------------- """

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
      #print("One")
      path_reward -= 100
    ### destination in different domain but the next hop is in same domain as that of source (looping in same domain)
    ### punish the agent
    elif src_in_domains == nxthop_in_domains:
      #print("Two")
      path_reward -= 100
    ### destination and nexthop both are same, but the next hop is not destination
    ### Pusnish the agent, not the shortest path
    elif dest_in_domains == nxthop_in_domains:
      #print("five")
      path_reward -= 100 

    else:
      #print("Three")
      ### destination domain is part of next hop domains. 
      ### i.e nexthop is the intermediate node between destination and source
      ### example: src = [1] dest = [2] nxthop = [1, 2]
      ### positive reward to agent
      for dmn_id in dest_in_domains:
          if dmn_id in nxthop_in_domains:
                #print("Four")
                path_reward += 100
                break
    
      ### destination is part of source domain but next hop is not
      ### ex: src = [1,2] dest = [1], next_hop = [2]
      ### Program Logic: 
      ### if dest_domain is part of src_domain, then nxthop_domain should be part of dest_domain
      ### else, agent is choosing the wrong path. 

      for dmn_id in dest_in_domains:
          if dmn_id in src_in_domains:
              for nh_dmn_id in nxthop_in_domains:
                    if nh_dmn_id not in dest_in_domains:
                      #print("Five")
                      path_reward -= 100
                      break


    print("path_reward:",path_reward)
    return path_reward
        

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

