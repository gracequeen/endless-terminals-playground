FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

RUN pip3 install pytest pandas==2.2.0 pyarrow

RUN mkdir -p /home/user/pipeline /home/user/data /home/user/output \
    && chmod 0777 /home/user /home/user/pipeline /home/user/data /home/user/output

RUN cat > /home/user/pipeline/ingest.py << 'PYEOF'
#!/usr/bin/env python3
"""ETL pipeline to ingest events and produce daily summary."""

import pandas as pd

def main():
    # Read the source CSV
    df = pd.read_csv('/home/user/data/events.csv')

    # Parse timestamp column with specific format
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')

    # Extract date and aggregate
    df['date'] = df['timestamp'].dt.date
    daily_summary = df.groupby('date').size().reset_index(name='count')

    # Write output
    daily_summary.to_parquet('/home/user/output/daily_summary.parquet', index=False)
    print(f"Successfully wrote {len(daily_summary)} daily summaries")

if __name__ == '__main__':
    main()
PYEOF

RUN chmod 0666 /home/user/pipeline/ingest.py

RUN cat > /home/user/pipeline/requirements.txt << 'REQEOF'
# Updated 2024-03-15 for unrelated fix
pandas==2.2.0
pyarrow==15.0.0
# Previous version: pandas==1.5.3
REQEOF

RUN chmod 0644 /home/user/pipeline/requirements.txt

RUN python3 << 'GENEOF'
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# Generate dates spread across multiple days
base_date = datetime(2024, 3, 1)
dates = [base_date + timedelta(days=i) for i in range(20)]

event_types = ['click', 'view', 'purchase', 'login', 'logout', 'signup']

rows = []
for i in range(500):
    event_id = f"evt_{i+1:05d}"
    user_id = f"user_{random.randint(1, 100):04d}"
    event_type = random.choice(event_types)

    # Pick a random date and time
    dt = random.choice(dates) + timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

    # Most rows use ISO format, but ~20 rows use US format with AM/PM
    if i in [23, 47, 68, 91, 112, 156, 189, 203, 245, 267, 289, 312, 334, 367, 389, 412, 434, 456, 478, 495]:
        # US format: MM/DD/YYYY H:MM:SS AM/PM
        hour_12 = dt.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        am_pm = "AM" if dt.hour < 12 else "PM"
        timestamp = f"{dt.month:02d}/{dt.day:02d}/{dt.year} {hour_12}:{dt.minute:02d}:{dt.second:02d} {am_pm}"
    else:
        # ISO format: YYYY-MM-DD HH:MM:SS
        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')

    rows.append([event_id, timestamp, user_id, event_type])

# Shuffle to distribute the US format rows throughout
random.shuffle(rows)

with open('/home/user/data/events.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['event_id', 'timestamp', 'user_id', 'event_type'])
    writer.writerows(rows)

print(f"Generated {len(rows)} rows")
GENEOF

RUN chmod 0444 /home/user/data/events.csv

RUN chown -R 1000:1000 /home/user

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
