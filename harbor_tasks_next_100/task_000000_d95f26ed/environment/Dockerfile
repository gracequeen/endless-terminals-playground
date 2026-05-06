FROM ubuntu:22.04
RUN sed -i "s|archive.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g; s|security.ubuntu.com|us-west-1.ec2.archive.ubuntu.com|g" /etc/apt/sources.list 2>/dev/null || true

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    lsof \
    psmisc \
    iproute2 \
    net-tools \
    procps \
    grep \
    gawk \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN useradd -m -d /home/user -s /bin/bash user

RUN cat > /entrypoint.sh << 'SCRIPT'
#!/bin/bash
su - user -c "python3 -c \"import socket; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('0.0.0.0', 8443)); s.listen(); exec('while True: pass')\" &"
sleep 1
exec "$@"
SCRIPT

RUN chmod +x /entrypoint.sh

WORKDIR /home/user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
