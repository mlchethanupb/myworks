#!/bin/bash
request=0
t1=$(date -d '- 15 seconds' "+%m%d%Y%H:%M:%S")
container=$(kubectl describe pod squid|grep 'Container ID'|cut -f3 -d':'|head -n1| sed -e 's/ //g')

while :
do
    rt=$(date -d '- 15 seconds' "+%m%d%Y%H:%M:%S")
    filename=$rt".html"
    echo $filename
    for i in `seq 1 2`;
        
    do

        Hit_Miss=$(docker exec $container /bin/sh -c "squidclient http://131.234.29.2:4842/$filename|grep 'X-Cache-Lookup:'|cut -c 17,18,19,20")
        echo $Hit_Miss
        n2=$(date -d '- 15 seconds' "+%m%d%Y%H:%M:%S")
        if [ "$t1" == "$n2" ]; then
            request=$(($request+1))

        else  
      
            t1=$(date -d '- 15 seconds' "+%m%d%Y%H:%M:%S")
            request=1
            
        fi
        echo $request>>squidIngestion.txt 
    done
    sleep 0.03
done
