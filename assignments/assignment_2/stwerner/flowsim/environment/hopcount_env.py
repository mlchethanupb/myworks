from ..environment.network import Network


class HopCountEnv(Network):

    def __init__(self, config, DG='default'):
        super(HopCountEnv, self).__init__(config, DG)
        
    def _Network__compute_reward(self):
        """ Define rewards as the negative amount of hopcounts summed over all active packets."""
        # compute the (negative) hopcounts over all packets currently active in the network
        rew = sum(p.hopcount for p in self.active)
        #rew += sum(self.env.now - p.start_time for p in self.active)
        return (-1)*rew

