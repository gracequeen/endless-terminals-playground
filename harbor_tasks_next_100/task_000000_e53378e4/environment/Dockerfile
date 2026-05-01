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

RUN mkdir -p /home/user/etl/logs && \
    chown -R user:user /home/user/etl && \
    chmod -R 0777 /home/user/etl

RUN cat > /home/user/etl/daily_ingest.sh << 'EOF'
#!/bin/bash
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting daily ingest"
echo "Processing data..."
echo "Ingest complete"
EOF

RUN chmod +x /home/user/etl/daily_ingest.sh && \
    chown user:user /home/user/etl/daily_ingest.sh

RUN chmod 0777 /home/user

RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash
service cron start
exec "$@"
EOF

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["su", "-", "user"]

WORKDIR /home/user

USER root
