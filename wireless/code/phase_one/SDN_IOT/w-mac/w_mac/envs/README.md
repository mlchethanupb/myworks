# Wireless transmission in a network with multiple collison domains and defect nodes

## Implementation of the environment
This is an implementation of Reinforcement Learning environment for transmitting a multiple packets at a time in wireless network with multiple collision domains and multiple defect nodes. The main objective of the agent is to transfer the packets present in packet queue of each of the nodes in the network to certain destination present in the packet. While transmitting the packets the agent has to avoid collision of the packets and defect node as next hop. Packet collision will happen when two or more nodes within the same collision domain are transmitting at the same time.


## Action Space
* The action for each node is to either Transmit or Wait.
    * Transmit - When selected next hop is within the collision domain of source node.
    * Wait - When selected next hop is equal to total number of nodes.



## Observation Space
Destination of the each packets present in nodes along with defect node information.

## Rewards
There are multiple scenarios to punish or reward the agent for the action it performs.
### Positive reward
* Packet reached destination
### Negative reward
* Next hop not present in the same collision domain
* Next hop is defect node
* Packet collision

## Environment Installation
1. git clone <git repo url>
2. Go to w-mac folder and run command `pip install -e .`
3. Run agents.py
4. Log results using tensorboard
    4. Create a folder using tensorboard_log `model = PPO2(MlpPolicy, env, verbose=1,tensorboard_log="./tensorboard/")`
    4. Go to tensorboard file and run command `tensorboard --logdir tensorboard`


## Usage Example
Let's consider, there is wireless network with 2 collision domains. node0, node1, node2, node3 are present in collision domain1 and node2, node3, node4, node5 are present in collision domain2. node2 and node3 are intermediate nodes, which are present in both collision domains. The nodes within the same collision domain are connected with each other and nodes in different collision domains are connected via intermediate node. For example, The packet at Source = node0 to be transmitted to Destination = node4 should avoid Defect node = node2 and collision with other transmission in the same collision domain.

![Network Topology](D:\Summer Sem 2020 -Corona Online\Network_Topology.PNG)

The network topology can be changed by providing the new graph data in agents.py

## Development Setup
The environment is developed using Python 3.6
Tensorflow 1.13.2
Libraries used - `gym, networkx, matplotlib, stable_baselines`



## Results



## Hyper-parameter Optimization