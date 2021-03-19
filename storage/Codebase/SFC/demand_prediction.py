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
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from datetime import timezone 
from sklearn.svm import SVR
import time
import pickle
import math


def storage_demand(pod_start_time):

    arr=[]
    
    ingestion_rate=0
    ingestion_len=0

    f2= open('squidIngestion.txt', 'r') 
    for line in f2: 
        in_list = line.split('\n')
        ingestion_rate=ingestion_rate+int(in_list[0])     
        ingestion_len= ingestion_len+1

    ingestion_rate=round(ingestion_rate/ingestion_len) 
    print("ingestion rate: ", ingestion_rate) 
    update_interval= 600 
    
    c_name=subprocess.check_output("kubectl describe pod squid|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.decode("utf-8")
    c_name=c_name.replace('\n', '')
    
    current_time = datetime.now()
    
    ##calculates pod run time
    ##squid requires some time to create all cache directories which takes almost 5 minutes in current configuration
    ##After that it can response to any request. As the model is train after this duration of time this time is subtracted from the run time.
    pod_runtime=(current_time-pod_start_time).total_seconds()
    time=(pod_runtime+update_interval)-300
   
    time= math.ceil(time)
    print("prediction time: ",time)
    


    predict1= [[time,ingestion_rate]] 
    regressor1 = pickle.load(open('model-cache-disk', 'rb'))   
    disk=float(regressor1.predict(predict1))
    print('predicted cache disk usage: ',disk)
     
    predict2= [[time,disk]]
    regressor2 = pickle.load(open('model-disk', 'rb'))
    squid_disk=float(regressor2.predict(predict2))
    squid_disk= math.ceil(squid_disk)
    print('predicted storage: ',squid_disk)
   
    file = open("predicted_squid.txt","a")
    file.write(str(squid_disk) + "," + str(time) + "," + str(ingestion_rate) + "\n")
    file.close()

    return squid_disk


