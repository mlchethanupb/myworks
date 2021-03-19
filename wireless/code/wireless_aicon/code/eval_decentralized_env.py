from ray.rllib.agents.ppo import PPOTrainer
import ray
import ast
import argparse
import numpy as np
import networkx as nx
from collections import defaultdict
from ray.tune.registry import register_env


from decentralized_env.env.environment import WirelessEnv
from decentralized_env.env.customcallback import PacketDeliveredCountCallback


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

def setup_and_test(agent, eval_episodes):

    #checkpoint_path = "/home/aicon/pavitra/Project_AICON/pg_aicon_new/pg-aicon/wireless/code/phase_two/wmac_marl/logs/wmac_marl/PPO_WirelessEnv_fa061_00000_0_num_sgd_iter=6_2021-02-03_23-34-28/checkpoint_4167/checkpoint-4167"

    # Create a single environment and register it
    def env_creator(_):
        return WirelessEnv(G, False)
    env_name = "WirelessEnv"
    single_env = WirelessEnv(G, False)
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
    print(policy_graphs)
    def policy_mapping_fn(agent_id):
            return 'agent-' + str(agent_id)

    # Define configuration with hyperparam and training details
    config={
                    "log_level": "ERROR",
                    "num_workers": 1,
                    "num_cpus_for_driver": 1,
                    "num_cpus_per_worker": 2,
                    "num_gpus": 0,
                    "num_envs_per_worker": 1,
                    "no_done_at_end": True,
                    "seed":10,
                    "gamma": 0.9392979332914239,

    #---------------------------------------------------------------------------------------

                    "use_critic": True,
                    "use_gae": True,
                    "lambda": 0.9844457867596674,
                    "kl_coeff": 0.2,
                    "rollout_fragment_length": 200,
                    "train_batch_size": 2048,
                    "sgd_minibatch_size": 128,
                    "shuffle_sequences": True,
                    "num_sgd_iter": 6,
                    "lr": 4.304049744289648e-05,
                    "lr_schedule": None,
                    "vf_share_layers": False,
                    "vf_loss_coeff": 1.0,
                    "entropy_coeff": 0.05427902707123386,
                    "entropy_coeff_schedule": None,
                    "clip_param": 0.1,
                    "vf_clip_param": 300,
                    "grad_clip": None,
                    "kl_target": 0.01,
                    "batch_mode": "truncate_episodes",
                    "observation_filter": "NoFilter",
                    "simple_optimizer": False,
                    "_fake_gpus": False,
    #---------------------------------------------------------------------------------------
                    "multiagent": {
                        "policies": policy_graphs,
                        "policy_mapping_fn": policy_mapping_fn,
                        "count_steps_by": "env_steps",
                    },
                    "env": "WirelessEnv",
                    "callbacks": PacketDeliveredCountCallback
    }

    config1={
                    "log_level": "ERROR",
                    "num_workers": 6,
                    "num_cpus_for_driver": 4,
                    "num_cpus_per_worker": 2,
                    "num_gpus": 0,
                    "multiagent": {
                        "policies": policy_graphs,
                        "policy_mapping_fn": policy_mapping_fn,
                        "count_steps_by": "env_steps",
                    },
                    "env": "WirelessEnv",
    }
    ray.shutdown()
    ray.init()
    agent = PPOTrainer(config=config1, env=env_name)
    agent.restore(checkpoint_path)

    # instantiate env class
    env = WirelessEnv(G, False)

    for itr in range(eval_episodes):
        episode_reward = 0
        obs = env.reset()
        timesteps = 0
        ts_pd_count = 0
        pkt_del_old = 0
        while (1):
            timesteps += 1
            actions = {}
            for i in range(num_agents):
                actions[i] = agent.compute_action(obs[i], policy_id = 'agent-' + str(i)) 
            obs, reward, done, info = env.step(actions)
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
                
                if itr % 5000 == 0:
                    print("packet delivered mean after ", itr," episodes:", np.mean(packet_delivered))
                    print("packet lost mean after ", itr," episodes:", np.mean(pac_lost))
                    print("Successfull transmission mean after ", itr," episodes:", np.mean(succ_trans))
                    print("Total transmission mean after ", itr," episodes:", np.mean(total_trans))
                    print("Total timesteps mean after ", itr," episodes:", np.mean(timesteps_list))
                    
                break
    print("final packt delivered MARL in % :", packet_delivered)
    print("final packt lost in MARL % :", pac_lost)
    print("final successful transmission MARL in % :", succ_trans)
    print("final total transmission mean MARL :", total_trans)
    print("final total timesteps mean MARL:", timesteps_list)
    print("ts_pd_list mean MARL:", ts_pd_list)


if __name__=='__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--agent', type=str, nargs='?', const=1,
                        default='MARL', help='agent to test MARL')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=50000,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--checkpoint', type=str, nargs='?', const=1,
                        default='./saved_models/checkpoint_4167/checkpoint-4167', help='Checkpoint of the saved model')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='[(0, 2), (0, 1), (0, 3), (1, 2), (1, 3), (2, 3),(2, 4), (3, 4), (5, 2), (5, 3), (5, 4)]', help='Pass a networkx graph or \'default\'')

    args = parser.parse_args()
    agent = args.agent  
    eval_episodes = args.eval_episodes
    checkpoint_path = args.checkpoint

    d = defaultdict(list)
    graph_data = args.graph
    graph_data = ast.literal_eval(graph_data)  
    data = graph_data#[(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]

    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)
        
    #nx.draw_networkx(G)

    setup_and_test(agent, eval_episodes)