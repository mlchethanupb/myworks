import shutil
print("started")
from subprocess import call
import time
while True:
    # Code executed here
    
    with open('st_11.sh', 'rb') as file:
    	script = file.read()
    rc = call(script, shell=True)
    time.sleep(30)