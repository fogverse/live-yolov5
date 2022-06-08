FROM ariqbasyar/opencv:v4.5.5-py3.8.10 as build

RUN --mount=type=cache,target=/var/cache/apt_update apt update \
    && apt install -y \
    libssl-dev \
    zlib1g-dev \
    gcc \
    g++ \
    make \
    git \
    vim \
    curl

RUN pip install pandas aiokafka
