# Minutes from 2021-01-22

Start: 11:00

End: 12:06


## Participants

* [X] Indranil Ghosh
* [X] Lameya Afroze
* [X] Nayela Tasnim Labonno
* [X] Shraddha Pawar


## Status of Last Action Points

*	Troubleshooting of Squid's slow data ingestion.
* Update storage allocator with different ingestion rate for predicting storage demand.
* Implementation of bashscript for predicting storage demand of Influxdb(without ML model).
* Trying to collect some new metrics for influxdb for better training.

## Discussed Issues
* Erronous data for kafka and squid because of volume mounting(kafka) and retrain policy(squid).
* First complete the allocation with single components then start working on sfc.
* How pod downtime is working.

## Action Points

* Perform storage allocation for kafka and squid with fresh data.
* Find out how downtime works for the current testbed (e.g, do we have to restart the pods or not?)
* Predict storage demand with ML model(influxdb) for storage allocator.  
