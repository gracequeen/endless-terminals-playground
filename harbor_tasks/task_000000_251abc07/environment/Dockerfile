FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    grep \
    gawk \
    sed \
    perl \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /var/log/app && chmod 0755 /var/log/app

RUN python3 << 'PYSCRIPT'
import random
import datetime

random.seed(42)

months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
user_agents = [
    "curl/7.68.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Python-urllib/3.9",
    "WebhookClient/1.0",
    "PostmanRuntime/7.29.0",
    "axios/0.21.1",
]
health_user_agent = "ELB-HealthChecker/2.0"

internal_paths = [
    "/api/v1/internal/users",
    "/api/v1/internal/status",
    "/api/v1/internal/config",
    "/api/v2/internal/users",
    "/api/v2/internal/metrics",
    "/api/v2/internal/audit",
    "/api/v3/internal/webhook",
    "/api/v3/internal/sync",
]

public_paths = [
    "/api/v1/public/data",
    "/api/v1/public/search",
    "/api/v2/public/items",
    "/api/v2/public/users",
    "/",
    "/index.html",
    "/static/js/app.js",
    "/static/css/style.css",
    "/favicon.ico",
]

health_paths = ["/health", "/ready"]

methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
statuses = [200, 201, 204, 400, 401, 403, 404, 500]

def random_ip_non_10():
    first = random.choice([192, 172, 203, 198, 185, 45, 52, 34])
    if first == 192:
        return f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
    elif first == 172:
        return f"172.{random.randint(16,31)}.{random.randint(0,255)}.{random.randint(1,254)}"
    else:
        return f"{first}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def random_ip_10():
    return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def random_timestamp():
    day = random.randint(1, 28)
    month = random.choice(months)
    year = 2024
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"[{day:02d}/{month}/{year}:{hour:02d}:{minute:02d}:{second:02d} +0000]"

def gen_log_line(ip, path, ua=None):
    ts = random_timestamp()
    method = random.choice(methods)
    status = random.choice(statuses)
    size = random.randint(0, 10000)
    if ua is None:
        ua = random.choice(user_agents)
    return f'{ip} - - {ts} "{method} {path} HTTP/1.1" {status} {size} "-" "{ua}"'

lines = []

# 4800 internal API calls from non-10.x.x.x IPs
for _ in range(4800):
    ip = random_ip_non_10()
    path = random.choice(internal_paths)
    lines.append(gen_log_line(ip, path))

# 200 internal API calls from 10.x.x.x IPs (to be excluded)
for _ in range(200):
    ip = random_ip_10()
    path = random.choice(internal_paths)
    lines.append(gen_log_line(ip, path))

# 15000 health checks from 10.x.x.x
for _ in range(15000):
    ip = random_ip_10()
    path = random.choice(health_paths)
    lines.append(gen_log_line(ip, path, health_user_agent))

# Fill remaining with other traffic to reach ~50000 total
remaining = 50000 - 4800 - 200 - 15000
for _ in range(remaining):
    ip = random_ip_non_10()
    path = random.choice(public_paths)
    lines.append(gen_log_line(ip, path))

random.shuffle(lines)

with open('/var/log/app/access.log', 'w') as f:
    for line in lines:
        f.write(line + '\n')
PYSCRIPT

RUN chmod 0644 /var/log/app/access.log

RUN useradd -m -d /home/user -s /bin/bash user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
