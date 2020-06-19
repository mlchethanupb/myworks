import os 
import sys
import matplotlib.pyplot as plt
import numpy as np


#read the input files
def read_data(fl):
    a=[]
    arr=open(fl,"r").readlines()
    for line in arr:
        a.append(line.strip().split(','))
    a=np.array(a).reshape(500,500)
    a=np.char.replace(a,'"','')
    a = a.astype('double')
    return a

#change the coordinates of (500*500) dataset 
def modify_data(ar):
    p=0
    i=499
    m=500
    rf_d=[[0 for x in range(m)] for y in range(m)]
    while i>=0 :
        q=0
        for j in range(0,500):
            rf_d[p][q]=ar[i][j]
            q=q+1
        p=p+1
        i=i-1
    return rf_d

#Histogram equalization calculation
def eqa(ar_1):
    #ar_1 = np.log(ar_1) 
    eqa_plt=[]
    x1,y1 = np.unique(ar_1,return_counts=True)
    size_ar1=len(ar_1)
    plt_val=y1/size_ar1
    for k in range(0,plt_val.size):
        if(k == 0 ):
            eqa_plt.append(plt_val[k])
        else:
            eqa_plt.append(plt_val[k] + eqa_plt[k - 1])
    i=0
    for i in range(0,len(eqa_plt)):
        eqa_plt[i] = eqa_plt[i] * 255
        i=i+1
    j=0
    for j in range(0,len(plt_val)):
        ar_1 = np.where(ar_1 == x1[j], eqa_plt[j], ar_1)
        j=j+1
    
    return ar_1

#Combination of histo-equalized data to create RGB image
def produce_rgb(arr_4,arr_3,arr_1):
    print("color:",arr_4[0][0],arr_3[0][0])
    rgb = []
    for i in  range(0,500):
        for j in range(0,500):
            for k in range(0,3):
                if k == 0:
                    rgb.append((arr_4[i][j]))
                elif k == 1:
                    rgb.append((arr_3[i][j]))
                elif k == 2:
                    rgb.append((arr_1[i][j]))
    rgb = (np.asarray(rgb))
    rgb = rgb.reshape(500,500,3)
    rgb =(rgb/255)
    
    return rgb

ar=[]
ar=read_data("i170b2h0_t0.txt")

# max, min, mean and variance value of this 2D data set
max_v=np.max(ar)
min_v=np.min(ar)
mean_v=np.mean(ar)
var_v=np.var(ar)
var_v=np.var(ar)
print("max",max_v," min",min_v, " mean",mean_v, "var",var_v)

###lt
n=500
rf=[[0 for x in range(n)] for y in range(n)]
rf=modify_data(ar)

    
#Plotting profile line
st=0
dif_mn=max_v - min_v
lr = [[0 for x in range(n)] for y in range(n)] 
for i in range(0,500):
    for j in range(0,500):
        if(max_v==ar[i][j]):
            #find the maximum value for profile line
            st=i
        #rescale the data set between 0 to 255
        lr[i][j]=((rf[i][j]-min_v)/dif_mn)*255 
        
plt.title('Profile line')
plt.yscale('log')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.plot(ar[st])
plt.savefig('Profile.png')
plt.show()

#Histogram
pd=np.log(ar)+1
hist,be=np.histogram(pd,bins=100)
bc = 0.5*(be[1:]+be[:-1])
plt.plot(bc,hist)
plt.title('Histogram')
plt.yscale('log')
plt.xscale('log')
plt.xlabel('X axis')
plt.ylabel('Y axis')
plt.savefig('Histogram.png')
plt.show()


###Histogram equalization subtask e
arr_1=read_data("i170b1h0_t0.txt")
arr_2=read_data("i170b2h0_t0.txt")
arr_3=read_data("i170b3h0_t0.txt")
arr_4=read_data("i170b4h0_t0.txt")
arr_1=modify_data(arr_1)
arr_2=modify_data(arr_2)
arr_3=modify_data(arr_3)
arr_4=modify_data(arr_4)

arr_1=eqa(arr_1)
arr_2=eqa(arr_2)
arr_3=eqa(arr_3)
arr_4=eqa(arr_4)



fig, axy = plt.subplots(nrows=2, ncols=3,figsize=(80, 40))
plt.subplots_adjust(hspace=.2)
ax = plt.gca()
p1=axy[0][1].imshow(arr_1 ,cmap="gray",extent=[0, 255, 0, 255])
axy[0][1].set_title('i170b1h0_t0.txt')
axy[0][1].set_xlabel('x axis')
axy[0][1].set_ylabel('y axis')
plt.colorbar(p1,ax=axy[0][1])

p2=axy[0][2].imshow(arr_2 ,cmap="gray",extent=[0, 255, 0, 255])
axy[0][2].set_title('i170b2h0_t0.txt')
axy[0][2].set_xlabel('x axis')
axy[0][2].set_ylabel('y axis')
plt.colorbar(p2,ax=axy[0][2])

p3=axy[1][1].imshow(arr_3 ,cmap="gray",extent=[0, 255, 0, 255])
axy[1][1].set_title('i170b3h0_t0.txt',y=-0.25)
axy[1][1].set_xlabel('x axis')
axy[1][1].set_ylabel('y axis')
plt.colorbar(p3,ax=axy[1][1])

p4=axy[1][2].imshow(arr_4 ,cmap="gray",extent=[0, 255, 0, 255])
axy[1][2].set_title('i170b4h0_t0.txt',y=-0.25)
axy[1][2].set_xlabel('x axis')
axy[1][2].set_ylabel('y axis')
plt.colorbar(p4,ax=axy[1][2])

#rescaling image subtask d
#plt.imshow(lr)
p6=axy[0][0].imshow(lr,extent=[0, 255, 0, 255])
axy[0][0].set_title('rescale Image')
axy[0][0].set_xlabel('x axis')
axy[0][0].set_ylabel('y axis')
plt.colorbar(p6,ax=axy[0][0])

##Generate RGB Image subtask f

rgb_arr=produce_rgb(arr_4/1000,arr_3/1000,arr_1/1000)
p5=axy[1][0].imshow(rgb_arr)
axy[1][0].set_title('RGB Image',y=-0.25)
axy[1][0].set_xlabel('x axis')
axy[1][0].set_ylabel('y axis')
plt.colorbar(p5,ax=axy[1][0])
plt.suptitle('Images for subtask d to e')
plt.savefig('Images.png')
plt.show()