FROM ubuntu:22.04
RUN sed -i "s|archive.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g; s|security.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g" /etc/apt/sources.list 2>/dev/null || true

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/webapp && chmod 0777 /home/user && chmod 0777 /home/user/webapp

RUN python3.11 -m venv /home/user/webapp/venv

RUN /home/user/webapp/venv/bin/pip install --upgrade pip

RUN /home/user/webapp/venv/bin/pip install flask==2.3.2 requests==2.31.0 gunicorn==21.2.0

RUN chmod -R 0777 /home/user/webapp

WORKDIR /home/user

CMD ["/bin/bash"]
