#!/bin/bash
# Auto-generated solve script
set -e

sqlite3 /home/user/fleet/telemetry.db ".schema devices"
sqlite3 /home/user/fleet/telemetry.db "ALTER TABLE devices ADD COLUMN last_seen TIMESTAMP;"
sqlite3 /home/user/fleet/telemetry.db ".schema devices"
sqlite3 /home/user/fleet/telemetry.db "SELECT COUNT(*) FROM devices;"
sqlite3 /home/user/fleet/telemetry.db "SELECT * FROM devices LIMIT 3;"
