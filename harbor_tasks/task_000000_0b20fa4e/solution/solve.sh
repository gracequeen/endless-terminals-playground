#!/bin/bash
# Auto-generated solve script
set -e

tar -tzf /home/user/metrics-export.tar.gz | grep -i dashboards
mkdir -p /home/user/dashboards
tar -xzf /home/user/metrics-export.tar.gz -C /home/user/dashboards --strip-components=3 --wildcards '*/dashboards/*.json'
ls -la /home/user/dashboards/
cat /home/user/dashboards/app-latency.json
