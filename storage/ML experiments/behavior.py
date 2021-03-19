"""
Storage behaviour plot of different VNFs over time
"""


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
plt.rcParams.update({'font.size': 7})
df = pd.read_csv("kafka_all.csv")
df2 = pd.read_csv("squid_1_tk.csv", encoding="ISO-8859-1")
df3 = pd.read_csv("Database3.csv")

x= df.loc[20985:,'Total Time(s)']
y= df.loc[20985:,'disk usage(mb)']
x2= df2.loc[:,'total_time']
y2= df2.loc[:,'disk']
x3= df3.loc[:,'total_time']
y3= df3.loc[:,'influxdb_diskBytes']


fig,axs = plt.subplots(3,figsize=(10,10))
axs[0].plot(x,y)
axs[0].set_title('Kafka Storage Consumption over Time')
axs[1].plot(x2,y2)
axs[1].set_title('Squid Storage Consumption over Time')
axs[2].plot(x3,y3)
axs[2].set_title('InfluxDB Storage Consumption over Time')

plt.xlabel('Time/s')
fig.text(.05, .5, 'Storage Consumption /mb', ha='center', va='center', rotation='vertical')
plt.tight_layout()
plt.subplots_adjust(left= 0.13,bottom=0.125,right=0.94, top=0.925, wspace=0.2, hspace=0.34)
plt.show()

