import os
import matplotlib as plt
import networkx as nx
import tensorflow as tf
import argparse
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines import A2C, PPO2
from stable_baselines.common.env_checker import check_env
from IPython.display import clear_output
import time
from copy import deepcopy
from ray import tune
from stable_baselines.common.callbacks import BaseCallback
import gym
import ast
import numpy as np
from collections import defaultdict
import w_mac
from DSDV_Agent import dsdv_wqueue
from DSDV_probability import dsdv_probability
from DSDV_RoundRobinTDMA import dsdv_RRTDMA
from w_mac.envs.w_mac_env import W_MAC_Env



def append_data():
    packet_loss = env.get_packet_lost()
    packet_delivered = env.get_packet_delivered()
    total_trans = env.get_total_transmission()
    succ_trans = env.get_succ_transmission()
    total_pkt_sent = env.get_total_packet_sent()

    timesteps_list.append(timestep)
    packet_lost.append(packet_loss)
    packet_delivered_list.append(packet_delivered)
    total_trans_list.append(total_trans)
    succ_trans_list.append(succ_trans)
    total_pkt_sent_list.append(total_pkt_sent)
def calculate_sum():   
    total_packets_sent_sum = sum(total_pkt_sent_list)
    total_packets_delivered_sum = sum(packet_delivered_list)
    total_packets_lost_sum = sum(packet_lost) 
    total_trans_sum = sum(total_trans_list)
    total_succ_trans_sum = sum(succ_trans_list)
    print("Total packets sent for agent", agent, "over evaluation episode",eval_episodes, "are", total_packets_sent_sum)
    print("Total packets delivered for agent", agent,"over evaluation episode",eval_episodes, "are", total_packets_delivered_sum)
    print("Total packets lost sum for agent over evaluation episode", agent, "over evaluation episode",eval_episodes, "are", total_packets_lost_sum)
    print("Total transmissions happened sum for agent", agent, "over evaluation episode",eval_episodes, "are", total_trans_sum)
    print("Total succ trans sum for agent",agent, "over evaluation episode",eval_episodes, "are", total_succ_trans_sum)

    
if __name__ == '__main__':

    d = defaultdict(list)
    """Larger network"""
    # data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10),(4,10)]#(4,6),(5,10),(6,10),(9,6),(8,10)]
    """Smaller netowrk"""
    # data = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]
    # defaultdict(<type 'list'>, {})
    """ Experiment details"""
    parser = argparse.ArgumentParser(
        description='Transmitting packets in wireless network.')
    parser.add_argument('--agent', type=str, nargs='?', const=1,
                        default='PPO2', help='Whether to use A2C, PPO2, dsdv_wqueue, dsdv_RRTDMA, dsdv_prob')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?',
                        const=1, default=1500000, help='Number of training steps for the agent')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=5,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='[(0, 2), (0, 1), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')
    
    
    args = parser.parse_args()
    agent = args.agent
    data = args.graph
    data = ast.literal_eval(data)
    print("data of graph", data)

    total_train_timesteps = args.total_train_timesteps
    eval_episodes = args.eval_episodes

    # Create a network graph
    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k, v in d.items():
        for vv in v:
            G.add_edge(k, vv)
    nx.draw_networkx(G)

    env = gym.make('wmac-graph-v0', graph=G)
    # check_env(env)
    dsdv_prob_env = dsdv_probability(env, G)
    dsdv_wqueue_env = dsdv_wqueue(env, G)
    dsdv_RRTDMA_env = dsdv_RRTDMA(env, G)

    class TensorboardCallback(BaseCallback):
        """
        Custom callback for plotting additional values in tensorboard.
        """

        def __init__(self, verbose=0):
            self.is_tb_set = False
            super(TensorboardCallback, self).__init__(verbose)

        def _on_step(self) -> bool:
            # Log additional tensor
            if not self.is_tb_set:
                with self.model.graph.as_default():
                    tf.summary.scalar(
                        'packet_lost', tf.reduce_mean(env.get_packet_lost()))
                    self.model.summary = tf.compat.v1.summary.merge_all()
                self.is_tb_set = True
            # Log scalar value (here a random variable)
            value = env.get_packet_lost()
            summary = tf.Summary(value=[tf.Summary.Value(
                tag='packet_lost', simple_value=value)])
            self.locals['writer'].add_summary(summary, self.num_timesteps)
            return True

    # Different agent's training and evaluation
    # Default agent is PPO2. To try new agents ->Ex: python agent_script.py --agent A2C
    if args.agent == 'A2C' or args.agent == 'PPO2':

        if args.agent == 'A2C':
            model = A2C(MlpPolicy, env, verbose=1,
                        tensorboard_log="./a2c_tensorboard/")
            model.learn(total_timesteps=total_train_timesteps,
                        callback=TensorboardCallback())
            model.save("a2c_wmac_small")

            model = A2C.load("a2c_wmac_small")

        else:
            model = PPO2(MlpPolicy, env, verbose=1, gamma=0.99, n_steps=2048, nminibatches=32, learning_rate=2.5e-4, lam=0.95, noptepochs=10, ent_coef=0.01, cliprange=0.2,
                         tensorboard_log="./PPO2_tensorboard_3collision_domain_morenodes/", seed=8, n_cpu_tf_sess=1)
            model.learn(total_timesteps=total_train_timesteps,
                        callback=TensorboardCallback())

            model.save("PPO2_wmac_3collision_domain_morenodes")

            model = PPO2.load("PPO2_wmac_3collision_domain_morenodes")
            # model = PPO2.load("PPO2_wmac_single_domain")

        timesteps_list = []
        packet_lost = []
        packet_delivered_list = []
        total_trans_list = []
        succ_trans_list = []
        total_pkt_sent_list = []
        for i in range(eval_episodes):
            obs = env.reset()
            timestep = 0
            done = False
            while done != True:
                timestep += 1
                action, _states = model.predict(obs)
                obs, rewards, done, info = env.step(action)
            
            append_data()
        calculate_sum()
        print("Mean timesteps taken to transfer all the packets in the network", np.mean(
            timesteps_list))
        

    # BASELINE 1: DSDV routing protocol with weighted queue based TDMA
    elif args.agent == 'dsdv_wqueue':

        timesteps_list = []
        packet_lost = []
        packet_delivered_list = []
        total_trans_list = []
        succ_trans_list = []
        total_pkt_sent_list = []
        for i in range(eval_episodes):
            obs = env.reset()
            destinations_list_with_anode = obs
            attack_node = [destinations_list_with_anode[-1]]
            routing_table = dsdv_wqueue_env.create_routing_table(attack_node)
            timestep = 0
            done = False
            while done != True:
                timestep += 1
                queue_size = env.get_queue_sizes()
                action = dsdv_wqueue_env.predict(obs, queue_size, routing_table)
                obs, rewards, done, info = env.step(action)

            
            append_data()
        calculate_sum()
        print("Mean timesteps taken to transfer all the packets in the network", np.mean(
            timesteps_list))
        

        
        

    # BASELINE 2: DSDV routing protocol with round robin TDMA
    elif args.agent == 'dsdv_RRTDMA':

        timesteps_list = []
        packet_lost = []
        packet_delivered_list = []
        total_trans_list = []
        succ_trans_list = []
        total_pkt_sent_list = []
        for i in range(eval_episodes):
            obs = env.reset()
            destinations_list_with_anode = obs
            attack_node = [destinations_list_with_anode[-1]]
            routing_table = dsdv_wqueue_env.create_routing_table(attack_node)
            timestep = 0
            done = False
            while done != True:
                timestep += 1
                queue_size = env.get_queue_sizes()
                action = dsdv_RRTDMA_env.predict(obs, queue_size, routing_table)
                obs, rewards, done, info = env.step(action)
           
            append_data()
        calculate_sum()
        print("Mean timesteps taken to transfer all the packets in the network", np.mean(
            timesteps_list))
        

    # BASELINE 3: DSDV routing protocol with probability based TDMA
    elif args.agent == 'dsdv_prob':
        rewards = 0
        timesteps_list = []
        packet_lost = []
        packet_delivered_list = []
        total_trans_list = []
        succ_trans_list = []
        total_pkt_sent_list = []
        for i in range(eval_episodes):
            obs = env.reset()
            destinations_list_with_anode = obs
            attack_node = [destinations_list_with_anode[-1]]
            routing_table = dsdv_wqueue_env.create_routing_table(attack_node)
            timestep = 0
            done = False
            while done != True:
                timestep += 1
                queue_size = env.get_queue_sizes()
                action = dsdv_prob_env.predict(obs, queue_size, rewards, routing_table)
                obs, rewards, done, info = env.step(action)
           
            append_data()
        calculate_sum()
       
        print("Mean timesteps taken to transfer all the packets in the network", np.mean(
            timesteps_list))
        
        

    else:
        raise ValueError('Unknown agent.')

