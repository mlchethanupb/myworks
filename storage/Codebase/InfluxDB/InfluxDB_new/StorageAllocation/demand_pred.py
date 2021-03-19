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
from prediction import make_prediction

def storage_demand():
    ingestion_rate= 0.4
    update_interval= 3600 
   
    
    c_name=subprocess.check_output("kubectl describe pod influxdbnew|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.replace('\n', '')
    
    
    
    pod_start_time=subprocess.check_output("kubectl get  pod "+str(c_name)+" -o yaml | grep -i Starttime | awk '{print $2}'", shell=True)
    pod_start_time=pod_start_time.replace('"',"").replace("Z","").replace("\n","").replace("T"," ")
    start_time=datetime.strptime(pod_start_time, '%Y-%m-%d %H:%M:%S')
    current_time = datetime.now()

    pod_runtime=current_time-start_time
    pod_runtime=(pod_runtime.total_seconds()/60)
    total_runtime=pod_runtime+(update_interval/60)
    # --------------
    Storage demand prediction for new request rate

    df = pd.read_csv("hit_miss_all.csv")
   
    # -------------------
    subprocess.check_output("sshpass -p 'resu' scp pg-aicon-storage-5:/tmp/data.csv .", shell=True)
    #-----------------
   
    filename="data.csv"
    df = pd.read_csv(filename)
    total_request=int(df['influxdb_httpd_writeReq'].max())
    df['request_datetime']=pd.to_datetime(df['request_datetime'])
    md_number=df['request_datetime'].count()/2
   
   #----------------
    injection_mean=df[['request_datetime']][-1000:][md_number: md_number + 1000][:1000].diff().mean() / np.timedelta64(1,'s') / 3600
    injection_rate_per_sec=float(str(injection_mean).replace("request_datetime","").replace("\ndtype: float64","").replace("  ", ""))
    total_request=(injection_rate_per_sec * total_runtime)
    total_request=round(total_request,2)
   #----------------
   
   #df contains data for different ingestion rates
    df2=df
    total_request = 162
   #total_runtime=total_runtime*60
    total_runtime = 750
    influxdb_disk=make_prediction(df,total_request,total_runtime)
    print(influxdb_disk)
    
storage_demand()