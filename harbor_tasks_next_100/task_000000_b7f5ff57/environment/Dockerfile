FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    netcat-openbsd \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest requests

RUN mkdir -p /home/user/loadtest && chmod 0777 /home/user && chmod 0777 /home/user/loadtest

RUN cat > /home/user/loadtest/mock_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import time
import random

class DelayHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Random delay between 50-150ms
        delay = random.uniform(0.05, 0.15)
        time.sleep(delay)
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == '__main__':
    PORT = 9222
    with socketserver.TCPServer(("127.0.0.1", PORT), DelayHandler) as httpd:
        httpd.serve_forever()
EOF

RUN chmod +x /home/user/loadtest/mock_server.py

RUN cat > /home/user/loadtest/client.py << 'EOF'
#!/usr/bin/env python3
"""
HTTP client that makes requests to the mock server and logs latencies.
"""
import requests
import time
import sys
import csv

def run_benchmark(num_requests=200, output_file="raw_timings.csv"):
    """Make HTTP requests and record latencies in milliseconds."""
    url = "http://127.0.0.1:9222/"

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['request_id', 'latency_ms'])

        for i in range(num_requests):
            start = time.time()
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Request {i} failed: {e}", file=sys.stderr)
                continue
            end = time.time()

            latency_ms = (end - start) * 1000  # Convert to milliseconds
            writer.writerow([i, f"{latency_ms:.2f}"])

    print(f"Completed {num_requests} requests, results in {output_file}")

if __name__ == '__main__':
    num_requests = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    run_benchmark(num_requests)
EOF

RUN chmod +x /home/user/loadtest/client.py

RUN cat > /home/user/loadtest/aggregate.py << 'EOF'
#!/usr/bin/env python3
"""
Reads raw_timings.csv and computes percentile statistics.
Writes results to stats.json.
"""
import csv
import json
import sys

def compute_percentile(sorted_data, percentile):
    """Compute the given percentile from sorted data."""
    if not sorted_data:
        return 0
    k = (len(sorted_data) - 1) * (percentile / 100)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

def aggregate(input_file="raw_timings.csv", output_file="stats.json"):
    """Read latencies and compute statistics."""
    latencies = []

    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            latencies.append(row['latency_ms'])

    if not latencies:
        print("No data to aggregate", file=sys.stderr)
        sys.exit(1)

    # BUG: sorting as strings instead of floats!
    # This causes "99.5" to sort after "9.1" due to string comparison
    sorted_latencies = sorted(latencies)

    # Convert to float for percentile calculation (but data is already wrongly sorted)
    sorted_latencies_float = [float(x) for x in sorted_latencies]

    stats = {
        'count': len(latencies),
        'min': min(sorted_latencies_float),
        'max': max(sorted_latencies_float),
        'p50': compute_percentile(sorted_latencies_float, 50),
        'p99': compute_percentile(sorted_latencies_float, 99)
    }

    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"Aggregated {stats['count']} samples to {output_file}")

if __name__ == '__main__':
    aggregate()
EOF

RUN chmod +x /home/user/loadtest/aggregate.py

RUN cat > /home/user/loadtest/report.py << 'EOF'
#!/usr/bin/env python3
"""
Reads stats.json and prints a human-readable latency report.
"""
import json
import sys

def print_report(stats_file="stats.json"):
    """Print the latency report to stdout."""
    with open(stats_file, 'r') as f:
        stats = json.load(f)

    print("=" * 50)
    print("         LATENCY REPORT")
    print("=" * 50)
    print(f"Total requests: {stats['count']}")
    print(f"Min latency:    {stats['min']:.2f} ms")
    print(f"Max latency:    {stats['max']:.2f} ms")
    print("-" * 50)
    # BUG: Labels are swapped! p50 shows p99 value and vice versa
    print(f"p50 (median):   {stats['p99']:.2f} ms")
    print(f"p99:            {stats['p50']:.2f} ms")
    print("=" * 50)

if __name__ == '__main__':
    print_report()
EOF

RUN chmod +x /home/user/loadtest/report.py

RUN cat > /home/user/loadtest/run_bench.sh << 'EOF'
#!/bin/bash
set -e

cd /home/user/loadtest

echo "Starting benchmark run..."

# Run the client to make requests
python3 client.py 200

# Aggregate the results
python3 aggregate.py

# Print the report
python3 report.py

echo "Benchmark complete."
EOF

RUN chmod +x /home/user/loadtest/run_bench.sh

RUN cat > /home/user/loadtest/start_server.sh << 'EOF'
#!/bin/bash
cd /home/user/loadtest
python3 mock_server.py &
echo $! > .server.pid
sleep 1
EOF

RUN chmod +x /home/user/loadtest/start_server.sh

RUN chown -R nobody:nogroup /home/user/loadtest
RUN chmod -R 0777 /home/user/loadtest

RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash
cd /home/user/loadtest
python3 mock_server.py &
SERVER_PID=$!
echo $SERVER_PID > .server.pid
chmod 0666 .server.pid

# Wait for server to be ready
for i in {1..10}; do
    if curl -s -o /dev/null http://127.0.0.1:9222/ 2>/dev/null; then
        break
    fi
    sleep 0.5
done

exec "$@"
EOF

RUN chmod +x /entrypoint.sh

WORKDIR /home/user/loadtest

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
