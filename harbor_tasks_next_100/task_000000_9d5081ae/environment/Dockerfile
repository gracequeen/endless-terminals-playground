FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    cron \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/scripts && chmod 0777 /home/user && chmod 0777 /home/user/scripts

RUN mkdir -p /var/spool/cron/crontabs && chmod 0777 /var/spool/cron/crontabs

RUN cat <<'EOF' > /var/spool/cron/crontabs/user
# m h dom mon dow command
0 2 * * * /home/user/scripts/backup.sh
30 6 * * 1 /home/user/scripts/weekly_report.sh
*/15 * * * * /home/user/scripts/healthcheck.sh
EOF

RUN chmod 0666 /var/spool/cron/crontabs/user

RUN useradd -m -d /home/user -s /bin/bash user && chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
