FROM node:20-slim

RUN apt-get update && apt-get install -y git python3 python3-pip patch && \
    pip3 install pytest --break-system-packages && \
    rm -rf /var/lib/apt/lists/*

# TODO: replace with repo at base_commit with test_patch applied
COPY app-generation-gateway/ /home/user/app-generation-gateway/

RUN cd /home/user/app-generation-gateway && npm install --ignore-scripts

WORKDIR /home/user/app-generation-gateway
