from gym.envs.registration import register

register(
    id='routing-v0',
    entry_point='routing_001.envs:Routing',
)
