FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sed \
    gawk \
    grep \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/webapp && chmod 0777 /home/user && chmod 0777 /home/user/webapp

RUN cat > /home/user/webapp/.env << 'EOF'
APP_NAME=webapp
DATABASE_HOST=db.internal.local
DATABASE_PORT=5432
DATABASE_USER=webapp_prod
DATABASE_PASSWORD=xK9#mP2$vL
REDIS_URL=redis://cache.internal.local:6379
LOG_LEVEL=info
EOF

RUN chmod 0666 /home/user/webapp/.env

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
