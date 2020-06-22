from gym.envs.registration import register

register(
    id='routing-v2',
    entry_point='routing_003.envs:Routing',
)