FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pandas pyyaml

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/pipeline/incoming \
    && mkdir -p /home/user/pipeline/output \
    && mkdir -p /home/user/pipeline/logs

RUN cat <<'EOF' > /home/user/pipeline/config.yaml
timestamp_cutoff: 1700000000
min_amount: 10.0
EOF

RUN python3 << 'PYSCRIPT'
import csv
import random
import os

random.seed(42)

statuses = ['active', 'pending', 'completed', 'cancelled']

# Generate vendor_a.csv - 500 rows, clean data
with open('/home/user/pipeline/incoming/vendor_a.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'timestamp', 'amount', 'status'])
    for i in range(500):
        id_val = f"A{i+1:04d}"
        # Timestamps between 1700000000 (Nov 2023) and 1710000000 (Mar 2024)
        # Some below cutoff, most above
        if i < 50:
            timestamp = random.randint(1690000000, 1699999999)  # Below cutoff
        else:
            timestamp = random.randint(1700000001, 1710000000)  # Above cutoff
        # Amounts - some below 10, most above
        if i < 30:
            amount = round(random.uniform(1.0, 9.99), 2)
        else:
            amount = round(random.uniform(10.01, 500.0), 2)
        status = random.choice(statuses)
        writer.writerow([id_val, timestamp, amount, status])

# Generate vendor_b.csv - 480 rows, clean data
with open('/home/user/pipeline/incoming/vendor_b.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'timestamp', 'amount', 'status'])
    for i in range(480):
        id_val = f"B{i+1:04d}"
        if i < 45:
            timestamp = random.randint(1690000000, 1699999999)
        else:
            timestamp = random.randint(1700000001, 1710000000)
        if i < 25:
            amount = round(random.uniform(1.0, 9.99), 2)
        else:
            amount = round(random.uniform(10.01, 500.0), 2)
        status = random.choice(statuses)
        writer.writerow([id_val, timestamp, amount, status])

# Generate vendor_c.csv - 520 rows, PROBLEMATIC FORMAT
# - timestamps are ISO 8601 strings
# - amounts have $ currency symbols
# - some status values have trailing whitespace
from datetime import datetime

with open('/home/user/pipeline/incoming/vendor_c.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'timestamp', 'amount', 'status'])
    for i in range(520):
        id_val = f"C{i+1:04d}"
        if i < 50:
            unix_ts = random.randint(1690000000, 1699999999)
        else:
            unix_ts = random.randint(1700000001, 1710000000)
        # Convert to ISO 8601 string
        dt = datetime.utcfromtimestamp(unix_ts)
        iso_timestamp = dt.strftime('%Y-%m-%dT%H:%M:%SZ')

        if i < 30:
            amount_val = round(random.uniform(1.0, 9.99), 2)
        else:
            amount_val = round(random.uniform(10.01, 500.0), 2)
        # Add $ currency symbol
        amount_str = f"${amount_val:.2f}"

        status = random.choice(statuses)
        # Add trailing whitespace to some status values
        if i % 5 == 0:
            status = status + "  "

        writer.writerow([id_val, iso_timestamp, amount_str, status])

print("CSV files generated successfully")
PYSCRIPT

RUN cat <<'EOF' > /home/user/pipeline/reconcile.py
#!/usr/bin/env python3
"""
Data reconciliation script - merges vendor CSVs into a single output.
"""

import pandas as pd
import yaml
import os
import logging

# Setup logging
logging.basicConfig(
    filename='/home/user/pipeline/logs/reconcile.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    config_path = '/home/user/pipeline/config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    logger.info("Starting reconciliation job")

    # Load config
    config = load_config()
    timestamp_cutoff = config['timestamp_cutoff']
    min_amount = config['min_amount']

    logger.info(f"Using timestamp_cutoff: {timestamp_cutoff}, min_amount: {min_amount}")

    incoming_dir = '/home/user/pipeline/incoming'
    output_path = '/home/user/pipeline/output/merged.csv'

    # Load all vendor CSVs
    df_a = pd.read_csv(os.path.join(incoming_dir, 'vendor_a.csv'))
    logger.info(f"Loaded {len(df_a)} rows from vendor_a.csv")

    df_b = pd.read_csv(os.path.join(incoming_dir, 'vendor_b.csv'))
    logger.info(f"Loaded {len(df_b)} rows from vendor_b.csv")

    df_c = pd.read_csv(os.path.join(incoming_dir, 'vendor_c.csv'))
    logger.info(f"Loaded {len(df_c)} rows from vendor_c.csv")

    # Filter by timestamp cutoff
    # BUG: This doesn't handle vendor_c's ISO 8601 string timestamps properly
    df_a_filtered = df_a[df_a['timestamp'] > timestamp_cutoff]
    df_b_filtered = df_b[df_b['timestamp'] > timestamp_cutoff]
    df_c_filtered = df_c[df_c['timestamp'] > timestamp_cutoff]

    # Filter by minimum amount
    # BUG: This doesn't handle vendor_c's "$123.45" format properly
    df_a_filtered = df_a_filtered[df_a_filtered['amount'] > min_amount]
    df_b_filtered = df_b_filtered[df_b_filtered['amount'] > min_amount]
    df_c_filtered = df_c_filtered[df_c_filtered['amount'] > min_amount]

    logger.info(f"After filtering: {len(df_a_filtered)} from A, {len(df_b_filtered)} from B, {len(df_c_filtered)} from C")

    # Add source column for tracking
    df_a_filtered = df_a_filtered.copy()
    df_a_filtered['source'] = 'vendor_a'
    df_b_filtered = df_b_filtered.copy()
    df_b_filtered['source'] = 'vendor_b'
    df_c_filtered = df_c_filtered.copy()
    df_c_filtered['source'] = 'vendor_c'

    # Merge all dataframes - using concat since ids are unique per vendor
    merged = pd.concat([df_a_filtered, df_b_filtered, df_c_filtered], ignore_index=True)

    logger.info(f"Merged output: {len(merged)} rows")

    # Write output
    merged.to_csv(output_path, index=False)

    logger.info("Reconciliation complete")
    print(f"Reconciliation complete. Output written to {output_path} with {len(merged)} rows.")

    return 0

if __name__ == '__main__':
    exit(main())
EOF

RUN chmod +x /home/user/pipeline/reconcile.py

RUN cat <<'EOF' > /home/user/pipeline/logs/reconcile.log
2024-01-20 02:00:01,234 - INFO - Starting reconciliation job
2024-01-20 02:00:01,235 - INFO - Using timestamp_cutoff: 1700000000, min_amount: 10.0
2024-01-20 02:00:01,456 - INFO - Loaded 500 rows from vendor_a.csv
2024-01-20 02:00:01,567 - INFO - Loaded 480 rows from vendor_b.csv
2024-01-20 02:00:01,678 - INFO - Loaded 520 rows from vendor_c.csv
2024-01-20 02:00:01,890 - INFO - After filtering: 498 from A, 475 from B, 8 from C
2024-01-20 02:00:02,012 - INFO - Merged output: 12 rows
2024-01-20 02:00:02,123 - INFO - Reconciliation complete
EOF

RUN cd /home/user/pipeline && python3 reconcile.py || true

RUN chmod -R 0777 /home/user/pipeline

WORKDIR /home/user

CMD ["/bin/bash"]
