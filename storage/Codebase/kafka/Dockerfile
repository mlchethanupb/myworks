FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
    iputils-ping \
    curl \
    openjdk-8-jre-headless \
    iproute2

RUN curl -L https://archive.apache.org/dist/kafka/2.2.0/kafka_2.12-2.2.0.tgz -O
RUN tar -xzf kafka_2.12-2.2.0.tgz
WORKDIR /kafka_2.12-2.2.0

ENV KAFKA_LISTEN 127.0.0.1
ENV KAFKA_PORT 9092

#ADD server.properties /kafka_2.12-2.2.0/config/
RUN printf "\ncompression.codec=0" >> /kafka_2.12-2.2.0/config/server.properties

ADD start.sh start.sh
RUN chmod +x start.sh

CMD ./start.sh

EXPOSE 9092

