#!/bin/bash
cpu_uti="CPU_Utilization";
memory_con="Memory_Consumption";
cur_time="Current_Time";
disk_spc="Disk Space";
echo "$cpu_uti $memory_con $cur_time $disk_spc">>kafka_metrics.txt
while true; 
do
    cpu_memory=$(docker stats --no-stream | grep c810e4f6025f | awk -v date="$(date +%T)" '{print $3, $4, date}' | sed -e 's/MiB//g'  | sed -e 's/GiB//g'| sed -e 's/%//g')
    diskSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "df -hT /var/lib/heketi/mounts/vg_0cdd94fb0ad06822f1d290707a9500e2/brick_5dc93c1a322ac5532a7e51de588b2ebe|tail -n 1| awk '{print \$4}'|sed -e 's/M//g'")
    heketiSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "df -hT /var/lib/heketi/mounts/vg_0cdd94fb0ad06822f1d290707a9500e2/brick_c09809ddd9fe395664ef124f97c3c203|tail -n 1| awk '{print \$4}'|sed -e 's/M//g'")
    echo "$cpu_memory $diskSpace">> kafka_metrics.txt; 
    #echo "$cpu_memory $heketiSpace">> d2.txt;
    #sleep 5;
done
