FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/dashboards && chmod 0777 /home/user && chmod 0777 /home/user/dashboards

RUN cat <<'EOF' > /home/user/dashboards/sample_metrics.json
{"cpu": [45, 52, 48, 51], "mem": [2048, 2100, 2080, 2095], "requests": [1200, 1350, 1280, 1400]}
EOF

RUN chmod 644 /home/user/dashboards/sample_metrics.json

RUN cat <<'EOF' > /home/user/dashboards/metric_agg.py
#!/usr/bin/env python
"""
Metric Aggregation Script
Reads metrics from sample_metrics.json and computes averages.
"""

import json
import os

def load_metrics(filepath):
    """Load metrics from a JSON file."""
    print "Loading metrics from file..."
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

def compute_average(values):
    """Compute the average of a list of numbers."""
    if not values:
        return 0
    return sum(values) / float(len(values))

def aggregate_metrics(metrics):
    """Aggregate all metrics by computing their averages."""
    print "Aggregating metrics..."
    results = {}
    for metric_name, values in metrics.items():
        avg = compute_average(values)
        results[metric_name] = avg
    return results

def display_results(results):
    """Display the aggregated results."""
    print "Results:"
    for metric_name in sorted(results.keys()):
        avg = results[metric_name]
        print "%s: %s" % (metric_name, avg)

def main():
    """Main entry point for the script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    metrics_file = os.path.join(script_dir, 'sample_metrics.json')

    metrics = load_metrics(metrics_file)
    results = aggregate_metrics(metrics)
    display_results(results)

    print "Done!"

if __name__ == '__main__':
    main()
EOF

RUN chmod 644 /home/user/dashboards/metric_agg.py

WORKDIR /home/user

CMD ["/bin/bash"]
