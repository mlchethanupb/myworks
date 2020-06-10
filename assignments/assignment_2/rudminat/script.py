import argparse
from networkx import nx
import gym
import numpy as np
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines.common.env_checker import check_env
from gym import spaces

class Network(gym.Env):

    def __init__(self, configuration: dict, graph: nx.Graph):

        super(Network, self).__init__()
        actionspace = [len(graph.nodes()) for _ in range(len(graph.nodes()))]
        obsspace = [128 for _ in range(len(graph.nodes()))]
        print(actionspace)
        print(obsspace)
        self.action_space = spaces.MultiDiscrete(actionspace)
        self.observation_space = spaces.MultiDiscrete(obsspace)

        self.arrival_time = config['arrival_time']
        self.maxsteps = config['maxsteps']
        # self.packet_size =config['packet_size']
        self.graph = graph
        self.current_timestep = 0
        self.sink,self.source = None,None

        #number of packets at each node
        self.packet_count_per_node=[0 for _ in range(len(self.graph.nodes()))]
        self.sending = [0 for _ in range(len(self.graph.nodes()))]

        #extract the sink and the source node from the graph
        for node,data in self.graph.nodes.data():
            if data['sink']: self.sink=node
            if data['source']: self.source=node
        if self.sink is None or self.source is None:
            print('no sink or no source defined')
            return

    def step(self, action):
        """the action is a list of -num_Nodes- length. action[i]=j means that a packet 
        is sent from node i to node j if possible"""

        reward = 0
        for i,j in enumerate(action):
            #transmitting packets with respect to the actions
            reward  -= self.transmit(i,j)

        #update the nodes according to the packets that has been sent
        for i in range(len(self.packet_count_per_node)):
            self.packet_count_per_node[i] += self.sending[i]
            if self.packet_count_per_node[i] >=128:
                print('dropping packet')
                self.packet_count_per_node[i]=127
                reward -=999999999
        self.sending = [0 for _ in range(len(self.graph.nodes()))]

        #handle packets that were routet successfully to the sink
        reward += self.packet_count_per_node[self.sink]*len(self.graph.nodes())
        self.packet_count_per_node[self.sink]=0

        self.current_timestep+=1
        if(self.current_timestep % self.arrival_time==0):
            #new packet arrives at source node
            self.packet_count_per_node[self.source]+=1

        info=dict()
        state = self.packet_count_per_node
        done = False
        if self.current_timestep >= self.maxsteps: done=True

        return np.array(state), reward, done, info

    def transmit(self,i,j):
        """transmit all packets from node i to node j
        returns the number of packets that were tried to sent"""

        #number of packets that will be tried to sent
        count = self.packet_count_per_node[i]

        #send packets if possible
        if (i,j) in self.graph.edges():
            self.sending[j] += self.packet_count_per_node[i]
            self.packet_count_per_node[i] = 0

        return count

    def reset(self):

        self.packet_count_per_node = [0 for _ in range(len(self.graph.nodes()))]
        self.sending = [0 for _ in range(len(self.graph.nodes()))]

        #the first packet already arrived at the source
        self.packet_count_per_node[self.source]=1
        return np.array(self.packet_count_per_node)

    def render(self, mode='human', close=False):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    #parser.add_argument('')

    config = {}
    config['maxsteps'] = 200000
    config['arrival_time'] = 2
    config['packet_size'] = 4.0

    G = nx.Graph()
    G.add_node(1, sink=False, source=False)
    G.add_node(2, sink=False, source=False)
    G.add_node(3, sink=False, source=False)
    G.add_node(0, sink=False, source=True)
    G.add_node(4, sink=True, source=False)
    G.add_edges_from([(0,1),(1,2),(1,3),(2,4)])
    # execute flowsim experiment
    network = Network(config,graph=G)

    print(network.reset())
    print(network.step([1, 2, 4, 0, 0]))
    print(network.step([1, 2, 4, 0, 0]))
    print(network.step([1, 2, 4, 0, 0]))
    print(network.step([1, 2, 4, 0, 0]))
    print(network.step([1, 2, 4, 0, 0]))
    network.step([3, 3, 5, 0, 0])

    env = Network(config,graph=G)
    print(check_env(env))

    model = A2C("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=25000)
    print('TESTTEST')
    #model.save("netw")

    #del model # remove to demonstrate saving and loading

    #model = DQN.load("netw")

    obs = env.reset()
    #print('Fist Observation = '+obs)
    for i in range(20):
        action, _states = model.predict(obs, deterministic=True)
        obs, rewards, dones, info = env.step(action)
        print('Observation = ')
        print(obs)
        print('Reward = '+str(rewards))
        #env.render()
    print('finished')
