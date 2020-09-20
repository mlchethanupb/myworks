## Master Node (pg-aicon-storage-1):
#### Distributed system using Kubernetes
* kafka service and deployment (Path:/home/user/heketi/extras/kubernetes/kafka/)
* digitaltwin service and deployment (Path:/home/user/heketi/extras/kubernetes/digitaltwin/)
* opc_ua_kafka_connector deployment (Path:/home/user/heketi/extras/kubernetes/opc)

## Worker Node (pg-aicon-storage-3):
#### kafka (Path:/home/user/kafka)
```
docker build -t kafka:dev .
```
#### Distributed system using docker
```
docker run -it --rm --name kafka \
-e KAFKA_PORT=9092 \
-v $PWD/shared:/tmp/kafka-logs \
-p 9092:9092 \
kafka:dev
```

## Worker Node (pg-aicon-storage-2):
#### digitaltwin (Path:/home/user/tng-industrial-pilot/vnfs/dt-digitaltwin-docker/containers/)
```
docker build -t digitaltwin:dev . 
```
#### Distributed system using docker
```
docker run -it --rm --name digitaltwin \
-e DT_WEB_LISTEN=0.0.0.0 \
-e DT_WEB_PORT=15001 \
-e OPCUA_HOST=0.0.0.0 \
-e OPCUA_PORT=4840 \
-p 4840:4840 \
digitaltwin:dev
``` 
#### opcua_kafka_connector (Path:/home/user/opc_ua_kafka_connector/)
```
docker build -t opc_ua_kafka_connector:dev .
```
#### Distributed system using docker
```
docker run -it --rm --name opc_ua_kafka_connector \
-e INSTANCE_NAME=dt-imms-opcua-0 \
-e OPCUA_SERVER=131.234.28.250 \
-e OPCUA_PORT=4840 \
-e KAFKA_SERVER=131.234.29.2 \
-e KAFKA_PORT=31090 \
-e KAFKA_TOPIC=dt-imms-opcua-0 \
-e SLEEP_DURATION=0.5 \
-e NUMBER_MESSAGES=100 \
-e OUT_FILE=/response_time_measurements/dt-imms-opcua-0.json \
-v "$PWD/response_time_measurements":/response_time_measurements \
opc_ua_kafka_connector:dev
```
