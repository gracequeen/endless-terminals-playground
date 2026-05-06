FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    coreutils \
    gawk \
    grep \
    bash \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/bin && chmod 0777 /home/user && chmod 0777 /home/user/bin

WORKDIR /home/user

CMD ["/bin/bash"]
