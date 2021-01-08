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
    yaml_file = 'squid.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(25)
    print("squid created")    


def delete_app():
    print("Restarting Squid") 
    config.load_kube_config()
    yaml_file = 'squid.yaml'
    k8s_client = client.ApiClient()
    core_api = client.CoreV1Api(k8s_client)
    ext_api = client.AppsV1Api(k8s_client)
    #core_api.delete_namespaced_service(name='squid-service',namespace="default", body={})
    ext_api.delete_namespaced_deployment(name='squid-deployment',namespace="default", body={})
    print("squid deleted") 
    time.sleep(1.5)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep squid| cut -f3 -d'1'|cut -c -6,-12", shell=True)
        if "Termi" not in str(status_check):
            delete_time = datetime.now().strftime('%H:%M:%S')
            print("**",delete_time)
            break


    print("squid deployment deleted")
    return delete_time
 
def recreate_app():
    config.load_kube_config()
    k8s_client = client.ApiClient() 
    yaml_file = 'squid2.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(20)
    print("squid recreated")
    
