FROM python:3-alpine as dev
RUN apk add --no-cache libxslt-dev libxml2-dev gcc musl-dev libffi-dev openssl-dev
COPY requirements.txt /app/
RUN pip3 install -r /app/requirements.txt

FROM python:3-alpine
RUN apk add --no-cache libxml2 libxslt && mkdir -p /app/csv/
COPY --from=dev /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY opc_ua_influxdb_connector.py /app/
WORKDIR /app/
#CMD ["/usr/bin/tail","-f","/dev/null"]
CMD ["python3", "/app/opc_ua_influxdb_connector.py"]
