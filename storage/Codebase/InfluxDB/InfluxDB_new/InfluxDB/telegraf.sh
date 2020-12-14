#!/bin/sh
echo "=> Starting Telegraf ..."
exec /sbin/setuser telegraf /usr/bin/telegraf -config /etc/telegraf/telegraf.conf >>/var/log/telegraf.log 2>&1

