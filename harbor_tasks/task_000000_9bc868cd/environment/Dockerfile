FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/infra && chmod 0777 /home/user && chmod 0755 /home/user/infra

RUN cat <<'EOF' > /home/user/infra/services.json
{
  "services": [
    {"name": "auth-api", "status": "healthy", "port": 8080},
    {"name": "payment-gateway", "status": "degraded", "port": 8081},
    {"name": "user-db", "status": "healthy", "port": 5432},
    {"name": "cache-redis", "status": "degraded", "port": 6379},
    {"name": "notification-svc", "status": "healthy", "port": 8082},
    {"name": "inventory-api", "status": "degraded", "port": 8083}
  ]
}
EOF

RUN chmod 0644 /home/user/infra/services.json

WORKDIR /home/user
