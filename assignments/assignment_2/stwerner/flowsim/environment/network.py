import logging
import simpy
import sys
import gym
import networkx as nx
from simpy import Resource
from ..environment.packet import Packet

"""

Network of nodes that serves as the agent's environment.

"""


class Network(gym.Env):
    def __init__(self, config: dict, DG: nx.DiGraph = None):
        # experiment parameters
        self.arrival_time = config['arrival_time']
        self.episode_length = config['episode_length']
        self.packet_size = config['packet_size']

        self.DG = nx.read_gpickle(r'./flowsim/environment/default.gpickle') if DG is None else DG
        self.source = next(node_id for node_id, data in self.DG.nodes(data=True) if data['source'])
        self.sink = next(node_id for node_id, data in self.DG.nodes(data=True) if data['sink'])
        self.num_nodes = len(self.DG.nodes())

        #self.action_space = gym.spaces.Discrete()

        # FOR DEVELOPMENT:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler()
            ]
        )

    def step(self, actions):
        #logging.info('Starting step at timestep {}.'.format(self.env.now))
        logging.info('{}'.format(self.queues))

        # TODO: check format of action
        # self.check_action(action)
        
        # TODO: what input type is expected in gym.Environment for action?
        for num, action in enumerate(actions):
            if action > 0: self.env.process(self.transmit(num + 1, action)) 

        # determine which packet to forward and transmit it via the selected link
        #logging.info('Previously triggered node: {}'.format(self.triggered_node))
        #logging.info(self.queues)
        #self.env.process(self.transmit(self.triggered_node, action))
        
        # process environment until timestep_event is triggered
        #self.triggered_node = self.env.run(self.timestep_event)
        self.env.run(self.timestep_event)
        self.timestep_event = self.env.event()
        #logging.info(self.queues)
        #logging.info('Step finished at timestep %s' % self.env.now)
        #logging.info('Step finished: {}'.format(list(map(lambda x: x.hops, self.queues[self.sink]))))
        logging.info('{}'.format(self.queues))
        logging.info('')

        # TODO: compute observations and collect rewards

    def reset(self):
        self.env = simpy.Environment()
        self.links = {(i, j): simpy.Container(
            self.env, data['bandwidth'], init=data['bandwidth']) for i, j, data in self.DG.edges(data=True)}
        self.queues = {i: [] for i in self.DG.nodes(data=False)}

        # register processes and events
        self.env.process(self.arrival_process())
        self.timestep_event = self.env.event()

        # temporary variables for processing
        # TODO: multiple triggered nodes?
        #self.triggered_node = None

        # TODO: run until first package is at the source node to get the init state
        #self.triggered_node = self.env.run(self.timestep_event)
        self.env.run(self.timestep_event)
        self.timestep_event = self.env.event()
        logging.info('')

    def arrival_process(self):
        while True:
            # create packet and register process
            packet = Packet(self.packet_size, self.env.now)
            self.queues[self.source].insert(0, packet)
            #logging.info('Arrival Process at timestep %s' % self.env.now)

            #logging.info('Arrival process triggering environment event')
            #self.timestep_event.succeed(value=self.source)
            if not self.timestep_event.triggered: self.timestep_event.succeed() 
            yield self.env.timeout(self.arrival_time)

    def transmit(self, i, j):
        # do nothing if the selected link does not exist or the queue is empty
        if (i,j) not in self.links or not self.queues[i]:
            return

        logging.info('Starting transmission {}'.format((i,j)))

        # get packet and link for transmission
        packet = self.queues[i].pop()
        link = self.links[(i, j)]

        # request capacity corresponding to bandwidth of the link or less if the 
        # packet does not scoop out the link's capacity
        request_capacity = min(packet.packet_size, link.level)
        if request_capacity <= 0.0:
            # the selected link is currently occupied, do nothing
            #logging.info('Requesting capacity from link {} failed, do nothing.'.format((i,j)))
            self.queues[i].insert(0, packet)
        
        else:
            #logging.info('Requesting {} of link ({})\'s capacity.'.format(request_capacity, (i,j)))

            yield link.get(request_capacity)
            # timeout until the packet is completely transmitted
            yield self.env.timeout(packet.packet_size / request_capacity)
            yield link.put(request_capacity)

            # update packet and environment's statistics
            packet.update_statistics()

            # enqueue the packet's at its next node 
            self.queues[j].append(packet)

            #logging.info('Finished transmitting packet {}; {}.'.format((i,j), self.queues))
            # invoke arrival event at node j
            #logging.info('Link triggering environment event: {}'.format(self.timestep_event.processed))
            #self.timestep_event.succeed(value=j)
            if not self.timestep_event.triggered: self.timestep_event.succeed()

    def check_action(self, action):
        # TODO:
        assert(True), 'Action must conform to the expected shape'

    def check_graph(self, DG):
        # TODO: check that nodes start with IDs > 0 !!
        pass

    def render(self):
        pass
