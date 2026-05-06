FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    tar \
    gzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /tmp/backup-2024-03-15/db && \
    mkdir -p /tmp/backup-2024-03-15/logs && \
    mkdir -p /tmp/backup-2024-03-15/uploads && \
    echo "-- users table dump" > /tmp/backup-2024-03-15/db/users.sql && \
    echo "-- orders table dump" > /tmp/backup-2024-03-15/db/orders.sql && \
    echo "-- products table dump" > /tmp/backup-2024-03-15/db/products.sql && \
    echo "access log content" > /tmp/backup-2024-03-15/logs/access.log && \
    echo "error log content" > /tmp/backup-2024-03-15/logs/error.log && \
    dd if=/dev/urandom of=/tmp/backup-2024-03-15/uploads/img001.jpg bs=1024 count=10 2>/dev/null && \
    dd if=/dev/urandom of=/tmp/backup-2024-03-15/uploads/img002.jpg bs=1024 count=10 2>/dev/null && \
    cd /tmp && tar -czvf /home/user/backup-2024-03-15.tar.gz backup-2024-03-15 && \
    rm -rf /tmp/backup-2024-03-15 && \
    chmod 644 /home/user/backup-2024-03-15.tar.gz

WORKDIR /home/user

CMD ["/bin/bash"]
