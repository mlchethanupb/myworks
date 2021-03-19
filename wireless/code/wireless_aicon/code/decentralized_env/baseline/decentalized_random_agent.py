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
    pac_lost = []
    succ_trans = []
    total_trans = []
    timesteps_list = []
    for itr in range(50000):
        episode_reward = 0
        obs = env.reset()
        timesteps = 0
        while (1):
            timesteps += 1
            obs, reward, done, info = env.step(get_actions())
            if done['__all__']:
                packet_delivered.append(env.get_packet_delivered_count())
                pac_lost.append(env.get_packet_lost())
                succ_trans.append(env.get_succ_transmissions())
                total_trans.append(env.get_total_transmissions())
                timesteps_list.append(timesteps)
                if itr % 5000 == 0:
                    print("packet delivered mean after ", itr," episodes:", np.mean(packet_delivered))
                    print("packet lost mean after ", itr," episodes:", np.mean(pac_lost))
                    print("Successfull transmission mean after ", itr," episodes:", np.mean(succ_trans))
                    print("Total transmission mean after ", itr," episodes:", np.mean(total_trans))
                    print("Total timesteps mean after ", itr," episodes:", np.mean(timesteps_list))
                break

    print("final packt delivered in % :", 100 * np.mean(packet_delivered)/env.get_total_packets())
    print("final packt lost in % :", 100 * np.mean(pac_lost)/env.get_total_packets())
    print("final successful transmission in % :", 100 * np.mean(succ_trans)/np.mean(total_trans))
    print("final total transmission mean :", np.mean(total_trans))
    print("final total timesteps mean", np.mean(timesteps_list))
