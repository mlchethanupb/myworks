import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.spaces import MultiDiscrete, Tuple, Box
import networkx as nx
import numpy as np
import random
import argparse
from w_mac.envs.packet import Packet


class W_MAC_Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
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
    self.collision_domain  = {0:[0,1,2],1:[2,3,4]}  #creating the collision domains
    self.common_domain = [2] #nodes common in both range

    observation_space = [5 for i in range(len(self.graph.nodes()))]
    self.observation_space = spaces.MultiDiscrete(observation_space)
    self.__reset_queue()


#   def __reset_queue(self):
#     self.queues = {i: [] for i in self.graph.nodes(data=False)}  #{1: [], 2: [], 3: [], 4: [], 5: []} create a empty list for all nodes
#     print(self.queues)

#     for i in self.graph.nodes(data=False):
#         for q_len in range(8):
#             src = i
#             dest = random.randrange(0,4)
#             domain_dest=[]
#             domain_src=[]
#             #now need to check whether the destination belong to same collision domain or not
#             #fetch the key of dest from coll_domain
#             #compare with the coll_domain of src
#             #if both have the same key, then assign dest and next_hop same
#             #else select any random num as net_hop from the same coll_domain, keep destination =dest This is for multi hop
#             for key in self.collision_domain.keys():
#                 node_list = self.collision_domain[key]
#                 print("Printing nodes in each domain", node_list)
#                 if dest in node_list:
#                     domain_dest.append(key)
#                 if src in node_list:
#                     domain_src.append(key)
#             print('domain of dest is',domain_dest) #fetch the key of dest from coll_domain {0:[0,1,2],1:[2,3,4]} it will print 0 or 1
#             print('domain of source is',domain_src) #fetch the key of source

#             if domain_dest == domain_src:
#                 print('src and destination from same domain i.e single hop')
#                 next_hop = dest
#                 packet = Packet(src,dest,next_hop)
#                 self.queues[src].insert(0, packet)
                
#             else:
#                 print('src and destination from different domain i.e multi hop')
#                 #select intermediate node common for both the range
#                 next_hop = self.common_domain
#                 packet = Packet(src,next_hop,dest)
#                 self.queues[src].insert(0, packet)

  def __reset_queue(self):
    self.queues = {i: [] for i in self.graph.nodes(data=False)}  #{1: [], 2: [], 3: [], 4: [], 5: []} create a empty list for all nodes
    print(self.queues)

    for i in graph.nodes(data=False):
    
        for q_len in range(1):
            hop_count =0
            src = i
            dest = random.randrange(0,4)
            print("Source",src,"destination",dest)
            while src == dest:
                dest = random.randrange(0,4)
                print('when src and dest were same select random dest again', dest)
            for key,values in self.collision_domain.items():
                if (src in values):  #doubt -- while selecting the range for common node what should i do?
                    source_key = key
                    print('source_key',source_key)
                if dest in values:
                    if dest == 2
                    dest_key = key
                    print('dest_key',dest_key)
                    
            if source_key == dest_key:
                print('same domain')
                next_hop = dest
                packet = Packet(src,dest,next_hop)
                self.queues[src].insert(0, packet)
                print("Packet Q",self.queues)
                
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
      pass


  def render(self, mode='human', close=False):
      pass

if __name__ == '__main__':
    

    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    config = {}
    env = W_MAC_Env()
    # # print(wireless.step([1, 0, 0, 0, 0]))
    # model = A2C("MlpPolicy", env, verbose=1)
    # model.learn(total_timesteps=25000)



    # new_state = env.reset()
    # print(new_state)
    # # rew=[]
    
    # for i in range(10):
    #     action, _states = model.predict(new_state, deterministic=True)
    #     new_state, reward, dones, info = env.step(action)
    
    #     print("Reward : ", reward,"Observation : ",new_state)

