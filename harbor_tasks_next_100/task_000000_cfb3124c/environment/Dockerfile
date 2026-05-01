FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /var/data/logs /var/data/cache /var/data/uploads /var/data/backups /var/data/tmp

# Create files in backups (~2.1GB)
RUN dd if=/dev/urandom of=/var/data/backups/backup1.tar.gz bs=1M count=700 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/backups/backup2.tar.gz bs=1M count=700 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/backups/backup3.tar.gz bs=1M count=700 2>/dev/null

# Create files in cache (~1.2GB)
RUN dd if=/dev/urandom of=/var/data/cache/cache1.db bs=1M count=400 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/cache/cache2.db bs=1M count=400 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/cache/cache3.db bs=1M count=400 2>/dev/null

# Create files in logs (~500MB)
RUN dd if=/dev/urandom of=/var/data/logs/app.log bs=1M count=200 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/logs/error.log bs=1M count=150 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/logs/access.log bs=1M count=150 2>/dev/null

# Create files in uploads (~300MB)
RUN dd if=/dev/urandom of=/var/data/uploads/file1.zip bs=1M count=100 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/uploads/file2.zip bs=1M count=100 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/uploads/file3.zip bs=1M count=100 2>/dev/null

# Create files in tmp (~50MB)
RUN dd if=/dev/urandom of=/var/data/tmp/temp1.dat bs=1M count=25 2>/dev/null
RUN dd if=/dev/urandom of=/var/data/tmp/temp2.dat bs=1M count=25 2>/dev/null

# Set permissions so non-root user can read
RUN chmod -R 755 /var/data

WORKDIR /home/user

CMD ["/bin/bash"]
