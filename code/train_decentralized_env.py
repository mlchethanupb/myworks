import ray
from ray import tune
import numpy as np
import networkx as nx

from ray.tune import grid_search
from ray.tune.registry import register_env
from ray.rllib.agents.ppo import PPOTrainer
from ray.tune.schedulers import AsyncHyperBandScheduler
from collections import defaultdict


# Import environment definition
from decentralized_env.marl_env.environment import WirelessEnv
from decentralized_env.marl_env.customcallback import PacketDeliveredCountCallback

# Driver code for training
def setup_and_train():

    d = defaultdict(list)
    """Larger network"""
    #data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10),(4,10)]#(4,6),(5,10),(6,10),(9,6),(8,10)]
    """Smaller netowrk"""
    data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]

    #data = [(0,1),(0,2),(1,2),(0,3),(1,3),(2,3)]
    # defaultdict(<type 'list'>, {})
    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)

    #nx.draw_networkx(G)

    # Create a single environment and register it
    def env_creator(_):
        return WirelessEnv(G, False)
    single_env = WirelessEnv(G, False)
    env_name = "WirelessEnv"
    register_env(env_name, env_creator)

    # Get environment obs, action spaces and number of agents
    obs_space = single_env.observation_space
    #act_space = single_env.action_space
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

    # Define configuration with hyperparam and training details
    config={
                "log_level": "ERROR",
                "num_workers": 6,
                "num_cpus_for_driver": 4,
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

    asha_scheduler = AsyncHyperBandScheduler(
        time_attr='timesteps_total',
        metric='episode_reward_mean',
        mode='max',
        max_t=120,
        grace_period=50,
        reduction_factor=2,
        brackets=2)


    # Define experiment details
    exp_name = 'wmac_marl'
    exp_dict = {
            'name': exp_name,
            'run_or_experiment': 'PPO',
            "stop": {
                #"training_iteration": 1500,
                "timesteps_total": 120,
            },
            'checkpoint_freq': 10,
            "local_dir":"logs/",
            "verbose": 1,
            "num_samples":1,
            #"search_alg":ax_search,
            "scheduler":asha_scheduler,
            "config": config,
            "checkpoint_at_end":True,
            "checkpoint_score_attr":"episode_reward_mean",
            "keep_checkpoints_num":1,
        }



    # Initialize ray and run
    ray.init()
    analysis = tune.run(**exp_dict)
    print("Best configuration is ",analysis.get_best_config(metric="episode_reward_mean", mode = "max"))

    checkpoints = analysis.get_trial_checkpoints_paths(trial=analysis.get_best_trial('episode_reward_mean', mode= "max"), metric='episode_reward_mean')

    print(checkpoints[0][0])
    agent = PPOTrainer(env=env_name,config=config)
    agent.restore(checkpoints[0][0])

    packet_delivered = []
    for itr in range(5000):
        episode_reward = 0
        done = {}
        obs = single_env.reset()
        while (1):
            actions = {}
            for i in range(num_agents):
                actions[i] = agent.compute_action(obs[i], policy_id = 'agent-' + str(i)) 
            obs, reward, done, info = single_env.step(actions)
            if done['__all__']:
                packet_delivered.append(single_env.get_packet_delivered_count())
                if itr % 500 == 0:
                    print("pckt delivered mean after ", itr," episodes:", np.mean(packet_delivered))
                break
    print("final packt delivered mean :", np.mean(packet_delivered))


if __name__=='__main__':
    setup_and_train()
