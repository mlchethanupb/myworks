from gym.envs.registration import register

register(
    id='wmac-graph-v0',
    entry_point='w_mac.envs:W_MAC_Env',
    kwargs = {'graph':True}
)
