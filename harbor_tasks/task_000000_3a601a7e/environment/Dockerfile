FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    bash \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/collector && chmod 0777 /home/user/collector

RUN mkdir -p /opt/mock-api && chmod 0755 /opt/mock-api

RUN cat > /home/user/collector/.env << 'EOF'
API_HOST=http://localhost:8080
API_KEY=sk_stg_9f7a2e3c8b
LOG_LEVEL=debug
EOF

RUN chmod 0666 /home/user/collector/.env

RUN cat > /home/user/collector/healthcheck.sh << 'EOF'
#!/bin/bash
set -e

# Load environment
source /home/user/collector/config.sh

RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health_response.json \
    -H "Authorization: Bearer $API_KEY" \
    "$API_HOST/v1/status")

if [ "$RESPONSE" -eq 200 ]; then
    echo "Health check passed"
    exit 0
else
    echo "Health check failed with status: $RESPONSE"
    exit 1
fi
EOF

RUN chmod 0777 /home/user/collector/healthcheck.sh

RUN cat > /home/user/collector/config.sh << 'EOF'
#!/bin/bash
# Collector configuration loader

# Source the env file
if [ -f /home/user/collector/.env ]; then
    export $(cat /home/user/collector/.env | xargs)
fi

# Override with cached credentials if present (for backwards compat)
if [ -f /home/user/collector/.credentials_cache ]; then
    source /home/user/collector/.credentials_cache
fi
EOF

RUN chmod 0777 /home/user/collector/config.sh

RUN cat > /home/user/collector/.credentials_cache << 'EOF'
API_KEY=sk_stg_7d4b1a9e2f
EOF

RUN chmod 0666 /home/user/collector/.credentials_cache

RUN cat > /opt/mock-api/server.py << 'PYEOF'
#!/usr/bin/env python3
"""Mock API server for testing healthcheck script."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

VALID_API_KEY = "sk_stg_9f7a2e3c8b"

class MockAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress logging

    def do_GET(self):
        if self.path == "/v1/status":
            auth_header = self.headers.get("Authorization", "")
            if auth_header == f"Bearer {VALID_API_KEY}":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "unauthorized"}).encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "not found"}).encode())

if __name__ == "__main__":
    server = HTTPServer(("localhost", 8080), MockAPIHandler)
    print("Mock API server running on http://localhost:8080")
    server.serve_forever()
PYEOF

RUN chmod 0755 /opt/mock-api/server.py

RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash
# Start the mock API server in the background
python3 /opt/mock-api/server.py &

# Wait for the server to be ready
for i in {1..30}; do
    if curl -s http://localhost:8080/v1/status -H "Authorization: Bearer sk_stg_9f7a2e3c8b" > /dev/null 2>&1; then
        break
    fi
    sleep 0.1
done

# Execute the command passed to the container (default: bash)
exec "$@"
EOF

RUN chmod 0755 /entrypoint.sh

WORKDIR /home/user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
