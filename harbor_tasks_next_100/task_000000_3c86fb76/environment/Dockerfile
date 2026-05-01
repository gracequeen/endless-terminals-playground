FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN cat <<EOF > /home/user/inventory.json
[
  {"instance_id": "i-0a1b2c3d4e5f67890", "type": "t3.medium", "az": "us-east-1a"},
  {"instance_id": "i-1b2c3d4e5f678901a", "type": "t3.large", "az": "us-east-1b"},
  {"instance_id": "i-2c3d4e5f678901a2b", "type": "t3.small", "az": "us-east-1a"}
]
EOF

RUN chmod 644 /home/user/inventory.json

WORKDIR /home/user

CMD ["/bin/bash"]
