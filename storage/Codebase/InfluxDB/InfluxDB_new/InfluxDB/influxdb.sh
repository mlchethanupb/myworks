#!/bin/sh
echo "=> Starting InfluxDB ..."
exec /sbin/setuser influxdb /usr/bin/influxd -config /etc/influxdb/influxdb.conf >>/var/log/influxdb.log 2>&1

