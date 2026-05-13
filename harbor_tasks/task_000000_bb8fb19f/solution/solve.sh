#!/bin/bash
# Auto-generated solve script
set -e

sqlite3 /home/user/experiments/tracking.db ".schema runs"
sqlite3 /home/user/experiments/tracking.db "ALTER TABLE runs ADD COLUMN gpu_hours REAL;"
sqlite3 /home/user/experiments/tracking.db ".schema runs"
sqlite3 /home/user/experiments/tracking.db "SELECT * FROM runs;"
