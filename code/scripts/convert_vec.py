import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import subprocess

path = 'results'

def convert_sca():
    files_sca = glob.glob(path + '/**/*.vec', recursive=True)

    processing_cmd = []
    process_running = []

    for file in files_sca:
        name_run = file
        csv_name = name_run + ".csv"
        cmd = "scavetool x " +  name_run + " -o " + csv_name
        #print(cmd)
        processing_cmd.append(cmd)
    
    for cmd in processing_cmd:
        print("Adding command: ", cmd)
        process_running.append(subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 universal_newlines=True,
                                 shell=True))
    
    for p in process_running:
        #print(p)
        proc_cmd = p.args
        if p.returncode == 0:
            print("process done: ", proc_cmd)
            process_running.remove()
        else:
            print("p.returncode: ", p.returncode)
    
    print("All files converted")

def main():
    print("main")
    convert_sca()

if __name__ == "__main__":
    main()