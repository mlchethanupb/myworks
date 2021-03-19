import csv 
from datetime import datetime
import numpy as np
file1 = open('opc_15.txt', 'r') 
ct = 0
ct2=0
f2= open('kafka_15.txt', 'r') 

num_line1 = sum(1 for line in open('opc_15.txt'))
num_line2 = sum(1 for line in open('k_15.txt'))
rows, cols = (num_line2, 8) 
row2, col2 = (num_line1, 6) 
arr2 = [["" for i in range(cols)] for j in range(rows)] 
arr = [[ "" for i in range(col2)] for j in range(row2)] 
arr_new=[[ "" for i in range(col2)] for j in range(row2)] 
ingestion=0
for line in file1: 
    if ct>0:
        word_list = line.split()
        met1=len(word_list)
        k=0
        for k in range(met1):
            arr[ct-1][k]=word_list[k]
    ct += 1

ary_indx=0
ct=ct-1

for i in range(ct):
    cur_time=arr[i][0]
    con_val=float(arr[i][1])
    prod_val=float(arr[i][2])
    response_time=float(arr[i][3])
    msg_size=float(arr[i][4])
    
    if i==0:
        arr_new[ary_indx][0]=cur_time
        arr_new[ary_indx][1]=con_val
        arr_new[ary_indx][2]=prod_val
        arr_new[ary_indx][3]=response_time
        arr_new[ary_indx][4]=msg_size
        ingestion=ingestion+1
        arr_new[ary_indx][5]=ingestion
    
    elif arr[i-1][0]==cur_time:
        arr_new[ary_indx][0]=cur_time
        arr_new[ary_indx][1]+=con_val
        arr_new[ary_indx][2]+=prod_val
        arr_new[ary_indx][3]+=response_time
        arr_new[ary_indx][4]+=msg_size
        arr_new[ary_indx][5]+=1
    else:
        ary_indx +=1
        arr_new[ary_indx][0]=cur_time
        arr_new[ary_indx][1]=con_val
        arr_new[ary_indx][2]=prod_val
        arr_new[ary_indx][3]=response_time
        arr_new[ary_indx][4]=msg_size
        ingestion=1
        arr_new[ary_indx][5]=ingestion

arr_main=[[ "" for i in range(6)] for j in range(ary_indx)]   
arr_final=[[ "" for i in range(11)] for j in range(ary_indx)]  
for i in range(ary_indx):
    arr_main[i][0:6]=arr_new[i]


for line2 in f2: 
    if ct2>0:
        cpu_l=line2.split()

        met2=len(cpu_l)
        
        for kk in range(met2):
            arr2[ct2-1][kk]=cpu_l[kk]
    ct2 += 1


ct2=ct2-1
coun_all=0
arr_final[coun_all][10]=1
msg_num=1
max_val=ct2
if ct2<ary_indx:
    max_val=ary_indx
for k in range(ct2):
    for k2 in range(ary_indx):
        if arr_main[k2][0]==arr2[k][2]:
            arr_final[coun_all][0:6]=arr_main[k2]
            arr_final[coun_all][6]=arr2[k][0]
            arr_final[coun_all][7]=arr2[k][1]
            arr_final[coun_all][8]=arr2[k][3]
            arr_final[coun_all][9]=arr2[k][4]
            
            ## calculating time difference
            if coun_all>0:
                time_start = str(arr[ct-2][0])
                pre_time=str(arr_final[coun_all-1][0])
                present_time=str(arr_final[coun_all][0])

                format = '%H:%M:%S'
                time_diff = datetime.strptime(present_time, format) - datetime.strptime(pre_time, format)
                time_diff= str(time_diff).split(':')
                
                time_diff=int(time_diff[2])
                
                
                arr_final[coun_all][4]=arr_final[coun_all][4]*time_diff
                arr_final[coun_all][10]=arr_final[coun_all-1][10]+time_diff
            coun_all+=1
      



file = open('kafka_all.csv', 'w+', newline ='')  
with file:     
    write = csv.writer(file)
    write.writerow(('Time', 'Consumer', 'Producer', 'Response time', 'Message size','Ingestion rate/s','CPU utilization/mb', 'Memory consumption/mb', 'Disk usage/mb','Topic space/mb','Total time/s'))
    write.writerows(arr_final) 
print("Done")
    

