#!/bin/bash
#cd ~/kafka_2.12-2.2.0
diskSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "gluster volume status vol_331392cba7ebacda46a545d968f8d9af detail | grep 'Disk Space Free' | cut -f2 -d":" | sed 's/^ *//g'| head -n1")
echo "$diskSpace">>currentMetrics.txt
consumedData=$(docker exec -t -i kafka bin/kafka-consumer-perf-test.sh --topic dt-imms-opcua-0  --broker-list localhost:9092 --messages 100 --threads 2 | sed -n 2p | cut -d, -f3)
echo "$consumedData"| xargs>>currentMetrics.txt
nMsg=$(docker exec -t -i kafka bin/kafka-consumer-perf-test.sh --topic dt-imms-opcua-0  --broker-list localhost:9092 --messages 100 --threads 2 | sed -n 2p | cut -d, -f6)
echo "$nMsg"| xargs>>currentMetrics.txt
avgLatency=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 | cut -d, -f3|sed 's/[^0-9]*//g')
echo "$avgLatency"| xargs>>currentMetrics.txt
maxLatency=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 | cut -d, -f4	)
echo "$maxLatency"| xargs>>currentMetrics.txt
inByte=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 --print-metrics| grep 'incoming-byte-rate'|cut -f4 -d":"| sed -n 1p)
echo "$inByte"| xargs>>currentMetrics.txt
outByte=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 --print-metrics| grep 'outgoing-byte-rate'|cut -f4 -d":"| sed -n 1p)
echo "$outByte"| xargs>>currentMetrics.txt
reqRate=$(docker exec -t -i kafka bin/kafka-producer-perf-test.sh --topic dt-imms-opcua-0 --num-records 50 --throughput 10 --producer-props bootstrap.servers=localhost:9092 --record-size 1 --print-metrics| grep 'request-rate' | cut -f4 -d":"| sed -n 1p)
echo "$reqRate"| xargs>>currentMetrics.txt
#sed 's/\s\+/,/g' a.csv>>tt.txt 




