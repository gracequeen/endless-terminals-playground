FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    procps \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/monitor/config \
    && mkdir -p /home/user/monitor/data \
    && mkdir -p /home/user/monitor/logs

RUN cat > /home/user/monitor/config/sources.yaml << 'EOF'
sources:
  - name: cpu_usage
    path: /proc/stat
    type: cpu
    poll_interval: 5
  - name: memory_usage
    path: /proc/meminfo
    type: memory
    poll_interval: 5
  - name: disk_usage
    path: /proc/diskstats
    type: disk
    poll_interval: 5
  - name: network_usage
    path: /proc/net/dev
    type: network
    poll_interval: 5
EOF

RUN cat > /home/user/monitor/config/thresholds.yaml << 'EOF'
thresholds:
  cpu_usage:
    warning: 70
    critical: 90
  memory_usage:
    warning: 80
    critical: 95
  disk_usage:
    warning: 75
    critical: 90
  network_usage:
    warning: 1000000
    critical: 5000000
EOF

RUN cat > /home/user/monitor/config/collector.conf << 'EOF'
[runtime]
max_cycles = 5
log_level = INFO
poll_interval = 5

[output]
format = jsonl
destination = data/metrics.jsonl
EOF

RUN cat > /home/user/monitor/collector.py << 'ENDOFCOLLECTOR'
#!/usr/bin/env python3
"""
Metric collector - polls system metrics and writes to metrics.jsonl
"""

import configparser
import json
import os
import sys
import time
import random
from datetime import datetime

import yaml


def setup_logging(log_level):
    """Simple logging setup."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'collector.log')


def log_message(log_file, message):
    """Write a log message."""
    timestamp = datetime.now().isoformat()
    with open(log_file, 'a') as f:
        f.write(f"{timestamp} - {message}\n")


def load_sources(config_path):
    """Load metric sources from YAML config."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('sources', [])


def collect_metric(source):
    """Collect a metric from a source."""
    # Simulate metric collection
    metric = {
        'timestamp': datetime.now().isoformat(),
        'source': source['name'],
        'type': source['type'],
        'value': random.uniform(0, 100),
        'unit': 'percent' if source['type'] in ['cpu', 'memory', 'disk'] else 'bytes'
    }
    return metric


def write_metric(output_path, metric):
    """Write a metric to the output file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'a') as f:
        f.write(json.dumps(metric) + '\n')


def main():
    """Main collector loop."""
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Load configuration
    config = configparser.ConfigParser()
    config.read('config/collector.conf')

    max_cycles = config.getint('runtime', 'max_cycles', fallback=0)
    poll_interval = config.getint('runtime', 'poll_interval', fallback=5)
    log_level = config.get('runtime', 'log_level', fallback='INFO')
    output_dest = config.get('output', 'destination', fallback='data/metrics.jsonl')

    # Setup logging
    log_file = setup_logging(log_level)
    log_message(log_file, "Collector starting up")
    log_message(log_file, f"Configuration: max_cycles={max_cycles}, poll_interval={poll_interval}")

    # Load sources
    sources_path = os.path.join(script_dir, 'config', 'sources.yaml')
    sources = load_sources(sources_path)
    log_message(log_file, f"Loaded {len(sources)} metric sources")

    output_path = os.path.join(script_dir, output_dest)

    cycle_count = 0

    while True:
        cycle_count += 1
        log_message(log_file, f"Starting collection cycle {cycle_count}")

        for source in sources:
            try:
                metric = collect_metric(source)
                write_metric(output_path, metric)
                log_message(log_file, f"Collected metric from {source['name']}: {metric['value']:.2f}")
            except Exception as e:
                log_message(log_file, f"Error collecting from {source['name']}: {e}")

        log_message(log_file, f"Completed collection cycle {cycle_count}")

        # Check if we should exit (the bug!)
        if max_cycles > 0 and cycle_count >= max_cycles:
            sys.exit(0)  # silent exit, no logging

        time.sleep(poll_interval)


if __name__ == '__main__':
    main()
ENDOFCOLLECTOR

RUN cat > /home/user/monitor/aggregator.py << 'ENDOFAGGREGATOR'
#!/usr/bin/env python3
"""
Metric aggregator - reads metrics.jsonl and computes rolling averages.
"""

import json
import os
from collections import defaultdict
from datetime import datetime


def load_metrics(input_path):
    """Load metrics from JSONL file."""
    metrics = []
    if os.path.exists(input_path):
        with open(input_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    metrics.append(json.loads(line))
    return metrics


def compute_averages(metrics):
    """Compute rolling averages by source."""
    by_source = defaultdict(list)
    for m in metrics:
        by_source[m['source']].append(m['value'])

    averages = {}
    for source, values in by_source.items():
        averages[source] = {
            'average': sum(values) / len(values) if values else 0,
            'min': min(values) if values else 0,
            'max': max(values) if values else 0,
            'count': len(values)
        }
    return averages


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, 'data', 'metrics.jsonl')
    output_path = os.path.join(script_dir, 'data', 'aggregated.json')

    metrics = load_metrics(input_path)
    averages = compute_averages(metrics)

    result = {
        'timestamp': datetime.now().isoformat(),
        'aggregations': averages
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Aggregated {len(metrics)} metrics into {output_path}")


if __name__ == '__main__':
    main()
ENDOFAGGREGATOR

RUN cat > /home/user/monitor/alert.py << 'ENDOFALERT'
#!/usr/bin/env python3
"""
Alert checker - reads aggregated.json and checks against thresholds.
"""

import json
import os

import yaml


def load_thresholds(config_path):
    """Load thresholds from YAML config."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('thresholds', {})


def load_aggregations(input_path):
    """Load aggregations from JSON file."""
    if os.path.exists(input_path):
        with open(input_path, 'r') as f:
            return json.load(f)
    return {}


def check_alerts(aggregations, thresholds):
    """Check aggregations against thresholds."""
    alerts = []

    agg_data = aggregations.get('aggregations', {})

    for source, stats in agg_data.items():
        if source in thresholds:
            threshold = thresholds[source]
            avg = stats.get('average', 0)

            if avg >= threshold.get('critical', float('inf')):
                alerts.append({
                    'source': source,
                    'level': 'CRITICAL',
                    'value': avg,
                    'threshold': threshold['critical']
                })
            elif avg >= threshold.get('warning', float('inf')):
                alerts.append({
                    'source': source,
                    'level': 'WARNING',
                    'value': avg,
                    'threshold': threshold['warning']
                })

    return alerts


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    thresholds_path = os.path.join(script_dir, 'config', 'thresholds.yaml')
    aggregations_path = os.path.join(script_dir, 'data', 'aggregated.json')

    thresholds = load_thresholds(thresholds_path)
    aggregations = load_aggregations(aggregations_path)

    alerts = check_alerts(aggregations, thresholds)

    if alerts:
        print("=== ALERTS ===")
        for alert in alerts:
            print(f"[{alert['level']}] {alert['source']}: {alert['value']:.2f} (threshold: {alert['threshold']})")
    else:
        print("No alerts.")


if __name__ == '__main__':
    main()
ENDOFALERT

RUN cat > /home/user/monitor/run.sh << 'ENDOFRUNSH'
#!/bin/bash
# Wrapper script to start the collector

cd "$(dirname "$0")"

echo "Starting metric collector..."
python3 collector.py
ENDOFRUNSH

RUN chmod +x /home/user/monitor/run.sh \
    && chmod +x /home/user/monitor/collector.py \
    && chmod +x /home/user/monitor/aggregator.py \
    && chmod +x /home/user/monitor/alert.py

RUN chmod -R 0777 /home/user/monitor

WORKDIR /home/user

CMD ["/bin/bash"]
