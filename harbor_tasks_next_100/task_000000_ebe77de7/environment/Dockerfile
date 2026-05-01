FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest requests

RUN mkdir -p /home/user/webapp && chmod 0777 /home/user && chmod 0777 /home/user/webapp

RUN python3 -m venv /home/user/webapp/venv

RUN chmod -R 0777 /home/user/webapp/venv

RUN useradd -m -d /home/user -s /bin/bash user || true

ENV HOME=/home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
