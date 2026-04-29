FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bash \
    gawk \
    sed \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/bin /home/user/project && \
    chmod 0777 /home/user && \
    chmod 0777 /home/user/bin && \
    chmod 0777 /home/user/project

RUN cat <<EOF > /home/user/project/.env.defaults
DATABASE_URL=postgres://localhost/dev
CACHE_TTL=300
DEBUG=false
API_KEY=default-key-123
EOF

RUN cat <<EOF > /home/user/project/.env.local
DEBUG=true
API_KEY=secret-prod-key-456
NEW_FEATURE=enabled
EOF

RUN chmod 644 /home/user/project/.env.defaults /home/user/project/.env.local

RUN useradd -m -d /home/user -s /bin/bash user && \
    chown -R user:user /home/user

USER user
WORKDIR /home/user

CMD ["/bin/bash"]
