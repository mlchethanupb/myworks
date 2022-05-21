import json
import glob
import subprocess
import re
import os
from os.path import exists

get_num_of_runs = './get_number_of_run.sh'
path_start_simulation = './start_simulations.sh'
working_directory = './'
scenario = 'InTAS'
config_dir = "../scenarios/InTAS/scenario/config"

CONST_settings_dict={ "config":"[Config ",
                      "result":"result-dir = ../results/",
                      "service":"*.node[*].middleware.services = xmldoc(\"configs/services_",
                      "fixedrate":"*.node[*].middleware.CpService.fixedRate = ",
                      "fixedinterval":"*.node[*].middleware.CpService.fixedInterval = ",
                      "en_mode4":"*.node[*].lteNic.enable_mode4 = "}



def create_config_file(config_name):
    print("creating config file for: ", config_name)
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
    if(config_name_split[1]=="mode3"):
        en_mode4_data = en_mode4_data + "false"
    else:
        en_mode4_data = en_mode4_data + "true"

    data_to_write.append(en_mode4_data)

    for data in data_to_write:
        print(data)

    file_path = config_dir + "/"+ config_name + ".ini"

    if not exists(config_dir):
             os.mkdir(config_dir)
    
    with open(file_path, "w+") as file_to_write:
        file_to_write.write("\n".join(data_to_write))
    
    if(exists(file_path)):
        print("file created successfully", file_path)
    else:
        print("File creation failed")


def launch_runs(simulations_to_run):
    cnt_simulations = 0
    process_running = []

    for run_config in simulations_to_run:
        cmd = get_num_of_runs + " " + run_config
        print("Initial cmd", cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True,
                             shell=True)

        output, errors = p.communicate()
        exit_code = p.returncode

        if not exit_code == 0:
            print("Error code", exit_code, "while obtaining number of simulations to run")
            print(errors)
            #return

        print("----------------------------------------------------------------------------------------------------")
        print(output)
        
        set_ids_simulations = output.replace('\n', '').split(' ')[1:]
        cnt_simulations = cnt_simulations + len(set_ids_simulations)

        print("set_ids_simulations",set_ids_simulations)

        for id_run in set_ids_simulations:
            cmd = path_start_simulation + " " + run_config + " " + id_run
            print("cmd for repeat", cmd)
            with open(working_directory + 'logs/log_' + scenario + "_" + run_config  + ".log", "w+") as log_file:
                process_running.append(subprocess.Popen(cmd, stdout=log_file, stderr=log_file,
                                                        universal_newlines=True,
                                                        shell=True))

    print('Number of simulations started:', cnt_simulations)
    exit_codes = [p.wait() for p in process_running]
    print(exit_codes)
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
                    print("add to run simulations", key)
                    simulaitons_to_run.append(key)
                    create_config_file(key)
                    print("-------------------------------------")

    print(simulaitons_to_run)
    launch_runs(simulaitons_to_run)

if __name__ == "__main__":
    main()