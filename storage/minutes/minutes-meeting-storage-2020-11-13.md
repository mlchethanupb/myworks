# Minutes from 2020-11-13

Start: 12:00

End: 01:25


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	Difficulties in kubernetes deploymnet for database (InfluxDb and Telegraf).
* Based on several perfomance metrics, regression models has been trained and ploted for cache (squid). 

## Discussed Issues
* Telegraf image becomes none once it deployed in kubernetes. 
*	Check if Telegraf is really needed for current scenario. If not then avoid it for further implementation.
* Why sometimes a request take longer time than others in squid. 


## Action Points

*	For InfluxDb, use image form Docker Hub and build the image with a tag. 
* Deploy InfluxDb  and pass data using the connector.
* Have a look how squid manager is taking request rate (performance metric). 
* Analyse kafka performance metrics and try to reduce error value. 
*	Start working on phase 2.
