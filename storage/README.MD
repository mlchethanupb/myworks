# Storage

**Advisor**: Marvin Illian

**Members**
* Indranil Ghosh
* Lameya Afroze
* Nayela Labonno
* Shraddha Pawar

**[Weekly Meeting](https://bbb.imt.uni-paderborn.de/b/mar-cze-jjj)**

* CPU allocation in NFV is being actively researched and is more and more well understood
* However, storage as another type of resource did not receive much attention, yet
* Storage is interesting because
    1. it is needed to keep state (especially important for container-based orchestration frameworks, like Kubernetes)
    2. it has implications on other VNFs and the availability of other resources
* Understand the difference between different resources in NFV: CPU vs. Storage vs. Network
* How can we characterise storage consumption?/How do characterisations of CPU consumption compare?
* Which parameters are suited to use ML to determine long-term required storage resources?

## Phase 1 -- Supervised Learning
* Long-term storage demands of different application types might differ substantially
    - Cache -- upper bound for total storage resources?
    - Database -- steadily growing demand?
    - Message Broker -- based on retention period, requests/s (incoming and outgoing data)?
* Familiarise with tools
    * [Docker](https://www.katacoda.com/courses/docker)
    * [Kubernetes](https://github.com/OrangeOnBlack/auto-kubernetes-setup)
    * [GlusterFS](https://github.com/OrangeOnBlack/stateful-kubernetes)
    * [Kafka](https://github.com/OrangeOnBlack/kafka)
    * [Digital Twin (Machine Data Generator)](https://github.com/sonata-nfv/tng-industrial-pilot/tree/f3a992871c8d5ef3272baf18c3fa12a65894be75/vnfs/dt-digitaltwin-docker/containers)
    * [OPC UA&rarr;Kafka Connector](https://github.com/OrangeOnBlack/opc_ua_kafka_connector)
    * Also required: OPC UA&rarr;Database/Cache Connectors
* Decide on storage applications
* Model profiling scenarios
    * Decide on parameters (e.g., retention time, requests/s)
    * Implement profiling scenarios
* Run experiments and collect data
* Train ML models and verify accuracy

## Phase 2 -- Resource Allocation
* Decide on VNF service chain
* Build self-managing system
    * Adjust storage allocation
    * Add/remove storage
    * Measure downtime, additional/reduced costs
    * Implement/re-used conttainers from Phase 1
    * Use RL to manage allocation decisions

## Further Research Questions
* Investigate Tradeoffs
    * Compression (lossy/lossless; during transmission/on disk)
    * Impact on
        * Required Storage
        * Network Load
        * CPU Utilisation
        * Data Access Latency


## Input for Mini-Seminar
* [S. Baig, W. Iqbal, J. L. Berral, A. Erradi and D. Carrera, "Adaptive Prediction Models for Data Center Resources Utilization Estimation," in IEEE Transactions on Network and Service Management, vol. 16, no. 4, pp. 1681-1693, Dec. 2019.](https://ieeexplore.ieee.org/document/8786216)
* [H. Kim, S. Jeong, D. Lee, H. Choi, J. Yoo and J. W. Hong, "A Deep Learning Approach to VNF Resource Prediction using Correlation between VNFs," 2019 IEEE Conference on Network Softwarization (NetSoft), Paris, France, 2019, pp. 444-449.](https://ieeexplore.ieee.org/document/8806620)
* [L. Nobach, I. Rimac, V. Hilt and D. Hausheer, "Statelet-Based Efficient and Seamless NFV State Transfer," in IEEE Transactions on Network and Service Management, vol. 14, no. 4, pp. 964-977, Dec. 2017.](https://ieeexplore.ieee.org/document/8058500)
* [Eddy Truyen, Dimitri Van Landuyt, Bert Lagaisse and Wouter Joosen, "Performance overhead of container orchestration frameworks for management of multi-tenant database deployments," In Proceedings of the 34th ACM/SIGAPP Symposium on Applied Computing (SAC ’19), 2019, Association for Computing Machinery, New York, NY, USA, 156–159
](https://dl.acm.org/doi/10.1145/3297280.3297536)
