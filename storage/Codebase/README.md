## Master Node (pg-aicon-storage-1):
* zookeeper service and deployment (Path:/home/user/heketi/extras/kubernetes/kafka/)
* kafka service and deployment (Path:/home/user/heketi/extras/kubernetes/kafka/)
* digitaltwin service and deployment (Path:/home/user/heketi/extras/kubernetes/digitaltwin/)

## Worker Node (pg-aicon-storage-2):
#### kafka (Path:/home/user/kafka)
docker build -t kafka:dev .

docker run -it --rm --name kafka \
-e KAFKA_PORT=9092 \
-v $PWD/shared:/tmp/kafka-logs \
-p 9092:9092 \
kafka:dev

## Worker Node (pg-aicon-storage-3):
#### digitaltwin (Path:/home/user/tng-industrial-pilot/vnfs/dt-digitaltwin-docker/containers/)
docker build -t digitaltwin:dev . 

docker run -it --rm --name digitaltwin \
-e DT_WEB_LISTEN=0.0.0.0 \
-e DT_WEB_PORT=15001 \
-e OPCUA_HOST=0.0.0.0 \
-e OPCUA_PORT=4840 \
-p 4840:4840 \
digitaltwin:dev
  
#### opcua_kafka_connector (Path:/home/user/opc_ua_kafka_connector/)
docker build -t opc_ua_kafka_connector:dev .

docker run -it --rm --name opc_ua_kafka_connector \
-e INSTANCE_NAME=dt-imms-opcua-0 \
-e OPCUA_SERVER=131.234.29.2 \
-e OPCUA_PORT=4840 \
-e KAFKA_SERVER=131.234.28.250\
-e KAFKA_TOPIC=dt-imms-opcua-0 \
-e SLEEP_DURATION=0.5 \
-e NUMBER_MESSAGES=100 \
-e OUT_FILE=/response_time_measurements/dt-imms-opcua-0.json \
-v "$PWD/response_time_measurements":/response_time_measurements \
opc_ua_kafka_connector:dev
