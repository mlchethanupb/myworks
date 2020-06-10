import logging
import simpy
import sys
import gym
import networkx as nx
import numpy as np
from contextlib import closing
from gym.spaces import Tuple, Discrete, Box
from io import StringIO
from simpy import Resource
from ..environment.packet import Packet

"""

Network of nodes that serves as the agent's environment.

"""


class Network(gym.Env):
    def __init__(self, config: dict, DG: nx.DiGraph = None):
        super(Network, self).__init__()

        # define experiment's parameters
        self.arrival_time = config['ARRIVAL_TIME']
        self.max_arrival_steps = config['MAX_ARRIVAL_STEPS']
        self.packet_size = config['PACKET_SIZE']

        # define environment's parameters
        self.DG = nx.read_gpickle(r'./flowsim/environment/default.gpickle') if DG is None else DG
        self.source = next(node_id for node_id, data in self.DG.nodes(data=True) if data['source'])
        self.sink = next(node_id for node_id, data in self.DG.nodes(data=True) if data['sink'])
        self.num_nodes = len(self.DG.nodes())
        self.num_links = len(self.DG.edges())
        self.max_bandwidth = max(data['bandwidth'] for i, j, data in self.DG.edges(data=True))
        self.max_packet_inputs = self.max_arrival_steps / self.arrival_time

        # define gym environment's parameters
        self.action_space = Tuple(Discrete(self.DG.out_degree(node))
                                  for node in range(1, self.num_nodes + 1) if node != self.sink)
        self.observation_space = Box(low=0.0, high=1.0, shape=(self.num_nodes + self.num_links,), dtype=np.float16)

        # FOR DEVELOPMENT:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )

    def step(self, actions):
        # process actions in the networking environment
        actions = self.map_actions(actions)
        for node, action in enumerate(actions):
            self.env.process(self.__transmit(node + 1, action)) 
        
        # run environment until the next packet arrives at some node
        self.env.run(self.timestep_event)
        self.timestep_event = self.env.event()

        # TODO: compute observations and collect rewards
        return self.__compute_observation(), self.__compute_reward(), self.__compute_isdone(), self.__compute_info()

    def reset(self):
        self.env = simpy.Environment()
        self.links = {(i, j): simpy.Container(
            self.env, data['bandwidth'], init=data['bandwidth']) for i, j, data in self.DG.edges(data=True)}
        self.queues = {i: [] for i in self.DG.nodes(data=False)}
        self.active = []
        self.arrival_steps = 0

        # register processes and events
        self.env.process(self.__arrival_process())
        self.timestep_event = self.env.event()

        # run environment until first packet arrives at source
        self.env.run(self.timestep_event)
        self.timestep_event = self.env.event()

        return self.__compute_observation()

    def __compute_observation(self):
        # represent states by the number of queued packages (fixed size)
        # normalize by the total number of packages (for NNs)
        node_repr = [len(self.queues[i]) / self.max_packet_inputs for i in range(1, self.num_nodes)]
        
        # represent links by their current load
        link_repr = [l.level / self.max_bandwidth for _, l in self.links.items()]
        
        node_repr.extend(link_repr)
        return np.asarray(node_repr, dtype=np.float16)

    def __compute_reward(self):
        raise NotImplementedError()

    def __compute_isdone(self):
        # check if all packets are at source
        return len(self.active) <= 0

    def __compute_info(self):
        return None

    def __arrival_process(self):
        while True:
            # terminate arrival process if self.max_arrival_steps packets were generated at source
            if self.arrival_steps < self.max_arrival_steps:
                self.arrival_steps += 1

            else:
                break

            # create packet and register process
            packet = Packet(self.env.now)
            self.queues[self.source].insert(0, packet)
            self.active.append(packet)
            
            if not self.timestep_event.triggered:
                self.timestep_event.succeed()
            yield self.env.timeout(self.arrival_time)

    def __transmit(self, i, j):

        # do nothing if the selected link does not exist or the queue is empty
        if (i, j) not in self.links or not self.queues[i]:
            return

        # get packet and link for transmission
        packet = self.queues[i].pop()
        link = self.links[(i, j)]

        # request capacity corresponding to bandwidth of the link or less if the
        # packet does not scoop out the link's capacity
        request_capacity = min(self.packet_size, link.level)
        if request_capacity <= 0.0:
            # the selected link is currently occupied, do nothing
            self.queues[i].insert(0, packet)

        else:
            yield link.get(request_capacity)
            # timeout until the packet is completely transmitted
            yield self.env.timeout(self.packet_size / request_capacity)
            yield link.put(request_capacity)

            # update packet and environment's statistics
            packet.update_statistics()

            # enqueue the packet's at its next node
            self.queues[j].append(packet)
            if self.sink == j:
                self.active.remove(packet)

            if not self.timestep_event.triggered:
                self.timestep_event.succeed()

    def render(self):
        """ Write environment's representation to standard output such that diagonal elements 
        denote the overall queued packet load whereas the remaining elements correspond 
        to each respective link's remaining bandwidth."""

        outfile = sys.stdout

        env_repr = [[float(sum(self.packet_size for p in self.queues[i])) if i == j else (self.links[(i, j)].level if (i, j) in self.links else '---')
                     for j in range(1, self.num_nodes + 1)] for i in range(1, self.num_nodes + 1)]

        outfile.write('\t' + '\t'.join(list(map(lambda x: str(x) + ':', range(1, self.num_nodes + 1)))) + '\n')
        for num, row in enumerate(env_repr):
            outfile.write(str(num + 1) + ': \t')
            outfile.write('\t'.join(list(map(lambda x: str(x), row))) + '\n')

        outfile.write('\n')
        closing(outfile)

    def map_actions(self, actions):
        # forbit action 'do nothing', each action forwards a packet to some node (except if the link is fully used)
        actions = list(map(lambda n, a: list(self.DG.successors(n+1))[a], range(len(actions)), actions))
        return actions

    def check_graph(self, DG):
        # TODO: check that nodes start with IDs > 0 !
        # TODO: sink is first node !
        # TODO: sink is last node !
        pass
