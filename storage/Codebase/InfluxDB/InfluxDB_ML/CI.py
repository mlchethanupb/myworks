import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math


dataset1 = pd.read_csv("pythontutorials\data.csv")

X1 = dataset1.iloc[:, 7].values.astype(float)
#X1=X1.cumsum() 
#influxdb_memstats_heap_inuse
y1 = dataset1.iloc[:, 11].values.astype(float)


dataset2 = pd.read_csv("pythontutorials\data1.csv")

X2 = dataset2.iloc[:, 7].values.astype(float)

y2 = dataset2.iloc[:, 11].values.astype(float)


zero=np.zeros(len(y1))
def merge(y1, zero): 
    y1n = [(y1[i], zero[i]) for i in range(0, len(y1))] 
    return y1n 

y1n=merge(y1,zero)
print("merged list is" , y1n)

a1 = np.array(y1n)
mean1=np.mean(a1,axis=1)
std1=np.std(a1,axis=1)
err_run=std1/math.sqrt(len(y1))
err_run1=0.975*err_run


def merge(y1, y2): 
      
    y1y2 = [(y1[i], y2[i]) for i in range(0, len(y2))] 
    return y1y2 
y1y2=merge(y1,y2)
print("merged list is" , y1y2)

a = np.array(y1y2)
c=np.mean(a,axis=1)
std11=np.std(a,axis=1)
err=std11/math.sqrt(len(y1))
err1=0.975*err
print("mean of y1y2 is",c) 



print("error 1",err_run1)
print("error 2",err1)


plt.errorbar(x=X1, y=y1, yerr=err_run1, color="dimgrey", capsize=3,
             linestyle="None",
             marker="h", markersize=7, mfc="midnightblue", mec="midnightblue",label='Run1')

plt.errorbar(x=X1, y=y1, yerr=err1, color="blue", capsize=3,
             linestyle="None",
             marker="s", markersize=7, mfc="black", mec="black",label='Run1,Run2')



plt.xlabel('Influxdb memstats heap_inuse (Bytes)')

plt.ylabel('Influxdb httpd writeReqest Bytes')
plt.legend()
plt.show()
