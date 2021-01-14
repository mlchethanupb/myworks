import os
import yaml
from os import path
from datetime import datetime
import subprocess
import pandas as pd
import numpy as np
from matplotlib import cm
from matplotlib import pyplot
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import mean_squared_error, r2_score
from matplotlib import font_manager as fm, rcParams  
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

def storage_demand(start_time):
  
    ingestion_rate= 0.4
    update_interval= 3600 

    c_name=subprocess.check_output("kubectl describe pod squid|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.replace('\n', '')

    #request rate calculation after a certain update interval 

    current_request_rate=str(subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'squidclient -h localhost cache_object://localhost/ mgr:info| grep 'Average HTTP requests per minute since start:'| cut -f2 -d':''", shell=True))
    current_request=subprocess.check_output("kubectl exec -ti " + str(c_name)+ " -- /bin/sh -c 'squidclient -h localhost cache_object://localhost/ mgr:info| grep 'received'| cut -f2 -d':'|head -n1 '", shell=True)
    new_request=(ingestion_rate*update_interval)/60 #after 1 hr total reqest
    print('new request',new_request)
    print('current request is:',current_request)
    total_request=int(current_request)+new_request
    print('total request is',total_request)

    #pod_runtime=str(subprocess.check_output("kubectl get pods| grep 'squid'| cut -c60-75", shell=True))
    subprocess.check_output("kubectl get pods", shell=True)
    print('counting pod runtime')
    pod_start_time=start_time
    current_time = datetime.now()

    pod_runtime=current_time-pod_start_time
    pod_runtime=(pod_runtime.total_seconds()/60)


    print('pod runtime in min is:',pod_runtime)

    total_runtime=pod_runtime+(update_interval/60)
        
    new_req_rate=(total_request/total_runtime)
    new_req_rate=round(new_req_rate,2)
   
    
    #Storage demand prediction for new request rate

    df = pd.read_csv("hit_miss_all.csv")
    #df contains data for different ingestion rates
    df2=df
    S1= df.iloc[:,4:6].values
    t1 = df['Squid_Memory_Usage(kb)']

    regressor1 = SVR(kernel = 'rbf',C=1e4, gamma=0.1)
    regressor2 = SVR(kernel = 'rbf',C=1e4, gamma=0.1)
    #training first model to predict squid memory usage 
    regressor1.fit(S1, t1)

    total_runtime=total_runtime*60
    print('new request rate is',new_req_rate)

    
    predict1= [[new_req_rate,total_runtime]]
    #df = df.append({'Request_Rate/(Min)': new_req_rate, 'Total_Time(s)':total_runtime}, ignore_index=True)
    Squid_mem=regressor1.predict(predict1)
    #regressor1.fit(predict1)
    
    #training second model to predict squid disk usage 
    S2= df.iloc[:,3:6].values
    t2 = df['Squid_Disk_Usage(mb)']
    
    regressor2.fit(S2, t2)
    
    predict2= [[Squid_mem,new_req_rate,total_runtime]]
    
    Squid_disk=int(regressor2.predict(predict2))
    print(Squid_disk)
    return Squid_disk
