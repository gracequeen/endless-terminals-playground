FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN useradd -m -s /bin/bash user

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /var/data/archives \
    /var/data/logs \
    /var/data/dumps \
    /var/data/media \
    /var/data/exports \
    /var/data/config \
    /var/data/cache \
    /var/data/temp \
    /var/data/backups \
    /var/data/reports

# Create the 5 largest files with exact sizes
RUN dd if=/dev/zero of=/var/data/archives/backup_2024_q1.tar.gz bs=1000000 count=512 2>/dev/null
RUN dd if=/dev/zero of=/var/data/logs/access_full.log bs=1048576 count=256 2>/dev/null
RUN dd if=/dev/zero of=/var/data/dumps/postgres_main.sql bs=1048576 count=128 2>/dev/null
RUN dd if=/dev/zero of=/var/data/media/training_video.mp4 bs=1048576 count=100 2>/dev/null
RUN dd if=/dev/zero of=/var/data/exports/customer_data.csv bs=1048576 count=50 2>/dev/null

# Create additional smaller files to reach ~50 files total
RUN dd if=/dev/zero of=/var/data/logs/error.log bs=1024 count=5000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/logs/debug.log bs=1024 count=2000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/logs/app.log bs=1024 count=1500 2>/dev/null
RUN dd if=/dev/zero of=/var/data/logs/system.log bs=1024 count=1000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/logs/audit.log bs=1024 count=500 2>/dev/null

RUN dd if=/dev/zero of=/var/data/archives/backup_2023_q4.tar.gz bs=1024 count=10000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/archives/backup_2023_q3.tar.gz bs=1024 count=8000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/archives/old_data.zip bs=1024 count=5000 2>/dev/null

RUN dd if=/dev/zero of=/var/data/dumps/mysql_backup.sql bs=1024 count=15000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/dumps/redis_dump.rdb bs=1024 count=3000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/dumps/mongo_export.json bs=1024 count=2500 2>/dev/null

RUN dd if=/dev/zero of=/var/data/media/presentation.pptx bs=1024 count=8000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/media/logo.png bs=1024 count=500 2>/dev/null
RUN dd if=/dev/zero of=/var/data/media/banner.jpg bs=1024 count=300 2>/dev/null
RUN dd if=/dev/zero of=/var/data/media/icon.svg bs=1024 count=50 2>/dev/null

RUN dd if=/dev/zero of=/var/data/exports/sales_report.csv bs=1024 count=7000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/exports/inventory.csv bs=1024 count=4000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/exports/users.csv bs=1024 count=2000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/exports/orders.csv bs=1024 count=1500 2>/dev/null

RUN dd if=/dev/zero of=/var/data/config/app.conf bs=1024 count=10 2>/dev/null
RUN dd if=/dev/zero of=/var/data/config/database.yml bs=1024 count=5 2>/dev/null
RUN dd if=/dev/zero of=/var/data/config/nginx.conf bs=1024 count=8 2>/dev/null
RUN dd if=/dev/zero of=/var/data/config/redis.conf bs=1024 count=6 2>/dev/null
RUN dd if=/dev/zero of=/var/data/config/settings.json bs=1024 count=3 2>/dev/null

RUN dd if=/dev/zero of=/var/data/cache/session_cache.dat bs=1024 count=5000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/cache/query_cache.dat bs=1024 count=3000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/cache/image_cache.dat bs=1024 count=2000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/cache/api_cache.dat bs=1024 count=1000 2>/dev/null

RUN dd if=/dev/zero of=/var/data/temp/upload_001.tmp bs=1024 count=500 2>/dev/null
RUN dd if=/dev/zero of=/var/data/temp/upload_002.tmp bs=1024 count=400 2>/dev/null
RUN dd if=/dev/zero of=/var/data/temp/processing.tmp bs=1024 count=300 2>/dev/null
RUN dd if=/dev/zero of=/var/data/temp/download.tmp bs=1024 count=200 2>/dev/null

RUN dd if=/dev/zero of=/var/data/backups/daily_2024_01_15.bak bs=1024 count=10000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/backups/daily_2024_01_14.bak bs=1024 count=9500 2>/dev/null
RUN dd if=/dev/zero of=/var/data/backups/daily_2024_01_13.bak bs=1024 count=9000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/backups/weekly_2024_01.bak bs=1024 count=15000 2>/dev/null

RUN dd if=/dev/zero of=/var/data/reports/q1_summary.pdf bs=1024 count=2000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/reports/q2_summary.pdf bs=1024 count=1800 2>/dev/null
RUN dd if=/dev/zero of=/var/data/reports/q3_summary.pdf bs=1024 count=1600 2>/dev/null
RUN dd if=/dev/zero of=/var/data/reports/q4_summary.pdf bs=1024 count=1400 2>/dev/null
RUN dd if=/dev/zero of=/var/data/reports/annual_report.pdf bs=1024 count=5000 2>/dev/null
RUN dd if=/dev/zero of=/var/data/reports/metrics.xlsx bs=1024 count=3000 2>/dev/null

# Set permissions for /var/data
RUN chmod -R 755 /var/data && chown -R root:root /var/data

# Create the audit directory for the user
RUN mkdir -p /home/user/audit && chmod 0777 /home/user/audit && chown user:user /home/user/audit

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
