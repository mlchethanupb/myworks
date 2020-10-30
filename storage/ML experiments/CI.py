import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math


dataset1 = pd.read_csv("E:\\ss.csv")
X1 = dataset1.iloc[:, -9].values.astype(float)
#X1=X1.cumsum() 
y1 = dataset1.iloc[:, -3].values.astype(float)


dataset2 = pd.read_csv("E:\\s2.csv")
X2 = dataset2.iloc[:, -9].values.astype(float)
#X2=X2.cumsum() 
y2 = dataset2.iloc[:, -3].values.astype(float)

dataset3 = pd.read_csv("E:\\s3.csv")
X3 = dataset3.iloc[:, -9].values.astype(float)
#X3=X3.cumsum() 
y3 = dataset3.iloc[:, -3].values.astype(float)

#Error for run 1
zero=np.zeros(3502)
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
#err_low=mean1-err_run1
#err_high=err_run1+mean1


#merging two y columns

def merge(y1, y2): 
      
    y1y2 = [(y1[i], y2[i]) for i in range(0, len(y2))] 
    return y1y2 
y1y2=merge(y1,y2)
print("merged list is" , y1y2)

#merging 3 y runs
y1y2y3=np.vstack((y1,y2,y3))

#print("merged list of 3 is" , y1y2y3)

#error for two runs
a = np.array(y1y2)
c=np.mean(a,axis=1)
std11=np.std(a,axis=1)
err=std11/math.sqrt(len(y1))
err1=0.975*err
print("mean of y1y2 is",c) 

#error for three runs 
b = np.array(y1y2y3)    
d=np.mean(b,axis=0)
std12=np.std(b,axis=0)
err2=std11/math.sqrt(len(y1))
err22=0.975*err2
#err2=2*std12
#print("mean of y1y2y3 is",d) 
#print("std of y1y2 is",2*err2) 



print("error 1",err_run1)
print("error 2",err1)
print("error 3",err22)

plt.errorbar(x=X1, y=y1, yerr=err_run1, color="dimgrey", capsize=3,
             linestyle="None",
             marker="h", markersize=7, mfc="midnightblue", mec="midnightblue",label='Run1')

plt.errorbar(x=X1, y=y1, yerr=err1, color="blue", capsize=3,
             linestyle="None",
             marker="s", markersize=7, mfc="black", mec="black",label='Run1,Run2')

plt.errorbar(x=X1, y=y1, yerr=err22, color="red", capsize=3,
             linestyle="None",
             marker="o", markersize=7, mfc="silver", mec="silver",label='Run1,Run2,Run3')

plt.xlabel('Response time/(ms)')
plt.ylabel('Kafka Disk Usage(MB)')
plt.legend()
plt.show()