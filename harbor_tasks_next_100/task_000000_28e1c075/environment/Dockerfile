FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    gnupg \
    cron \
    tar \
    gzip \
    python3 \
    python3-pip \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN useradd -m -s /bin/bash user

RUN mkdir -p /home/user/infra /home/user/backups /home/user/appdata /home/user/.gnupg && \
    chmod 0777 /home/user /home/user/infra /home/user/backups /home/user/appdata && \
    chmod 700 /home/user/.gnupg && \
    chown -R user:user /home/user

RUN cat > /home/user/infra/setup_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/home/user/backups
SOURCE_DIR=/home/user/appdata
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"
tar -czf "$ARCHIVE" -C "$(dirname $SOURCE_DIR)" "$(basename $SOURCE_DIR)"
gpg --symmetric --cipher-algo AES256 --passphrase "backupkey2024" -o "${ARCHIVE}.gpg" "$ARCHIVE"
rm "$ARCHIVE"
EOF

RUN chmod +x /home/user/infra/setup_backup.sh && \
    chown user:user /home/user/infra/setup_backup.sh

RUN mkdir -p /home/user/appdata/documents /home/user/appdata/images /home/user/appdata/config /home/user/appdata/logs && \
    chown -R user:user /home/user/appdata

RUN dd if=/dev/urandom of=/home/user/appdata/documents/report1.txt bs=1M count=2 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/documents/report2.txt bs=1M count=2 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/documents/notes.txt bs=512K count=1 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/images/photo1.bin bs=1M count=3 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/images/photo2.bin bs=1M count=2 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/images/thumbnail.bin bs=256K count=1 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/config/settings.conf bs=128K count=1 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/config/database.conf bs=64K count=1 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/logs/app.log bs=1M count=2 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/logs/error.log bs=1M count=1 2>/dev/null && \
    dd if=/dev/urandom of=/home/user/appdata/data.bin bs=1M count=2 2>/dev/null && \
    chown -R user:user /home/user/appdata

RUN echo "backup_20240115_020000" > /tmp/corrupt1_name && \
    echo "backup_20240116_020000" > /tmp/corrupt2_name && \
    echo "backup_20240117_020000" > /tmp/corrupt3_name

RUN head -c 180 /dev/urandom > /home/user/backups/backup_20240115_020000.tar.gz.gpg && \
    head -c 210 /dev/urandom > /home/user/backups/backup_20240116_020000.tar.gz.gpg && \
    head -c 195 /dev/urandom > /home/user/backups/backup_20240117_020000.tar.gz.gpg && \
    chown user:user /home/user/backups/*.tar.gz.gpg

USER user
WORKDIR /home/user

RUN gpg --batch --passphrase "" --quick-gen-key "user@localhost" default default never 2>/dev/null || true

RUN echo "*/5 * * * * /home/user/infra/setup_backup.sh" | crontab -

RUN cat > /home/user/.cron_env << 'EOF'
# Simulated cron environment
# No TTY, minimal PATH, no DISPLAY, no GPG_TTY
PATH=/usr/bin:/bin
HOME=/home/user
SHELL=/bin/sh
EOF

USER root
RUN chown user:user /home/user/.cron_env && chmod 644 /home/user/.cron_env

USER user
CMD ["/bin/bash"]
