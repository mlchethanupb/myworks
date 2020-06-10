import argparse
from flowsim.environment.network import Network
from flowsim.environment.hopcount_env import HopCountEnv


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    #parser.add_argument('')

    config = {}
    config['ARRIVAL_TIME'] = 5
    config['MAX_ARRIVAL_STEPS'] = 15
    config['PACKET_SIZE'] = 1.0


    hopcount = HopCountEnv(config)
    obs = hopcount.reset()
    hopcount.render()
    print(obs)
    print()
    obs,rew,_,_ = hopcount.step([1, 0, 0, 0])
    hopcount.render()
    print(obs)
    print()
    obs,rew,_,_ = hopcount.step([0, 0, 0, 0])
    hopcount.render()
    print(obs)
    print()
    obs,rew,_,_ = hopcount.step([2, 0, 0, 0])
    hopcount.render()
    print(obs)
    print()

    