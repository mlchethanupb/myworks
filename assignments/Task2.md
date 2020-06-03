# Task2

**Objective**: Learn how to formulate an RL problem and implement it in using openAI Gym

**Assignment**: We have a network that consists of nodes, which are connected with links. You are asked to do the following:

 - Create an RL environment for routing in wired networks with the following properties:
  	* The network has at least 5 nodes
  	* source and destination can be any of these nodes
	* packets have a fixed size and constant arrival rate
 - At the end you should have four different enviroments with
	* two different network topologies (of your own)
 	* metric is hop count, where all links have the same bandwidth
	* metric is network delay, where links have different bandwidth

 - Use a central learning algorithm (with global knoweledge) to find a routing solution. Using a multi-agent solution is a bonus

 - As a bonus task, you may compare your trained algorithm for network routing with an existing routing heuristic. 

**Submission**: At the end you will show a Demo of your RL agent (after training/learning). Codes should be submitted on Git.

**Deadline**: 

 - *Soft Deadline*: 05.June 2020. Have a running code - Do not worry if you have problems by then.
 - *Hard Deadline*: 12.June 2020. Everything should be working.
