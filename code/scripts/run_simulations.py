import json
import glob
import subprocess
import re
import os
from os.path import exists
import time


MAX_PROCESS_COUNT = 24
get_num_of_runs = './get_number_of_run.sh'
path_start_simulation = './start_simulations.sh'
working_directory = './'
scenario = 'InTAS'
config_dir = "../scenarios/InTAS/scenario/config"

CONST_settings_dict={ "config":"[Config ",
                      "result":"result-dir = ../results/",
                      "service":"*.node[*].middleware.services = xmldoc(\"services/services_",
                      "constsize": "*.node[*].middleware.CpService.enable_constsize = ",
                      "fixedrate": "*.node[*].middleware.CpService.fixedRate = ",
                      "fixedinterval": "*.node[*].middleware.CpService.fixedInterval = ",
                      "en_mode4": "*.node[*].lteNic.enable_mode4 = "}



def create_config_file(config_name):
    #print("creating config file for: ", config_name)
    config_name_split = config_name.split('_')
    #print(config_name_split)

    data_to_write = []
    
    config_data = CONST_settings_dict["config"]
    config_data = config_data + config_name + "]"
    #print(config_data)
    data_to_write.append(config_data)
    
    result_data = CONST_settings_dict["result"]
    for item in config_name_split:
        result_data = result_data + item + "/"
    #print(result_data)
    data_to_write.append(result_data)

    service_data = CONST_settings_dict["service"]
    service_data = service_data + config_name_split[-1] + ".xml\")"
    #print(service_data)
    data_to_write.append(service_data)

    constsize_data = CONST_settings_dict["constsize"]
    if(config_name_split[1] == "constsize"):
        constsize_data = constsize_data + "true"
    else:
        constsize_data = constsize_data + "false"
    #print(constsize_data)
    data_to_write.append(constsize_data)
    
    fixedrate_data = CONST_settings_dict["fixedrate"]
    fixedinterval_data = CONST_settings_dict["fixedinterval"]
    
    num_data = re.findall("\d+", config_name)
    periodicity = int(num_data[0])/1000
    #print(periodicity)

    if(config_name_split[0] == "etsi"):
        fixedrate_data = fixedrate_data + "false"
        fixedinterval_data = fixedinterval_data + "0.1s" #dummy value
    else:
        fixedrate_data = fixedrate_data + "true"
        fixedinterval_data = fixedinterval_data + str(periodicity) +"s"

    #print(fixedrate_data)
    #print(fixedinterval_data)
    data_to_write.append(fixedrate_data)
    data_to_write.append(fixedinterval_data)

    en_mode4_data = CONST_settings_dict["en_mode4"]
    if(config_name_split[2]=="mode3"):
        en_mode4_data = en_mode4_data + "false"
    else:
        en_mode4_data = en_mode4_data + "true"

    data_to_write.append(en_mode4_data)

    #for data in data_to_write:
    #    print(data)

    if not exists(config_dir):
             os.mkdir(config_dir)

    file_path = config_dir + "/"+ config_name + ".ini"

    with open(file_path, "w+") as file_to_write:
        file_to_write.write("\n".join(data_to_write))
    
    if(exists(file_path)):
        print("file created successfully", file_path)
    else:
        print("File creation failed")


def start_parallel_processing(process_to_start, process_running, track_process_running, process_error):
    #start the process running and add it to process_running[]
    print("------------------------------------------------------")
    attempt = 0
    for cmd in process_to_start:
        if len(track_process_running) < MAX_PROCESS_COUNT:
            if cmd in process_error:
                attempt =  process_error[cmd]
            cmd_split = cmd.split(' ')
            run_config = cmd_split[-2]
            id_run =  cmd_split[-1]
            with open(working_directory + 'logs/log_' + scenario + "_" + run_config + "_" +  id_run  + "_a"+ str(attempt) + ".log", "w+") as log_file:
                    print("Adding process to run: ", cmd, attempt)
                    track_process_running.append(subprocess.Popen(cmd, stdout=log_file, stderr=log_file,
                                                            universal_newlines=True,
                                                            shell=True))
            process_running.append(cmd)
    
    #remove all the process that are running from start list:
    for p in process_running:
        if p in process_to_start:
            process_to_start.remove(p)


def launch_runs(simulations_to_run):
    cnt_simulations = 0
    track_process_running = []
    process_to_start = []
    process_running = []
    process_done = []
    process_error = {}
    process_failed = []

    start_time = time.time()

    for run_config in simulations_to_run:
        cmd = get_num_of_runs + " " + run_config
        #print("Initial cmd", cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True,
                             shell=True)

        output, errors = p.communicate()
        exit_code = p.returncode

        if not exit_code == 0:
            print("Error code", exit_code, "while obtaining number of simulations to run")
            print(errors)
            #return
        
        set_ids_simulations = output.replace('\n', '').split(' ')[1:]
        cnt_simulations = cnt_simulations + len(set_ids_simulations)

        #print("set_ids_simulations",set_ids_simulations)

        for id_run in set_ids_simulations:
            cmd = "time " + path_start_simulation + " " + run_config + " " + id_run
            process_to_start.append(cmd)
            """
            with open(working_directory + 'logs/log_' + scenario + "_" + run_config + "_" +  id_run  + ".log", "w+") as log_file:
                process_running.append(subprocess.Popen(cmd, stdout=log_file, stderr=log_file,
                                                        universal_newlines=True,
                                                        shell=True))
            """
    print("----------------------------------------------------------------------------------------------------")
    print("Total simulaitons to run: ", len(process_to_start))
    #Start the process for execution
    start_parallel_processing(process_to_start, process_running, track_process_running, process_error)

    while True:

        for p in track_process_running:
            proc_cmd = p.args
            if p.poll() is None:
                ...
            elif p.returncode == 0:
                print("process done:",proc_cmd)
                process_done.append(proc_cmd)

                if proc_cmd in process_running:
                    process_running.remove(proc_cmd)

                track_process_running.remove(p)
                process_error.pop(proc_cmd,None)
            else:
                print("process error:",p.returncode, proc_cmd)

                #remove from process running list
                if proc_cmd in process_running:
                    process_running.remove(proc_cmd)
                track_process_running.remove(p)
                
                
                #add to the process error
                if(None == process_error.get(proc_cmd, None)):
                    process_error[proc_cmd] = 1
                else:
                    process_error[proc_cmd] = process_error[proc_cmd] + 1
             
                if process_error[proc_cmd] < 3:
                    process_to_start.append(proc_cmd)
                else:
                    process_failed.append(proc_cmd)
                    process_error.pop(proc_cmd,None)

        print("------------------------------------------------------")
        time_now = time.time()
        elapsed_time = time_now - start_time
        hours, rem = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(rem, 60)
        print("{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds))

        if not process_to_start and not track_process_running:
            break
        else:
            #Start the process for execution
            start_parallel_processing(process_to_start, process_running, track_process_running, process_error)
            print("------------------------------------------------------")
            print("process to start", len(process_to_start))
            print("process_running", len(process_running))
            print("process_done", len(process_done))
            print("process_error", len(process_error))
            print("process_failed", len(process_failed))
            print("track_process_running", len(track_process_running))
            print("------------------------------------------------------")
            #sleep for 1 hour
            time.sleep(30)
            


    #print("process done: ", process_done)
    print("process failed: ", process_failed)
    print("process error: ", process_error)    
    #exit_codes = [p.wait() for p in process_running]
    #print(exit_codes)
    #print(command)

def main():
    print("main")

    simulaitons_to_run = []
    with open('config_list.json') as json_file:
        data = json.load(json_file)
        #print(data)
        #print(type(data))

        for key in data:
            #print(key)
            for in_key in data[key]:
                if(data[key][in_key] == True):
                    #print("add to run simulations", key)
                    simulaitons_to_run.append(key)
                    create_config_file(key)

    print("====================================================================================")
    #print(simulaitons_to_run)
    launch_runs(simulaitons_to_run)

if __name__ == "__main__":
    main()
