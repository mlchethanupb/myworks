import logging
import simpy
import sys
import gym
import networkx as nx
import numpy as np
from contextlib import closing
from gym.spaces import Tuple, Discrete, Box, MultiDiscrete
from io import StringIO
from simpy import Resource
from ..environment.packet import Packet

"""
Network of nodes that simulate packet forwarding from some source node to a sink. The environment implements
the OpenAI Gym interface and is usable as a RL testbed.
"""


class Network(gym.Env):
    def __init__(self, config: dict, DG='default'):
        super(Network, self).__init__()

        # define experiment's parameters
        self.arrival_time = config['ARRIVAL_TIME']
        self.max_arrival_steps = config['MAX_ARRIVAL_STEPS']
        self.packet_size = config['PACKET_SIZE']

        # define environment's parameters
        self.DG = nx.read_gpickle(
            r'./flowsim/environment/default.gpickle') if DG == 'default' else nx.read_gpickle(DG)
        self.check_graph()
        self.source = next(node_id for node_id, data in self.DG.nodes(
            data=True) if data['source'])
        self.sink = next(node_id for node_id,
                         data in self.DG.nodes(data=True) if data['sink'])
        self.num_nodes = len(self.DG.nodes())
        self.num_links = len(self.DG.edges())
        self.max_bandwidth = max(data['bandwidth']
                                 for i, j, data in self.DG.edges(data=True))
        self.max_packet_inputs = self.max_arrival_steps / self.arrival_time

        # define gym environment's parameters
        # forbit 'do nothing' action & do not define an action for the sink (last node by assumption)
        self.action_space = MultiDiscrete(
            [self.DG.out_degree(node) for node in range(1, self.num_nodes)])
        self.observation_space = Box(low=0.0, high=1.0, shape=(
            self.num_nodes + self.num_links,), dtype=np.float16)

        # FOR DEVELOPMENT:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )

    def step(self, actions):
        """ Process forwarding actions for each node until an event is invoked. Here, events correspond to 
        an incoming packet at some node. """
        # process actions in the networking environment
        actions = self.map_actions(actions)
        for node, action in enumerate(actions):
            self.env.process(self.__transmit(node + 1, action))

        # run environment until the next packet arrives at some node
        self.env.run(self.timestep_event)
        self.timestep_event = self.env.event()

        # compute observations, collect rewards and decide whether the episode should be terminated
        return self.__compute_observation(), self.__compute_reward(), self.__compute_isdone(), self.__compute_info()

    def reset(self):
        """ Reset the environment, i.e. reset the network along with the input process and execute
        the environment until the first packet was generated at the source node. """
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
        """ Compute the environment's state representation at the current timestep. """
        # represent states by the number of queued packages (fixed size)
        # normalize by the total number of packages (for NNs)
        node_repr = [len(
            self.queues[i]) / self.max_packet_inputs for i in range(1, self.num_nodes + 1)]

        # represent links by their current load
        link_repr = [l.level / self.max_bandwidth for _,
                     l in self.links.items()]
        node_repr.extend(link_repr)
        return np.asarray(node_repr, dtype=np.float16)

    def __compute_reward(self):
        raise NotImplementedError()

    def __compute_isdone(self):
        """ Terminate the episode if all packets are processed and the arrival process 
        will generate no more packets at the source node. """
        return len(self.active) <= 0 and self.arrival_steps >= self.max_arrival_steps

    def __compute_info(self):
        return {}

    def __arrival_process(self):
        """ Generate incoming packets at the source node while adhering to the arrival process's configuration. """
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
        """ Transmit the first packet from node i's queue to node j via the link (i,j). """
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

        outfile.write('\t' + '\t'.join(list(map(lambda x: str(x) +
                                                ':', range(1, self.num_nodes + 1)))) + '\n')
        for num, row in enumerate(env_repr):
            outfile.write(str(num + 1) + ': \t')
            outfile.write('\t'.join(list(map(lambda x: str(x), row))) + '\n')

        outfile.write('\n')
        closing(outfile)

    def map_actions(self, actions):
        """ Map actions from the agent's input format to node ids used for the networking environment. """
        # forbit action 'do nothing', each action forwards a packet to some node (except if the link is fully used)
        actions = list(map(lambda n, a: sorted(list(
            self.DG.successors(n+1)))[a], range(len(actions)), actions))
        return actions

    def inv_map_actions(self, actions):
        """ Map actions from the network's format to their corresponding action in the action space. """
        actions = list(map(lambda n, a: sorted(list(self.DG.successors(n+1))).index(a), range(len(actions)), actions))
        return actions

    def check_graph(self):
        """ Check if the provided graph adheres to the environment's assumptions. """
        assert(self.DG.nodes(data=True)[1]['source'])
        num_nodes = len(self.DG.nodes)
        assert(self.DG.nodes(data=True)[num_nodes]['sink'])
