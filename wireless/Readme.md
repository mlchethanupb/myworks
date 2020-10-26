# Wireless transmission in a network with multiple collison domains and defect nodes

**Advisor**: [Haitham Afifi](https://github.com/haithamafifi)

**Developers**: [Chethan Lokesh Mariyaklla](https://github.com/mlchethanupb), [Pavitra B Gudimani](https://github.com/gudimani), [Priyanka Giri](https://github.com/pikuzz)

## Motivation 
<!-- what is the project
what is the problem and what is the solution

*the default routing protocols are vulnerable to network with defect nodes
* transmission in wireless network where each node will have a packet and they face the interference problem and here we are using the  RL what is the role of RL here.
* RL plays a role in dynamically assigning a time slot to transfer or wait for each node.
* RL also dynamically avoids a defect node in the network while transmitting the packet.
* We have merged the concept of dynamically allocating the time slot and defect node avoidance from the other paper. -->

In wireless networks to have the packets delivered to destination the nodes need to consider the interference caused by other nodes, hidden terminal problem and the accurate routing path by avoiding defect nodes. To achieve this we use Deep Reinforcement Learning (DRL) technique. The DRL agent would observe the environment and assign transmit or wait action to each of the node in the network and minimizes packet collision. Also it will allocate valid next hop in the routing path. The above ideas are based on research papers [Deep-Reinforcement Learning Multiple Access for Heterogeneous Wireless Networks](https://ieeexplore.ieee.org/document/8422168) and [Deep-Reinforcement-Learning-Based QoS-Aware Secure Routing for SDN-IoT](https://ieeexplore.ieee.org/document/8935210). 




## Implementation of the environment
This is an implementation of Reinforcement Learning environment for transmitting a multiple packets at a time in wireless network with multiple collision domains and defect node. The main objective of the agent is to transfer the packets present in packet queue of each of the nodes in the network to it's destination.

## Network Topology
Small network with 6 nodes and 2 collision domains.

<p align="center">
<img src="images/Network Topology_Small.png" alt="Small Network Topology" width="500"/>
</p>

Large network with 11 nodes and 6 collision domains.

<p align="center">
<img src="images/Network Topology_Large.png" alt="Large Network Topology" width="500"/>
</p>


## Action Space
* Next hop of each node within range and Transmit/Wait (T/W) status.
* Action space for 6 nodes network
   * MultiDiscrete ( [4, 4, 6, 6, 4, 4] )
   * Example [1, 1, 2, 3, 4, 5] = [T, W, W, W, W, W]



## Observation Space
* Destination of a packet at each node
* Defect node 
* State space for 6 nodes network
   * MultiDiscrete ( [7, 7, 7, 7, 7, 7, 6] )

## Rewards
The rewards to agent are given by considering the two criterias to transmit the packet.
1. The agent has to deliver the packet by avoiding collision of packets.
2. The agent has to select a routing path without a defect node.


## RL Agent
* A2C

## Environment Installation
1. Open `pg-aicon/wireless/code/phase_one/SDN_IOT/w-mac` run command `pip install -e .`.
1. To train agent open `../w-mac/agents/` run cells in  `agent_train.ipynb`.
1. To test the model created open `../w-mac/agents/` run cells in `test.ipynb`.



## Usage Example
The network topology is given in graph format. We are using the `Networkx` library to define our topology. For example - the input for the below network can be given as [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]. 0, 1, 2, 3, 4 and 5 are switches/nodes in the network. Edge between nodes 0 and 1 is given as (0,1). Based on the edges between two switches the collision domain of each node will be decided. Here, 0 is connected with 1, 2 and 3. Similarly 1 is connected with 0, 2 and 3. 
Therefore, collision domain for nodes 0, 1, 2 and 3 will be same. The switches 4 and 5 are not connected directly with 0 and 1, so the collision domain of 4 and 5 will be different. Switches 2 and 3 are connected with all the other nodes in the network, therefore they are intermediate nodes.
Therefore, collision domain1 includes switches [0, 1, 2, 3] and collision domain2 includes switches [2, 3, 4, 5].


<p align="center">
<img src="images/Network_Topology.png" alt="Network Topology" width="500"/>
</p>

The network topology can be changed by updating graph connection data = [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)] in `agents.ipynb`

## Development Setup
The environment is developed using Python 3.7.9
Tensorflow 1.15.0
Libraries used - `gym = 0.17.3, networkx = 2.5, matplotlib = 3.3.2, stable_baselines = 2.10.1`



## Results and Observations
The trained agent has significantly reduced the packet loss by learning to avoid collision and defect nodes while routing the packets to destination in wireless networks with multiple collision domains. The expected result of having 0 packet loss was not achieved and larger network significantly increased the packet losses.


The below graph shows the performance of A2C over the 400000 timesteps for smaller network.
###### Reward Convergence Graph
<p align="center">
<img src="images/Reward convergence graph_small.PNG" alt="Reward Convergence Graph" width="500"/>
</p>

###### Packet Loss Graph
<p align="center">
<img src="images/Packet loss graph_small.PNG" alt="Packet Loss Graph" width="500"/>
</p>

The below graph shows the performance of A2C over the 10000000 timesteps for larger network.
###### Reward Convergence Graph
<p align="center">
<img src="images/Reward Convergence graph_large.PNG" alt="Reward Convergence Graph" width="500"/>
</p>

###### Packet Loss Graph
<p align="center">
<img src="images/Packet loss graph_large.PNG" alt="Packet Loss Graph" width="500"/>
</p>



