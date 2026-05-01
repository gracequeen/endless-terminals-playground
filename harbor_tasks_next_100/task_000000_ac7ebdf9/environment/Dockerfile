FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    cron \
    python3 \
    python3-pip \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN useradd -m -s /bin/bash user

RUN mkdir -p /home/user/scripts /home/user/logs && \
    chown -R user:user /home/user && \
    chmod 0777 /home/user && \
    chmod 0755 /home/user/scripts && \
    chmod 0755 /home/user/logs

RUN cat <<'EOF' > /home/user/scripts/metrics_push.sh
#!/bin/bash
echo "$(date -Iseconds) metrics pushed" >> /home/user/logs/metrics.log
EOF

RUN chmod +x /home/user/scripts/metrics_push.sh && \
    chown user:user /home/user/scripts/metrics_push.sh

RUN touch /var/spool/cron/crontabs/user && \
    chown user:crontab /var/spool/cron/crontabs/user && \
    chmod 600 /var/spool/cron/crontabs/user

RUN cat <<'EOF' > /entrypoint.sh
#!/bin/bash
cron
exec "$@"
EOF

RUN chmod +x /entrypoint.sh

WORKDIR /home/user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
