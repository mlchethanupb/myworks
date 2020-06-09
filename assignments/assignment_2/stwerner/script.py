import argparse
from flowsim.environment.network import Network


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FlowSim experiment specification.')
    #parser.add_argument('')

    config = {}
    config['arrival_time'] = 2
    config['episode_length'] = 15
    config['packet_size'] = 4.0

    # execute flowsim experiment
    network = Network(config)
    # TODO: create agent
    # TODO: training loop
    # TODO: write results to file

    network.reset()
    network.step([2, 0, 0, 0, 0])
    network.step([3, 0, 0, 0, 0])
    network.step([3, 3, 0, 0, 0])
    network.step([2, 0, 5, 0, 0])
    network.step([4, 0, 5, 0, 0])
    network.step([3, 3, 5, 0, 0])

    