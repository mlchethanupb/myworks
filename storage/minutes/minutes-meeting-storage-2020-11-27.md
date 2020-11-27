# Minutes from 2020-11-27

Start: 13:50

End: 14:30


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	Database is running on Kubernetes 

## Discussed Issues

* Discussion on how to unmount Kafka's volume file from previous run. 
* Discussion on current Database deployment and metrics.


## Action Points

*	Try unmounting Kafka volume from entry point of docker image first, try to track down GlusterFS volume files from inside container to delete Kafka volume file if first approach doesn't work.
* Analyze InfluxDB with current metrics first. If the result is not satisfactory, consider collecting other relevant metrics, for instance, response time.
* In case of another implementation approach of InfluxDB, consider Python API. 
