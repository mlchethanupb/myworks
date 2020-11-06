#!/bin/bash
filename='file_List.txt'
File='File'
CPU_Usage='CPU_Usage'
Hit_Miss='Hit_Miss'
Squid_Memory_Usage="Squid_Memory_Usage"
Squid_Disk_Usage="Squid_Disk_Usage"
Request_Rate="Request_Rate/(Min)"
Cache_Memory_Usage="Cache_Memory_Usage"
Time="Time"
Response_Time="Response_Time"


echo "${File} ${Time} ${CPU_Usage} ${Hit_Miss} ${Squid_Memory_Usage} ${Request_Rate} ${Squid_Disk_Usage} ${Cache_Memory_Usage} ${Response_Time}">>squid_metrics_hit.txt
while read line; do

    echo $line
    n1=$(date +%s%N)
    Hit_Miss=$(docker exec 51348f564d3f /bin/sh -c "squidclient http://131.234.28.250:4840/$line|grep 'X-Cache-Lookup:'|cut -c 17,18,19,20")
    docker exec 51348f564d3f  /bin/sh -c "wget http://131.234.28.250:4840/$line -e use_proxy=yes -e http_proxy=10.0.0.82:3128 -O $line"
    CPU_Usage=$(docker exec 51348f564d3f  /bin/sh -c "squidclient -h localhost cache_object://localhost/ mgr:info| grep 'CPU Usage:'| cut -f2 -d":"| sed -e 's/%//g'")
    Squid_Memory_Usage=$(docker exec 51348f564d3f  /bin/sh -c "squidclient -h localhost cache_object://localhost/ mgr:info| grep 'Maximum Resident Size:'| cut -f2 -d":"|sed 's/[^0-9]*//g'")
    Squid_Disk_Usage=$(docker exec 51348f564d3f /bin/sh -c "du -sh / 2>/dev/null |cut -c-1,-2,-3") 
    Request_Rate=$(docker exec 51348f564d3f  /bin/sh -c "squidclient -h localhost cache_object://localhost/ mgr:info| grep 'Average HTTP requests per minute since start:'| cut -f2 -d":"")
    Cache_Memory_Usage=$(docker exec 51348f564d3f  /bin/sh -c "squidclient -h localhost cache_object://localhost/ mgr:info| grep 'Storage Mem size:'| cut -f2 -d":"|sed -e 's/KB//g'")
    #docker exec 51348f564d3f  /bin/sh -c "squidclient -h localhost cache_object://localhost/ mgr:info"
    Time=$(date +%T)
    n2=$(date +%s%N)
    #r=$(echo "$n2 - $now" | bc)
    Response_Time=$(($n2-$n1))
    Response_Time=$((Response_Time/1000000))
    echo $line ${Time} ${CPU_Usage} ${Hit_Miss} ${Squid_Memory_Usage} ${Request_Rate} ${Squid_Disk_Usage} ${Cache_Memory_Usage} ${Response_Time}>>squid_metrics_hit.txt
    sleep 1
done < "$filename"

