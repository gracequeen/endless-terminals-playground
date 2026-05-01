FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    procps \
    sudo \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN useradd -m -d /home/user -s /bin/bash user

RUN echo "user ALL=(ALL) NOPASSWD: /usr/sbin/sysctl, /usr/sbin/sysctl *" >> /etc/sudoers.d/user-sysctl && \
    chmod 0440 /etc/sudoers.d/user-sysctl

RUN chmod 0777 /etc/sysctl.d

RUN test -f /etc/sysctl.conf || touch /etc/sysctl.conf

ENV HOME=/home/user
WORKDIR /home/user

USER user

CMD ["/bin/bash"]
