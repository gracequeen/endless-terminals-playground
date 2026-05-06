FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    sqlite3 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN sqlite3 /home/user/artifacts.db "CREATE TABLE packages (id INTEGER PRIMARY KEY, name TEXT NOT NULL, version TEXT NOT NULL, checksum TEXT, created_at TEXT);" && \
    sqlite3 /home/user/artifacts.db "INSERT INTO packages (name, version, checksum, created_at) VALUES ('numpy', '1.24.0', 'abc123def456', '2024-01-15 10:30:00');" && \
    sqlite3 /home/user/artifacts.db "INSERT INTO packages (name, version, checksum, created_at) VALUES ('pandas', '2.0.1', 'def789ghi012', '2024-01-16 14:22:00');" && \
    sqlite3 /home/user/artifacts.db "INSERT INTO packages (name, version, checksum, created_at) VALUES ('requests', '2.31.0', 'jkl345mno678', '2024-01-17 09:15:00');" && \
    sqlite3 /home/user/artifacts.db "INSERT INTO packages (name, version, checksum, created_at) VALUES ('flask', '3.0.0', NULL, '2024-01-18 16:45:00');" && \
    sqlite3 /home/user/artifacts.db "INSERT INTO packages (name, version, checksum, created_at) VALUES ('django', '4.2.7', 'pqr901stu234', '2024-01-19 11:00:00');" && \
    chmod 0666 /home/user/artifacts.db

WORKDIR /home/user

CMD ["/bin/bash"]
