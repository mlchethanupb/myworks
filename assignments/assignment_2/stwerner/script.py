import argparse
import networkx as nx
from flowsim.environment.network import Network
from flowsim.environment.hopcount_env import HopCountEnv
from flowsim.environment.delay_env import NetworkDelayEnv
from flowsim.baselines import HotPotatoRouting, ShortestPathRouting
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C, PPO1
from stable_baselines.common.env_checker import check_env


if __name__ == '__main__':
    # parse configuration of experiment
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    parser.add_argument('--setting', type=str, nargs='?', const=1, default='hopcount', help='Whether to simulate \'hopcount\' or network \'delay\'')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='default', help='Either the path to a pickled networkx graph or \'default\'')
    parser.add_argument('--arrival', type=int, nargs='?', const=1, default=1, help='(Constant) time between generating packets at the source node')
    parser.add_argument('--max_arrival', type=int, nargs='?', const=1, default=30, help='Maximum timestep considered to generate packets')
    parser.add_argument('--packet_size', type=float, nargs='?', const=1, default=2.0, help='(Constant) size of generated packages')
    parser.add_argument('--agent', type=str, nargs='?', const=1, default='PPO1', help='Whether to use A2C, PPO1, hot potato or shorest path routing .')
    parser.add_argument('--logs', type=str,  nargs='?', const=1, default=None, help='Path of tensorboard logs')
    args = parser.parse_args()


    total_train_timesteps = 50000
    max_eval_episodes = 1000

    config = {}
    config['ARRIVAL_TIME'] = args.arrival
    config['MAX_ARRIVAL_STEPS'] = args.max_arrival
    config['PACKET_SIZE'] = args.packet_size

    graph = args.graph if hasattr(args, 'graph') else None
    env = HopCountEnv(config, graph) if args.setting == 'hopcount' else NetworkDelayEnv(config, graph)
    check_env(env)
    
    if args.agent == 'A2C':
        agent = A2C("MlpPolicy", env, verbose=1, tensorboard_log=args.logs)
        agent.learn(total_timesteps=total_train_timesteps)
    
    elif args.agent == 'PPO1':
        agent = PPO1("MlpPolicy", env, verbose=1, tensorboard_log=args.logs)
        agent.learn(total_timesteps=total_train_timesteps)
    
    elif args.agent == 'hot-potato':
        agent = HotPotatoRouting(env)
        agent.learn(total_timesteps=total_train_timesteps, tensorboard_log=args.logs)
    
    elif args.agent == 'shortest-path':
        agent = ShortestPathRouting(env)
        agent.learn(total_timesteps=total_train_timesteps, tensorboard_log=args.logs)

    else:
         raise ValueError('Unknown agent.')

    # evaluate trained policy and render last episode
    avg_cumulated_reward = 0
    for episode in range(max_eval_episodes):
        cumulated_episode_reward = 0
        obs = env.reset()
        
        isdone = False
        while not isdone:
            actions, _ = agent.predict(obs, deterministic=False)

            # render last evaluation episode
            if episode == max_eval_episodes-1: 
                env.render()
                print(env.map_actions(actions))

            obs, rew, isdone, _ = env.step(actions)
            cumulated_episode_reward += rew


        avg_cumulated_reward += cumulated_episode_reward / max_eval_episodes
        
    print('AVG CUMULATED REWARD: %s' % avg_cumulated_reward)    