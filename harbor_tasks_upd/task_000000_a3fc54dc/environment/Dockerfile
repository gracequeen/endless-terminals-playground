FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/monitor/config && chmod -R 0777 /home/user

RUN cat <<'EOF' > /home/user/monitor/config/manifest.json
{
    "services": {
        "metrics-api": {
            "schema": "schema_metrics.json",
            "endpoint": "http://metrics.internal:8080/api/v1",
            "interval": 30
        },
        "logs-collector": {
            "schema": "schema_logs.json",
            "endpoint": "http://logs.internal:8081/api/v1",
            "interval": 60
        },
        "traces-exporter": {
            "schema": "schema_traces.json",
            "endpoint": "http://traces.internal:8082/api/v1",
            "interval": 45
        }
    },
    "version": "2.1.0",
    "last_updated": "2024-01-15T10:30:00Z"
}
EOF

RUN cat <<'EOF' > /home/user/monitor/config/schema_metrics.json
{
    "type": "object",
    "properties": {
        "cpu_usage": {"type": "number", "minimum": 0, "maximum": 100},
        "memory_usage": {"type": "number", "minimum": 0, "maximum": 100},
        "disk_io": {"type": "number", "minimum": 0},
        "network_throughput": {"type": "number", "minimum": 0},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["cpu_usage", "memory_usage", "timestamp"]
}
EOF

RUN cat <<'EOF' > /home/user/monitor/config/schema_logs.json
{
    "type": "object",
    "properties": {
        "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]},
        "message": {"type": "string", "maxLength": 4096},
        "source": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "retention_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30}
    },
    "required": ["level", "message", "timestamp"]
}
EOF

RUN cat <<'EOF' > /home/user/monitor/config/schema_traces.json
{
    "type": "object",
    "properties": {
        "trace_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
        "span_id": {"type": "string", "pattern": "^[a-f0-9]{16}$"},
        "parent_span_id": {"type": "string", "pattern": "^[a-f0-9]{16}$"},
        "operation_name": {"type": "string"},
        "duration_ms": {"type": "number", "minimum": 0},
        "status": {"type": "string", "enum": ["OK", "ERROR", "TIMEOUT"]},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["trace_id", "span_id", "operation_name", "timestamp"]
}
EOF

RUN cd /home/user/monitor/config && \
    MANIFEST_HASH=$(sha256sum manifest.json | awk '{print $1}') && \
    METRICS_HASH=$(sha256sum schema_metrics.json | awk '{print $1}') && \
    LOGS_ACTUAL_HASH=$(sha256sum schema_logs.json | awk '{print $1}') && \
    TRACES_HASH=$(sha256sum schema_traces.json | awk '{print $1}') && \
    printf 'SHA256 (manifest.json) = %s\n' "$MANIFEST_HASH" > checksums.sha256 && \
    printf 'SHA256 (schema_metrics.json) = %s\n' "$METRICS_HASH" >> checksums.sha256 && \
    printf 'SHA256 (schema_logs.json) = c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6\n' >> checksums.sha256 && \
    printf 'SHA256 (schema_traces.json) = %s \n' "$TRACES_HASH" >> checksums.sha256

RUN cat <<'DASHEOF' > /home/user/monitor/dashboard.py
#!/usr/bin/env python3
"""
Dashboard script that pulls metrics from upstream services and renders a summary.
Performs checksum verification on startup to ensure config integrity.
"""

import os
import re
import sys
import json
import hashlib

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config')
CHECKSUMS_FILE = os.path.join(CONFIG_DIR, 'checksums.sha256')
MANIFEST_FILE = os.path.join(CONFIG_DIR, 'manifest.json')


def verify_checksums(checksum_file, config_dir):
    """
    Verify SHA256 checksums of config files.
    Reads BSD-style format: SHA256 (filename) = hash
    """
    if not os.path.exists(checksum_file):
        print("Error: Checksums file not found")
        return False

    with open(checksum_file, 'r') as f:
        for line in f:
            line = line.strip('\n')
            if not line:
                continue

            # Parse BSD-style checksum format
            match = re.match(r'SHA256 \(([^)]+)\) = (.+)', line)
            if match:
                filename, expected = match.groups()
                # BUG: .+ captures trailing whitespace, but we only strip newline above
                expected = expected.rstrip('\n')

                filepath = os.path.join(config_dir, filename)
                if not os.path.exists(filepath):
                    print(f"Integrity error: {filename} not found")
                    return False

                with open(filepath, 'rb') as file_to_check:
                    actual = hashlib.sha256(file_to_check.read()).hexdigest()

                if actual != expected:
                    print(f"Integrity error: {filename} checksum mismatch")
                    return False

    return True


def load_manifest(manifest_file):
    """Load and parse the service manifest."""
    with open(manifest_file, 'r') as f:
        return json.load(f)


def fetch_metrics(service_name, service_config):
    """
    Simulate fetching metrics from an upstream service.
    In production, this would make HTTP requests to the service endpoints.
    """
    # Simulated metrics data
    metrics = {
        'metrics-api': {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'disk_io': 1250,
            'network_throughput': 8500,
            'status': 'healthy'
        },
        'logs-collector': {
            'ingestion_rate': 15000,
            'buffer_usage': 23.5,
            'dropped_logs': 0,
            'status': 'healthy'
        },
        'traces-exporter': {
            'traces_per_second': 850,
            'export_latency_ms': 12.3,
            'queue_depth': 45,
            'status': 'healthy'
        }
    }
    return metrics.get(service_name, {})


def render_summary(manifest):
    """Render the metrics summary for all services."""
    print("=" * 60)
    print("                    Metrics Summary")
    print("=" * 60)
    print()

    services = manifest.get('services', {})

    for service_name, service_config in services.items():
        metrics = fetch_metrics(service_name, service_config)

        print(f"Service: {service_name}")
        print(f"  Endpoint: {service_config.get('endpoint', 'N/A')}")
        print(f"  Poll Interval: {service_config.get('interval', 'N/A')}s")
        print(f"  Status: {metrics.get('status', 'unknown')}")

        # Print service-specific metrics
        for key, value in metrics.items():
            if key != 'status':
                print(f"  {key}: {value}")

        print()

    print("=" * 60)
    print(f"Manifest Version: {manifest.get('version', 'unknown')}")
    print(f"Last Updated: {manifest.get('last_updated', 'unknown')}")
    print("=" * 60)


def main():
    """Main entry point for the dashboard."""
    print("Starting dashboard...")
    print("Verifying configuration integrity...")

    # Verify checksums before loading config
    if not verify_checksums(CHECKSUMS_FILE, CONFIG_DIR):
        print("\nConfiguration integrity check failed!")
        print("Please verify your config files and checksums.")
        sys.exit(1)

    print("Integrity check passed.\n")

    # Load manifest and render summary
    try:
        manifest = load_manifest(MANIFEST_FILE)
        render_summary(manifest)
    except Exception as e:
        print(f"Error loading manifest: {e}")
        sys.exit(1)

    return 0


if __name__ == '__main__':
    sys.exit(main())
DASHEOF

RUN chmod 0755 /home/user/monitor/dashboard.py && \
    chmod -R 0777 /home/user/monitor

WORKDIR /home/user
