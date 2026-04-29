FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/pipeline/data && \
    mkdir -p /home/user/pipeline/output && \
    chmod -R 0777 /home/user/pipeline

RUN python3 << 'PYGEN'
import json
import random
from datetime import datetime, timedelta

random.seed(42)

categories = ['web', 'mobile', 'api', 'batch', 'streaming', 'analytics', 'auth', 'payment', 'notification', 'storage']

base_time = datetime(2024, 1, 1, 0, 0, 0)

with open('/home/user/pipeline/data/events.json', 'w') as f:
    for i in range(50000):
        timestamp = base_time + timedelta(seconds=i*10)
        record = {
            'id': i + 1,
            'timestamp': timestamp.isoformat(),
            'category': random.choice(categories),
            'value': round(random.uniform(0.01, 100.0), 2)
        }
        f.write(json.dumps(record) + '\n')
PYGEN

RUN cat > /home/user/pipeline/process.py << 'EOF'
import json
import sqlite3
import os

BATCH_SIZE = 1000

def load_checkpoint():
    try:
        with open('.checkpoint', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_checkpoint(batch_num):
    # BUG: not using context manager, buffer may not flush
    # BUG: saving batch_num but calling it 'last_line'
    json.dump({'last_line': batch_num}, open('.checkpoint', 'w'))

def process_batch(conn, batch):
    aggregates = {}
    for event in batch:
        cat = event['category']
        if cat not in aggregates:
            aggregates[cat] = {'total': 0, 'count': 0}
        aggregates[cat]['total'] += event['value']
        aggregates[cat]['count'] += 1

    for cat, data in aggregates.items():
        # BUG: INSERT OR REPLACE overwrites instead of accumulating on resume
        conn.execute('INSERT OR REPLACE INTO summary VALUES (?, ?, ?)',
                     (cat, data['total'], data['count']))

def process():
    conn = sqlite3.connect('output/summary.db')
    conn.execute('CREATE TABLE IF NOT EXISTS summary (category TEXT PRIMARY KEY, total_value REAL, count INTEGER)')

    checkpoint = load_checkpoint()
    start_from = checkpoint['last_line'] if checkpoint else 0

    with open('data/events.json', 'r') as f:
        batch = []
        batch_num = 0
        for i, line in enumerate(f):
            if i < start_from:  # This skips based on 'last_line' which is actually batch_num
                continue
            batch.append(json.loads(line))
            if len(batch) >= BATCH_SIZE:
                process_batch(conn, batch)
                batch_num += 1
                save_checkpoint(batch_num)  # Saves batch_num as 'last_line'
                batch = []
        if batch:
            process_batch(conn, batch)
            save_checkpoint(batch_num + 1)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    process()
EOF

RUN cat > /home/user/pipeline/run.sh << 'EOF'
#!/bin/bash
cd /home/user/pipeline
python3 /home/user/pipeline/process.py
EOF

RUN chmod +x /home/user/pipeline/run.sh && \
    chmod 0666 /home/user/pipeline/process.py && \
    chmod -R 0777 /home/user/pipeline

WORKDIR /home/user

CMD ["/bin/bash"]
