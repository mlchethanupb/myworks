# comparison plot of different storage allocator models interms of used, allocated and predicted storage

import pandas as pd
import matplotlib.pyplot as plt
import csv 
import numpy as np
import seaborn as sns
import math
from sklearn.metrics import mean_squared_error
plt.rcParams.update({'font.size': 8})

df=pd.read_csv('Model1.csv')
df1=pd.read_csv('Model2.csv')
df2=pd.read_csv('Model4.csv')
df3=pd.read_csv('Model3.csv')
fig,axs = plt.subplots(2,2,figsize=(10,10))
fig.tight_layout()
plt.subplots_adjust(left  = 0.128,bottom=0.10,right=0.93, top=0.85, wspace=0.25, hspace=0.42)
fig.suptitle('Performance Comparison of Storage-allocator Models (Kafka-VNF)',size=10, y=1)


sns.lineplot(ax=axs[0,0],data=df, x='Time /s', y='Disk Usage /mb', hue='Storage')
axs[0,0].set_title('Model 1\n Sub-model 1: Polynomial(VNF Runtime, Ingestion Rate (per second)) > Topic Space\n Sub-model 2: SVR(Topic Space) > Kafka Disk', size=7.5)


sns.lineplot(ax=axs[0,1],data=df1, x='Time /s', y='Disk Usage /mb', hue='Storage')
axs[0,1].set_title('Model 2\n Sub-model 1: SVR(VNF Runtime, Ingestion Rate (per second)) > Topic Space\n Sub-model 2: SVR(Topic Space) > Kafka Disk', size=7.5)

sns.lineplot(ax=axs[1,1],data=df2, x='Time /s', y='Disk Usage /mb', hue='Storage')
axs[1,1].set_title('Model 4\n Sub-model 1: SVR(VNF Runtime, Ingestion Rate (average per minute)) > Topic Space\n Sub-model 2: SVR(Topic Space) > Kafka Disk', size=7.5)

sns.lineplot(ax=axs[1,0],data=df3, x='Time /s', y='Disk Usage /mb', hue='Storage')
axs[1,0].set_title('Model 3\n Sub-model 1: SVR(VNF Runtime, Ingestion Rate (average per minute)) > Topic Space\n Sub-model 2: SVR(Time, Topic Space) > Kafka Disk', size=7.5)
plt.show()

