FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/app && chmod 0777 /home/user && chmod 0777 /home/user/app

RUN cat <<'EOF' > /home/user/app/docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass hunter2
    ports:
      - "6379:6379"
  app:
    image: myapp:latest
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=hunter2
    depends_on:
      - redis
EOF

RUN chmod 0666 /home/user/app/docker-compose.yml
