FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    openssh-client \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN useradd -m -s /bin/bash user

RUN mkdir -p /home/user/.ssh && \
    chown user:user /home/user/.ssh && \
    chmod 700 /home/user/.ssh

RUN chown user:user /home/user && \
    chmod 0777 /home/user

USER user
WORKDIR /home/user
