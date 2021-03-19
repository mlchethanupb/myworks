import argparse
import gym
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import ray
from ray import tune
from ray.tune.registry import register_env
from collections import defaultdict

from centralized_env.with_routing.w_mac_env import W_MAC_Env
from decentralized_env.env.environment import WirelessEnv



parser = argparse.ArgumentParser()
parser.add_argument("--run", type=str, default="PPO")
parser.add_argument("--torch", action="store_true")
parser.add_argument("--stop_timesteps", type=int, default=500000)
parser.add_argument('--graph', type=str, nargs='?', const=1, default='[(0, 2), (0, 1), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

all_graphs = [ 
    [ (0,1), (0,2), (0,3), (1,2), (1,3), (2,3), (2,4), (3,4), (5,2), (5,3), (5,4)],
    [ (0,1), (0,2), (0,3), (0,4), (0,5), (1,2), (1,3), (1,4), (1,5), (2,3), (2,4), 
      (2,5), (3,4), (3,5), (3,6), (3,7), (3,8), (3,9), (4,5), (4,6), (4,7), (4,8), 
      (4,9), (5,6), (5,7), (5,8), (5,9), (6,7), (6,8), (6,9), (7,8), (7,9), (8,9)],
    [  (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7), (1,2), (1,3), (1,4), (1,5),
       (1,6), (1,7), (2,3), (2,4), (2,5), (2,6), (2,7), (3,4), (3,5), (3,6), (3,7),
       (4,5), (4,6), (4,7), (5,6), (5,7), (5,8), (5,9), (5,10),(5,11),(5,12),(6,7),
       (6,8), (6,9), (6,10),(6,11),(6,12),(7,8), (7,9), (7,10),(7,11),(7,12),(8,9),
       (8,10),(8,11),(8,12),(9,10),(9,11),(9,12),(10,11),(10,12),(11,12) ]
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
                "num_workers": 6,
                "num_cpus_for_driver": 4,
                "num_cpus_per_worker": 2,
                "num_gpus": 0,
                "num_envs_per_worker": 1,
                "lr": 0.001,
                "env": "centalized_env",
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
                "num_workers": 6,
                "num_cpus_for_driver": 4,
                "num_cpus_per_worker": 2,
                "num_gpus": 0,
                "num_envs_per_worker": 1,
                "no_done_at_end": True,
                "lr": 0.001,
                "multiagent": {
                    "policies": policy_graphs,
                    "policy_mapping_fn": policy_mapping_fn,
                },
                "env": "decentalized_env",
                "framework": "torch" if args.torch else "tf"
    }

    return config


def get_exp_dict(config, centralized_flag):
        exp_name = 'scaling'

        total_timesteps = args.stop_timesteps 
        if centralized_flag == False:
            total_timesteps = args.stop_timesteps * 1.5
        
        exp_dict = {
            'name': exp_name,
            'run_or_experiment': 'PPO',
            "stop": {
                "timesteps_total": total_timesteps,
            },
            'checkpoint_freq': 10,
            "local_dir":"logs/",
            "verbose": 1,
            "num_samples":1,
            "config": config,
            "checkpoint_at_end":True,
            "checkpoint_score_attr":"episode_reward_mean",
            "keep_checkpoints_num":1,
        }

        return exp_dict

def train_model(exp_dict):
    analysis = tune.run(**exp_dict)
    print("Best configuration is ",analysis.get_best_config(metric="episode_reward_mean", mode = "max"))

if __name__ == "__main__":

    args = parser.parse_args()
    """
    for list_itr in all_graphs:
        graph = create_graph(list_itr)
    
    """
    for list_itr in all_graphs:
        ray.init()
        graph = create_graph(list_itr)
        config = get_centralized_config(graph)
        exp_dict = get_exp_dict(config, True)
        train_model(exp_dict)
        ray.shutdown()
    
    for list_itr in all_graphs:
        ray.init()
        graph = create_graph(list_itr)
        config = get_decentralized_config(graph)
        exp_dict = get_exp_dict(config, False)
        train_model(exp_dict)
        ray.shutdown()
