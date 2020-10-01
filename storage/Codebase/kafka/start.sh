#!/bin/bash

INTERNAL_IP=$(/sbin/ip route|awk '/default/ { print $3 }')

printf "\nlisteners=PLAINTEXT://:9092,EXTERNAL://:31090" >> /kafka_2.12-2.2.0/config/server.properties
printf "\nadvertised.listeners=PLAINTEXT://$INTERNAL_IP:9092,EXTERNAL://10.0.0.80:31090" >> /kafka_2.12-2.2.0/config/server.properties
printf "\nlistener.security.protocol.map=PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT" >> /kafka_2.12-2.2.0/config/server.properties
printf "\ninter.broker.listener.name=EXTERNAL" >> /kafka_2.12-2.2.0/config/server.properties
nohup bin/zookeeper-server-start.sh config/zookeeper.properties </dev/null >/dev/null 2>&1 &
zookeeperpid=$!
bin/kafka-server-start.sh config/server.properties
