FROM ubuntu:22.04
RUN sed -i "s|archive.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g; s|security.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g" /etc/apt/sources.list 2>/dev/null || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /etc/cron.d

RUN cat <<EOF > /etc/cron.d/logrotate-daily
# Daily log rotation
0 2 * * * root /usr/sbin/logrotate /etc/logrotate.conf
EOF

RUN chmod 0666 /etc/cron.d/logrotate-daily

RUN useradd -m -d /home/user -s /bin/bash user

ENV HOME=/home/user
WORKDIR /home/user

USER user

CMD ["/bin/bash"]
