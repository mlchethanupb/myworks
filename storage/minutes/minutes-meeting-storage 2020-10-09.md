# Minutes from 2020-10-09

Start: 12:00

End: 12:38


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	Gluster volume is mounted on Kafka.
* Linear behaviour of storage consumption over time and storage consumption over total ingested data has been found using the three regression algorithmm (Linear, Polynomial and Support Vector Regression with 95% confidence interval).

## Discussed Issues

*	The way data has been collected is okay. Some missing values would not cause that much problem. However we can aggregate these missing values with matched timestamp.  
* Set Retention Size, Segment Size, etc (posted on gitter) in Kafka configuration file and analyse how it effects on storage consumption.  


## Action Points

*	Make changes on Kafka configuration file and analyse its effect on storage consumption. 
