import argparse
import networkx as nx
from flowsim.environment.network import Network
from flowsim.environment.hopcount_env import HopCountEnv
from flowsim.environment.delay_env import NetworkDelayEnv
from flowsim.hot_potato import HotPotatoRouting
from stable_baselines.deepq.policies import MlpPolicy
from stable_baselines import A2C, PPO1
from stable_baselines.common.env_checker import check_env


if __name__ == '__main__':
    # parse configuration of experiment
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    parser.add_argument('--setting', type=str, nargs='?', const=1, default='hopcount', help='Whether to simulate \'hopcount\' or network \'delay\'')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='default', help='Either the path to a pickled networkx graph or \'default\'')
    parser.add_argument('--arrival', type=int, nargs='?', const=1, default=3, help='(Constant) time between generating packets at the source node')
    parser.add_argument('--max_arrival', type=int, nargs='?', const=1, default=20, help='Maximum timestep considered to generate packets')
    parser.add_argument('--packet_size', type=float, nargs='?', const=1, default=2.0, help='(Constant) size of generated packages')
    parser.add_argument('--model', type=str, nargs='?', const=1, default='A2C', help='Whether to train A2C or use hotpotato routing')
    parser.add_argument('--logs', type=str,  nargs='?', const=1, default=None, help='Whether to train A2C or use hotpotato routing')
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
    
    if args.model == 'A2C':
        tensorboard_logpath = args.logs
        model = A2C("MlpPolicy", env, verbose=1, tensorboard_log=tensorboard_logpath)
        model.learn(total_timesteps=total_train_timesteps)
    
    elif args.model == 'PPO1':
        model = PPO1("MlpPolicy", env, verbose=1, tensorboard_log=tensorboard_logpath)
        model.learn(total_timesteps=total_train_timesteps)
    
    elif args.model == 'hot-potato':
        model = HotPotatoRouting(env)

    else:
         raise ValueError('Unknown model.')

    # evaluate trained policy and render last episode
    avg_cumulated_reward = 0
    for episode in range(max_eval_episodes):
        cumulated_episode_reward = 0
        obs = env.reset()
        
        isdone = False
        while not isdone:
            actions, _ = model.predict(obs, deterministic=False)

            if episode == max_eval_episodes-1: 
                env.render()
                print(env.map_actions(actions))

            obs, rew, isdone, _ = env.step(actions)
            cumulated_episode_reward += rew


        avg_cumulated_reward += cumulated_episode_reward / max_eval_episodes
        
    print('AVG CUMULATED REWARD: %s' % avg_cumulated_reward)    