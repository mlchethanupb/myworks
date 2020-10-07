#!/bin/bash
cpu_uti="CPU_Utilization";
memory_con="Memory_Consumption";
cur_time="Current_Time";
disk_spc="Disk_Space(mb)";
kafka_total_disk="Kafka_Disk_Usage(mb)"
kafka_topic_usage="Topic_Disk_Usage(mb)"
heketi_spc="Heketi_Space(mb)"
brick_spc="Brick_Space(mb)"
echo "$cpu_uti $memory_con $cur_time $disk_spc $brick_spc $kafka_total_disk $kafka_topic_usage $heketi_spc">>kafka_metrics.txt
while true; 
do
    cpu_memory=$(docker stats --no-stream | grep c810e4f6025f | awk -v date="$(date +%T)" '{print $3, $4, date}' | sed -e 's/MiB//g'  | sed -e 's/GiB//g'| sed -e 's/%//g')
    brickSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "df -hT /var/lib/heketi/mounts/vg_0cdd94fb0ad06822f1d290707a9500e2/brick_5dc93c1a322ac5532a7e51de588b2ebe|tail -n 1| awk '{print \$4}'|sed -e 's/M//g'")
    heketiSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "df -hT /var/lib/heketi/mounts/vg_0cdd94fb0ad06822f1d290707a9500e2/brick_c09809ddd9fe395664ef124f97c3c203|tail -n 1| awk '{print \$4}'|sed -e 's/M//g'")
    kafka_total_disk_usage=$(docker exec -t -i c810e4f6025f /bin/sh -c "du -sh / 2>/dev/null |cut -c-1,-2,-3")
    kafka_topic_usage=$(docker exec -t -i c810e4f6025f /bin/sh -c "du -sh /tmp/kafka-logs/*|grep '/tmp/kafka-logs/dt-imms-opcua-0-0' | cut -f1 -d"\t"|sed -e 's/M//g'|sed 's/^\///;s/\// /g'|sed -r 's/.{2}$//'||sed -e 's/\\n//g'")
    diskSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "gluster volume status vol_331392cba7ebacda46a545d968f8d9af detail | grep 'Disk Space Free' | cut -f2 -d":" | head -n1 |sed -e 's/GB//g'")
    disk_sp=$(echo $diskSpace | sed -e 's/\r//g')
    brick_sp=$(echo $brickSpace | sed -e 's/\r//g')
    kafka_all=$(echo $kafka_total_disk_usage | sed -e 's/\r//g')
    kafka_topic=$(echo $kafka_topic_usage | sed -e 's/\r//g')
    heketi_sp=$(echo $heketiSpace | sed -e 's/\r//g')
    echo ${cpu_memory} ${disk_sp} ${brick_sp} ${kafka_all} ${kafka_topic} ${heketi_sp}>>kafka_metrics.txt
done
