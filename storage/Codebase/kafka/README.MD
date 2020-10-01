# Apache Kafka
A containerised version of Apache Kafka.

## Setup

### Build Docker Container
```
$ docker build -t kafka .
```

### Start Apache Kafka Docker
```
$ docker run -it --rm --name kafka \
  -v $PWD/shared:/tmp/kafka-logs \
  -p 9092:9092 \
  kafka
```
