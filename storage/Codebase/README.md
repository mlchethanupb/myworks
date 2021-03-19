## Environment Setup
Setup the testbed with Kubernetes and GlusterFS by following the provided instructions on corresponding repository.
* [Kubernetes](https://github.com/OrangeOnBlack/auto-kubernetes-setup)
* [GlusterFS](https://github.com/OrangeOnBlack/stateful-kubernetes)

## Setup VNF Architecture:

#### Kafka
The implementation of Kafka VNF is designed in such a way where Digitatwin continuously mimics machine states as messages. OPC UA client fetches those messages
from Digitaltwin and publishes them to Kafka topic. The overall system is distributed where Kafka is running on a worker node and Digitaltwin and OPC UA is running on another worker node of kubernetes cluster. The implementation can be done by following the steps below.
* Build docker image for Digitaltwin, OPC UA Kafka Connector and kafka using ``docker build -t 'image name':tag .`` command.
* Run ``kubectl apply -f 'file name'`` to deploy the application on kubernetes. Necessary files (docker image, kubernetes servive and deployment) can be found on particular folders inside ``Codebase``. For example, using the following commands ``Kafka`` application can be deployed successfully on kubernetes.
```
docker build -t kafka:dev .
```
```
kubectl apply -f kafka-deployment.yaml
```
* The Kafka application contains single broker with single topic( ``dt-imms-opcua-0``) and single partition(``dt-imms-opcua-0-0``). However, the topics has some configurations which can be applied by using the following command.
```
docker exec -ti 'container id' /bin/sh -c "./bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic dt-imms-opcua-0 --config retention.bytes=62914560"
```
```
docker exec -ti 'container id' /bin/sh -c "./bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic dt-imms-opcua-0 --config segment.bytes=20971520"
```
```
docker exec -ti 'container id' /bin/sh -c "./bin/kafka-topics.sh --zookeeper localhost:2181 --alter --topic dt-imms-opcua-0 --config cleanup.policy=delete"
```
* For checking topic configuration run the following command
```
docker exec -ti 'container name' /bin/sh -c " bin/kafka-topics.sh --zookeeper localhost:2181 --describe --topic dt-imms-opcua-0"
```
* For collecting metrics from kafka application run file ``metrics.sh`` using ``./metrics.sh`` and store the logs from opcua container for collecting metrics from container by using ``kubectl logs -f 'opcua pod name'>> opcua_metrics.txt``. 

#### Squid
In Squid scenario, Digitaltwin mimics the machine states like kafka scenario. But instead of saving the states as text messages this time Digitaltwin creates html file for every states. Like kafka the setup was implemented in a distributed manner where ``Squid`` and ``Digitaltwin`` were ruuning on different worker node.
* For creating html file include ``IMMS_APP_SQUID.py`` instead of ``IMMS_APP.py``in DigitaltwinServer. 
* Copy all the html files from Digitaltwin container to virtual machine using the following command.
```
docker cp 'container id':/IMMS_APP Squid_all
```
* Turn the VM into a server by running the following command(path ``Codebase/DigitaltwinServer/Squid_all``)
```
python3 dtServer.py
```
* Build image and deploy it on kubernetes in the same way mentioned in kafka. 
* Copy ``file_List.txt`` from ``Codebase/DigitaltwinServer/Squid_all`` to the path of ``squid worker node``.
* Finally run ``./squid_metrics.sh`` and ``./squid_request.sh`` (in squid worker node) at the same time in two different terminal for collecting squid metrices. 


#### Storage Allocator 
* For kafka build docker images for the applications (Kafka, OPC UA and Digitaltwin) on different worker node. While building docker image for OPC UA instead of ``opcua_kafka_connector.py`` use ``opcua_storage_allocator.py``. After that start the allocator(path ``Codebase/Storage_allocator_kafka``) by running the following command. Deployment files is provided respective application folder (e.g, Kafka, Squid, etc.) 
```
python3 storage_allocation.py
```
* For squid, at first build docker image for squid and start the server(path ``Codebase/DigitaltwinServer/Squid_all``). After that start the allocator for squid ``Codebase/Storage_allocator_squid``) and run ``./request_squid.sh`` file in a different terminal(at the same time) to send continuous request in squid.


#### SFC
* For implementing SFC run ``storage_allocation_sfc.py``.
* Build docker image ``http_server:s`` for pythons's ``SimpleHTTPServer`` and run the following command to start the container.

```
docker run -ti --rm -p 8000:8000 http_server:s
```
* Wait some time (5 minutes for current configuration) as squid needs some time to create all cache directories. Finally run ``request.sh`` to send continuous request in squid. 

