from gym.envs.registration import register

register(
    id='routing-v1',
    entry_point='routing_002.envs:Routing',
)
