from kafka import KafkaConsumer
import time
import json
import sys
import os
from datetime import datetime
import threading
from queue import Queue
import _thread

KAFKA_TOPIC="dt-imms-opcua-0"
KAFKA_SERVER="10.0.0.81"
KAFKA_PORT="31090"
kafka_consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers='%s:%s' % (KAFKA_SERVER, KAFKA_PORT),
                             # auto_offset_reset='earliest',
                             consumer_timeout_ms=30000)
while True:
    message = next(kafka_consumer)
    timestamp_received = datetime.now()
    msg = json.loads(message.value.decode('utf-8'))
    timestamp_sent = datetime.strptime(str(msg['TimestampSent']), '%Y-%m-%d %H:%M:%S.%f')
    print(message,"***",timestamp_sent)
    filename = str(datetime.now().strftime("%m%d%Y%H:%M:%S"))+ '.html'
            #print(filename)
    #file_list = open("/data/file_List.txt","a")
    #file_list.write(filename)
    #file_list.write("\n")
    #file_list.close()

            
            #f = open(filename,'w+')
    f = open("/data/"+filename, "a")
    message1 = """<html>
    <head></head>
    <body>"""
    f.write(message1)
    f.write("---------------------------------------------")
    f.write("DATE = ")
    f.write(str(msg['date']))
    f.write("TIME = ")
    f.write(str(msg['time']))
    f.write("@ActSimPara1 = ")
    f.write(str(msg['ATActSimPara1']))
    f.write("@ActSimPara2 = ")
    f.write(str(msg['ATActSimPara2']))
    f.write("ActCntCyc = ")
    f.write(str(msg['ActCntCyc']))
    f.write("ActCntPrt = ")
    f.write(str(msg['ActCntPrt']))
    f.write("ActStsMach = ")
    f.write(str(msg['ActStsMach']))
    f.write("ActTimCyc = ")
    f.write(str(msg['ActTimCyc']))
    f.write("SetCntMld = ")
    f.write(str(msg['SetCntMld']))
    f.write("SetCntPrt = ")
    f.write(str(msg['SetCntPrt']))
    f.write("SetTimCyc = ")
    f.write(str(msg['SetTimCyc']))
    f.write("---------------------------------------------")
       
    message2="""</body>
    </html>"""
    f.write(message2)
    f.close()
    print("done")
