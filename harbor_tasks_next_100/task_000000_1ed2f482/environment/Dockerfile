FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    jq \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest requests flask

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/batch/config \
    && mkdir -p /home/user/batch/logs \
    && mkdir -p /home/user/batch/.cache

RUN cat <<'EOF' > /home/user/batch/config/credentials.json
{"key_id": "sa-batch-7f2a", "secret": "newsecret7f2a9x"}
EOF

RUN cat <<'EOF' > /home/user/batch/.cache/auth_token
{"key_id": "sa-batch-4e1c", "token": "bearer-old-4e1c-abc123", "cached_at": "2024-01-15T10:00:00Z"}
EOF

RUN cat <<'EOF' > /home/user/batch/logs/runner.log
[2024-01-15 13:45:22] [INFO] Starting batch processor
[2024-01-15 13:45:22] [INFO] Loaded credentials from config
[2024-01-15 13:45:22] [DEBUG] Found cached auth token, skipping credential exchange
[2024-01-15 13:45:22] [DEBUG] Cache file age: 0.5 hours (valid)
[2024-01-15 13:45:22] [INFO] Using cached token for authentication
[2024-01-15 13:45:23] [ERROR] API request failed: 403 Forbidden (request_id: req-8a7b6c)
[2024-01-15 13:50:15] [INFO] Starting batch processor
[2024-01-15 13:50:15] [INFO] Loaded credentials from config
[2024-01-15 13:50:15] [DEBUG] Found cached auth token, skipping credential exchange
[2024-01-15 13:50:16] [ERROR] API request failed: 403 Forbidden (request_id: req-9c8d7e)
EOF

RUN cat <<'PYEOF' > /home/user/batch/runner.py
#!/usr/bin/env python3
"""Batch processor runner script."""

import json
import os
import sys
import time
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config", "credentials.json")
CACHE_PATH = os.path.join(SCRIPT_DIR, ".cache", "auth_token")
LOG_PATH = os.path.join(SCRIPT_DIR, "logs", "runner.log")
API_BASE = "http://localhost:9100"

CACHE_MAX_AGE_HOURS = 24

def log(level, message):
    """Write a log message."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}\n"
    with open(LOG_PATH, "a") as f:
        f.write(line)
    print(line.strip())

def load_credentials():
    """Load credentials from config file."""
    with open(CONFIG_PATH, "r") as f:
        creds = json.load(f)
    log("INFO", "Loaded credentials from config")
    return creds

def get_cached_token():
    """Check for and return cached auth token if valid."""
    if not os.path.exists(CACHE_PATH):
        return None

    # Check cache age by mtime
    mtime = os.path.getmtime(CACHE_PATH)
    age_hours = (time.time() - mtime) / 3600

    if age_hours >= CACHE_MAX_AGE_HOURS:
        log("DEBUG", f"Cache file age: {age_hours:.1f} hours (expired)")
        return None

    log("DEBUG", "Found cached auth token, skipping credential exchange")
    log("DEBUG", f"Cache file age: {age_hours:.1f} hours (valid)")

    with open(CACHE_PATH, "r") as f:
        cached = json.load(f)

    return cached.get("token")

def authenticate(credentials):
    """Exchange credentials for a token."""
    log("INFO", "Exchanging credentials for new token")
    resp = requests.post(
        f"{API_BASE}/api/auth",
        json={"key_id": credentials["key_id"], "secret": credentials["secret"]},
        timeout=10
    )

    if resp.status_code != 200:
        log("ERROR", f"Authentication failed: {resp.status_code} {resp.text}")
        return None

    data = resp.json()
    token = data.get("token")

    # Cache the new token
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump({
            "key_id": credentials["key_id"],
            "token": token,
            "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }, f)

    log("INFO", "New token cached successfully")
    return token

def process_batch(token):
    """Call the batch processing API."""
    log("INFO", "Calling batch processing API")
    resp = requests.get(
        f"{API_BASE}/api/process",
        headers={"Authorization": token},
        timeout=10
    )

    if resp.status_code != 200:
        log("ERROR", f"API request failed: {resp.status_code} Forbidden (request_id: req-{os.urandom(3).hex()})")
        return False

    log("INFO", f"API request successful: {resp.status_code} {resp.json()}")
    return True

def main():
    """Main entry point."""
    log("INFO", "Starting batch processor")

    # Always load credentials first (for logging/validation)
    credentials = load_credentials()

    # Check for cached token
    token = get_cached_token()

    if token:
        log("INFO", "Using cached token for authentication")
    else:
        # No valid cache, authenticate with credentials
        token = authenticate(credentials)
        if not token:
            log("ERROR", "Failed to obtain authentication token")
            sys.exit(1)

    # Process the batch
    success = process_batch(token)

    if success:
        log("INFO", "Batch processing completed successfully")
        sys.exit(0)
    else:
        log("ERROR", "Batch processing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
PYEOF

RUN chmod +x /home/user/batch/runner.py

RUN cat <<'SERVEREOF' > /home/user/mock_api_server.py
#!/usr/bin/env python3
"""Mock API server for testing."""

from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

VALID_CREDENTIALS = {
    "key_id": "sa-batch-7f2a",
    "secret": "newsecret7f2a9x"
}

VALID_TOKEN = "bearer-new-7f2a-xyz789"
OLD_TOKEN = "bearer-old-4e1c-abc123"

@app.route("/")
def index():
    return jsonify({"status": "mock api server running"})

@app.route("/api/auth", methods=["POST"])
def auth():
    data = request.get_json() or {}

    if (data.get("key_id") == VALID_CREDENTIALS["key_id"] and 
        data.get("secret") == VALID_CREDENTIALS["secret"]):
        return jsonify({"token": VALID_TOKEN})

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/process", methods=["GET"])
def process():
    auth_header = request.headers.get("Authorization", "")

    if auth_header == VALID_TOKEN:
        return jsonify({"status": "ok", "processed": 42})

    if auth_header == OLD_TOKEN:
        return jsonify({"error": "Forbidden", "message": "Token revoked"}), 403

    return jsonify({"error": "Unauthorized"}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
SERVEREOF

RUN chmod +x /home/user/mock_api_server.py

RUN cat <<'ENTRYEOF' > /entrypoint.sh
#!/bin/bash

# Start the mock API server in the background
python3 /home/user/mock_api_server.py &

# Wait for the server to be ready
for i in {1..30}; do
    if curl -s http://localhost:9100/ > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# Touch the cache file to make it recent
touch /home/user/batch/.cache/auth_token

exec "$@"
ENTRYEOF

RUN chmod +x /entrypoint.sh

RUN chown -R 1000:1000 /home/user && chmod -R 0777 /home/user

WORKDIR /home/user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
