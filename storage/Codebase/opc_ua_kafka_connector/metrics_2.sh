#!/bin/bash
cpu_uti="CPU_Utilization";
memory_con="Memory_Consumption";
cur_time="Current_Time";
echo "$cpu_uti $memory_con $cur_time">>c.txt
while true; do docker stats --no-stream | grep 302b4fa69c72 | awk -v date="$(date +%T)" '{print $3, $4, date}' | sed -e 's/MiB//g'  | sed -e 's/GiB//g' >> c.txt; sleep 5;done
