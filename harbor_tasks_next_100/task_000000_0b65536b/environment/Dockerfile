FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user/scanner && chmod 0777 /home/user && chmod 0777 /home/user/scanner

RUN cat <<'EOF' > /home/user/scanner/scan.yaml
scanner:
  name: edge-node-scan
  version: 2.1

targets:
  network: 10.0.1.0/24
  ports: [22, 443, 8883]
  protocol: tcp

options:
  timeout: 30
  retries: 3
  verbose: false
EOF

RUN chmod 0666 /home/user/scanner/scan.yaml

WORKDIR /home/user

CMD ["/bin/bash"]
