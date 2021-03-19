#!/usr/bin/env python
# coding: utf-8

# **Code Starts here**

# In[1]:


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats
import seaborn as sns
import random
from matplotlib import rcParams
from matplotlib.cm import rainbow
get_ipython().run_line_magic('matplotlib', 'inline')
import warnings
warnings.filterwarnings('ignore')
import pickle
from pandas import Series
from numpy.random import randn
from datetime import timezone 
from sklearn.svm import SVR
import time
import math
#from demand_pred import storage_demand


# In[2]:


def make_prediction(df,count,total_runtime):
    regr1 = SVR(kernel = 'rbf',gamma=0.1, C=1e4)
    regr2 = SVR(kernel = 'rbf',gamma=0.1, C=1e4)
    S1= df.iloc[:,4:6].values
    t1 = df['influxdb_memstats_sys']
    #training first model to predict squid memory usage 
    regr1.fit(S1, t1)
    predict1= [[count, total_runtime]]
    #df = df.append({'Request_Rate/(Min)': new_req_rate, 'Total_Time(s)':total_runt regressor1.fit(S1, t1)ime}, ignore_index=True)
    Influx_write=regr1.predict(predict1)
    
    #training second model to predict squid disk usage 
    S2= df.iloc[:,14:17].values
    t2=df['influxdb_diskBytes'] / 1024
    
    regr2.fit(S2, t2)
    
    predict2= [[Influx_write]]
    
    influxdb_disk=int(regr2.predict(predict2)) / 1024
    return influxdb_disk


# In[2]:


#regr1 = SVR(kernel = 'rbf',gamma=0.1, C=1e4)
#regr2 = SVR(kernel = 'rbf',gamma=0.1, C=1e4)



# In[51]:


#total_time= 572
#print(total_time)


# In[52]:


#count=162
#print(count)


# In[53]:


#predict1= [[total_time,count]] 
#regr1 = pickle.load(open('model1', 'rb'))   
#Influx_write_dur=float(regr1.predict(predict1))


# In[54]:


#print (Influx_write_duration)


# In[55]:


#regr2 = pickle.load(open('model2', 'rb'))
#predict3= [[total_time,Influx_write_dur]]


# In[56]:


#influx_disk = float(regr2.predict(predict3))
#influx_disk= math.ceil(influx_disk)
    


# In[57]:


#print(influx_disk)


# In[ ]:




