FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    tzdata \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN rm -f /etc/localtime && ln -s /usr/share/zoneinfo/UTC /etc/localtime

RUN echo "UTC" > /etc/timezone

RUN chmod 777 /etc/localtime && chmod 666 /etc/timezone

RUN chmod 777 /etc

RUN useradd -m -d /home/user -s /bin/bash user

ENV HOME=/home/user
WORKDIR /home/user

USER user

CMD ["/bin/bash"]
