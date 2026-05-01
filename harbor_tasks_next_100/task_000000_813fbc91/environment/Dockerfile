FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/inventory && chmod 0777 /home/user && chmod 0777 /home/user/inventory

RUN cat <<'EOF' > /home/user/inventory/switches.json
[
  {"hostname": "sw-core-01", "status": "online", "ip": "10.0.1.1"},
  {"hostname": "sw-dist-03", "status": "offline", "ip": "10.0.2.3"},
  {"hostname": "sw-access-17", "status": "online", "ip": "10.0.3.17"},
  {"hostname": "sw-edge-42", "status": "offline", "ip": "10.0.4.42"},
  {"hostname": "sw-access-09", "status": "offline", "ip": "10.0.3.9"}
]
EOF

RUN chmod 0644 /home/user/inventory/switches.json

WORKDIR /home/user
