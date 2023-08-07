# Collective-Perception in Artery-C framework for large scale simulations

In my master thesis work, I performed simulation research study for comparing managed mode and unmanged mode of Cellular-V2X for [Collective Perception Service](https://www.etsi.org/deliver/etsi_tr/103500_103599/103562/02.01.01_60/tr_103562v020101p.pdf) of vehicular communication. This work includes extending the [Artery-C](https://github.com/anupama1990/Artery-C) simulation framework with Collective Perception Service in the facilities layer and integrating it with [InTAS](https://github.com/silaslobo/InTAS) sumo scenario and performing simulation experiments and comparing results. The detailed report of work done is in my thesis report - [Simulation-based Performance Evaluation of Collective Perception Service with Cellular-V2X](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/Master_Thesis_Report_09082022.pdf)

The results of this work has been publised in IEEE publications: [Radio Resource Allocation for Collective Perception in 5G-NR Vehicle-to-X Communication Systems](https://ieeexplore.ieee.org/document/10118606)


The files which I implemented/adopted for adding CP service in the facility layer of C-V2X stack are as below: 

1. [CpObject.cc](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/CpObject.cc)
2. [CpObject.h](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/CpObject.h)
3. [CpService.cc](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/CpService.cc)
4. [CpService.h](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/CpService.h)
5. [CpService.ned](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/CpService.ned)
6. [FilterObjects.cc](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/FilterObjects.cc)
7. [FilterObjects.h](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/FilterObjects.h)
8. [ObjectInfo.cpp](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/ObjectInfo.cpp)
9. [ObjectInfo.h](https://github.com/mlchethanupb/myworks/blob/master/master_thesis/code/src/artery/application/ObjectInfo.h)


With this opportunity, I gained good understanding on different aspects of vehicular communication like C-V2X communication stack, Sensing-Based Semi Persistant Scheduling, V2X applicaitons. 
