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

In our work, we mainly aim to evaluate Reinforcement Learning algorithms to route the packets in the network to there respective destination by minimizing the loss of packets due some of important challenges such as signal interference, defect nodes in the network and hidden terminal problem that occur in most of the wireless communication networks. The above ideas are based on research papers [Deep-Reinforcement Learning Multiple Access for Heterogeneous Wireless Networks](https://ieeexplore.ieee.org/document/8422168) and [Deep-Reinforcement-Learning-Based QoS-Aware Secure Routing for SDN-IoT](https://ieeexplore.ieee.org/document/8935210). 

## Solution Approaches
We have three different environments to measure the performance of RL agent
* Centralized agent with no routing - The agent gives the action to transmit or wait
* Centralized agent with routing - Agent gives the routing information along with the transmit or wait
* Decentralized agent with routing - Agent gives the routing information along with the transmit or wait

## Environment Setup

### Install Conda
Install Anaconda (version 4.9.2)

### Create environment to run the project
`conda env create -f environment.yml` this will install all the prerequisits and creates an environment needed to execute the project

### Train the different agents for centralized approaches
`python training_script.py --agent='PPO2_MAC_routing` will use PPO2 for the centralized network with MAC and routing
`python training_script.py --agent='A2C_MAC_routing` will use A2C for the centralized network with MAC and routing
`python training_script.py --agent='PPO2_MAC` will use PPO2 for the centralized network with MAC alone
Agents can be trained for different network topologies by giving a graph as an argument while running the training_script.py
Example - `python training_script.py --graph='[(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),(2,4),(3,4),(5,2),(5,3),(5,4)]'

### To evaluate the performance of agents
`python eval_script.py` will evaluate the performance of PPO2_MAC_routing agent

### To generate the box-plots to analyse the performance
`python box.py` generates the box plot for all the agent's performance on different metrics considered

## Results and Observations
To measure the performance of trained RL agents, we have considered metrics such as Packet delivery rate, successfull transmission rate, total timesteps taken to delivery all the packets and time steps taken to transfer fixed number of packets.
The performance of trained RL agents is compared with the baselines. The baselines which uses Destination Sequenced Distance Vector (DSDV) routing protocol and Time-Division Multiple Access (TDMA) MAC protocol. The baseline DSDV priority based round-robin allocates the time slot based on weight of the queue at each node and DSDV round-robin variant assigns the timeslot in round-robin fashion.


### Successful Transmission Rate
Capability of the agent to identify the collision-free time slot to transfer the packet.

### Packet Delivery Rate
Transferring the packets from source to destination.

### Time-steps for all packets
Total time taken for the agent to transfer all the packets in the network to respective destinations. This metric includes
the time steps for every transmission which can lead to packet loss or packet transmission to next-hop or to destination.


### Time-steps for fixed packets delivery
Total time taken for the agent to transfer fixed number of packets in the network to respective destinations. This metric includes only time steps for successful packet delivery.















