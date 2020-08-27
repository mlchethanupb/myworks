import shutil
import os
import csv
lines = []
print("program started")
from subprocess import call
import time
while True:
    # Code executed here
    
    with open('metrics_collect.sh', 'rb') as file:
    	script = file.read()
    rc = call(script, shell=True)

    f = open(r'/home/user/kafka/currentMetrics.txt') # Open file on read mode
    lines = f.read().split("\n") 
    lines[-1] = lines[-1].strip()
    f.close()
    print (lines[-1])
    os.remove("/home/user/kafka/currentMetrics.txt")

    with open("/home/user/kafka/perfMetrics.csv","a",newline='') as f:
        wr = csv.writer(f)
        wr.writerow(lines)

    time.sleep(30)
