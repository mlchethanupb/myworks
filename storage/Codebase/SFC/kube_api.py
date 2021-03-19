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
    yaml_file = 'vol-kafka.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(1)
    print("volume created")

def create_pvc():
    config.load_kube_config()
    k8s_client = client.ApiClient()
    yaml_file = 'pvc-kafka.yaml'
    utils.create_from_yaml(k8s_client, yaml_file)
    time.sleep(1)
    yaml_file2 = 'pvc-squid.yaml'
    utils.create_from_yaml(k8s_client, yaml_file2)
    time.sleep(1)
    print("pvc created") 


def create_app():
    config.load_kube_config()
    k8s_client = client.ApiClient() 
    digitaltwin= 'dt.yaml'
    utils.create_from_yaml(k8s_client,digitaltwin)
    kafka= 'kafka-deployment.yaml'
    utils.create_from_yaml(k8s_client,kafka)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep kafka| cut -f3 -d'1'|cut -c 6-12", shell=True)
        if "Running" in str(status_check):
            print("Kafka pod started")
            break 
    time.sleep(20)   
    opcua='opcua.yaml'
    utils.create_from_yaml(k8s_client,opcua)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep opcua| cut -f3 -d'1'|cut -c 6-12", shell=True)
        if "Running" in str(status_check):
            print("Opcua pod started")
            break 
    time.sleep(120)
            
    kafka= 'squid-deployment.yaml'
    utils.create_from_yaml(k8s_client,kafka)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep squid| cut -f3 -d'1'|cut -c 6-12", shell=True)
        if "Running" in str(status_check):
            print("Squid pod started")
            break 
    time.sleep(20) 

