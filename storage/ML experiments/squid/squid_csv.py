import csv 
import numpy as np
file1 = open('G:\squid\squid\squid_metrics_miss.txt', 'r') 
ct = 0
ct2=0
rows, cols = (2000, 9) 
arr = [["" for i in range(cols)] for j in range(rows)] 
for line in file1: 
    if ct>0:
        word_list = line.split()
        met1=len(word_list)
        k=0
        #print(word_list)
        for k in range(1,met1):
            arr[ct-1][k-1]=word_list[k]
    ct += 1

file = open('G:\\squid_metrics_hit_miss.csv', 'w+', newline ='')  
with file:     
    write = csv.writer(file)
    write.writerow(('Time', 'CPU Usage (%)', 'Hit_Miss', 'Squid_Memory_Usage(kb)', 'Request_Rate/(Min)','Squid_Disk_Usage(mb)', 'Cache_Memory_Usage(kb)', 'Response_Time(ms)'))
    write.writerows(arr) 
print("Done")

