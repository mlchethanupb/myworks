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
import kube_api_squid
import demand_prediction

#Creating PV, PVC and starting squid application

c_name=subprocess.check_output("kubectl describe pod squid|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
c_name=c_name.decode("utf-8") 
c_name=c_name.replace('\n', '')
print('Squid container name:',c_name)


check_loop=0
while check_loop<1:

    start_time=subprocess.check_output("kubectl describe pod squid|grep 'Start Time'| cut -c 26-45", shell=True)
    start_time=start_time.decode("utf-8")
    start_time=start_time.replace('\n', '')
    start_time=str(start_time)
    #print(start_time)
    pod_start_time=datetime.strptime(start_time, '%d %b %Y %H:%M:%S')
    current_time = datetime.now()
    pod_runtime=math.ceil((current_time-pod_start_time).total_seconds())


    #check current disk usage of squid 
    squid_disk=subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'du -sh / 2>/dev/null |sed 's/[^0-9]//g'|cut -c-1,-2,-3'", shell=True)
    current_usage=squid_disk.decode("utf-8")
    
    if current_usage=="":
        current_usage=0
    

    current_usage=int(current_usage)
    print('current disk usage is:',current_usage)
    

    fin = open("pvc-squid.yaml", "r+")
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
    
    if (int(s_limit)-current_usage<=170):
        os.system("rm -rf squidIngestion.txt")
        time.sleep(15)
        print("file deleted")
   
        demand=demand_prediction.storage_demand()
        demand=math.ceil(demand)
        demand=str(demand)+'Mi'
        print('New storage demand according to ML model is:',demand)


        ##if demand is less than current usage then don't need to change
        if (demand<s_limit):
            print("No need to update volume") 
            #let the storage increase meanwhile
            time.sleep(400)
        else:
            subprocess.check_output('kubectl patch pvc squid03 -p \'{"spec":{"resources":{"requests":{"storage":"'+demand+'"}}}}\'', shell=True)



            ##Applying demand on PVC
            fin = open("pvc-squid.yaml", "r+")
            fout = open("out.yaml", "w+")
            append_change=[]
        
            for line in fin:
	    #read replace the string and write to output file
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
            shutil.copy('out.yaml', 'pvc-squid.yaml')

            subprocess.check_output("kubectl apply -f pvc-squid.yaml", shell=True)
            
            print("check")
            time.sleep(100)

            
    
