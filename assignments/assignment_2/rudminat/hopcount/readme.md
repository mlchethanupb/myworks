## Hopcount



A small summary of the  functionality of this environment:



The Agent will learn the shortest path from each node to each node.

The state is 0. So there are no state information given.

The action is a matrix. For 5 nodes it could be look like this:

$$ A = \left( \begin{matrix} 0 & 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 & 4 \\ 0 & 1 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0 & 0 \end{matrix} \right) $$

An entry $x_{i,j}$ means that a packet at node $i$ with the destination node $j$ is sent to the node $x_{i,j}$. 
In the example node 2 will sent a packet with destination 4 to node 4. In the most cases (in this example) each node will route each packet to node 0, which is obviously not optimal.


In the end the agent learns the optimal shortest path matrix because no state information are given.


Reward: -Hopcount + a small reward if the destination is reached.



The agent is PPO2 from Stable Baselines.


With the parameter --load it is possible to load the previously learned agent.

The algorithm will  also create tensorboard logs in the Log folder.