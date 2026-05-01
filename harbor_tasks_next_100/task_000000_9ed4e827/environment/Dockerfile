FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/experiments && chmod 0777 /home/user && chmod 0777 /home/user/experiments

RUN cat <<'EOF' > /home/user/experiments/run_047.json
{"run_id": "047", "learning_rate": 0.001, "batch_size": 32, "epochs": 50, "dropout": 0.2, "optimizer": "adam"}
EOF

RUN chmod 0644 /home/user/experiments/run_047.json

WORKDIR /home/user
