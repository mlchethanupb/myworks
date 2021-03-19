# plots confidence interval of predicted disk usage of the best model

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math


dataset1 = pd.read_csv("p1.csv")
print(dataset1)
X1 = dataset1.iloc[3:8, -6].values.astype(float)
y1 = dataset1.iloc[3:8, -5].values.astype(float)
y3 = dataset1.iloc[3:8, -3].values.astype(float)
y4 = dataset1.iloc[3:8, -2].values.astype(float)
y5 = dataset1.iloc[3:8, -1].values.astype(float)


#Error for run 1
zero=np.zeros(11)
def merge(y1, zero): 
      
    y1n = [(y1[i], zero[i]) for i in range(0, len(y1))] 
    return y1n 
y1n=merge(y1,zero)
#print("merged list is" , y1n)
a1 = np.array(y1n)
mean1=np.mean(a1,axis=1)
std1=np.std(a1,axis=1)
err_run=std1/math.sqrt(len(y1))
err_run1=0.975*err_run
norm1 = np.linalg.norm(err_run1)
normal1 = err_run1/norm1


#merging multiple y columns
def merge(y1, y3): 
      
    y1y3 = [(y1[i], y3[i]) for i in range(0, len(y3))] 
    return y1y3 
y1y3=merge(y1,y3)
#print("merged list is" , y1y3)
y1y3y4=np.vstack((y1,y3,y4))
y1y3y4y5=np.vstack((y1,y3,y4,y5))
#print(y1y3y4y5)

#error for two runs
a = np.array(y1y3)
c=np.mean(a,axis=1)
std11=np.std(a,axis=1)
err=std11/math.sqrt(len(y1))
err1=0.975*err


#error for three runs 
b = np.array(y1y3y4)    
d=np.mean(b,axis=0)
std12=np.std(b,axis=0)
err2=std12/math.sqrt(len(y1))
err22=0.975*err2

#error for 4 runs 
b2 = np.array(y1y3y4y5)    
d2=np.mean(b2,axis=0)
std121=np.std(b2,axis=0)
err21=std121/math.sqrt(len(y1))
err211=0.975*err21


print("error 1",normal1)
print("error 2",err1)
print("error 3",err22)
print("error 4",err211)

plt.errorbar(x=X1, y=y1, yerr=normal1, color="blue", capsize=3,
             linestyle="None",
             marker="o", markersize=7, mfc="black", mec="black",label='Run1')

plt.errorbar(x=X1, y=y1, yerr=err1, color="grey", capsize=3,
             linestyle="None",
             marker="o", markersize=7, mfc="black", mec="black",label='Run1,Run2')

plt.errorbar(x=X1, y=y1, yerr=err22, color="red", capsize=3,
             linestyle="None",
             marker="o", markersize=7, mfc="black", mec="black",label='Run1,Run2,Run3')

plt.errorbar(x=X1, y=y1, yerr=err211, color="green", capsize=3,
             linestyle="None",
             marker="o", markersize=7, mfc="black", mec="black",label='Run1,Run2,Run3,Run4')


plt.xlabel('Total time /s')
plt.ylabel('Squid Disk Usage /mb')
plt.legend()
plt.show()