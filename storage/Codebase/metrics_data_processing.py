import csv 
file1 = open('G:\\ne.txt', 'r') 
ct = 0
ct2=0
f2= open('G:\\c.txt', 'r') 
rows, cols = (6000, 4) 
row2, col2 = (6000, 5) #5 
arr2 = [[0 for i in range(cols)] for j in range(rows)] 
arr = [[0 for i in range(col2)] for j in range(row2)] 
arr_new=[[0 for i in range(col2)] for j in range(row2)] 

for line in file1: 
    if ct>0:
        word_list = line.split()
        met1=len(word_list)
        k=0
        for k in range(met1):
            arr[ct-1][k]=word_list[k]
    ct += 1

ary_indx=0
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
    
    elif arr[i-1][0]==cur_time:
        arr_new[ary_indx][0]=cur_time
        arr_new[ary_indx][1]+=con_val
        arr_new[ary_indx][2]+=prod_val
        arr_new[ary_indx][3]+=response_time
        arr_new[ary_indx][4]+=msg_size
    else:
        ary_indx +=1
        arr_new[ary_indx][0]=cur_time
        arr_new[ary_indx][1]=con_val
        arr_new[ary_indx][2]=prod_val
        arr_new[ary_indx][3]=response_time
        arr_new[ary_indx][4]=msg_size

arr_main=[[0 for i in range(5)] for j in range(ary_indx)]   
arr_final=[[0 for i in range(8)] for j in range(ary_indx)]  
for i in range(ary_indx):
    arr_main[i][0:5]=arr_new[i]  

for line2 in f2: 
    if ct2>0:
        cpu_l=line2.split()

        met2=len(cpu_l)
        for kk in range(met2):
            arr2[ct2-1][kk]=cpu_l[kk]
    ct2 += 1

coun_all=0
msg_num=1
max_val=ct2
if ct2<ary_indx:
    max_val=ary_indx
for k in range(ct2):
    for k2 in range(ary_indx):
        if arr_main[k2][0]==arr2[k][2]:
            arr_final[coun_all][0:5]=arr_main[k2]
            arr_final[coun_all][5]=arr2[k][0]
            arr_final[coun_all][6]=arr2[k2][1]
            arr_final[coun_all][7]=arr2[k2][3]
            
            coun_all+=1


file = open('G:\\metrics_data.csv', 'w+', newline ='')  
with file:     
    write = csv.writer(file)
    write.writerow(('Time', 'consumer', 'producer', 'response time', 'message size','cpu utilization(mb)', 'memory consumption(in gigabytes)', 'disk usage(gb)'))
    write.writerows(arr_final) 
print("Done")
    

