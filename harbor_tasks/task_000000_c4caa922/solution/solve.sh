#!/bin/bash
# Auto-generated solve script
set -e

cat /home/user/backups/users_20240115.csv
mkdir -p /home/user/restore
python3 -c "import csv, json; f=open('/home/user/backups/users_20240115.csv'); rows=list(csv.DictReader(f)); f.close(); print(json.dumps(rows, indent=2))" > /home/user/restore/users.json
cat /home/user/restore/users.json
