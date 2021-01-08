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
import kube_apis


#Uploading Squid pod initially
kube_api.create_app()
start_time = datetime.now()
#subprocess.call(['sh', './check.sh'])


#Squid's current disk usage 

check_loop=0
while check_loop<1:
    c_name=subprocess.check_output("kubectl describe pod squid|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.replace('\n', '')
    squid_disk=str(subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'du -sh / 2>/dev/null |sed 's/[^0-9]//g'|cut -c-1,-2,-3'", shell=True))
    current_usage=squid_disk.replace('\r\n','')
    if current_usage=="":
        current_usage=0
    current_usage=int(current_usage)
    print('current disk usage is:',current_usage)


    ######update pvc with new storage 

    fin = open("squid.yaml", "r+")
    for line in fin:
        if 'storage:' in line:
            a=line
            a=a[14:]
            s_limit=a[:-3]

    print('Current storage limit is',s_limit)
    fin.close()

    if (int(s_limit)-current_usage<=2):
        check_loop=1
        #squid storage demand prediction with ml model, according to which squid pvc will  be patched
    
        import demand_prediction
        demand=demand_prediction.storage_demand(start_time)
        demand=str(demand)+'Mi'
        print('New storage demand according to Ml model is:',demand)
        subprocess.check_output('kubectl patch pvc squid-pvc -p \'{"spec":{"resources":{"requests":{"storage":"'+demand+'"}}}}\'', shell=True)


        ##Restarting Squid pod to update PVC
    
        delete_time = datetime.now().strftime('%H:%M:%S')
        print("POd delete time:",delete_time)
        kube_api.delete_app()
        kube_api.recreate_app()
        #subprocess.call(['sh', './check.sh'])


        #Calculate downtime
        subprocess.check_output("kubectl get pods", shell=True)
        started_time=str(subprocess.check_output("kubectl describe pod squid-deployment|grep 'Started'| cut -c 38-45| head -n1", shell=True))
        print('start time of new Pod:',started_time)

        if ':' in delete_time:
            sec1=int(delete_time[-2:])
            minute1=int(delete_time[-5:-3])
            t1=minute1*60+sec1

        if ':' in started_time:
            sec2=int(started_time[-3:-1])
            minute2=int(started_time[-6:-4])
            t2=minute2*60+sec2


        downtime=t2-t1
        print('Downtime in sec is:',downtime)
