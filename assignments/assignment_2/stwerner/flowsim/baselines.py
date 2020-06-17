import gym
import numpy as np
import networkx as nx
import tensorflow as tf
from abc import ABC, abstractmethod


class Baseline(ABC):
    def __init__(self, env:gym.Env):
        self.env = env

    def learn(self, total_timesteps, tensorboard_log):
        num_episodes = 0
        num_timesteps = 0
        cum_eps_rew = 0

        while True:
            obs = self.env.reset()
            isdone = False
            tmp_eps_rew = 0

            while not isdone:
                actions, _ = self.predict(obs) 
                obs, rew, isdone, _ = self.env.step(actions)
                tmp_eps_rew += rew
                num_timesteps += 1
                if num_timesteps >= total_timesteps:
                    # log cum_eps_rew / num_episodes for tensorboard
                    self._log_constant_summary(tensorboard_log, total_timesteps, cum_eps_rew / num_episodes)
                    self.env.close()
                    return
            
            cum_eps_rew += tmp_eps_rew
            num_episodes += 1



    def _log_constant_summary(self, tensorboard_log, total_timesteps, avg_eps_rew):
        tf.reset_default_graph()   
        avg_rew = tf.constant(avg_eps_rew)
        avg_rew_summary = tf.summary.scalar(name='episode_reward' , tensor=avg_rew)
        avg_rew = tf.global_variables_initializer()
        
        with tf.Session() as sess:
            writer = tf.summary.FileWriter(tensorboard_log, sess.graph)
            for step in range(total_timesteps):
                sess.run(avg_rew)
                summary = sess.run(avg_rew_summary)
                writer.add_summary(summary, step)

    @abstractmethod
    def predict(self, state, **kwargs):
        pass


class HotPotatoRouting(Baseline):
    def __init__(self, env: gym.Env):
        super(HotPotatoRouting, self).__init__(env)

    def predict(self, state, **kwargs):
        # randomly sample action from multidiscrete action space
        return self.env.action_space.sample(), None


class ShortestPathRouting(Baseline):
    def __init__(self, env: gym.Env):
        super(ShortestPathRouting, self).__init__(env)
        shortest_path = np.asarray(nx.shortest_path(
            self.env.DG, self.env.source, self.env.sink), dtype=np.int)
        # choose a valid action for each node and subsequently adjust the actions as to match the shortest path
        self.actions = np.asarray(
            [list(self.env.DG.successors(n+1))[0] for n in range(self.env.num_nodes - 1)])
        self.actions[shortest_path[:-1] - 1] = shortest_path[1:]
        self.actions = self.env.inv_map_actions(self.actions)

    def predict(self, state, **kwargs):
        return self.actions, None
