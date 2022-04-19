FROM ubuntu:20.04

ENV TZ=Asia/Jakarta

RUN --mount=type=cache,target=/var/cache/apt_update apt update \
    && apt install -y \
        python-is-python3 \
        python3-pip \
        python3-dev \
        libssl-dev \
        zlib1g-dev \
        gcc \
        g++ \
        make \
        curl

ARG LIBRDKAFKA_VER=1.6.2
ARG LIBKAFKA=librdkafka-$LIBRDKAFKA_VER
RUN --mount=type=cache,target=/var/cache/librdkafka \
    curl -L https://github.com/edenhill/librdkafka/archive/refs/tags/v$LIBRDKAFKA_VER.tar.gz | tar xzf - \
        && cd $LIBKAFKA\
        && ./configure --prefix=/usr \
        && make \
        && make install

ARG C_KAFKA_VER=1.8.2
ARG KAFKA=confluent-kafka-python-$C_KAFKA_VER
RUN --mount=type=cache,target=/var/cache/kafka \
    curl -L https://github.com/confluentinc/confluent-kafka-python/archive/refs/tags/v$C_KAFKA_VER.tar.gz | tar xzf - \
        && cd $KAFKA \
        && python setup.py build \
        && python setup.py install

RUN rm -rf $LIBKAFKA $KAFKA

RUN pip install flask

