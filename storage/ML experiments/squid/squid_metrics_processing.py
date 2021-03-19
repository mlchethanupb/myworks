# merge squid metrics from separate text files and combines them into a csv file 
import csv 
from datetime import datetime
from datetime import timezone
import numpy as np

file1 = open('set3_metrics.txt', 'r') 
f2= open('set3_request.txt', 'r') 
r_num = sum(1 for line in open('set3_request.txt'))
m_num = sum(1 for line in open('set3_metrics.txt'))
rows, cols = (r_num, 5) 
row2, col2 = (m_num, 6)  
arr2 = [["" for i in range(cols)] for j in range(rows)] 
arr = [["" for i in range(col2)] for j in range(row2)] 
arr_new=[["" for i in range(11)] for j in range(rows)] 
ct = 0
ct2=0

for line in file1: 
    if ct>0:
        word_list = line.split()
        met1 = len(word_list)
        k=0
        for k in range(met1):
            arr[ct-1][k] = word_list[k]
    ct + = 1

ingestion = 1
indx=0

for line in f2: 
    if ct2 == 0:
        ct2 += 1
    else:
        word_list = line.split()
        if not word_list:
            break
        met1 = len(word_list)
        k = 0
        if ct2 == 1:
            for k in range(met1):
           
                arr2[ct2-1][k] = word_list[k]
            indx+ = 1
            arr2[ct2-1][4] = 1
            ct2 = 3
        
        elif word_list[1] == arr2[indx-1][1]:
            arr2[indx-1][4]+ = 1
        
        elif word_list[1]!= arr2[indx-1][1]:

            for k in range(met1):
                arr2[indx][k] = word_list[k]
                arr2[indx][4] = 1
            indx+ = 1
    
k = 0

for i in range(ct-1):
    for j in range(indx-1):
        if arr[i][0] ==a rr2[j][1]:
            
            if k == 0:
                for i1 in range(2):
                    arr_new[k][i1] = arr[i][i1]
                arr_new[k][3] = arr2[j][2]
                arr_new[k][4] = arr2[j][3]
                arr_new[k][5] = arr2[j][4]
                arr_new[k][6] = arr2[j][0]
                arr_new[k][7] = 1
                arr_new[k][8] = arr[i][3]
                arr_new[k][9] = arr[i][4]
                arr_new[k][10] = arr[i][5]
                k = k + 1

            elif k>0 and arr2[j][1]!= arr_new[k-1][0]:
                for i1 in range(2):
                    arr_new[k][i1] = arr[i][i1]
                
                arr_new[k][3] = arr2[j][2]
                arr_new[k][4] = arr2[j][3]
                arr_new[k][5] = arr2[j][4]
                arr_new[k][6] = arr2[j][0]
                pre_time = str(arr_new[k-1][0])
                present_time = str(arr_new[k][0])

                format = '%H:%M:%S'
                time_diff = datetime.strptime(present_time, format) - datetime.strptime(pre_time, format)
                time_diff= str(time_diff).split(':')
                
                time_diff_1 = int(time_diff[2])
                time_diff_2 = int(time_diff[1])
                time_diff_2 = time_diff_2*60
                
                arr_new[k][7] = arr_new[k-1][7]+time_diff_1+time_diff_2
                arr_new[k][8] = arr[i][3]
                arr_new[k][9] = arr[i][4]
                arr_new[k][10] = arr[i][5]
                
            
                k+ = 1
        
        
file = open('squid_set_3.csv', 'w+', newline ='')  
with file:     
    write = csv.writer(file)
    write.writerow(('Time', 'Cache Disk/mb', 'Cache Memory/kb','Hit/miss','Response Time/ns','Ingestion Rate/sec','File_name','Data_time/s','Disk Usage/mb','CPU Utilization','Squid Memory/kb'))
    write.writerows(arr_new) 
print("Done")
