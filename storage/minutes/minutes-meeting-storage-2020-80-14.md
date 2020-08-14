# Minutes from 2020-08-14

Start: 13:00

End: 13:33


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	OPCUA_Kafka connection is established using docker container.
* More specific metrics based on the current scenario are discussed and fixed. 

## Discussed Issues

*	Discussion on how to establish OPCUA_Kafka connection on Kubernetes pod.
* Discussion on retrieving metrics values by running bash scripts on terminal. 


## Action Points

*	To fix OPCUA_Kafka connector Kubernetes deployment, use the internal ip address of Kafka pod and append it in start.sh file of kafka deployment.
* Create a new scenario including current componenets and new metrics. Show where the bash scripts are being used to retrieve relative Kafka metrics.  
*	Furthermore, run the environment for several days and write a python script to collect the data in a CSV file and analyze it with supervised learning.
