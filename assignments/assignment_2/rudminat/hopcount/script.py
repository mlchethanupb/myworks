import matplotlib.pyplot as plt
import argparse
from networkx import nx
import gym
import numpy as np
from stable_baselines import PPO2
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C
from stable_baselines.common.env_checker import check_env
from gym import spaces
import random
class Network(gym.Env):

    def __init__(self, configuration: dict, graph: nx.Graph):

        super(Network, self).__init__()

        self.shape=(len(graph.nodes()),len(graph.nodes()))
        # self.observation_space = spaces.Box(low=0, high=8, shape=self.shape,dtype=np.uint8)
        self.observation_space = spaces.Discrete(1)

        #self.action_space = spaces.Box(low=0, high=len(graph.nodes()),shape=(self.shape[0]*self.shape[1],),dtype=np.uint8)
        actionspace=np.zeros(self.shape[0]*self.shape[1])
        actionspace+=len(graph.nodes())
        self.action_space = spaces.MultiDiscrete(actionspace)

        self.arrival_time = config['arrival_time']
        self.maxsteps = config['maxsteps']
        # self.packet_size =config['packet_size']
        self.graph = graph
        self.current_timestep = 0

        #number of packets at each node
        self.packet_count_per_node = np.zeros(self.shape)
        self.sending = np.zeros(self.shape)

    def step(self, action, training=True):
        """the action is a list of -num_Nodes- length. action[i]=j means that a packet 
        is sent from node i to node j if possible"""

        reward = 0
        action=action.reshape(self.shape)
        for i,node_state in enumerate(action):
            for j,z in enumerate(node_state):
                #transmitting packets with respect to the actions
                reward  -= self.transmit(i,j,z)

        #update the nodes according to the packets that has been sent
        for i in range(len(self.packet_count_per_node)):
            for j in range(len(self.packet_count_per_node[i])):
                self.packet_count_per_node[i][j] += self.sending[i][j]
                #if self.packet_count_per_node[i][j] >7:
                    # print('dropping packet')
                   # self.packet_count_per_node[i][j]=7
                    #reward -=9999999*len(self.graph.nodes())
        self.sending = np.zeros(self.shape)

        #handle packets that were routet successfully to the sink
        # reward += self.packet_count_per_node[self.sink]*len(self.graph.nodes())
        for i in range(len(self.packet_count_per_node)):
            if self.packet_count_per_node[i][i]>0:
                reward+=len(self.graph.nodes)
                #*self.packet_count_per_node[i][i]
                self.packet_count_per_node[i][i]=0

        self.current_timestep+=1
        if(self.current_timestep % self.arrival_time==0):
            #new packet arrives at source node
            if training==False:
                packet=self.next_packet()
                self.packet_count_per_node[packet[0]][packet[1]]+=1
            else:
                
                self.packet_count_per_node+=1
                self.packet_count_per_node-=np.identity(len(self.graph.nodes()))


        info=dict()
        state = self.packet_count_per_node
        done = False
        if self.current_timestep >= self.maxsteps: done=True
        #return np.array(state), reward, done, info
        return 0, reward, done, info

    def transmit(self,i,j,z):
        """transmit all packets with the destination j from node i to node z
        returns the number of packets that were tried to sent"""

        #number of packets that will be tried to sent
        count = self.packet_count_per_node[i][j]

        #send packets if possible
        if (i,z) in self.graph.edges():
            self.sending[z][j] += self.packet_count_per_node[i][j]
            self.packet_count_per_node[i][j] = 0

        return count

    def reset(self):

        self.packet_count_per_node = np.zeros(self.shape)
        self.sending = np.zeros(self.shape)

        #the first packet already arrived at the source
        packet = self.next_packet()
        self.packet_count_per_node[packet[0]][packet[1]] = 1
        #return np.array(self.packet_count_per_node)
        return 0

    def next_packet(self):
        source=random.randint(0, self.shape[0]-1)
        sink = random.randint(0, self.shape[0]-1)
        #print("this is the tuple: %s" %((source,sink),))
        return (source,sink)

    def render(self, mode='human', close=False):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    parser.add_argument('--modelstr', default='netw')
    parser.add_argument('--printgraph', default=False, action="store_true")
    parser.add_argument('--load', default=False, action="store_true")
    args = parser.parse_args()
    print(args.modelstr)
    print(args.load)
    config = {}
    config['maxsteps'] = 6000000000000
    config['arrival_time'] = 2
    config['packet_size'] = 4.0

    G = nx.Graph()
    G.add_node(1)
    G.add_node(2)
    G.add_node(3)
    G.add_node(0)
    G.add_node(4)
    G.add_edges_from([(0,1),(1,2),(1,3),(2,4)])
    if args.printgraph:
        nx.draw(G)
        plt.show()
    # Example of stepts and actions:
    #network = Network(config,graph=G)

    #print(network.reset())
    #print(network.step([1, 2, 4, 0, 0]))
    #print(network.step([1, 2, 4, 0, 0]))
    #print(network.step([1, 2, 4, 0, 0]))
    #print(network.step([1, 2, 4, 0, 0]))
    #print(network.step([1, 2, 4, 0, 0]))
    #network.step([3, 3, 5, 0, 0])


    env = Network(config,graph=G)
    # print(check_env(env))

    if args.load is False:
        model = PPO2("MlpPolicy", env, verbose=1, tensorboard_log='./logs/{}_tensorboard/'.format(args.modelstr))
        model.learn(total_timesteps=250000)
        model.save(args.modelstr)

    else:
        model = PPO2.load(args.modelstr)

    obs = env.reset()
    print(env.packet_count_per_node)
    for i in range(20):
        action, _states = model.predict(obs, deterministic=True)
        obs, rewards, dones, info = env.step(action,training=False)
        print("this action")
        print (action.reshape(5,5))
        print('Leads to this observation = ')
        print(env.packet_count_per_node)
        print('Reward = '+str(rewards))
        #env.render()
    print('finished')
