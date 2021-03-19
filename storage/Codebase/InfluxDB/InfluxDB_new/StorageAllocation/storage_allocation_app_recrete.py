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
import kube_api


#Uploading influxdbnew pod initially
#kube_api.create_app()
start_time = datetime.now()
#subprocess.call(['sh', './check.sh'])


#influxdbnew's current disk usage 

check_loop=0
while check_loop<1:
    c_name=subprocess.check_output("kubectl describe pod influxdbnew|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.decode("utf-8")
    c_name=c_name.replace('\n', '')
    influxdbnew_disk=str(subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'du -sh /var/lib/influxdb 2>/dev/null |sed 's/[^0-9]//g'|cut -c-1,-2,-3'", shell=True))
    current_usage=influxdbnew_disk.replace('\r\n','')
    if current_usage=="":
        current_usage=0
    current_usage=int(current_usage)
    print('current disk usage is:',current_usage)


    ######update pvc with new storage 

    #fin = open("influx-Deployment_only.yaml", "r+")
    #for line in fin:
    #    if 'storage:' in line:
          #  a=line
            #a=a[14:]
           # s_limit=a[:-3]
            #s_limit='2Gi'
    #fin.close()
    size_current=subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'df -m' |grep /var/lib/influxdb | awk '{print $2'}",shell=True)
    print('Current storage limit is',size_current)

    if (int(size_current)-current_usage<65):
        check_loop=1
        #influxdbnew storage demand prediction with ml model, according to which influxdbnew pvc will  be patched
    
 #       import demand_prediction
 #       demand=demand_prediction.storage_demand(start_time)
 #       demand=str(demand)+'Mi'
	demand=int(size_current) + 50
        demand=str(demand)+ 'Mi'
        print('New storage demand according to Ml model is:',demand)
        subprocess.check_output('kubectl patch pvc gluster1 -p \'{"spec":{"resources":{"requests":{"storage":"'+demand+'"}}}}\'', shell=True)
	print('Storage added successfully')


        ##Restarting influxdbnew pod to update PVC
    
        delete_time = datetime.now().strftime('%H:%M:%S')
        print("POd delete time:",delete_time)
        kube_api.delete_app()
        kube_api.recreate_app()
        #subprocess.call(['sh', './check.sh'])


        #Calculate downtime
        subprocess.check_output("kubectl get pods", shell=True)
        started_time=str(subprocess.check_output("kubectl describe pod influxdbnew|grep 'Started'| cut -c 38-45| head -n1", shell=True))
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
