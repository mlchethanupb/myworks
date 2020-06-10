from ..environment.network import Network


class HopCountEnv(Network):

    def __init__(self, config):
        super(HopCountEnv, self).__init__(config)
        
    
    def _Network__compute_reward(self):
        # compute the (negative) hopcounts over all packets currently active in the network
        rew = sum(p.hopcount for p in self.active)
        # TODO: not needed anymore, since we forbit 'do nothing' actions
        # add the packet's lifetime so that the agent is penalized for doing nothing
        #rew += sum(self.env.now - p.start_time for p in self.active)
        return (-1)*rew

