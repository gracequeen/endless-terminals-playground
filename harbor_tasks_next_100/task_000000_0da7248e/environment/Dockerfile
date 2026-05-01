FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    tar \
    gzip \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/backups /home/user/restore

RUN mkdir -p /tmp/archive_build/var/www/html /tmp/archive_build/var/db /tmp/archive_build/var/log

RUN echo '<!DOCTYPE html><html><head><title>Site</title></head><body><h1>Welcome</h1></body></html>' > /tmp/archive_build/var/www/html/index.html

RUN echo 'body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }' > /tmp/archive_build/var/www/html/style.css

RUN cat <<'EOF' > /tmp/archive_build/var/db/dump.sql
-- PostgreSQL dump
-- Database: mysite
-- Dumped by pg_dump version 14.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email) VALUES ('admin', 'admin@example.com');
INSERT INTO users (username, email) VALUES ('user1', 'user1@example.com');

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO posts (user_id, title, content) VALUES (1, 'Welcome', 'Welcome to our site!');

-- Dump complete
EOF

RUN echo '192.168.1.100 - - [15/Mar/2024:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 1234' > /tmp/archive_build/var/log/access.log && \
    echo '192.168.1.101 - - [15/Mar/2024:10:16:45 +0000] "GET /style.css HTTP/1.1" 200 567' >> /tmp/archive_build/var/log/access.log

RUN cd /tmp/archive_build && tar -czvf /home/user/backups/site-2024-03-15.tar.gz var/

RUN rm -rf /tmp/archive_build

RUN chmod 0777 /home/user && \
    chmod 0777 /home/user/backups && \
    chmod 0777 /home/user/restore && \
    chmod 0644 /home/user/backups/site-2024-03-15.tar.gz

RUN useradd -m -d /home/user -s /bin/bash user || true

WORKDIR /home/user

CMD ["/bin/bash"]
