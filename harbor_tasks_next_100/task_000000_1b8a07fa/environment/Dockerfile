FROM ubuntu:22.04
RUN sed -i "s|archive.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g; s|security.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g" /etc/apt/sources.list 2>/dev/null || true

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/pipeline && chmod 0777 /home/user && chmod 0777 /home/user/pipeline

RUN cat <<EOF > /home/user/pipeline/optim.cfg
[general]
log_level = info
output_dir = /tmp/optim_out

[solver]
algorithm = simplex
timeout_sec = 30
max_iterations = 10000

[cache]
enabled = true
path = /var/cache/optim
EOF

RUN chmod 0666 /home/user/pipeline/optim.cfg
