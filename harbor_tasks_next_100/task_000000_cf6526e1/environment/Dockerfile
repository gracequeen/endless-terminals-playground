FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest pandas

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/pipeline/stages \
    && mkdir -p /home/user/pipeline/intake \
    && mkdir -p /home/user/pipeline/output \
    && mkdir -p /home/user/pipeline/logs

RUN cat > /home/user/pipeline/intake/servers.csv << 'EOF'
hostname,ip,os,cve_list
srv-web-01,10.0.1.10,Ubuntu 22.04,CVE-2023-1234|CVE-2022-5678
srv-web-02,10.0.1.11,Ubuntu 22.04,CVE-2023-2345|CVE-2022-6789
srv-db-01,10.0.1.20,RHEL 8,CVE-2023-3456|CVE-2021-7890
srv-db-02,10.0.1.21,RHEL 8,CVE-2023-4567|CVE-2021-8901
srv-app-01,10.0.1.30,CentOS 7,CVE-2022-1111|CVE-2022-2222
srv-app-02,10.0.1.31,CentOS 7,CVE-2022-3333|CVE-2022-4444
srv-app-03,10.0.1.32,CentOS 7,CVE-2022-5555|CVE-2022-6666
srv-mail-01,10.0.1.40,Debian 11,CVE-2023-7777|CVE-2023-8888
srv-dns-01,10.0.1.50,Ubuntu 20.04,CVE-2021-9999|CVE-2021-1010
srv-dns-02,10.0.1.51,Ubuntu 20.04,CVE-2021-1111|CVE-2021-1212
srv-proxy-01,10.0.1.60,Alpine 3.18,CVE-2023-1313|CVE-2023-1414
srv-proxy-02,10.0.1.61,Alpine 3.18,CVE-2023-1515|CVE-2023-1616
srv-backup-01,10.0.1.70,RHEL 9,CVE-2022-1717|CVE-2022-1818
srv-monitor-01,10.0.1.80,Ubuntu 22.04,CVE-2023-1919|CVE-2023-2020
srv-log-01,10.0.1.90,Debian 12,CVE-2023-2121|CVE-2023-2222
EOF

RUN cat > /home/user/pipeline/intake/workstations.csv << 'EOF'
hostname,ip,os,cve_list
ws-dev-01,10.0.2.10,Windows 11,CVE-2023-3001|CVE-2023-3002
ws-dev-02,10.0.2.11,Windows 11,CVE-2023-3003|CVE-2023-3004
ws-dev-03,10.0.2.12,macOS 14,CVE-2023-3005|CVE-2023-3006
ws-dev-04,10.0.2.13,macOS 14,CVE-2023-3007|CVE-2023-3008
ws-dev-05,10.0.2.14,Ubuntu 22.04,CVE-2023-3009|CVE-2023-3010
ws-qa-01,10.0.2.20,Windows 10,CVE-2022-4001|CVE-2022-4002
ws-qa-02,10.0.2.21,Windows 10,CVE-2022-4003|CVE-2022-4004
ws-qa-03,10.0.2.22,Windows 10,CVE-2022-4005|CVE-2022-4006
ws-design-01,10.0.2.30,macOS 13,CVE-2023-5001|CVE-2023-5002
ws-design-02,10.0.2.31,macOS 13,CVE-2023-5003|CVE-2023-5004
ws-design-03,10.0.2.32,macOS 13,CVE-2023-5005|CVE-2023-5006
ws-hr-01,10.0.2.40,Windows 11,CVE-2023-6001|CVE-2023-6002
ws-hr-02,10.0.2.41,Windows 11,CVE-2023-6003|CVE-2023-6004
ws-finance-01,10.0.2.50,Windows 11,CVE-2023-7001|CVE-2023-7002
ws-finance-02,10.0.2.51,Windows 11,CVE-2023-7003|CVE-2023-7004
ws-finance-03,10.0.2.52,Windows 11,CVE-2023-7005|CVE-2023-7006
ws-exec-01,10.0.2.60,macOS 14,CVE-2023-8001|CVE-2023-8002
ws-exec-02,10.0.2.61,macOS 14,CVE-2023-8003|CVE-2023-8004
ws-intern-01,10.0.2.70,Windows 10,CVE-2022-9001|CVE-2022-9002
ws-intern-02,10.0.2.71,Windows 10,CVE-2022-9003|CVE-2022-9004
EOF

RUN cat > /home/user/pipeline/intake/network_devices.csv << 'EOF'
hostname,ip,os,cve_list
fw-main-01,10.0.0.1,PAN-OS 11,CVE-2023-0001|CVE-2023-0002
fw-main-02,10.0.0.2,PAN-OS 11,CVE-2023-0003|CVE-2023-0004
fw-branch-01,10.0.0.3,Fortinet 7,CVE-2023-0005|CVE-2023-0006
sw-core-01,10.0.0.10,Cisco IOS-XE,CVE-2022-0101|CVE-2022-0102
sw-core-02,10.0.0.11,Cisco IOS-XE,CVE-2022-0103|CVE-2022-0104
sw-access-01,10.0.0.20,Cisco IOS,CVE-2021-0201|CVE-2021-0202
sw-access-02,10.0.0.21,Cisco IOS,CVE-2021-0203|CVE-2021-0204
sw-access-03,10.0.0.22,Cisco IOS,CVE-2021-0205|CVE-2021-0206
rt-edge-01,10.0.0.30,Juniper Junos,CVE-2023-0301|CVE-2023-0302
rt-edge-02,10.0.0.31,Juniper Junos,CVE-2023-0303|CVE-2023-0304
ap-floor1-01,10.0.0.40,Aruba OS,CVE-2022-0401|CVE-2022-0402
ap-floor2-01,10.0.0.41,Aruba OS,CVE-2022-0403|CVE-2022-0404
EOF

RUN cat > /home/user/pipeline/stages/__init__.py << 'EOF'
EOF

RUN cat > /home/user/pipeline/stages/ingest.py << 'EOF'
"""
Ingest stage: reads CSV files from intake directory and returns list of dicts.
"""
import os
import csv


def ingest(intake_dir):
    """
    Read all CSV files from the intake directory.

    Args:
        intake_dir: Path to directory containing CSV files

    Returns:
        List of dictionaries, one per row across all CSVs
    """
    records = []

    for filename in os.listdir(intake_dir):
        if filename.endswith('.csv'):
            filepath = os.path.join(intake_dir, filename)
            with open(filepath, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Add source file metadata
                    row['_source_file'] = filename
                    records.append(row)

    return records
EOF

RUN cat > /home/user/pipeline/stages/normalize.py << 'EOF'
"""
Normalize stage: standardizes field names and converts types.
"""


# Field name mapping from source CSV columns to standardized names
FIELD_MAPPING = {
    'hostname': 'host_name',
    'ip': 'ip_address',
    'os': 'operating_system',
    'cve_list': 'cve_references',  # BUG: should be 'cve_reference' (no 's')
    '_source_file': 'source_file'
}


def normalize(records):
    """
    Normalize field names and data types.

    Args:
        records: List of dictionaries from ingest stage

    Returns:
        List of dictionaries with standardized field names
    """
    normalized = []

    for record in records:
        new_record = {}

        for old_key, value in record.items():
            # Map to new field name if in mapping, otherwise keep original
            new_key = FIELD_MAPPING.get(old_key, old_key)

            # Convert value types as needed
            if new_key == 'ip_address':
                value = value.strip()
            elif new_key == 'host_name':
                value = value.strip().lower()
            elif new_key == 'operating_system':
                value = value.strip()

            new_record[new_key] = value

        normalized.append(new_record)

    return normalized
EOF

RUN cat > /home/user/pipeline/stages/enrich.py << 'EOF'
"""
Enrich stage: adds metadata and consolidates CVE references.
"""
import os
import logging
from datetime import datetime


# Set up logging for this stage
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'enrich.log')

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Output schema - only these fields will be in final output
OUTPUT_SCHEMA = ['host_name', 'ip_address', 'operating_system', 'cve_refs', 'enriched_at', 'source_file']


def enrich(records):
    """
    Enrich records with metadata and process CVE references.

    Args:
        records: List of normalized dictionaries

    Returns:
        List of enriched dictionaries conforming to output schema
    """
    enriched = []
    timestamp = datetime.utcnow().isoformat()

    for record in records:
        try:
            # Process CVE references - expects 'cve_reference' field (without 's')
            if 'cve_reference' in record:
                record['cve_refs'] = record['cve_reference'].split('|')
                del record['cve_reference']
        except KeyError as e:
            logger.warning(f"KeyError on cve_reference for host {record.get('host_name', 'unknown')}, skipping field: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing CVE for {record.get('host_name', 'unknown')}: {e}")

        # Add enrichment timestamp
        record['enriched_at'] = timestamp

        # Enforce output schema - only keep fields in schema
        output_record = {}
        for field in OUTPUT_SCHEMA:
            if field in record:
                output_record[field] = record[field]

        enriched.append(output_record)

    return enriched
EOF

RUN cat > /home/user/pipeline/run.py << 'EOF'
#!/usr/bin/env python3
"""
Pipeline orchestrator: runs all stages in sequence.
"""
import os
import sys
import json
import logging

# Add stages directory to path
sys.path.insert(0, os.path.dirname(__file__))

from stages.ingest import ingest
from stages.normalize import normalize
from stages.enrich import enrich


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run the asset inventory pipeline."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    intake_dir = os.path.join(base_dir, 'intake')
    output_dir = os.path.join(base_dir, 'output')
    output_file = os.path.join(output_dir, 'assets.json')

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Stage 1: Ingest
    logger.info("Starting ingest stage...")
    records = ingest(intake_dir)
    logger.info(f"Ingest complete: {len(records)} records loaded")

    # Stage 2: Normalize
    logger.info("Starting normalize stage...")
    records = normalize(records)
    logger.info(f"Normalize complete: {len(records)} records processed")

    # Stage 3: Enrich
    logger.info("Starting enrich stage...")
    records = enrich(records)
    logger.info(f"Enrich complete: {len(records)} records enriched")

    # Write output
    logger.info(f"Writing output to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)

    logger.info("Pipeline complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
EOF

RUN chmod -R 0777 /home/user/pipeline

RUN chown -R 1000:1000 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
