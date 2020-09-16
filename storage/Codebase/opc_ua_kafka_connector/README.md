# Start OPC UA Kafka Connector
```bash
docker run -it --rm --name opc_ua_kafka_connector   -e INSTANCE_NAME=dt-imms-opcua-0   -e OPCUA_SERVER=131.234.29.2   -e OPCUA_PORT=4840   -e KAFKA_SERVER=131.234.29.2   -e KAFKA_TOPIC=dt-imms-opcua-0   -e SLEEP_DURATION=1   -e NUMBER_MESSAGES=12   -e   OUT_FILE_TXT=/response_time_measurements/fileWrite.txt   -v "$PWD/response_time_measurements":/response_time_measurements   opc_ua_kafka_connector:dev
```
