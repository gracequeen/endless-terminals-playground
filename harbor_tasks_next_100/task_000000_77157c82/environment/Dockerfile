FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/logpipe/output && chmod -R 0777 /home/user/logpipe

RUN cat <<'EOF' > /home/user/logpipe/filter.py
#!/usr/bin/env python3
"""
Log filter script that routes container logs to different outputs
based on severity and source service.
"""

import re
import os
import yaml
from configparser import ConfigParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_LOG = os.path.join(SCRIPT_DIR, 'raw.log')
PATTERNS_CONF = os.path.join(SCRIPT_DIR, 'patterns.conf')
ROUTING_YAML = os.path.join(SCRIPT_DIR, 'routing.yaml')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')


def load_patterns(conf_path):
    """Load regex patterns from patterns.conf"""
    config = ConfigParser()
    config.read(conf_path)
    patterns = {}
    for section in config.sections():
        patterns[section] = {}
        for key, value in config.items(section):
            patterns[section][key.upper()] = value
    return patterns


def load_routing(yaml_path):
    """Load routing rules from routing.yaml"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def get_severity(line, patterns):
    """Extract severity level from log line using regex patterns."""
    severity_patterns = patterns.get('severity', {})
    for level, pattern in severity_patterns.items():
        if re.match(pattern, line):
            return level
    return None


def get_service(line, patterns):
    """Extract service name from log line."""
    service_patterns = patterns.get('service', {})
    for service_name, pattern in service_patterns.items():
        if re.search(pattern, line):
            return service_name
    return 'unknown'


def classify_line(line):
    """
    Classify a log line as structured (JSON-like) or plaintext.
    Returns 'structured' or 'plaintext'.
    """
    # Quick check for structured logs (JSON-like)
    if 'T' in line[:25] and ':' in line[:25]:
        return 'structured'
    # Check for actual JSON
    stripped = line.strip()
    if stripped.startswith('{') and stripped.endswith('}'):
        return 'structured'
    return 'plaintext'


def normalize_line(line):
    """Normalize a log line by stripping control characters."""
    # Remove leading non-printable characters
    result = []
    started = False
    for char in line:
        if started or char.isprintable() or char in '\t\n':
            result.append(char)
            started = True
    return ''.join(result)


def route_line(line, severity, service, routing_config):
    """Determine output file for a log line based on routing rules."""
    rules = routing_config.get('rules', [])
    for rule in rules:
        if rule.get('severity') == severity:
            return rule.get('output', 'default.log')
        if rule.get('service') == service:
            return rule.get('output', 'default.log')
    return routing_config.get('default_output', 'default.log')


def process_logs():
    """Main processing function."""
    patterns = load_patterns(PATTERNS_CONF)
    routing = load_routing(ROUTING_YAML)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Open output file handles
    output_files = {}

    with open(RAW_LOG, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue

            # Normalize the line
            normalized = normalize_line(line)

            # Classify line type
            line_type = classify_line(normalized)

            if line_type == 'structured':
                # Route to structured.log
                output_path = os.path.join(OUTPUT_DIR, 'structured.log')
                if output_path not in output_files:
                    output_files[output_path] = open(output_path, 'w')
                output_files[output_path].write(line + '\n')
                continue

            # Get severity and service
            severity = get_severity(normalized, patterns)
            service = get_service(normalized, patterns)

            # Route based on rules
            output_file = route_line(normalized, severity, service, routing)
            output_path = os.path.join(OUTPUT_DIR, output_file)

            if output_path not in output_files:
                output_files[output_path] = open(output_path, 'w')

            output_files[output_path].write(line + '\n')

    # Close all output files
    for f in output_files.values():
        f.close()


if __name__ == '__main__':
    process_logs()
EOF

RUN cat <<'EOF' > /home/user/logpipe/patterns.conf
[severity]
ERROR = ^.*\[ERROR\].*$
WARN = ^.*\[WARN\].*$
INFO = ^.*\[INFO\].*$
DEBUG = ^.*\[DEBUG\].*$

[service]
auth = service=auth-service
inventory = service=inventory-service
payment = service=payment-svc
EOF

RUN cat <<'EOF' > /home/user/logpipe/routing.yaml
# Log routing configuration
version: 1

rules:
  - severity: ERROR
    output: errors.log
    description: "Route all ERROR level logs to errors.log"

  - severity: WARN
    output: warnings.log
    description: "Route all WARN level logs to warnings.log"

  - severity: INFO
    output: info.log
    description: "Route INFO level logs"

  - severity: DEBUG
    output: debug.log
    description: "Route DEBUG level logs"

default_output: other.log

service_subdirs:
  enabled: false

retention:
  max_size_mb: 100
  max_age_days: 7
EOF

RUN cat <<'PYEOF' > /tmp/generate_logs.py
#!/usr/bin/env python3
import random
from datetime import datetime, timedelta

random.seed(42)

services = ['auth-service', 'inventory-service', 'payment-svc']
levels = ['DEBUG', 'INFO', 'WARN', 'ERROR']
level_weights = [0.3, 0.4, 0.15, 0.15]

auth_messages = [
    'user login successful',
    'failed login attempt',
    'session expired',
    'token refresh',
    'password reset requested',
    'MFA verification failed',
    'account locked',
    'permission denied',
]

inventory_messages = [
    'stock check completed',
    'low stock alert',
    'reorder triggered',
    'inventory sync started',
    'warehouse update received',
    'SKU not found',
    'batch update failed',
    'cache invalidated',
]

payment_messages = [
    'transaction initiated',
    'payment processed',
    'refund requested',
    'card validation failed',
    'transaction timeout',
    'gateway connection error',
    'insufficient funds',
    'fraud check triggered',
]

base_time = datetime(2024, 1, 15, 8, 0, 0)
lines = []

for i in range(520):
    timestamp = base_time + timedelta(seconds=i * 5 + random.randint(0, 3))
    service = random.choice(services)
    level = random.choices(levels, weights=level_weights)[0]

    if service == 'auth-service':
        msg = random.choice(auth_messages)
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{level}] {ts_str} service=auth-service msg="{msg}" user_id={random.randint(1000,9999)}'
    elif service == 'inventory-service':
        msg = random.choice(inventory_messages)
        ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        line = f'[{level}] {ts_str} service=inventory-service msg="{msg}" sku={random.randint(10000,99999)}'
    else:
        msg = random.choice(payment_messages)
        ts_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        line = f'{ts_str} [{level}] service=payment-svc msg="{msg}" txn_id={random.randint(1000,9999)}'

    lines.append(line)

for i in range(50):
    timestamp = base_time + timedelta(seconds=520 * 5 + i * 10)
    ts_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    msg = random.choice(['transaction failed', 'gateway timeout', 'payment declined', 'processing error'])
    line = f'{ts_str} [ERROR] service=payment-svc msg="{msg}" txn_id={random.randint(1000,9999)} error_code={random.randint(400,599)}'
    lines.append(line)

for i in range(5):
    timestamp = base_time + timedelta(seconds=600 * 5 + i * 20)
    ts_str = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    line = '{"timestamp": "' + ts_str + '", "level": "DEBUG", "service": "metrics-collector", "data": {"cpu": ' + str(random.randint(10,90)) + ', "memory": ' + str(random.randint(20,80)) + '}}'
    lines.append(line)

random.shuffle(lines)

with open('/home/user/logpipe/raw.log', 'w') as f:
    for line in lines:
        f.write(line + '\n')

print(f"Generated {len(lines)} log lines")
PYEOF

RUN python3 /tmp/generate_logs.py && rm /tmp/generate_logs.py

RUN cd /home/user/logpipe && python3 filter.py

RUN chmod -R 0777 /home/user/logpipe

WORKDIR /home/user
