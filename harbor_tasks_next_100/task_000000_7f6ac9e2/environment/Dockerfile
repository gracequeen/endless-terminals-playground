FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    jq \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/alerts && chmod 0777 /home/user && chmod 0777 /home/user/alerts

RUN cat <<'EOF' > /home/user/alerts/incidents.json
{
  "incidents": [
    {"service": "payment-gateway", "status": "critical", "since": "2024-01-15T08:30:00Z"},
    {"service": "auth-service", "status": "warning", "since": "2024-01-15T09:00:00Z"},
    {"service": "cdn-edge-03", "status": "critical", "since": "2024-01-15T07:45:00Z"},
    {"service": "metrics-collector", "status": "ok", "since": "2024-01-15T06:00:00Z"},
    {"service": "api-gateway", "status": "critical", "since": "2024-01-15T08:00:00Z"},
    {"service": "search-indexer", "status": "warning", "since": "2024-01-15T10:00:00Z"}
  ]
}
EOF

RUN chmod 0644 /home/user/alerts/incidents.json

WORKDIR /home/user

CMD ["/bin/bash"]
