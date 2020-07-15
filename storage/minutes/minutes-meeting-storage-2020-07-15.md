
# Minutes from 2020-07-015

Start: 13:00

End: 13:53


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	Fixed testbed issues for both Kubernetes and GlusterFS.
* Presentation of Kafka scenario.


## Discussed Issues

*	Discussed about the scenario using Kafka. 
* Proposal to start working with single broker initially. 
* After that check the storage performance with distributed broker and for varied load over time duration.
* Providing constraint on pods for Kafka deployment.
* Overview of Digital Twin. Don't need to provide anything as input on Digital Twin. Need to build the docker image to produce the output.
* Use required storage, latency and request rate as metric.


## Action Points

*	Run Digital Twin on kubernetes to generate data (will be used as producer).
*	Start working with single broker on current testbed.
*	Initially start the work by considering how much storage will be needed over time as metric.
*	Use the command given on the last slide of pg-aicon-storage.pptx for comparing the resource (disk space).

