import ast
import argparse
import numpy as np
import networkx as nx
from collections import defaultdict
from decentralized_env.marl_env.environment import WirelessEnv

packet_delivered = []
pac_lost = []
succ_trans = []
total_trans = []
timesteps_list = []
ts_pd_list = []

def time_steps():
    
    return timesteps_list

def packets_delivered():

    return packet_delivered

def packet_lost_total():
    return pac_lost

def succ_transmission():
    return succ_trans
def ts_pd():
    return ts_pd_list

def get_actions(env):
    action_dict = {}
    for i in range(env.num_agents):
        act_space = env.get_agent_action_space(i)
        action_dict[i] = act_space.sample()
    return action_dict 


def reset_lists():
    packet_delivered.clear()
    pac_lost.clear()
    succ_trans.clear()
    total_trans.clear()
    timesteps_list.clear()
    ts_pd_list.clear()

def test_random_agent(graph,agent,eval_episodes):
    G= graph
    env = WirelessEnv(G, False)
    num_agents = env.num_agents
    print("entered random agent")
    reset_lists()
    for itr in range(eval_episodes):
        episode_reward = 0
        obs = env.reset()
        timesteps = 0
        ts_pd_count = 0
        pkt_del_old = 0
        while (1):
            timesteps += 1
            obs, reward, done, info = env.step(get_actions(env))
            pkt_delivered_count = env.get_packet_delivered_count()
            if pkt_delivered_count > pkt_del_old and pkt_delivered_count <= 15:
                pkt_del_old = pkt_delivered_count
                ts_pd_count += 1
            if done['__all__']:
                total_packet_delivered = env.get_packet_delivered_count()
                total_packet_lost = env.get_packet_lost()
                total_succ_trans = env.get_succ_transmissions()
                total_transmissions = env.get_total_transmissions()
                timesteps_list.append(timesteps)
                ts_pd_list.append(ts_pd_count)

                total_packet_delivered_percentage = (total_packet_delivered/25)*100
                total_packet_lost_percentage = (total_packet_lost/25)*100
                total_succ_trans_percentage = (total_succ_trans/total_transmissions)* 100
                 
                

                packet_delivered.append(total_packet_delivered_percentage)
                pac_lost.append(total_packet_lost_percentage)
                succ_trans.append(total_succ_trans_percentage)
                total_trans.append(total_transmissions)

                # if itr % 5000 == 0:
                #     print("packet delivered mean after ", itr," episodes:", np.mean(packet_delivered))
                #     print("packet lost mean after ", itr," episodes:", np.mean(pac_lost))
                #     print("Successfull transmission mean after ", itr," episodes:", np.mean(succ_trans))
                #     print("Total transmission mean after ", itr," episodes:", np.mean(total_trans))
                #     print("Total timesteps mean after ", itr," episodes:", np.mean(timesteps_list))
                break

    print("final packt delivered in % :", packet_delivered)
    print("final packt lost in % :", pac_lost)
    print("final successful transmission in % :", succ_trans)
    print("final total transmission mean :", total_trans)
    print("final total timesteps mean", timesteps_list)


if __name__=='__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--agent', type=str, nargs='?', const=1,
                        default='random_agent', help='for evaluation')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=50000,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='[(0, 2), (0, 1), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

    args = parser.parse_args()
    agent = args.agent
    graph_data = args.graph
    graph_data = ast.literal_eval(graph_data)  
    eval_episodes = args.eval_episodes

    d = defaultdict(list)
    data = graph_data #[(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]
    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)



    test_random_agent(G, agent,eval_episodes)


