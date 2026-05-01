FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    redis-server \
    redis-tools \
    iproute2 \
    procps \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /etc/redis && chmod 0755 /etc/redis

RUN mkdir -p /var/lib/redis && chmod 0777 /var/lib/redis

RUN cat > /etc/redis/redis.conf << 'EOF'
# Redis configuration file

# Accept connections on the specified port
port 6379

# Bind to all interfaces
bind 0.0.0.0

# Set the working directory
dir /var/lib/redis

# Daemonize Redis (run in background)
daemonize yes

# Specify the log file
logfile /var/lib/redis/redis.log

# Set the database filename
dbfilename dump.rdb

# Disable protected mode for local testing
protected-mode no
EOF

RUN chmod 0644 /etc/redis/redis.conf

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user && \
    chown -R user:user /var/lib/redis

ENV HOME=/home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
