# Minutes from 2020-09-25

Start: 12:00

End: 12:15


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	Kafka distributed environment on Kubernetes is up and running.
* Performance metrics are being collected from Kafka and OPCUA connector and merged using timestamp.
* Message size over CPU utilization is analysed with Linear, Polynomial and Support Vector Regression.

## Discussed Issues

*	A short discussion on how to correlate current metrics for storage consumption.
* Current storage data extracted from gluster may not updating due to the fact that volume is not initialized inside Kafka deployment file. 


## Action Points

*	Generate plot with confidence intervals.
* Make sure gluster volume is introduced in Kafka deployment.
* Analyse the storage consumed over time, over response time and over total ingested message so far. 
