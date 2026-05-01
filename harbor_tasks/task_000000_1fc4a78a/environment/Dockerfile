FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    findutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/monitoring/alerts/platform \
    && mkdir -p /home/user/monitoring/alerts/infra \
    && mkdir -p /home/user/monitoring/alerts/app

RUN cat <<'EOF' > /home/user/monitoring/validate_alerts.sh
#!/bin/bash
find /home/user/monitoring/alerts -maxdepth 1 -name "*.yaml" | xargs python3 /home/user/monitoring/check_yaml.py
EOF

RUN chmod +x /home/user/monitoring/validate_alerts.sh

RUN cat <<'EOF' > /home/user/monitoring/check_yaml.py
#!/usr/bin/env python3
import sys
import yaml

for path in sys.argv[1:]:
    try:
        with open(path) as f:
            yaml.safe_load(f)
        print(f"OK: {path}")
    except yaml.YAMLError as e:
        print(f"ERROR: {path}: {e}")
    except Exception as e:
        print(f"ERROR: {path}: {e}")
EOF

RUN chmod +x /home/user/monitoring/check_yaml.py

RUN cat <<'EOF' > /home/user/monitoring/alerts/platform/cpu_high.yaml
name: cpu_high
description: Alert when CPU usage exceeds threshold
threshold: 90
severity: warning
team: platform
EOF

RUN cat <<'EOF' > /home/user/monitoring/alerts/platform/memory_critical.yaml
name: memory_critical
description: Alert when memory usage is critical
threshold: 95
severity: critical
team: platform
EOF

RUN cat <<'EOF' > /home/user/monitoring/alerts/infra/disk_full.yaml
name: disk_full
description: Alert when disk is nearly full
threshold: 85
severity: warning
threshold: 90
team: infra
EOF

RUN cat <<'EOF' > /home/user/monitoring/alerts/infra/network_down.yaml
name: network_down
description: Alert when network connectivity is lost
timeout: 30
severity: critical
team: infra
EOF

RUN cat <<'EOF' > /home/user/monitoring/alerts/app/latency_spike.yaml
name: latency_spike
description: Alert when latency exceeds acceptable levels
threshold_ms: 500
severity: warning
team: app
EOF

RUN cat <<'EOF' > /home/user/monitoring/alerts/app/error_rate.yaml
name: error_rate
severity: warning
description: Alert when error rate is too high
severity: critical
threshold_percent: 5
team: app
EOF

RUN cat <<'EOF' > /home/user/monitoring/alerts/app/queue_depth.yaml
name: queue_depth
description: Alert when message queue depth is too high
threshold: 1000
severity: warning
team: app
EOF

RUN chmod -R 0777 /home/user/monitoring

WORKDIR /home/user

CMD ["/bin/bash"]
