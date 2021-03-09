import os
import argparse
import logging
import gym
import numpy as np
from typing import Union
from copy import deepcopy
from ax.service.ax_client import AxClient
import ray
from ray import tune
from ray.tune import report
from ray.tune.suggest.ax import AxSearch
from stable_baselines import A2C, PPO2, TRPO, PPO2
from stable_baselines.common.env_checker import check_env
from stable_baselines.common.callbacks import EveryNTimesteps
from stable_baselines.common.evaluation import evaluate_policy
from stable_baselines.common.vec_env import DummyVecEnv, VecEnv, sync_envs_normalization
from stable_baselines.common.callbacks import BaseCallback
import environment
import job_distribution
import parameters
from stable_baselines.common import make_vec_env
from stable_baselines.common.policies import FeedForwardPolicy, register_policy


class OptimizationCallback(BaseCallback):

    def __init__(self, eval_env: Union[gym.Env, VecEnv],
                 n_eval_episodes: int = 5,
                 deterministic: bool = True,
                 verbose=0):
        super(OptimizationCallback, self).__init__(verbose)
        self.eval_env = deepcopy(eval_env)
        self.eval_env.reset()
        self.n_eval_episodes = n_eval_episodes
        self.deterministic = deterministic

    def _on_step(self):
        sync_envs_normalization(self.training_env, self.eval_env)

        episode_rewards, episode_lengths = evaluate_policy(self.model, self.eval_env,
                                                           n_eval_episodes=self.n_eval_episodes,
                                                           render=False,
                                                           deterministic=self.deterministic,
                                                           return_episode_rewards=True)

        mean_reward, std_reward = np.mean(
            episode_rewards), np.std(episode_rewards)
        mean_ep_length, std_ep_length = np.mean(
            episode_lengths), np.std(episode_lengths)

        report(
            mean_reward=mean_reward,
            std_reward=std_reward,
            mean_ep_length=mean_ep_length,
            std_ep_length=std_ep_length
        )


class CustomPolicy(FeedForwardPolicy):

    def __init__(self, *args, **kwargs):
        super(CustomPolicy, self).__init__(*args, **kwargs,
                                           net_arch=[dict(
                                               pi=[4480, 20, 11],
                                               vf=[4480, 20, 11])],
                                           feature_extraction="mlp")


def main(pa, args):
    # parse configuration of experiment
    parser = argparse.ArgumentParser(description='Tune Agent')
    parser.add_argument('--agent', type=str, nargs='?', const=1, default='PPO2',
                        help='Whether to use A2C, PPO2, DQN or TRPO')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?',
                        const=1, default=25000, help='Number of training steps for the agent')
    parser.add_argument('--report_interval', type=int, nargs='?', const=1, default=1000,
                        help='Interval between reportings from callback (in timesteps)')
    parser.add_argument('--ray_eval_episodes', type=int, nargs='?', const=1, default=1,
                        help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--ray_tune_samples', type=int, nargs='?', const=1,
                        default=100, help='Number of trials for hyperparameter optimization')
    parser.add_argument('--ray_cpus', type=int, nargs='?', const=1, default=12,
                        help='Number of cpus ray tune will use for the optimization')
    default_objective = pa.objective_Ctime
    if args['objective'] != None:
        default_objective = args['objective']
    parser.add_argument('--objective', type=str, nargs='?', const=1, default=default_objective,
                        help='Path to search spaces for hyperparameter optimization')
    parser.add_argument('--logs', type=str, nargs='?', const=1, default=None,
                        help='Path of tensorboard logs for best model after optimization')

    args = parser.parse_args()

    # Reduce the number of Ray warnings that are not relevant here.
    logger = logging.getLogger(tune.__name__)
    logger.setLevel(level=logging.CRITICAL)

    EVAL_EPISODES = args.ray_eval_episodes
    TOTAL_TIMESTEPS = args.total_train_timesteps
    RAY_TUNE_SAMPLES = args.ray_tune_samples

    if args.objective == pa.objective_slowdown:
        pa.objective = pa.objective_slowdown
    else:
        pa.objective = pa.objective_Ctime

    print("pa objective is ->", pa.objective)

    base_env = environment.Env(
        pa, render=False, repre='image', end='all_done')
    base_env = make_vec_env(lambda: base_env, n_envs=1)
    tune_env = deepcopy(base_env)
    tune_monitor = OptimizationCallback(tune_env, EVAL_EPISODES, False)
    monitor_callback = EveryNTimesteps(
        n_steps=args.report_interval, callback=tune_monitor)

    def evaluate_objective(config):
        print("config-> ", config)

        if args.agent == 'A2C':
            print("A2C Agent")
            tune_agent = A2C
            tune_env = deepcopy(base_env)
            tune_monitor = OptimizationCallback(tune_env, EVAL_EPISODES, False)
            monitor_callback = EveryNTimesteps(
                n_steps=args.report_interval, callback=tune_monitor)

            # model = models[i]['load'](
            #         CustomPolicy, env1,
            #         gamma=0.9, learning_rate=1e-3,
            #         tensorboard_log=pa.tensorBoard_Logs)

            tune_agent = tune_agent(CustomPolicy, tune_env)
            tune_agent.learn(total_timesteps=TOTAL_TIMESTEPS,
                             callback=monitor_callback)

        elif args.agent == 'PPO2':
            print("PPO2 Agent")
            tune_agent = PPO2
            tune_env = deepcopy(base_env)
            tune_monitor = OptimizationCallback(tune_env, EVAL_EPISODES, False)
            monitor_callback = EveryNTimesteps(
                n_steps=args.report_interval, callback=tune_monitor)
            tune_agent = tune_agent(CustomPolicy, tune_env)
            tune_agent.learn(total_timesteps=TOTAL_TIMESTEPS,
                             callback=monitor_callback)

        elif args.agent == 'TRPO':
            print("TRPO Agent")
            tune_agent = TRPO
            tune_env = deepcopy(base_env)
            tune_monitor = OptimizationCallback(tune_env, EVAL_EPISODES, False)
            monitor_callback = EveryNTimesteps(
                n_steps=args.report_interval, callback=tune_monitor)
            tune_agent = tune_agent(CustomPolicy, tune_env)
            tune_agent.learn(total_timesteps=TOTAL_TIMESTEPS,
                             callback=monitor_callback)

        else:
            print("Unknown parameters passed in the argument")

    ax_client = AxClient(enforce_sequential_optimization=False)
    if args.agent == 'PPO2':
        parameters = [
            {"name": "learning_rate", "type": "range",
                "bounds": [3e-05, 0.003]},
            {"name": "gamma", "type": "range", "bounds": [0.20, 1.0]},
            {"name": "max_grad_norm", "type": "range", "bounds": [0.3, 7.0]},
        ]
    elif args.agent == 'A2C':
        parameters = [
            {"name": "learning_rate", "type": "range",
                "bounds": [3e-04, 0.003]},
            {"name": "gamma", "type": "range", "bounds": [0.2, 1.0]},
            {"name": "vf_coef", "type": "range", "bounds": [0.10, 0.5]},
            {"name": "alpha", "type": "range", "bounds": [0.1, 0.8]},
            {"name": "epsilon", "type": "range", "bounds": [3e-5, 1e-3]},
            {"name": "max_grad_norm", "type": "range", "bounds": [0.3, 7.0]}
        ]
    elif args.agent == 'TRPO':
        parameters = [
            {"name": "gamma", "type": "range", "bounds": [0.2, 1.0]},
            {"name": "lam", "type": "range", "bounds": [0.80, 0.99]},
            {"name": "cg_damping", "type": "range", "bounds": [1e-3, 1e-2]},
            {"name": "max_kl", "type": "range", "bounds": [0.01, 0.02]}
        ]

    else:
        print("Invalid argument given for agent")

    ax_client.create_experiment(
        name="tune_RL",
        parameters=parameters,
        objective_name='mean_reward',
        minimize=False)

    # ignore_reinit_error=True
    ray.shutdown()
    ray.init(num_cpus=args.ray_cpus)
    # ray.init(webui_host='0.0.0.0', num_cpus=args.ray_cpus)
    tune.run(
        evaluate_objective,
        num_samples=RAY_TUNE_SAMPLES,
        search_alg=AxSearch(ax_client=ax_client),
        verbose=1
    )

    # get best parameters, retrain agent and log results for best agent
    best_parameters, values = ax_client.get_best_parameters()

    return best_parameters, args


if __name__ == '__main__':
    pa = parameters.Parameters()
    parser = argparse.ArgumentParser(description='Tune Agent')
    parser.add_argument('--objective', type=str, nargs='?', const=1, default="Job_Completion_Time",
                        help='Job Objective')
    args = parser.parse_args()
    objective = pa.PPO2_Tuned_CT
    log_dir = objective['log_dir']
    save_path = log_dir
    # Give objective of completion time here
    objective = pa.objective_Ctime
    args = {'objective': objective}
    best_parameters, args = main(pa, args)
    env = environment.Env(pa, render=False, repre='image', end='all_done')
    env1 = make_vec_env(lambda: env, n_envs=1)
    if args.agent == 'A2C' or args.agent == 'PPO2' or args.agent == 'TRPO':
        tune_agent = A2C
        if args.agent == 'PPO2':
            tune_agent = PPO2
        elif args.agent == 'TRPO':
            tune_agent = TRPO

        best_agent = tune_agent(
            CustomPolicy, env1, **best_parameters, verbose=1, tensorboard_log=log_dir)
        best_agent.learn(total_timesteps=int(args.total_train_timesteps))
        print("Tensorboard logs path -> ", log_dir)
        print("The best parameters were as follows = ", best_parameters)
        print("Agent save path = ", save_path)
        print(best_parameters)
        best_agent.save(save_path + "Tuned_PPO2")

    else:
        print("Invalid agent is passed as input")

    print("Raytune Processing for the agent = " + args.agent +
          " for the objective = " + args.objective + " is done ")
