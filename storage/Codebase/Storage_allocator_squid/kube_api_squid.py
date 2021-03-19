import os
from kubernetes import client, config, utils
import yaml
import time
from os import path
from datetime import datetime
import subprocess


def create_pv():
    config.load_kube_config()
    k8s_client = client.ApiClient()
    yaml_file = 'vol-squid.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(1)
    print("volume created")

def create_pvc():
    config.load_kube_config()
    k8s_client = client.ApiClient()
    yaml_file = 'pvc-squid.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(1)
    print("pvc created") 


def create_app():
    config.load_kube_config()
    k8s_client = client.ApiClient()
    yaml_file= 'squid-deployment.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)

    while True:
        status_check=subprocess.check_output("kubectl get pods|grep squid| cut -f3 -d'1'|cut -c 6-12", shell=True)
        if "Running" in str(status_check):
            print("Squid pod started")
            break 
    time.sleep(20)   
    


 
