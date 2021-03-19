import os
from kubernetes import client, config, utils
import yaml
from os import path
from datetime import datetime
import subprocess
from subprocess import Popen, PIPE
import shutil
import time
import json
from datetime import timezone 
import math

#Uploads Kafka and relevant pods initially

import kube_api

kube_api.create_pv()
kube_api.create_pvc()
kube_api.create_app()


#sets kafka properties :retention.size, segment.bytes, cleanup.policy
os.system("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c './bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic dt-imms-opcua-0 --config retention.bytes=62914560'")
os.system("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c './bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic dt-imms-opcua-0 --config segment.bytes=20971520'")
os.system("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c './bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic dt-imms-opcua-0 --config cleanup.policy=delete'")


# check current disk usage of VNF, current storage limit and extract pod runtime 
c_name=subprocess.check_output("kubectl describe pod kafka|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
c_name=c_name.decode("utf-8") 
c_name=c_name.replace('\n', '')

check_loop=0
while check_loop<1:

    c_name=subprocess.check_output("kubectl describe pod kafka|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.decode("utf-8") 
    c_name=c_name.replace('\n', '')

    start_time=subprocess.check_output("kubectl describe pod kafka|grep 'Start Time'| cut -c 26-45", shell=True)
    start_time=start_time.decode("utf-8")
    start_time=start_time.replace('\n', '')
    start_time=str(start_time)
    pod_start_time=datetime.strptime(start_time, '%d %b %Y %H:%M:%S')
    current_time = datetime.now()
    pod_runtime=math.ceil((current_time-pod_start_time).total_seconds())



    kafka_disk=subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'du -sh / 2>/dev/null |sed 's/[^0-9]//g'|cut -c-1,-2,-3'", shell=True)
    current_usage=kafka_disk.decode("utf-8")
     
    if current_usage=="":
        current_usage=0
    

    current_usage=int(current_usage)
    print('current disk usage is:',current_usage)
    

    fin = open("pvc-kafka.yaml", "r+")
    for line in fin:
        if 'storage:' in line:
            a=line
            a=a[14:]
            s_limit=a[:-3]
    
    if current_usage>0:
        file = open("usedDisk.txt", "a")
        file.write(str(current_usage) + "," + str(pod_runtime) +"," + str(s_limit)+ "\n")
        file.close()

    print('Current storage limit is',s_limit)
    fin.close()


    
    #If disk usage excceds threshhold, predict storage demand for a future time 

    if (int(s_limit)-current_usage<=270):  
        import demand_prediction
 
        demand=demand_prediction.storage_demand()
        demand=math.ceil(demand)
        demand=str(demand)+'Mi'
        print('New storage demand according to ML model is:',demand)


        #If demand is less than current usage, no update of pvc needed
        #Sleep for 400s and let the storage increase meanwhile
        if (demand<s_limit):
            print("No need to update volume") 
            time.sleep(400)
        else:
            subprocess.check_output('kubectl patch pvc kaf3 -p \'{"spec":{"resources":{"requests":{"storage":"'+demand+'"}}}}\'', shell=True)

            ##New storage demand applying on PVC
            fin = open("pvc-kafka.yaml", "r+")
            fout = open("out.yaml", "w+")
            append_change=[]
        
            for line in fin:
                if 'storage:' in line:
                    append_change=line
                    append_change=append_change[14:]
                    old_val=append_change[:-3]
                    new_val='     storage: '+str(demand)+'\n'           
                    fout.write(new_val)
                else:
                    fout.write(line)

            fin.close()
            fout.close()
            shutil.copy('out.yaml', 'pvc-kafka.yaml')
            subprocess.check_output("kubectl apply -f pvc-kafka.yaml", shell=True)
            time.sleep(100)


        #delete msg_rate.txt file everytime from inside of opcua connector to take a recent ingestion rate
        opc_name=subprocess.check_output("kubectl describe pod opcua|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
        opc_name=opc_name.decode("utf-8") 
        opc_name=opc_name.replace('\n', '')
        os.system("kubectl exec -ti " + str(opc_name)+ " -- /bin/sh -c 'rm -rf msg_rate.txt'")
        print("check")
        time.sleep(100)
