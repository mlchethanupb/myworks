import os
import argparse
import logging
import dill
import networkx as nx
from copy import deepcopy
from ax.service.ax_client import AxClient
import ray
from ray import tune
from ray.tune import report
from ray.tune.suggest.ax import AxSearch
from flowsim.environment.network import Network
from flowsim.environment.hopcount_env import HopCountEnv
from flowsim.environment.delay_env import NetworkDelayEnv
from flowsim.tuning.monitor import OptimizationCallback
from stable_baselines3 import A2C, PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import EveryNTimesteps


if __name__ == '__main__':
# parse configuration of experiment
    parser = argparse.ArgumentParser(description='FlowSim tuning experiment specification.')
    parser.add_argument('--setting', type=str, nargs='?', const=1, default='delay', help='Whether to simulate \'hopcount\' or network \'delay\'')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='default', help='Either the path to a pickled networkx graph or \'default\'')
    parser.add_argument('--arrival', type=int, nargs='?', const=1, default=1, help='(Constant) time between generating packets at the source node')
    parser.add_argument('--max_arrival', type=int, nargs='?', const=1, default=30, help='Maximum timestep considered to generate packets')
    parser.add_argument('--packet_size', type=float, nargs='?', const=1, default=2.0, help='(Constant) size of generated packages')
    parser.add_argument('--agent', type=str, nargs='?', const=1, default='PPO', help='Whether to use A2C, PPO, hot potato or shortest path routing')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?', const=1, default=100000, help='Number of training steps for the agent')
    parser.add_argument('--report_interval', type=int, nargs='?', const=1, default=1000, help='Interval between reportings from callback (in timesteps)')
    parser.add_argument('--ray_eval_episodes', type=int, nargs='?', const=1, default=5, help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--ray_tune_samples', type=int, nargs='?', const=1, default=48, help='Number of trials for hyperparameter optimization')
    parser.add_argument('--ray_cpus', type=int, nargs='?', const=1, default=12, help='Number of cpus ray tune will use for the optimization')
    parser.add_argument('--search_space', type=str, nargs='?', const=1, default=r'./search_spaces/ppo.json', help='Path to search spaces for hyperparameter optimization')
    parser.add_argument('--logs', type=str, nargs='?', const=1, default=None, help='Path of tensorboard logs for best model after optimization')
    args = parser.parse_args()

    # Reduce the number of Ray warnings that are not relevant here.
    logger = logging.getLogger(tune.__name__)  
    logger.setLevel(level=logging.CRITICAL)

    EVAL_EPISODES = args.ray_eval_episodes
    TOTAL_TIMESTEPS = args.total_train_timesteps
    RAY_TUNE_SAMPLES = args.ray_tune_samples

    net_config = {}
    net_config['ARRIVAL_TIME'] = args.arrival
    net_config['MAX_ARRIVAL_STEPS'] = args.max_arrival
    net_config['PACKET_SIZE'] = args.packet_size

    graph = args.graph if hasattr(args, 'graph') else None
    base_env = HopCountEnv(net_config, graph) if args.setting == 'hopcount' else NetworkDelayEnv(net_config, graph)

    # DEBUG: check environment for gym interface & serializability
    assert(dill.pickles(base_env))
    #check_env(base_env)

    ### Define objective function for hyperparameter tuning
    def evaluate_objective(config):
        tune_env = deepcopy(base_env)
        tune_monitor = OptimizationCallback(tune_env, EVAL_EPISODES, True)
        monitor_callback = EveryNTimesteps(n_steps=args.report_interval, callback=tune_monitor)

        tune_agent = PPO if args.agent == 'PPO' else A2C 
        tune_agent = tune_agent("MlpPolicy", tune_env, **config)
        tune_agent.learn(total_timesteps=TOTAL_TIMESTEPS, callback=monitor_callback)

    ax_client = AxClient(enforce_sequential_optimization=False)

    parameters=[
            {"name": "learning_rate", "type": "range", "bounds": [3e-5, 3e-3]},
            {"name": "gamma", "type": "range", "bounds": [0.99, 1.0]},
            {"name": "gae_lambda", "type": "range", "bounds": [0.80, 1.0]},
            {"name": "max_grad_norm", "type": "range", "bounds": [0.3, 7.0]}
    ]   

    ax_client.create_experiment(
        name="tune_RL",
        parameters=parameters,
        objective_name='mean_reward',
        minimize=False
    )

    ray.init(num_cpus=args.ray_cpus)
    tune.run(
        evaluate_objective, 
        num_samples=RAY_TUNE_SAMPLES, 
        search_alg=AxSearch(ax_client),  
        verbose=2
    )

    # get best parameters, retrain agent and log results for best agent
    best_parameters, values = ax_client.get_best_parameters()

    # log results for the best parameterization of the agent
    best_agent = PPO("MlpPolicy", base_env, **best_parameters, tensorboard_log=r'./delay_tuning_PPO')
    best_agent.learn(total_timesteps=TOTAL_TIMESTEPS)
    