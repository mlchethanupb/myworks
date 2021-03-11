import argparse
import gym
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

import ray
from ray import tune
from ray.tune.registry import register_env

from collections import defaultdict
#from centralized_env.w_mac.envs.w_mac_env import W_MAC_Env as W_MAC_Env
from decentralized_env.environment import WirelessEnv
from decentralized_env.customcallback import PacketDeliveredCountCallback



parser = argparse.ArgumentParser()
parser.add_argument("--run", type=str, default="PPO")
parser.add_argument("--torch", action="store_true")
parser.add_argument("--stop-timesteps", type=int, default=100000)
parser.add_argument('--graph', type=str, nargs='?', const=1, default='[(0, 2), (0, 1), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

all_graphs = [ 
    [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)],
    [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3), (2,4), (3,4), (5,2), (5,3), (5,4)],
    [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3), (2,4), (3,4), (5,2), (5,3), (5,4), (4,6), (4,7), (5,6), (5,7), (6,7)]
]

def create_graph(graph_list):
    d = defaultdict(list)

    data = graph_list #[(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]

    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)

    #nx.draw_networkx(G)
    return G

def get_centralized_config(graph: nx.Graph):
    def env_creator(_):
        return W_MAC_Env(graph)
    env_name = "centalized_env"
    register_env(env_name, env_creator)

    config={
                "seed":10,
                "env": "decentalized_env",
                "callbacks": PacketDeliveredCountCallback,
                "framework": "torch" if args.torch else "tf"
    }

    return config


def get_decentralized_config(graph: nx.Graph):
    def env_creator(_):
        return WirelessEnv(graph, False)
    single_env = WirelessEnv(graph, False)
    env_name = "decentalized_env"
    register_env(env_name, env_creator)

    # Get environment obs, action spaces and number of agents
    obs_space = single_env.observation_space
    num_agents = single_env.num_agents

    # Create a policy mapping
    def gen_policy(agent_id):
        act_space = single_env.get_agent_action_space(agent_id)
        return (None, obs_space, act_space, {})

    policy_graphs = {}
    for i in range(num_agents):
        policy_graphs['agent-' + str(i)] = gen_policy(i)

    def policy_mapping_fn(agent_id):
        return 'agent-' + str(agent_id)

    config={
                "seed":10,
                "multiagent": {
                    "policies": policy_graphs,
                    "policy_mapping_fn": policy_mapping_fn,
                },
                "env": "decentalized_env",
                "callbacks": PacketDeliveredCountCallback,
                "framework": "torch" if args.torch else "tf"
    }

    return config


def get_exp_dict(config):
        exp_name = 'scaling'
        exp_dict = {
            'name': exp_name,
            'run_or_experiment': 'PPO',
            "stop": {
                "timesteps_total": 1000,
            },
            'checkpoint_freq': 10,
            "local_dir":"logs/",
            "verbose": 1,
            "num_samples":1,
            #"search_alg":ax_search,
            "config": config,
            "checkpoint_at_end":True,
            "checkpoint_score_attr":"episode_reward_mean",
            "keep_checkpoints_num":1,
        }

        return exp_dict

if __name__ == "__main__":

    import os, sys
    sys.path.insert(0,"/home/oc/Momo/Studies/SS2020/Project/repo/pg-aicon/wireless/code/wireless_aicon/")

    args = parser.parse_args()
    for list_itr in all_graphs:
        graph = create_graph(list_itr)
        nx.draw_networkx(graph)
        plt.show()
    """
    ray.init()

    
    exp_dict = get_exp_dict(config)

    results = tune.run(**exp_dict)

    ray.shutdown()
    """