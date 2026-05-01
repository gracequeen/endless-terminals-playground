FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/releases/builds/46/config && \
    mkdir -p /home/user/releases/builds/47 && \
    mkdir -p /home/user/app

RUN echo "version=46" > /home/user/releases/builds/46/config/app.conf

RUN echo "version=47" > /home/user/releases/builds/47/app.conf

RUN cat > /home/user/releases/deploy.sh << 'SCRIPT'
#!/bin/bash
set -e
BUILD="$1"
if [ -z "$BUILD" ]; then
    echo "usage: deploy.sh <build-number>" >&2
    exit 1
fi

cd /home/user/releases
ln -sfn "builds/$BUILD" current

CONFIG="/home/user/releases/active/config/app.conf"
if [ ! -f "$CONFIG" ]; then
    echo "config not found: $CONFIG" >&2
    exit 1
fi

cp "$CONFIG" /home/user/app/runtime.conf
echo "deployed build $BUILD"
SCRIPT

RUN chmod +x /home/user/releases/deploy.sh

RUN cd /home/user/releases && ln -s builds/46 current

RUN cd /home/user/releases && ln -s current active

RUN chmod -R 0777 /home/user/releases && \
    chmod -R 0777 /home/user/app

WORKDIR /home/user
