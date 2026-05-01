FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gnupg \
    tar \
    gzip \
    python3 \
    python3-pip \
    file \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/backups && chmod 0777 /home/user && chmod 0777 /home/user/backups

RUN printf 'hunter2-old-key' > /home/user/.old_backup_key && \
    printf 'correcthorse-new-key' > /home/user/.new_backup_key && \
    chmod 644 /home/user/.old_backup_key && \
    chmod 644 /home/user/.new_backup_key

RUN mkdir -p /tmp/backup_prep && \
    echo "-- PostgreSQL database dump\n-- Dumped from database version 15.2\n-- Started on 2024-01-15 02:00:00 UTC\n\nSET statement_timeout = 0;\nSET lock_timeout = 0;\nSET client_encoding = 'UTF8';\n\nCREATE TABLE users (\n    id SERIAL PRIMARY KEY,\n    username VARCHAR(255) NOT NULL,\n    email VARCHAR(255) NOT NULL,\n    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);\n\nINSERT INTO users (username, email) VALUES\n    ('alice', 'alice@example.com'),\n    ('bob', 'bob@example.com'),\n    ('charlie', 'charlie@example.com');\n\n-- Completed on 2024-01-15 02:00:01 UTC\n-- PostgreSQL database dump complete" > /tmp/backup_prep/dump.sql && \
    cd /tmp/backup_prep && tar -czf /tmp/backup_prep/db-2024-01-15.tar.gz dump.sql && \
    gpg --batch --yes --passphrase "hunter2-old-key" --symmetric --cipher-algo AES256 -o /home/user/backups/db-2024-01-15.tar.gz.gpg /tmp/backup_prep/db-2024-01-15.tar.gz && \
    rm -rf /tmp/backup_prep

RUN chmod 644 /home/user/backups/db-2024-01-15.tar.gz.gpg

WORKDIR /home/user

CMD ["/bin/bash"]
