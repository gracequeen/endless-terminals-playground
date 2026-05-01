FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    patch \
    diffutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/project/src && chmod -R 0777 /home/user

RUN cat > /home/user/project/src/config.py << 'EOF'
DEBUG = False
MAX_CONNECTIONS = 100
TIMEOUT = 30
LOG_LEVEL = "INFO"
EOF

RUN printf '%s\n' \
    '--- src/config.py	2024-01-15 10:00:00.000000000 +0000' \
    '+++ src/config.py	2024-01-15 10:05:00.000000000 +0000' \
    '@@ -1,4 +1,4 @@' \
    '-DEBUG = False' \
    '+DEBUG = True' \
    ' MAX_CONNECTIONS = 100' \
    ' TIMEOUT = 30' \
    ' LOG_LEVEL = "INFO"' \
    > /home/user/project/changes.patch

RUN chmod -R 0777 /home/user/project

WORKDIR /home/user

CMD ["/bin/bash"]
