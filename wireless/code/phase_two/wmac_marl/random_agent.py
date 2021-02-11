from environment import WirelessEnv
import numpy as np

env = WirelessEnv()
num_agents = env.num_agents

def get_actions():
    action_dict = {}
    for i in range(env.num_agents):
        act_space = env.get_agent_action_space(i)
        action_dict[i] = act_space.sample()
    return action_dict 

if __name__=='__main__':

    packet_delivered = []
    for itr in range(50000):
        episode_reward = 0
        obs = env.reset()
        while (1):
            obs, reward, done, info = env.step(get_actions())
            if done['__all__']:
                packet_delivered.append(env.get_packet_delivered_count())
                if itr % 500 == 0:
                    print("pckt delivered mean after ", itr," episodes:", np.mean(packet_delivered))
                break

    print("final packt delivered mean :", np.mean(packet_delivered))