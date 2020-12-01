
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common import make_vec_env
from stable_baselines.common.env_checker import check_env
import gym
import w_mac
from collections import defaultdict
import matplotlib as plt
import networkx as nx
import os
import argparse
from stable_baselines import A2C, PPO2
from stable_baselines.bench import Monitor


if __name__ == '__main__':
    # parse configuration of experiment
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    parser.add_argument('--graph', type=str, nargs='?', const=1, default='default', help='Either the path to a pickled networkx graph or \'default\'')
    parser.add_argument('--packet_size', type=float, nargs='?', const=1, default=2.0, help='(Constant) size of generated packages')
    parser.add_argument('--agent', type=str, nargs='?', const=1, default='A2C', help='Whether to use A2C, PPO, hot potato or shortest path routing')
    parser.add_argument('--total_train_timesteps', type=int,  nargs='?', const=1, default=400000, help='Number of training steps for the agent')
    parser.add_argument('--eval_episodes', type=int,  nargs='?', const=1, default=1000, help='Maximum number of episodes for final (deterministic) evaluation')
    parser.add_argument('--logs', type=str,  nargs='?', const=1, default='./a2c_tensorboard/', help='Path of tensorboard logs')
    args = parser.parse_args()

    total_train_timesteps = args.total_train_timesteps
    eval_episodes = args.eval_episodes

    config = {}
    config['PACKET_SIZE'] = args.packet_size


    d = defaultdict(list)
    """Larger network"""
    #data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4),(5,6),(6,7),(6,8),(7,8),(8,9),(9,10),(4,10)]#(4,6),(5,10),(6,10),(9,6),(8,10)]
    """Smaller netowrk"""
    data = [(0,2),(0,1),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]
    # defaultdict(<type 'list'>, {})
    for node, dest in data:
        d[node].append(dest)

    G = nx.Graph()
    for k,v in d.items():
        for vv in v:
            G.add_edge(k,vv)
    nx.draw_networkx(G)
    graph = args.graph if hasattr(args, 'graph') else None
    env = gym.make('wmac-graph-v1',graph=G)
    check_env(env)

    # Create log dir & monitor training so that episode rewards are logged
    os.makedirs(args.logs, exist_ok=True)
    env = Monitor(env, args.logs)
    
    if args.agent == 'A2C':
        agent = A2C("MlpPolicy", env, verbose=1, tensorboard_log=args.logs)
        agent.learn(total_timesteps=total_train_timesteps)
    
    elif args.agent == 'PPO2':
        agent = PPO2("MlpPolicy", env, verbose=1, tensorboard_log=args.logs)
        agent.learn(total_timesteps=total_train_timesteps)

    else:
         raise ValueError('Unknown agent.')

    # evaluate trained policy and render last episode
    avg_cumulated_reward = 0
    for episode in range(eval_episodes):
        cumulated_episode_reward = 0
        obs = env.reset()
        
        isdone = False
        while not isdone:
            actions, _ = agent.predict(obs, deterministic=False)

            # render last evaluation episode
            if episode == eval_episodes-1: 
                env.render()
                print(env.map_actions(actions))

            obs, rewards, isdone, _ = env.step(actions)
            cumulated_episode_reward += rewards

        avg_cumulated_reward += cumulated_episode_reward / eval_episodes
        
    print('AVG CUMULATED REWARD: %s' % avg_cumulated_reward)    