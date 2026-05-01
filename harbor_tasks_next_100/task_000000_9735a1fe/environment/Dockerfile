FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gawk \
    grep \
    sed \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /var/log/app && chmod 0755 /var/log/app

RUN python3 << 'PYSCRIPT'
import random
import datetime

# Configuration
total_lines = 200000
target_5xx = 847

# Status code distribution
status_codes_2xx = [200, 200, 200, 200, 200, 200, 200, 200, 201, 204]
status_codes_3xx = [301, 302, 304]
status_codes_4xx = [400, 401, 403, 404, 404, 404, 404, 405, 408, 429]
status_codes_5xx = [500, 502, 503, 504]

# Sample data
ips = [f"192.168.1.{i}" for i in range(1, 255)] + \
      [f"10.0.0.{i}" for i in range(1, 100)] + \
      [f"172.16.{j}.{i}" for j in range(10) for i in range(1, 50)]

methods = ["GET", "GET", "GET", "GET", "GET", "POST", "POST", "PUT", "DELETE", "HEAD"]
paths = [
    "/", "/index.html", "/api/users", "/api/products", "/api/orders",
    "/static/js/app.js", "/static/css/style.css", "/images/logo.png",
    "/api/v1/data", "/api/v2/search", "/health", "/metrics",
    "/login", "/logout", "/register", "/profile", "/settings",
    "/api/items/123", "/api/items/456", "/docs", "/swagger.json"
]
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "curl/7.68.0",
    "python-requests/2.28.0",
    "PostmanRuntime/7.29.0"
]
referrers = ["-", "https://example.com/", "https://google.com/search", "https://internal.app/dashboard"]

# Determine which lines will be 5xx
five_xx_indices = set(random.sample(range(total_lines), target_5xx))

# Generate log file
base_time = datetime.datetime(2024, 1, 15, 0, 0, 0)

with open('/var/log/app/access.log', 'w') as f:
    for i in range(total_lines):
        ip = random.choice(ips)
        timestamp = base_time + datetime.timedelta(seconds=i * 0.5 + random.randint(0, 10))
        time_str = timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")
        method = random.choice(methods)
        path = random.choice(paths)

        if i in five_xx_indices:
            status = random.choice(status_codes_5xx)
        else:
            r = random.random()
            if r < 0.85:
                status = random.choice(status_codes_2xx)
            elif r < 0.92:
                status = random.choice(status_codes_3xx)
            else:
                status = random.choice(status_codes_4xx)

        size = random.randint(100, 50000) if status != 304 else 0
        referrer = random.choice(referrers)
        user_agent = random.choice(user_agents)

        # Combined log format: IP - - [timestamp] "METHOD PATH HTTP/1.1" status size "referrer" "user-agent"
        line = f'{ip} - - [{time_str}] "{method} {path} HTTP/1.1" {status} {size} "{referrer}" "{user_agent}"\n'
        f.write(line)

print(f"Generated {total_lines} log lines with {target_5xx} 5xx errors")
PYSCRIPT

RUN chmod 0644 /var/log/app/access.log

WORKDIR /home/user

CMD ["/bin/bash"]
