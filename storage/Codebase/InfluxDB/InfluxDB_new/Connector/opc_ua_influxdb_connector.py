

#pip3 install prometheus_client influxdb requests opcua

import time
from opcua import Client
from prometheus_client.parser import text_string_to_metric_families
from influxdb import InfluxDBClient
import requests
import os, sys, signal, logging
import csv
from datetime import datetime

OPCUA_SERVER = os.environ.get('OPCUA_SERVER', os.getenv('DIGITALTWIN_SERVICE_HOST', 'digitaltwin'))
OPCUA_PORT = os.environ.get('OPCUA_PORT', '4840')
SLEEP_DURATION = os.environ.get('SLEEP_DURATION', 5) 
INSTANCE_NAME = os.environ.get('INSTANCE_NAME', os.uname()[1])
INFLUXDB_HOST = os.environ.get('INFLUXDB_HOST', os.getenv('INFLUXDB_SERVICE_HOST', 'influxdb'))
INFLUXDB_PORT = os.environ.get('INFLUXDB_PORTNUM', 8086)
INFLUXDB_METRICS_PORT = os.environ.get('INFLUXDB_METRICS_PORTNUM', 9273)
INFLUXDB_DB = os.environ.get('INFLUXDB_DB', 'data')
METRICS_USER = os.environ.get('METRICS_USER', 'foo')
METRICS_PASS = os.environ.get('METRICS_PASS', 'bar')
CSV_FILE = os.environ.get('CSV_FILE', datetime.now().strftime("%Y%m%d_%H%M%S") + '.csv')


#CRITICAL-50, ERROR-40,WARNING-30,INFO-20,DEBUG-10,NOTSET-0
DEBUG_MODE = os.getenv('DEBUG_MODE', 'INFO')

logger = logging.getLogger()
stdout_handler = logging.StreamHandler()
logger.setLevel(DEBUG_MODE)
logger.addHandler(stdout_handler)

def terminateProcess(signalNumber, frame):
    raise SystemExit('Exiting...')
    return

def main():
    signal.signal(signal.SIGTERM, terminateProcess)

    try:
        influx_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT)
        #influx_client.get_list_database()
        influx_client.create_database(INFLUXDB_DB)
        influx_client.switch_database(INFLUXDB_DB)
    except Exception as e:
        logger.debug(INFLUXDB_HOST)
        logger.debug(INFLUXDB_PORT)
        logger.error("InfluxDB connection error, please check InfluxDB is running. Error=" + str(e))
        sys.exit(1)

    opcua_client = Client("opc.tcp://{}:{}/freeopcua/server/".format(OPCUA_SERVER, OPCUA_PORT))

    cols = ["request_datetime","msg_size","request_time_ms","request_ret","cpu_usage_active","disk_used_percent","mem_available_percent","influxdb_memstats_sys","influxdb_memstats_heap_inuse","influxdb_shard_diskBytes","influxdb_diskBytes","influxdb_shard_writeBytes","influxdb_database_numSeries","influxdb_httpd_writeReqBytes","influxdb_httpd_writeReqDurationNs","influxdb_httpd_writeReq","influxdb_httpd_writeReqActive"]
    with open("./csv/" + CSV_FILE, mode='w+', newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()

    try:
        logger.setLevel("WARNING")
        opcua_client.connect()
        root = opcua_client.get_root_node()
        imms = root.get_child(["0:Objects", "2:IMMS"])
    except Exception as e:
        logger.error("OPCUA connection error, please check OPCUA is running. Error=" + str(e))
        sys.exit(1)

    logger.setLevel(DEBUG_MODE)
    while True:
        try:
            logger.info('Connected to OPC UA server %s:%s' % (OPCUA_SERVER, OPCUA_PORT))

            request_datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            json_body = [
                {
                  "measurement": "imms",
                  "time": request_datetime,
                  "tags": {
                    "InstanceName": INSTANCE_NAME
                  },
                  "fields": {
                    "date": str(imms.get_variables()[0].get_value()),
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
                  }
                }
            ]
            #logger.debug(json_body)
            start = time.time()
            if influx_client.write_points(json_body):
                request_ret = 1
            else:
                request_ret = 0
            request_time = time.time() - start
            logger.debug("Request completed in {0:.0f}ms".format(request_time))
            msg_size = int(sys.getsizeof(json_body))

            influxdb_metrics = {}
            influxdb_metrics['request_datetime'] = request_datetime
            influxdb_metrics['msg_size'] = msg_size
            influxdb_metrics['request_time_ms'] = request_time
            influxdb_metrics['request_ret'] = request_ret

            metrics = requests.get("http://" + INFLUXDB_HOST + ":" + str(INFLUXDB_METRICS_PORT) + "/metrics", auth=requests.auth.HTTPBasicAuth(METRICS_USER, METRICS_PASS)).text

            for family in text_string_to_metric_families(metrics):
              for sample in family.samples:
                if sample[0] == "cpu_usage_active" and sample[1]['cpu'] == "cpu-total":
                    influxdb_metrics['cpu_usage_active'] = sample[2]
                    continue
                if sample[0] == "disk_used_percent" and sample[1]['path'] == '/etc/hosts':
                    influxdb_metrics['disk_used_percent'] = sample[2]
                    continue
                if sample[0] == "mem_available_percent":
                    influxdb_metrics['mem_available_percent'] = sample[2]
                    continue
                if sample[0] == "influxdb_memstats_sys":
                    influxdb_metrics['influxdb_memstats_sys'] = sample[2]
                    continue
                if sample[0] == "influxdb_memstats_heap_inuse":
                    influxdb_metrics['influxdb_memstats_heap_inuse'] = sample[2]
                    continue
                if sample[0] == "influxdb_shard_diskBytes" and sample[1]['database'] == INFLUXDB_DB:
                    influxdb_metrics['influxdb_shard_diskBytes'] = sample[2]
                    continue
                if sample[0] == "filecount_size_bytes" and sample[1]['directory'] == '/var/lib/influxdb':
                    influxdb_metrics['influxdb_diskBytes'] = sample[2]
                    continue
                if sample[0] == "influxdb_shard_writeBytes" and sample[1]['database'] == INFLUXDB_DB:
                    influxdb_metrics['influxdb_shard_writeBytes'] = sample[2]
                    continue
                if sample[0] == "influxdb_database_numSeries" and sample[1]['database'] == INFLUXDB_DB:
                    influxdb_metrics['influxdb_database_numSeries'] = sample[2]
                    continue
                if sample[0] == "influxdb_httpd_writeReqBytes":
                    influxdb_metrics['influxdb_httpd_writeReqBytes'] = sample[2]
                    continue
                if sample[0] == "influxdb_httpd_writeReqDurationNs":
                    influxdb_metrics['influxdb_httpd_writeReqDurationNs'] = sample[2]
                    continue
                if sample[0] == "influxdb_httpd_writeReq":
                    influxdb_metrics['influxdb_httpd_writeReq'] = sample[2]
                    continue
                if sample[0] == "influxdb_httpd_writeReqActive":
                    influxdb_metrics['influxdb_httpd_writeReqActive'] = sample[2]
                    continue
            logger.info(influxdb_metrics)
            with open("./csv/" + CSV_FILE, mode='a+', newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=cols, extrasaction='ignore')
                writer.writerow(influxdb_metrics)
            time.sleep(SLEEP_DURATION)

        except Exception as e:
            logger.error(e)
        #finally:
        #    opcua_client.disconnect()

if __name__== "__main__":
    main()


