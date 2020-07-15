# Scheduling

**Advisor: Asif Hasnain**

**Members**

* Aluri Mohini

* Kunal Pratap Singh Sisodia

* Tejas Ravindra Dhawale

**[Discussion Room](https://bbb.imt.uni-paderborn.de/b/asi-nrc-egt)**


## Problem Statement :

  It is all about making the system to learn resource management by its own.
  To overcome the drawbacks associated with  heuristic based solutions, Reinforcement learning approach is considered (Thanks to machine learning).
  Our team is currently working to reproduce the results.

## Prerequisite

  * [VM Dashboard](https://vsc.cs.uni-paderborn.de/ui/) (Use IMT Login)
  * VS Code
  * Knowledge of python programming language
  * Info about TensorFlow, Deep Reinforcement Learning.

## Proposal :

We are currently assuming that, the mind of job is known once it is arrived.

1) State : The jobs that are allocated currently to the resource, 
           the jobs in waiting list.
		   
2) Action : As an action, any number of jobs can be choosen from the waiting list.

3) Reward : Minimizing average slowdown.

This is our current proposal for the problem we have choosen. 

## Phase 1 -- Supervised Learning

MileStones

1) Designing the Job scheduling Enviroment
2) Finalizing the factors Discounts, learning curves, baselines methods DRL, Tensor flow, theano, entropy, input samples.
3) Finalize all the input parameters like - output freq, job length, timespan, new job rate, etc
4) Designing Job Distribution - Defining work distribution, resources required, Job sequence.
5) Agent Design and Training
6) Designing Network - containing state, actions reward, neural network design for training
7) Slow down calculations.
8) Designing inputs or getting it from a source
9) Familiarise with libraries - theano, numpy, cPickle,lasagne, Tensorflow,DRL Techniques.
10) Comparing the obtained results with the original paper

## Input :

* [Learning scheduling algorithms for data processing clusters](https://web.mit.edu/decima/content/sigcomm-2019.pdf)
* [Resource Management with Deep Reinforcement Learning](https://people.csail.mit.edu/alizadeh/papers/deeprm-hotnets16.pdf)
* [Variance Reduction for Reinforcement Learning in Input-driven Environments](https://people.csail.mit.edu/malte/pub/papers/2019-iclr-variance.pdf)
