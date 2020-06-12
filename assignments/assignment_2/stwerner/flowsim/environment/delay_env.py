from ..environment.network import Network


class NetworkDelayEnv(Network):

    def __init__(self, config, DG='default'):
        super(NetworkDelayEnv, self).__init__(config, DG)
        
    def _Network__compute_reward(self):
        """ Define rewards as the negative lifespan of all active packets."""
        # sum lifespans of active packets in terms of the underlying network environment's discrete timesteps  
        rew = sum(self.env.now - p.start_time for p in self.active) 
        return (-1)*rew

        

