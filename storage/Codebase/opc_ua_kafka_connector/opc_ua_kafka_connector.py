'''A simple OPC UA client which reads values from the OPC UA server and publishes them to a Apache Kafka Cluster'''

import time
from opcua import Client
from kafka import KafkaConsumer, KafkaProducer
import json
import sys
import os
from datetime import datetime
import threading
from queue import Queue
import _thread

import csv
lines = []
print("program started")
from subprocess import call
tempList=[]
consumerList=[]
producerList=[]
countConsumer=0
countProducer=0
msg_arr=[]
INSTANCE_NAME = os.environ.get('INSTANCE_NAME', 'MY-INSTACE')
OPCUA_SERVER = os.environ.get('OPCUA_SERVER', 'localhost')
OPCUA_PORT = os.environ.get('OPCUA_PORT', '4840')
KAFKA_SERVER = os.environ.get('KAFKA_SERVER', '192.168.0.7')
KAFKA_PORT = os.environ.get('KAFKA_PORT', '9092')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC', 'my-topic')
SLEEP_DURATION = os.environ.get('SLEEP_DURATION', '1') # seconds sleep after each update written to kafka
#OUT_FILE = os.environ.get('OUT_FILE', 'response_time.json')
OUT_FILE_TXT= os.environ.get('OUT_FILE_TXT','fileWrite.txt')
NUMBER_MESSAGES = os.environ.get('NUMBER_MESSAGES', 10)
t_slot=4
number_messages = 0
set_c=0
q = Queue()
#file = open(OUT_FILE, "w")
fileTxt=open(OUT_FILE_TXT, "w+")

kafka_consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers='%s:%s' % (KAFKA_SERVER, KAFKA_PORT),
                             # auto_offset_reset='earliest',
                             consumer_timeout_ms=30000)

def _monitor_response_time(kafka_consumer, q):
    global number_messages
    global countConsumer
    t1 = datetime.now()
    i=0
    while True:
        try:
            message = next(kafka_consumer)
            print("Inside consumer")
            timestamp_received = datetime.now()
            msg = json.loads(message.value.decode('utf-8'))
            timestamp_sent = datetime.strptime(str(msg['TimestampSent']), '%Y-%m-%d %H:%M:%S.%f')
            response_time = timestamp_received - timestamp_sent
            print("Response time: %f seconds" % response_time.total_seconds())
            print("\n\n\nSlot time",s_time)
            q.put(response_time.total_seconds())
            tempList.append(response_time.total_seconds())
            number_messages += 1
            if s_time==0 or s_time % t_slot==1:
                t11 = datetime.now()
            elif s_time% t_slot==0 :
                t22 = datetime.now()
                t33=t22-t11
                consumerList.insert(countConsumer,t33)
                countConsumer+=1
                print('Till now consumer list', consumerList)

                print("\n\ncon 33time: %f seconds" % t33.total_seconds())


            if int(NUMBER_MESSAGES) > 0:
                if number_messages >= int(NUMBER_MESSAGES):
                    _thread.interrupt_main()
                    t2 = datetime.now()
                    t3=t2-t1
                    print("consume time: %f seconds" % t3.total_seconds())                   
                    sys.exit()
        except StopIteration:
            pass
        # except Exception:
        #     pass

def listToString(s):  
    
    # initialize an empty string 
    str1 = ""  
    
    # traverse in the string   
    for ele in s:  
        str1 += str(ele)
    
    # return string   
    return str1  

if __name__== "__main__":

    global countProducer
    thread = threading.Thread(target=_monitor_response_time, args=(kafka_consumer, q,))
    thread.daemon = True
    thread.start()

    opcua_client = Client("opc.tcp://%s:%s/freeopcua/server/" % (OPCUA_SERVER, OPCUA_PORT))
    opcua_client.connect()
    print('Connected to OPC UA server %s:%s' % (OPCUA_SERVER, OPCUA_PORT))
    root = opcua_client.get_root_node()
    imms = root.get_child(["0:Objects", "2:IMMS"])

    kafka_producer = KafkaProducer(bootstrap_servers='%s:%s' % (KAFKA_SERVER, KAFKA_PORT),
                                retries=5,
                                batch_size=0,
                                compression_type=None)
                                # compression_type='gzip')
                                # compression_type='snappy')
                                # compression_type='lz4')
    kafka_producer.flush()
    # thred.sleep(500)
    print('Connected to Kafka %s:%s' % (KAFKA_SERVER, KAFKA_PORT))
    s_time=0
    if s_time==0 or s_time % t_slot==1:
        t4 = datetime.now()

    while True:
        try:
            s_time=s_time+1
            msg = {
                "date": float(imms.get_variables()[0].get_value()),
                "time": str(imms.get_variables()[1].get_value()),
                "ATActSimPara1": float(imms.get_variables()[2].get_value()),
                "ATActSimPara2": float(imms.get_variables()[3].get_value()),
                "ActCntCyc": float(imms.get_variables()[4].get_value()),
                "ActCntPrt": float(imms.get_variables()[5].get_value()),
                "ActStsMach": str(imms.get_variables()[6].get_value()),
                "ActTimCyc": float(imms.get_variables()[7].get_value()),
                "SetCntMld": float(imms.get_variables()[8].get_value()),
                "SetCntPrt": float(imms.get_variables()[9].get_value()),
                "SetTimCyc": float(imms.get_variables()[10].get_value()),
                "InstanceName": INSTANCE_NAME,
                "TimestampSent": datetime.now()
            }
            

            future = kafka_producer.send(KAFKA_TOPIC, json.dumps(msg, default=str).encode('utf-8'))
            msg_size=int(sys.getsizeof(msg))
            msg_arr.append(msg_size)
            kafka_producer.flush()
            
            if s_time% t_slot==0 and s_time>0:
                t5 = datetime.now()
                t6=t5-t4
                producerList.insert(countProducer,t6)
                countProducer+=1
                print("\n\n\nPro time: %f seconds" % t6.total_seconds())
                arr_s=s_time-t_slot
                arr_e=s_time+t_slot-1
                set_c=set_c+1
                print("\n\n Set val:",set_c)
                chk_arr=[]
                chk_arr=tempList[arr_s:arr_e]
                chk_msg=msg_arr[arr_s:arr_e]
                maxList=max(chk_arr)
                sumList=sum(chk_arr)
                sumMsg=sum(chk_msg)
                avgList=float(sumList/int(t_slot))
                print("Max List",maxList," Whole List",tempList)
                print("Average of List",avgList)
                fileTxt.write(str(maxList))
                fileTxt.write(" ")
                fileTxt.write(str(avgList))
                fileTxt.write(" ")
                fileTxt.write(str(sumMsg))
                #fileTxt.write("\n")
                
                fileTxt.write("    ")
                fileTxt.write(str(consumerList[countConsumer-1]))
                fileTxt.write("   ")
                fileTxt.write(str(producerList[countProducer-1]))
                fileTxt.write("\n")
                fileTxt.write("\n")
                fileTxt.write("\n")
                print('Till now consumer list', consumerList)
                
                time.sleep(float(SLEEP_DURATION))




                
            print('sys.argv[0] =', sys.argv[0])             
            pathname = os.path.dirname(sys.argv[0])        
            print('path =', pathname)
            print('full path =', os.path.abspath(pathname))
            print('Update written to topic %s' % KAFKA_TOPIC)
            fileDir = os.path.dirname(os.path.realpath('/home/user/opc_ua_kafka_connector/'))
            print ("fileDir",fileDir)
            filename = os.path.join(fileDir, 'opc_ua_kafka_connector/c.txt')
            print ("filename ",filename)
            #with open('/home/user/opc_ua_kafka_connector/met.sh', 'r') as file:
            #with open(filename, 'r') as file:
            #    script = file.read()
            #rc = call(script, shell=True)            

            time.sleep(float(SLEEP_DURATION))
        except KeyboardInterrupt:
            try:
                opcua_client.disconnect()
                kafka_producer.close()
                kafka_consumer.close()
            except Exception:
                pass
            finally:
                #print("Witing response time to", OUT_FILE_TXT)
                #fileTxt.write(listToString(list(q.queue)))
                #print("Consumer List", consumerList)
                #print("Writing response times to", OUT_FILE)
                #file.write(json.dumps(list(q.queue)))
                #file.close()
                sys.exit()
