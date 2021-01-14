#!/bin/sh
echo "=> Starting InfluxDB ..."
chmod -R 777 /var/lib/influxdb
exec /sbin/setuser influxdb /usr/bin/influxd -config /etc/influxdb/influxdb.conf >>/var/log/influxdb.log 2>&1

