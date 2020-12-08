FROM phusion/baseimage:bionic-1.0.0

ENV DEBIAN_FRONTEND=noninteractive
RUN curl -s https://repos.influxdata.com/influxdb.key | apt-key add - && echo "deb https://repos.influxdata.com/ubuntu bionic stable" | tee /etc/apt/sources.list.d/influxdb.list && apt update && apt install -y telegraf influxdb net-tools && mkdir /etc/service/telegraf /etc/service/influxdb

COPY telegraf.sh /etc/service/telegraf/run
COPY influxdb.sh /etc/service/influxdb/run
COPY telegraf.conf /etc/telegraf/

RUN sed -i 's/^\[http\]/[http]\n  enabled = true/g' /etc/influxdb/influxdb.conf && chown -R influxdb:influxdb /var/lib/influxdb /etc/influxdb && chown -R telegraf:telegraf /etc/telegraf && chmod +x /etc/service/telegraf/run /etc/service/influxdb/run && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EXPOSE 9273 8086
CMD ["/sbin/my_init"]