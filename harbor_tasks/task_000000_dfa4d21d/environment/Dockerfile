FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    tar \
    gzip \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/backups /home/user/restored && \
    chmod 0777 /home/user /home/user/backups /home/user/restored

WORKDIR /tmp/archive_build

RUN mkdir -p etc/nginx etc/systemd/system var/log/nginx var/log/syslog usr/local/bin

RUN cat > etc/nginx/nginx.conf << 'EOF'
worker_processes auto;
events { worker_connections 1024; }
http {
    server {
        listen 80;
        server_name legacy.internal;
        root /var/www/legacy;
    }
}
EOF

RUN cat > etc/systemd/system/myapp.service << 'EOF'
[Unit]
Description=My Application Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/myapp
Restart=always

[Install]
WantedBy=multi-user.target
EOF

RUN cat > etc/systemd/system/backup.service << 'EOF'
[Unit]
Description=Backup Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh

[Install]
WantedBy=multi-user.target
EOF

RUN cat > etc/systemd/system/backup.timer << 'EOF'
[Unit]
Description=Daily Backup Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

RUN for i in $(seq 1 10); do echo "Log entry $i - $(date)" > var/log/nginx/access_$i.log; done && \
    for i in $(seq 1 10); do echo "Error log entry $i" > var/log/nginx/error_$i.log; done && \
    for i in $(seq 1 5); do echo "Syslog entry $i" > var/log/syslog/messages_$i.log; done

RUN cat > usr/local/bin/myapp << 'EOF'
#!/bin/bash
echo "My Application Running"
EOF

RUN cat > usr/local/bin/backup.sh << 'EOF'
#!/bin/bash
echo "Running backup..."
tar -czf /backups/backup-$(date +%Y%m%d).tar.gz /data
EOF

RUN cat > usr/local/bin/cleanup.sh << 'EOF'
#!/bin/bash
find /var/log -name "*.log" -mtime +30 -delete
EOF

RUN cat > usr/local/bin/monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "System status: OK"
    sleep 60
done
EOF

RUN cat > usr/local/bin/deploy.sh << 'EOF'
#!/bin/bash
echo "Deploying application..."
cd /app && git pull && systemctl restart myapp
EOF

RUN for i in $(seq 1 10); do echo "Utility script $i" > usr/local/bin/util_$i.sh; done

RUN chmod +x usr/local/bin/*

RUN tar -czvf /home/user/backups/services-2024.tar.gz etc var usr

RUN chmod 644 /home/user/backups/services-2024.tar.gz

WORKDIR /home/user

RUN rm -rf /tmp/archive_build

USER root
