
import os
import matplotlib as plt
import networkx as nx
import tensorflow as tf
import argparse
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines import A2C, PPO2
from stable_baselines.common.env_checker import check_env
from stable_baselines.common.callbacks import BaseCallback
import gym
import ast
import numpy as np
from collections import defaultdict

from centralized_env.baseline.DSDV_Priority_Based_RR import dsdv_wqueue
from centralized_env.baseline.DSDV_RR import dsdv_RRTDMA
from centralized_env.with_routing.w_mac_env import W_MAC_Env
from centralized_env.without_routing.MAC_RL_env import MAC_RL


timesteps_list = []
packet_lost = []
packet_delivered_list = []
total_trans_list = []
succ_trans_list = []
total_pkt_sent_list = []
ts_pd_list = []

def reset_lists():
    # reset lists
    timesteps_list.clear()
    packet_lost.clear()
    packet_delivered_list.clear()
    total_trans_list.clear()
    succ_trans_list.clear()
    total_pkt_sent_list.clear()
    ts_pd_list.clear()

"Evaluate the performance of all the agents"
def testing_agent(agent, eval_episodes):
    reset_lists()

    agent = agent
    eval_episodes = eval_episodes
    if agent == 'A2C_MAC_routing' or agent == 'PPO2_MAC_routing':
        if agent == 'A2C_MAC_routing':
            model = A2C.load("A2C_MAC_Routing_last.zip")

        elif agent == 'PPO2_MAC_routing':
            model = PPO2.load("saved_models/PPO2_MAC_Routing_last.zip")

        for i in range(eval_episodes):
            obs = env.reset()
            timestep = 0
            ts_pd_count = 0
            pkt_del_old = 0
            done = False
            while done != True:
                timestep += 1
                action, _states = model.predict(obs)
                obs, rewards, done, info = env.step(action)
                pkt_delivered_count = env.get_packet_delivered()
                if pkt_delivered_count > pkt_del_old and pkt_delivered_count <= 15:
                    pkt_del_old = pkt_delivered_count
                    ts_pd_count += 1

            append_data(env, timestep, ts_pd_count)
        calculate_sum()

    elif agent == 'PPO2_MAC':
        print("entering RL_MAC")
        
        model = PPO2.load("saved_models/PPO2_RL_MAC_FINAL.zip")  
        

        for i in range(eval_episodes):
            obs = env_RL_MAC.reset()
            timestep = 0
            ts_pd_count = 0
            pkt_del_old = 0
            done = False
            while done != True:
                timestep += 1
                action, _states = model.predict(obs)
                obs, rewards, done, info = env_RL_MAC.step(action)
                pkt_delivered_count = env_RL_MAC.get_packet_delivered()
                if pkt_delivered_count > pkt_del_old and pkt_delivered_count <= 15:
                    pkt_del_old = pkt_delivered_count
                    ts_pd_count += 1

            append_data(env_RL_MAC, timestep, ts_pd_count)
        calculate_sum()

    elif agent == 'dsdv_wqueue': 

        print("entering into dsdv wqueue")
        for i in range(eval_episodes):
            obs = env.reset()
            destinations_list_with_anode = obs
            attack_node = [destinations_list_with_anode[-1]]
            routing_table = dsdv_wqueue_env.create_routing_table(attack_node)
            timestep = 0
            ts_pd_count = 0
            pkt_del_old = 0
            done = False
            while done != True:
                timestep += 1
                queue_size = env.get_queue_sizes()
                action = dsdv_wqueue_env.predict(
                    obs, queue_size, routing_table)
                obs, rewards, done, info = env.step(action)
                pkt_delivered_count = env.get_packet_delivered()
                if pkt_delivered_count > pkt_del_old and pkt_delivered_count <= 15:
                    pkt_del_old = pkt_delivered_count
                    ts_pd_count += 1

            append_data(env, timestep, ts_pd_count)
        calculate_sum()

    elif agent == 'dsdv_RRTDMA':
        print("entering RRTDMA")
        for i in range(eval_episodes):
            obs = env.reset()
            destinations_list_with_anode = obs
            attack_node = [destinations_list_with_anode[-1]]
            routing_table = dsdv_RRTDMA_env.create_routing_table(attack_node)
            timestep = 0
            ts_pd_count = 0
            pkt_del_old = 0
            done = False
            while done != True:
                timestep += 1
                queue_size = env.get_queue_sizes()
                action = dsdv_RRTDMA_env.predict(
                    obs, queue_size, routing_table)
                obs, rewards, done, info = env.step(action)
                pkt_delivered_count = env.get_packet_delivered()
                if pkt_delivered_count > pkt_del_old and pkt_delivered_count <= 15:
                    pkt_del_old = pkt_delivered_count
                    ts_pd_count += 1

            append_data(env, timestep, ts_pd_count)
        calculate_sum()

    else:
        raise ValueError('Unknown agent.')


def time_steps():

    return timesteps_list


def packets_delivered():

    return packet_delivered_list


def packet_lost_total():

    return packet_lost


def succ_transmission():

    return succ_trans_list


def ts_pd():

    return ts_pd_list


def append_data(env_eval, timestep, ts_pd_count):
    env_to_eval = env_eval
    packet_loss = env_to_eval.get_packet_lost()
    packet_delivered = env_to_eval.get_packet_delivered()

    # print("packet_delivered", packet_delivered)

    total_trans = env_to_eval.get_total_transmission()
    # print("total_trans",total_trans)
    succ_trans = env_to_eval.get_succ_transmission()
    total_pkt_sent = env_to_eval.get_total_packet_sent()
    # print("total_pkt_sent", total_pkt_sent)

    packet_loss_percentage = (packet_loss/total_pkt_sent) * 100
    packet_delivered_percentage = (packet_delivered/total_pkt_sent) * 100
    # print("packet_delivered_percentage", packet_delivered_percentage)
    succ_trans_percentage = (succ_trans/total_trans) * 100

    # calculate percentage and append
    timesteps_list.append(timestep)
    ts_pd_list.append(ts_pd_count)

    packet_lost.append(packet_loss_percentage)
    packet_delivered_list.append(packet_delivered_percentage)
    total_trans_list.append(total_trans)
    succ_trans_list.append(succ_trans_percentage)
    total_pkt_sent_list.append(total_pkt_sent)


def calculate_sum():
    list1 = total_pkt_sent_list
    list2 = packet_delivered_list
    list3 = packet_lost
    list4 = total_trans_list
    list5 = succ_trans_list
    list6 = timesteps_list


if __name__ == '__main__':


    """ Experiment details"""
    parser = argparse.ArgumentParser(
        description='Transmitting packets in wireless network.')
    parser.add_argument('--agent', type=str, nargs='?', const=1,
                        default='PPO2_MAC_routing', help='Whether to use PPO2_MAC_routing, A2C_MAC_routing, PPO2_MAC, dsdv_wqueue, dsdv_RRTDMA')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?',
                        const=1, default=1500000, help='Number of training steps for the agent')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=50000,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--graph', type=str, nargs='?', const=1,
                        default='[(0, 2), (0, 1), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

    args = parser.parse_args()
    agent = args.agent
    graph_data = args.graph
    graph_data = ast.literal_eval(graph_data)
    print("data of graph", graph_data)

    total_train_timesteps = args.total_train_timesteps
    eval_episodes = args.eval_episodes

    d = defaultdict(list)
    data = graph_data

    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k, v in d.items():
        for vv in v:
            G.add_edge(k, vv)
    # nx.draw_networkx(G)

    env = W_MAC_Env(G)
    dsdv_wqueue_env = dsdv_wqueue(env, G)
    dsdv_RRTDMA_env = dsdv_RRTDMA(env, G)
    env_RL_MAC = MAC_RL(G)

    testing_agent(agent, eval_episodes)
