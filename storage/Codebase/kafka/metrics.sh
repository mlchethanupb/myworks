#!/bin/bash
cpu_uti="CPU_Utilization";
memory_con="Memory_Consumption";
cur_time="Current_Time";
disk_spc="Disk Space";
echo "$cpu_uti $memory_con $cur_time $disk_spc">>c.txt
while true; 
do
    cpu_memory=$(docker stats --no-stream | grep fcf75c06b76d | awk -v date="$(date +%T)" '{print $3, $4, date}' | sed -e 's/MiB//g'  | sed -e 's/GiB//g')
    diskSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "gluster volume status vol_331392cba7ebacda46a545d968f8d9af detail | grep 'Disk Space Free' | cut -f2 -d":" | head -n1 |sed -e 's/GB//g'")
    echo "$cpu_memory $diskSpace">> c.txt; 
    #sleep 5;
done
