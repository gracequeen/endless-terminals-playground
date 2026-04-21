FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sed \
    gawk \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install pytest pyyaml toml tomli tomli_w

# Create home directory with appropriate permissions
RUN mkdir -p /home/user && chmod 0777 /home/user

# Create monitoring directory with appropriate permissions
RUN mkdir -p /etc/monitoring && chmod 0777 /etc/monitoring

# Create alerts.yaml file
RUN cat <<'EOF' > /etc/monitoring/alerts.yaml
# Prometheus alerting rules
groups:
  - name: service_alerts
    rules:
      - alert: HighLatency
        expr: http_request_duration_seconds > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected on {{ $labels.instance }}"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighMemoryUsage
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage critical on {{ $labels.instance }}"
EOF

# Create uptime.toml file
RUN cat <<'EOF' > /etc/monitoring/uptime.toml
# Uptime checker daemon configuration

[global]
check_interval = 60
retry_count = 3
log_level = "info"

[[endpoints]]
name = "api-gateway"
url = "https://api.example.com/health"
expected_status = 204
method = "GET"

[[endpoints]]
name = "auth-service"
url = "https://auth.internal.example.com/ping"
expected_status = 200
critical = false

[[endpoints]]
name = "frontend"
url = "https://www.example.com"
expected_status = 200
EOF

# Set permissions on config files
RUN chmod 0666 /etc/monitoring/alerts.yaml && chmod 0666 /etc/monitoring/uptime.toml

# Set working directory
WORKDIR /home/user
