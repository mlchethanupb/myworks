import ray
from ray import tune
from ray.rllib.agents.registry import get_agent_class
from ray.rllib.models import ModelCatalog
from ray.tune import run_experiments
from ray.tune.registry import register_env
from ray.rllib.agents.ppo import PPOTrainer

# Import environment definition
from environment import WirelessEnv

# Driver code for training
def setup_and_train():

    # Create a single environment and register it
    def env_creator(_):
        return WirelessEnv()
    single_env = WirelessEnv()
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
                "log_level": "WARN",
                "num_workers": 4,
                "num_cpus_for_driver": 1,
                "num_cpus_per_worker": 3,
                "num_gpus": 0,
                "train_batch_size": 200,
                "batch_mode": "truncate_episodes",
                "num_envs_per_worker": 1,
                "no_done_at_end": True,
                "lr": 5e-3,
                "multiagent": {
                    "policies": policy_graphs,
                    "policy_mapping_fn": policy_mapping_fn,
                    "count_steps_by": "agent_steps",
                },
                "env": "WirelessEnv"}

    # Define experiment details
    exp_name = 'wmac_marl'
    exp_dict = {
            'name': exp_name,
            'run_or_experiment': 'PPO',
            "stop": {
                "training_iteration": 1500
            },
            'checkpoint_freq': 20,
            "local_dir":"logs/",
            "config": config,
        }

    # Initialize ray and run
    ray.init()
    tune.run(**exp_dict)

if __name__=='__main__':
    setup_and_train()
