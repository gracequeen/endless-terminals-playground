FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN useradd -m -s /bin/bash user

RUN mkdir -p /home/user/webapp && \
    chown user:user /home/user/webapp && \
    chmod 755 /home/user/webapp

RUN cat <<EOF > /home/user/webapp/.env
DB_PASSWORD=hunter2
API_KEY=sk-test-12345
EOF

RUN chown user:user /home/user/webapp/.env && \
    chmod 644 /home/user/webapp/.env

RUN chmod 0777 /home/user

USER user
WORKDIR /home/user
