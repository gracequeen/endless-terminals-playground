FROM ubuntu:22.04

RUN apt-get update && apt-get install -y python3 python3-pip && pip3 install pytest

RUN mkdir -p /home/user/shortcuts /home/user/app && \
    chmod 0777 /home/user && \
    chmod 0777 /home/user/shortcuts && \
    chmod 0777 /home/user/app

RUN echo '{"debug": false, "timeout": 30}' > /home/user/app/settings.json && \
    chmod 0666 /home/user/app/settings.json
