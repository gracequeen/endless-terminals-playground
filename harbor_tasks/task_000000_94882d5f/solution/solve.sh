#!/bin/bash
# Auto-generated solve script
set -e

cat /home/user/inventory/hosts.json
mkdir -p /home/user/reports && jq -r '["hostname","memory"], (.[] | [.hostname, .memory_gb]) | @csv' /home/user/inventory/hosts.json > /home/user/reports/mem.csv
cat /home/user/reports/mem.csv
