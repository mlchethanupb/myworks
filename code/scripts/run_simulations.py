import json
import glob
import subprocess

path_start_simulation = './start_simulations.sh'
working_directory = './'
scenario = 'InTAS'



#def create_config_file(config):






def launch_runs(simulations_to_run):
    cnt_simulations = 0
    process_running = []

    for run_config in simulations_to_run:
        cmd = path_start_simulation + " " + run_config
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
        """
        set_ids_simulations = output.replace('\n', '').split(' ')[1:]
        cnt_simulations = cnt_simulations + len(set_ids_simulations)

        print("set_ids_simulations",set_ids_simulations)

        for id_run in set_ids_simulations:
            cmd = path_start_simulation + " " + run_config
            print("cmd for repeat", cmd)
            with open(working_directory + 'logs/log_' + scenario + "_" + run_config  + ".log", "w+") as log_file:
                process_running.append(subprocess.Popen(cmd, stdout=log_file, stderr=log_file,
                                                        universal_newlines=True,
                                                        shell=True))
        """
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

    print(simulaitons_to_run)
    launch_runs(simulaitons_to_run)

if __name__ == "__main__":
    main()