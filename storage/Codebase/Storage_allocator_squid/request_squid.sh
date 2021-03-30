#!/bin/bash
filename='file_List.txt'
container=$(kubectl describe pod squid|grep 'Container ID'|cut -f3 -d':'|head -n1| sed -e 's/ //g')

request=0
t1=$(date +%s)
while read line; do

    
    for i in `seq 1 2`;
        
        do
      
        n1=$(date +%s)
    	Hit_Miss=$(docker exec $container  /bin/sh -c "squidclient http://131.234.28.250:4841/$line|grep 'X-Cache-Lookup:'|cut -c 17,18,19,20")
        n2=$(date +%s)
        #echo $Hit_Miss
        if [ "$t1" == "$n2" ]; then
            request=$(($request+1))

        else  
      
            t1=$(date +%s)
            request=1
            
        fi
        echo $request>>squidIngestion.txt             
    done 
    sleep 0.03
done < "$filename"
exit 0
