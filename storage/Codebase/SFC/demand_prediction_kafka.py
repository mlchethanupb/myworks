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
    pod=subprocess.check_output("kubectl describe pod opcua|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    print('opcua pod: ',pod)

    pod=pod.decode("utf-8")
    pod=pod.replace('\n', '')
    
    #fetch msg_rate.txt from inside opcua container to extract recent ingestion rate
    os.system("kubectl cp default/"+pod+":msg_rate.txt msg_rate.txt")
    
 
    ingestion_rate=0
    ingestion_len=0
    
    f2= open('msg_rate.txt', 'r') 
    for line in f2: 

        in_list = line.split('\n')
        
        ingestion_rate=ingestion_rate+int(in_list[0]) 
            
        ingestion_len= ingestion_len+1
   
    ingestion_rate= round(ingestion_rate/ingestion_len)
    print("ingestion rate: ", ingestion_rate)
 
    print("file removed") 
    update_interval= 600  

    c_name=subprocess.check_output("kubectl describe pod kafka|grep 'Name'|cut -f2 -d':'|head -n1| sed -e 's/ //g'", shell=True)
    c_name=c_name.decode("utf-8")
    c_name=c_name.replace('\n', '')
    

    current_time = datetime.now()
    pod_runtime=(current_time-pod_start_time).total_seconds()
    time=(pod_runtime+update_interval)
    time= math.ceil(time)
    print("prediction time: ",time)
    
    #Storage demand prediction for new ingestion rate
    #predict cpu util and topic space based on time and ingestion rate
    #predict total storage from the two ml models above

    predict1= [[time,ingestion_rate]]
    regressor1 = pickle.load(open('model-topic', 'rb'))
    topic_space=float(regressor1.predict(predict1))
    print('predicted topic space: ',topic_space)

    regressor3 = pickle.load(open('topic_time_disk', 'rb'))
    predict3= [[time,topic_space]]
     
    Kafka_disk = float(regressor3.predict(predict3))
    Kafka_disk= math.ceil(Kafka_disk)
    
    print('predicted storage: ',Kafka_disk)
    file = open("predicted_kafka.txt","a")
    file.write(str(Kafka_disk) + "," + str(time) + "," + str(ingestion_rate) + "\n")
    file.close()

    
    return Kafka_disk

