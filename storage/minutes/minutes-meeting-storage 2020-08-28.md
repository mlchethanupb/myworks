# Minutes from 2020-08-28

Start: 14:02

End: 14:40


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

* Creation of current scenario including current components and metrics.
* Metrics value has been collected (by using python script, kafka-consumer-perf-test.sh and kafka-producer-perf-test.sh) for several times which contains a specific duration of time and these values has been stored in a csv file.


## Discussed Issues

* Stop Zookeeper and restart kafka. After that check in which ip address kafka is running. Is that correct or not.
* Initially for testing purpose we can run files inside a container. But once testing is done it must be included in Dockerfile and image needed to build again for running the container. 
* Include timestamps on csv files if the programs can't start at the same time.


## Action Points

* Should have a look on disk usage (how fast it grows, current storage is sufficient enough or not). Run the python scripts for a long time and make message time more frequently on Digital Twin to see the effects of disk usage. May need to find another way to measure disk useage if it doesn't work for current scenario. 
* Setup the components on different vms and test whether they works properly on distributed system.
* Use OPC UA connector for collecting the previously discussed metrics.


