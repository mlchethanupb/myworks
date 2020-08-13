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
    print("init")

    #Create the graph
    self.graph = nx.Graph()
    self.graph.add_nodes_from([1, 2, 3, 4, 5])
    self.graph.add_edges_from([(1, 2), (1, 3), (2, 3), (3, 4), (3, 5), (4, 5)])
    #nx.draw(self.graph, with_labels=True, font_weight='bold')

    #Each node can do 2 actions {Transmit, Wait}
    self.action_space  = MultiDiscrete([2,2,2,2,2]) 
    print(self.action_space.sample())

    #todo - next hop : only if it has a direct connection | Queue size
    self.state_space = MultiDiscrete([5,5,5,5,5])#Tuple([MultiDiscrete([5,5,5,5,5]),MultiDiscrete([3,3,3,3,3])])
    print(self.state_space.sample())

    """self.num_nodes = len(self.graph.nodes())
    self.num_links = len(self.graph.edges())
    self.observation_space = [Box(low=0, high=5, shape=(
             self.num_nodes,), dtype=np.int8), 
             Box(low=0, high=5, shape=(
             self.num_nodes,), dtype=np.int8)]
    print(self.observation_space)"""

    self.__reset_queue()

  def __reset_queue(self):
    self.queues = {i: [] for i in self.graph.nodes(data=False)}
    print(self.queues)

    for i in self.graph.nodes(data=False):
      
      #Assumption : same destination for all the queued packets in the node
      src = i
      dest = random.randrange(1,5)
      while (False == (self.graph.has_edge(src,dest))):
        dest = random.randrange(1,5)
      print(src,dest)

      for count in range(2):
        # create packet and register process
        packet = Packet(src,dest,dest) #for now consider single hop. Hence dest = nxt_hop
        self.queues[src].insert(0, packet)

    # Print the number of elements in queue.
    # print(len(self.queues[1]))

    #Frame the state - Next hop of all first packets in queue.

  def reset(self):
    print('reset')

    #reset the queue
    self.__reset_queue()

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

    #todo : add ques lenght to state space
    #return the state
    return(state)

  def step(self, actions):
    print("received action",actions)

    for node, action in enumerate(actions):
      print(node, action)

    #next hop list
    nxt_hop_list = [] #empty list for state
    for node in self.queues.values():
      if len(node):
        nxt_hop_list.append(node[len(node)-1].nxt_hop)
    print('next hop',nxt_hop_list)
    
    #Check for Hidden terminal problem
    htp_exists = self.hidden_terminal_problem(actions, nxt_hop_list)


    if (actions[0] == 1):
      print('one sending')
      if ((actions[1] == 1) or (actions[2] == 1) or htp_exists):
        print('n1 collision')
      else:
        print('one transmit success')
    
    if (actions[1] == 1):
      print('two sending')
      if ((actions[0] == 1) or (actions[2] == 1) or htp_exists):
        print('n2 collision')
      else:
        print('two transmit success')

    if (actions[2] == 1):
      print('three sending')
      #check for next hop
      """n3_queue = self.queues[3]
      n3_first_packet = n3_queue[len(n3_queue)-1]"""
      n3_nxt_hop =  nxt_hop_list[2]
      print('n3_nxt_hop', n3_nxt_hop)

      if (n3_nxt_hop == 1) or (n3_nxt_hop == 2): 
        if (actions[0] == 1) or (actions[1] == 1):
          print('n3 collision')
        else:
          print('three transmit success')
      elif (n3_nxt_hop == 4) or (n3_nxt_hop == 5):
        if (actions[3] == 1) or (actions[4] == 1):
          print('n3 collision')
        else:
          print('three transmit success')


    if (actions[3] == 1):
      print('four sending')
      if ((actions[2] == 1) or (actions[4] == 1) or htp_exists):
        print('n4 collision')
      else:
        print('four transmit success')

    if (actions[4] == 1):
      print('five sending')
      if ((actions[2] == 1) or (actions[3] == 1) or htp_exists) :
        print('n5 collision')
      else:
        print('five transmit success')



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
