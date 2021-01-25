import ray
from ray import tune
from ray.tune import grid_search
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
                "log_level": "ERROR",
                "num_workers": 4,
                "num_cpus_for_driver": 1,
                "num_cpus_per_worker": 3,
                "num_gpus": 0,
                "train_batch_size": 200,
                "batch_mode": "truncate_episodes",
                "num_envs_per_worker": 1,
                "no_done_at_end": True,
                #"lr": grid_search([1e-3, 3e-4]),
                #"lambda": 0.95,
                #"explore": True,
                #"exploration_config": {
                #    "type": "EpsilonGreedy",
                #    "initial_epsilon": 1.0,
                #    "final_epsilon": 0.08,
                #    "epsilon_timesteps": 950000, # Timesteps over which to anneal epsilon.
                #},

#---------------------------------------------------------------------------------------
                # Should use a critic as a baseline (otherwise don't use value baseline;
                # required for using GAE).
                "use_critic": True,
                # If true, use the Generalized Advantage Estimator (GAE)
                # with a value function, see https://arxiv.org/pdf/1506.02438.pdf.
                "use_gae": True,
                # The GAE (lambda) parameter.
                "lambda": 0.9,
                # Initial coefficient for KL divergence.
                "kl_coeff": 0.2,
                # Size of batches collected from each worker.
                "rollout_fragment_length": 200,
                # Number of timesteps collected for each SGD round. This defines the size
                # of each SGD epoch.
                "train_batch_size": 4000,
                # Total SGD batch size across all devices for SGD. This defines the
                # minibatch size within each epoch.
                "sgd_minibatch_size": 128,
                # Whether to shuffle sequences in the batch when training (recommended).
                "shuffle_sequences": True,
                # Number of SGD iterations in each outer loop (i.e., number of epochs to
                # execute per train batch).
                "num_sgd_iter": 30,
                # Stepsize of SGD.
                "lr": 5e-5,
                # Learning rate schedule.
                "lr_schedule": None,
                # Share layers for value function. If you set this to True, it's important
                # to tune vf_loss_coeff.
                "vf_share_layers": False,
                # Coefficient of the value function loss. IMPORTANT: you must tune this if
                # you set vf_share_layers: True.
                "vf_loss_coeff": 1.0,
                # Coefficient of the entropy regularizer.
                "entropy_coeff": 0,
                # Decay schedule for the entropy regularizer.
                "entropy_coeff_schedule": None,
                # PPO clip parameter.
                "clip_param": 0.3,
                # Clip param for the value function. Note that this is sensitive to the
                # scale of the rewards. If your expected V is large, increase this.
                "vf_clip_param": 10.0,
                # If specified, clip the global norm of gradients by this amount.
                "grad_clip": None,
                # Target value for KL divergence.
                "kl_target": 0.01,
                # Whether to rollout "complete_episodes" or "truncate_episodes".
                "batch_mode": "truncate_episodes",
                # Which observation filter to apply to the observation.
                "observation_filter": "NoFilter",
                # Uses the sync samples optimizer instead of the multi-gpu one. This is
                # usually slower, but you might want to try it if you run into issues with
                # the default optimizer.
                "simple_optimizer": False,
                # Whether to fake GPUs (using CPUs).
                # Set this to True for debugging on non-GPU machines (set `num_gpus` > 0).
                "_fake_gpus": False,
#---------------------------------------------------------------------------------------
                "multiagent": {
                    "policies": policy_graphs,
                    "policy_mapping_fn": policy_mapping_fn,
                    "count_steps_by": "env_steps",
                },
                "env": "WirelessEnv"}

    # Define experiment details
    exp_name = 'wmac_marl'
    exp_dict = {
            'name': exp_name,
            'run_or_experiment': 'PPO',
            "stop": {
                "training_iteration": 1500,
                "timesteps_total": 3000000,
            },
            'checkpoint_freq': 200,
            "local_dir":"logs/",
            "verbose": 1,
            "config": config,
        }

    # Initialize ray and run
    ray.init()
    tune.run(**exp_dict)

if __name__=='__main__':
    setup_and_train()
