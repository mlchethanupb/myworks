""" This code converts two text file into a csv file and shows the performance of storage allocater.
 The text files are created when the storage allocator starts to run """
import pandas as pd
import matplotlib.pyplot as plt
import csv 
import numpy as np
import seaborn as sns
import math
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
arr2=[]
arr3=[]

#reads text file and stores the values in an array
def txt_to_csv(filename):
    file1 = open(filename, 'r') 
    ct = 1
    file_len = sum(1 for line in open(filename))
    file_len= file_len*3
    print(file_len)
    rows, cols = (file_len, 3) 
    
    arr = [["" for i in range(cols)] for j in range(rows)] 
    filename=filename.replace(".txt","")
    
    for line in file1: 
        
        word_list = line.split(",")
        print(word_list)
        met1=len(word_list)
        k=0
        
        if filename=="squid_used":
            arr[ct-1][0]="used disk"
        else:
            arr[ct-1][0]="predicted disk"
        
        if filename=="squid_used":
        
            up_bound=int(file_len/3)+ct-1
            arr[ct-1][1]=word_list[0]
            arr[ct-1][2]=word_list[1]
            
            arr[up_bound][0]="allocated"
            word_list[2]=word_list[2].replace("\n","")
            arr[up_bound][1]=word_list[2]
            arr[up_bound][2]=word_list[1]

        else:
            for k in range(0,met1-1):
                arr[ct-1][k+1]=word_list[k] 
 

        
        ct += 1
    return arr
arr3=txt_to_csv('squid_used.txt')
arr2=txt_to_csv('squid_predicted.txt')
print(arr3,len(arr2))


file = open('squid_comparison.csv', 'w+', newline ='')  
with file:     
    write = csv.writer(file)
    write.writerow(('Type','Disk Usage/MB','Time/s'))
    write.writerows(arr3) 
    write.writerows(arr2) 
print("Done")

df=pd.read_csv('squid_comparison.csv')
sns.lineplot(data=df, x='Time/s', y='Disk Usage/MB', hue='Type')
plt.show()

