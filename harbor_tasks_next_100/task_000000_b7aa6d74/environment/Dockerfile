FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest aiohttp flask

RUN mkdir -p /home/user/audit /home/user/services && \
    chmod 0777 /home/user && \
    chmod 0777 /home/user/audit && \
    chmod 0777 /home/user/services

RUN cat > /home/user/services/auth_service.py << 'ENDOFFILE'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return jsonify({
        "active_sessions": 142,
        "failed_logins": 7,
        "token_refreshes": 89
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9001)
ENDOFFILE

RUN cat > /home/user/services/billing_service.py << 'ENDOFFILE'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return jsonify({
        "transactions_today": 523,
        "revenue_cents": 1547832,
        "refunds": 12
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9002)
ENDOFFILE

RUN cat > /home/user/services/inventory_service.py << 'ENDOFFILE'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return jsonify({
        "items_in_stock": 8472,
        "pending_orders": 156,
        "backorders": 23
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=9003)
ENDOFFILE

RUN cat > /home/user/services/start_all.sh << 'ENDOFFILE'
#!/bin/bash
cd /home/user/services

python3 auth_service.py &
echo $! > auth.pid

python3 billing_service.py &
echo $! > billing.pid

python3 inventory_service.py &
echo $! > inventory.pid

sleep 2
ENDOFFILE

RUN chmod +x /home/user/services/start_all.sh

RUN cat > /home/user/audit/collect.py << 'ENDOFFILE'
#!/usr/bin/env python3
"""
Compliance audit metrics collector.
Pulls metrics from auth, billing, and inventory services and produces a consolidated report.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

SERVICES = {
    "auth": "http://localhost:9001/metrics",
    "billing": "http://localhost:9002/metrics",
    "inventory": "http://localhost:9003/metrics",
}

TIMEOUT_SECONDS = 5


async def fetch_service_metrics(session, service_name, url):
    """Fetch metrics from a single service."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error: {service_name} returned status {response.status}")
                return None
    except asyncio.TimeoutError:
        print(f"timeout")
        return None
    except Exception as e:
        print(f"Error fetching {service_name}: {e}")
        return None


def collect_metrics_inner():
    """Inner collection function that creates its own event loop."""
    async def do_collection():
        results = {}
        # Bug: connector with limit=1 causes connection pool exhaustion
        # Combined with keep-alive timeout issues
        connector = aiohttp.TCPConnector(limit=1, force_close=False, enable_cleanup_closed=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            for service_name, url in SERVICES.items():
                data = await fetch_service_metrics(session, service_name, url)
                results[service_name] = data
        return results

    # Bug: creating a new event loop here when called from existing loop context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(do_collection())
    finally:
        loop.close()


async def main_wrapper():
    """Async wrapper that calls the collection function."""
    # This creates the problematic nested loop situation
    results = collect_metrics_inner()
    return results


def generate_report():
    """Generate the compliance audit report."""
    # Bug: using asyncio.run() which creates a loop, then calling function that creates another
    try:
        metrics = asyncio.run(main_wrapper())
    except Exception as e:
        print(f"Collection failed: {e}")
        metrics = {"auth": None, "billing": None, "inventory": None}

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "auth": metrics.get("auth"),
        "billing": metrics.get("billing"),
        "inventory": metrics.get("inventory"),
    }

    with open("/home/user/audit/report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = generate_report()
    print(json.dumps(report, indent=2))
ENDOFFILE

RUN chmod +x /home/user/audit/collect.py

RUN cat > /home/user/audit/report.json << 'ENDOFFILE'
{
  "timestamp": "2024-01-15T10:30:00Z",
  "auth": null,
  "billing": null,
  "inventory": null
}
ENDOFFILE

RUN chmod 0666 /home/user/audit/report.json

RUN chown -R 1000:1000 /home/user

RUN cat > /entrypoint.sh << 'ENDOFFILE'
#!/bin/bash
cd /home/user/services

python3 auth_service.py &
echo $! > auth.pid

python3 billing_service.py &
echo $! > billing.pid

python3 inventory_service.py &
echo $! > inventory.pid

# Wait for services to be ready
sleep 2

# Verify services are up
for port in 9001 9002 9003; do
    for i in {1..10}; do
        if curl -s http://localhost:$port/metrics > /dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
done

exec "$@"
ENDOFFILE

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
