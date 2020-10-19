import gym
from gym.envs.registration import register

gym.envs.register(
    id='wmac-tune-v0',
    entry_point='w_mac.envs:W_MAC_Env'
    # kwargs = {'graph':True}
)
