FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    redis-server \
    redis-tools \
    grep \
    sed \
    gawk \
    vim \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user/services/auth-gateway && \
    mkdir -p /var/log/auth-gateway && \
    chmod 0777 /home/user && \
    chmod 0777 /home/user/services && \
    chmod 0777 /home/user/services/auth-gateway && \
    chmod 0777 /var/log/auth-gateway

RUN cat << 'GOBIN' > /tmp/create_binary.py
import struct
import os

# Create a fake "Go binary" that's actually a shell script but padded to look like a binary
# This script will read config.yaml, parse session_ttl, and crash if it has 's' suffix

script = '''#!/bin/bash
CONFIG_FILE="${1#-config=}"
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="./config.yaml"
fi
if [ "$1" = "-config" ]; then
    CONFIG_FILE="$2"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: auth-gateway starting..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Loading config from $CONFIG_FILE"

SESSION_TTL=$(grep 'session_ttl:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"' | tr -d "'")
echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Configured session_ttl: $SESSION_TTL"

# Check if session_ttl contains non-numeric characters (the bug)
if [[ "$SESSION_TTL" =~ [^0-9] ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting health check routine..."
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Redis connection established"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Listening on :8080"
    # Simulate running for a bit then crashing
    sleep 3
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] FATAL: session pool refresh failed" 
    echo "panic: strconv.Atoi: parsing \"$SESSION_TTL\": invalid syntax" >&2
    echo "" >&2
    echo "goroutine 1 [running]:" >&2
    echo "main.parseSessionTTL(0xc0000b2000, 0x6, 0x0)" >&2
    echo "        /app/session/manager.go:147 +0x123" >&2
    echo "main.refreshSessionPool(0xc0000a4000)" >&2
    echo "        /app/session/manager.go:89 +0x456" >&2
    echo "main.main()" >&2
    echo "        /app/main.go:52 +0x789" >&2
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting health check routine..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Redis connection established"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Listening on :8080"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Session TTL configured: ${SESSION_TTL}s"

# Keep running
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: Health check OK"
    sleep 30
done
'''

# Write the script
with open('/home/user/services/auth-gateway/auth-gateway', 'w') as f:
    f.write(script)
    # Pad to ~8MB with comments to simulate Go binary size
    padding = "\n# " + "x" * 1000 + "\n"
    for _ in range(8000):
        f.write(padding)

os.chmod('/home/user/services/auth-gateway/auth-gateway', 0o555)
GOBIN
RUN python3 /tmp/create_binary.py && rm /tmp/create_binary.py

RUN cat << 'EOF' > /home/user/services/auth-gateway/config.yaml
# Auth Gateway Configuration
# Last modified: 2024-01-15 01:50:32 UTC

server:
  host: 0.0.0.0
  port: 8080
  read_timeout: 30
  write_timeout: 30

redis:
  host: localhost
  port: 6379
  db: 0
  pool_size: 10
  max_retries: 3

session:
  session_ttl: 3600s
  cookie_name: auth_session
  cookie_secure: true
  cookie_httponly: true

auth:
  jwt_secret_file: /etc/auth-gateway/jwt.key
  token_expiry: 86400
  refresh_enabled: true

logging:
  level: info
  format: json

rate_limit:
  enabled: true
  requests_per_minute: 100
  burst: 20
EOF
RUN chmod 0666 /home/user/services/auth-gateway/config.yaml

RUN cat << 'EOF' > /home/user/services/auth-gateway/run.sh
#!/bin/bash
cd /home/user/services/auth-gateway
./auth-gateway -config ./config.yaml >> /var/log/auth-gateway/auth-gateway.log 2>> /var/log/auth-gateway/error.log &
echo $! > /tmp/auth-gateway.pid
echo "Started auth-gateway with PID $(cat /tmp/auth-gateway.pid)"
EOF
RUN chmod 0755 /home/user/services/auth-gateway/run.sh

RUN cat << 'LOGGEN' > /tmp/generate_logs.py
import random
from datetime import datetime, timedelta

# Generate auth-gateway.log with ~2000 lines including crash cycles
base_time = datetime(2024, 1, 15, 2, 0, 0)
log_lines = []

info_messages = [
    "INFO: Health check OK",
    "INFO: Request handled: GET /api/v1/auth/verify",
    "INFO: Request handled: POST /api/v1/auth/login",
    "INFO: Request handled: GET /api/v1/user/profile",
    "INFO: Session validated for user_id={}".format(random.randint(1000, 9999)),
    "INFO: Token refresh completed",
    "INFO: Redis PING successful",
    "INFO: Connection pool stats: active=8, idle=2",
    "INFO: Rate limit check passed for IP 10.0.{}.{}".format(random.randint(0,255), random.randint(1,254)),
    "INFO: JWT token validated",
]

# Generate 7 crash cycles
crash_times = []
current_time = base_time
for cycle in range(7):
    # Startup messages
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] INFO: auth-gateway starting...")
    current_time += timedelta(seconds=1)
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Loading config from ./config.yaml")
    current_time += timedelta(seconds=1)
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Configured session_ttl: 3600s")
    current_time += timedelta(seconds=1)
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Starting health check routine...")
    current_time += timedelta(seconds=1)
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Redis connection established")
    current_time += timedelta(seconds=1)
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] INFO: Listening on :8080")

    # Normal operation for ~90 seconds worth of logs
    for _ in range(250):
        current_time += timedelta(seconds=random.uniform(0.1, 0.5))
        msg = random.choice(info_messages)
        if "{}" in msg:
            msg = msg.format(random.randint(1000, 9999))
        log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

    # Crash
    current_time += timedelta(seconds=1)
    log_lines.append(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] FATAL: session pool refresh failed")
    crash_times.append(current_time)

    # Wait before restart (12-15 minutes)
    current_time += timedelta(minutes=random.randint(12, 15))

with open('/var/log/auth-gateway/auth-gateway.log', 'w') as f:
    f.write('\n'.join(log_lines) + '\n')

# Generate access.log with ~500 lines
access_lines = []
current_time = base_time
for _ in range(500):
    current_time += timedelta(seconds=random.uniform(5, 20))
    ip = f"10.0.{random.randint(0,255)}.{random.randint(1,254)}"
    method = random.choice(["GET", "POST", "GET", "GET"])
    path = random.choice(["/api/v1/auth/verify", "/api/v1/auth/login", "/api/v1/user/profile", "/api/v1/auth/refresh", "/health"])
    status = random.choice([200, 200, 200, 200, 201, 401, 403])
    size = random.randint(100, 5000)
    access_lines.append(f'{ip} - - [{current_time.strftime("%d/%b/%Y:%H:%M:%S +0000")}] "{method} {path} HTTP/1.1" {status} {size}')

with open('/var/log/auth-gateway/access.log', 'w') as f:
    f.write('\n'.join(access_lines) + '\n')

# Generate error.log with ~150 lines (panic messages from crashes)
error_lines = []
for i, crash_time in enumerate(crash_times):
    error_lines.append(f'panic: strconv.Atoi: parsing "3600s": invalid syntax')
    error_lines.append('')
    error_lines.append('goroutine 1 [running]:')
    error_lines.append('main.parseSessionTTL(0xc0000b2000, 0x6, 0x0)')
    error_lines.append('        /app/session/manager.go:147 +0x123')
    error_lines.append('main.refreshSessionPool(0xc0000a4000)')
    error_lines.append('        /app/session/manager.go:89 +0x456')
    error_lines.append('main.(*SessionManager).RefreshPool(0xc0000a4000)')
    error_lines.append('        /app/session/manager.go:72 +0x234')
    error_lines.append('main.main()')
    error_lines.append('        /app/main.go:52 +0x789')
    error_lines.append('')
    # Add some warning lines between crashes
    for _ in range(10):
        error_lines.append(f'[WARN] Connection timeout to upstream, retrying...')

with open('/var/log/auth-gateway/error.log', 'w') as f:
    f.write('\n'.join(error_lines) + '\n')

print("Logs generated successfully")
LOGGEN
RUN python3 /tmp/generate_logs.py && rm /tmp/generate_logs.py

RUN chmod 0666 /var/log/auth-gateway/*.log

RUN cat << 'EOF' > /entrypoint.sh
#!/bin/bash
# Start Redis
redis-server --daemonize yes --bind 127.0.0.1
# Wait for Redis to be ready
for i in {1..30}; do
    if redis-cli -h localhost -p 6379 PING 2>/dev/null | grep -q PONG; then
        break
    fi
    sleep 0.5
done
exec "$@"
EOF
RUN chmod +x /entrypoint.sh

RUN chown -R root:root /home/user/services/auth-gateway/auth-gateway && \
    chmod 0555 /home/user/services/auth-gateway/auth-gateway

WORKDIR /home/user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
