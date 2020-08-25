#!/bin/bash
#cd ~/kafka_2.12-2.2.0
diskSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "gluster volume status vol_331392cba7ebacda46a545d968f8d9af detail | grep 'Disk Space Free' | cut -f2 -d":" | sed 's/^ *//g' | head -n1")
echo "$diskSpace">>a.txt
conPer=$(docker exec -t -i kafka bin/kafka-consumer-perf-test.sh --topic dt-imms-opcua-0  --broker-list localhost:9092 --messages 100 --threads 2 | sed -n 2p | cut -d, -f3,6)
echo "$conPer">>a.txt
proPer=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 | cut -d, -f3,4)
echo "$proPer">>a.txt
inByte=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 --print-metrics| grep 'incoming-byte-rate'|cut -f4 -d":"| sed -n 2p)
echo "$inByte">>a.txt
outByte=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 --print-metrics| grep 'outgoing-byte-rate'|cut -f4 -d":"| sed -n 2p)
echo "$outByte">>a.txt
reqRate=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 --print-metrics| grep 'request-rate' | cut -f4 -d":"| sed -n 2p)
echo "$reqRate">>a.txt

