FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    grep \
    gawk \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/docs && chmod 0777 /home/user && chmod 0777 /home/user/docs

RUN mkdir -p /var/log/app && chmod 0755 /var/log/app

RUN python3 << 'PYSCRIPT'
import random
import datetime

# Configuration
num_lines = 2000
target_503_count = 47

# Sample data
ips = [
    "192.168.1.100", "10.0.0.50", "172.16.0.25", "203.0.113.45", "198.51.100.78",
    "192.0.2.123", "10.20.30.40", "172.31.255.1", "192.168.50.3", "10.100.200.55",
    "203.0.113.100", "198.51.100.200", "192.0.2.50", "10.0.50.3", "172.16.100.50"
]

users = ["-", "-", "-", "-", "-", "admin", "user123", "webuser", "-", "-"]

methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]

paths = [
    "/", "/index.html", "/api/users", "/api/products", "/api/orders",
    "/static/css/main.css", "/static/js/app.js", "/images/logo.png",
    "/api/v1/data", "/api/v2/items", "/health", "/status", "/login",
    "/logout", "/dashboard", "/admin", "/api/search", "/api/upload",
    "/downloads/file.pdf", "/page/503", "/item/503", "/user/503/profile",
    "/api/item/5032", "/content/id/15034", "/path/to/resource"
]

# Status codes with approximate distribution
status_codes = [200] * 60 + [301] * 5 + [302] * 5 + [304] * 10 + \
               [400] * 3 + [403] * 2 + [404] * 8 + [500] * 2 + \
               [502] * 2 + [504] * 3

referers = [
    "-", "https://www.google.com/", "https://example.com/",
    "https://internal.app.com/dashboard", "-", "-",
    "https://www.bing.com/search?q=test", "-"
]

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "curl/7.68.0",
    "python-requests/2.28.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0)"
]

# Generate base timestamp
base_time = datetime.datetime(2024, 1, 15, 0, 0, 0)

lines = []

# First, determine which line indices will have 503
indices_503 = set(random.sample(range(num_lines), target_503_count))

# Also add some lines with 503 in non-status positions (for anti-shortcut)
# These will have other status codes but 503 in path or bytes
indices_503_in_path = set(random.sample([i for i in range(num_lines) if i not in indices_503], 15))

for i in range(num_lines):
    ip = random.choice(ips)
    user = random.choice(users)

    # Increment time
    time_offset = datetime.timedelta(seconds=random.randint(1, 30))
    current_time = base_time + datetime.timedelta(seconds=i * 15) + time_offset
    time_str = current_time.strftime("%d/%b/%Y:%H:%M:%S +0000")

    method = random.choice(methods)

    if i in indices_503:
        # This line will have 503 as status code
        status = 503
        path = random.choice([p for p in paths if "503" not in p])
        bytes_sent = random.randint(0, 1000)
    elif i in indices_503_in_path:
        # This line has 503 in path or bytes but NOT as status
        status = random.choice(status_codes)
        # Use paths that contain 503
        path = random.choice(["/page/503", "/item/503", "/user/503/profile", "/api/item/5032", "/content/id/15034"])
        bytes_sent = random.choice([503, 5030, 15034, random.randint(100, 5000)])
    else:
        status = random.choice(status_codes)
        path = random.choice(paths)
        bytes_sent = random.randint(100, 50000)

    request = f"{method} {path} HTTP/1.1"
    referer = random.choice(referers)
    ua = random.choice(user_agents)

    # Combined log format
    line = f'{ip} - {user} [{time_str}] "{request}" {status} {bytes_sent} "{referer}" "{ua}"'
    lines.append(line)

# Write to file
with open('/var/log/app/access.log', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f"Generated {len(lines)} log lines")
print(f"Lines with 503 status: {len(indices_503)}")
print(f"Lines with 503 in other positions: {len(indices_503_in_path)}")
PYSCRIPT

RUN chmod 0644 /var/log/app/access.log

RUN useradd -m -d /home/user -s /bin/bash user

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
