# FlowSim

FlowSim is a simple Deep Reinforcement Learning environment that simulates packet forwarding tasks from some source to a sink node via an arbitrary topology that is represented as a directed graph. FlowSim provides two primary experimental settings for the agent, i.e. whether to optimize packet forwarding with respect to hop counts or network delay.
## Example 
The ``script.py`` file provides an entrypoint to running FlowSim experiments. Here, you can specify whether rewards are attributed wrt. to hop counts or network delay, set the arrival process's specifications, the network's topologies and properties, an episode's parameters along with the agent's configuration. The following call simulates optimizing for network delay via the PPO1 RL agent:
```
python script.py --setting delay --model PPO1 
```
## Results
The network's topology is given by the following graph, where the task is to forward packets that are generated at the source (node 1) to the sink (node 7).

![Network's topology](figures/graph.svg)

Here, we show the results for PPO1 for the hopcount environment. Performance is recorded over the training period for 50,000 timesteps with tensorboard.

![PPO1 optimizing wrt. hop counts](figures/PPO1_hopcount.svg)

Here, we show the results for PPO1 for the network delay environment. Performance is recorded over the training period for 50,000 timesteps with tensorboard.

![PPO1 optimizing wrt. network delay](figures/PPO1_delay.svg)