#!/bin/bash

DOCKER_INTERNAL_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

printf "\nadvertised.listeners=PLAINTEXT://$DOCKER_INTERNAL_IP:$KAFKA_PORT" >> /kafka_2.12-2.2.0/config/server.properties
nohup bin/zookeeper-server-start.sh config/zookeeper.properties </dev/null >/dev/null 2>&1 &
zookeeperpid=$!
bin/kafka-server-start.sh config/server.properties

