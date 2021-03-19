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
            time.sleep(20)
            break  

def delete_app():
    print("Restarting Kafka") 
    config.load_kube_config()
    k8s_client = client.ApiClient()
    core_api = client.CoreV1Api(k8s_client)
    ext_api = client.AppsV1Api(k8s_client)
    ext_api.delete_namespaced_deployment(name='opcua',namespace="default", body={})
    ext_api.delete_namespaced_stateful_set(name='kafka',namespace="default", body={})
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep kafka| cut -f3 -d'1'|cut -c -6,-12", shell=True)
        if "Termi" not in str(status_check):
            delete_time = datetime.now().strftime('%H:%M:%S')
            print("Kafka deleted")
            break

    return delete_time

 
def recreate_app():
    config.load_kube_config()
    k8s_client = client.ApiClient() 
    kafka_re= 'kafka_del.yaml'
    utils.create_from_yaml(k8s_client,kafka_re)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep kafka-0| cut -f3 -d'1'|cut -c 6-12", shell=True)
        if "Running" in str(status_check):
            start_time = datetime.now().strftime('%H:%M:%S')	
            print("Kafka pod restarted")
            break    
    opcua='opcua.yaml'
    utils.create_from_yaml(k8s_client,opcua)
    while True:
        status_check=subprocess.check_output("kubectl get pods|grep opcua| cut -f3 -d'1'|cut -c 6-12", shell=True)
        if "Running" in str(status_check):
            print("Opcua pod restarted")
            break
    return start_time
