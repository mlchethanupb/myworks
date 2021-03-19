import os
from kubernetes import client, config, utils
import yaml
import time
from os import path
from datetime import datetime
import subprocess

def create_app():
    config.load_kube_config()
    k8s_client = client.ApiClient()
    yaml_file = 'influx-Deployment_only.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(25)
    print("influxdb new created")    


def delete_app():
    print("Restarting Influx") 
    config.load_kube_config()
    yaml_file = 'influx-Deployment_only.yaml'
    k8s_client = client.ApiClient()
    core_api = client.CoreV1Api(k8s_client)
    ext_api = client.AppsV1Api(k8s_client)
    subprocess.check_output("kubectl delete -f influx-Deployments.yaml",shell=True)
    print("influxdbnew deleted") 
    time.sleep(1.5)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep influxdbnew| cut -f3 -d'1'|cut -c -6,-12", shell=True)
        if "Termi" not in str(status_check):
            delete_time = datetime.now().strftime('%H:%M:%S')
            print("**",delete_time)
            break


    print("influxdbnew deployment deleted")
    return delete_time
 
def recreate_app():
    config.load_kube_config()
    k8s_client = client.ApiClient() 
    yaml_file = 'influx-Deployments.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(20)
    print("influxdbnew recreated")
    
