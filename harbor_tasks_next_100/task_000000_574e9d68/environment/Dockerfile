FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    gawk \
    sed \
    perl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/logs && chmod 0777 /home/user && chmod 0777 /home/user/logs

RUN python3 << 'PYSCRIPT'
import random
import datetime

methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
paths = ["/api/users", "/api/products", "/api/orders", "/index.html", "/static/js/app.js", 
         "/static/css/style.css", "/api/auth/login", "/api/auth/logout", "/health", 
         "/api/v2/items", "/dashboard", "/api/reports", "/favicon.ico"]
statuses = ["200", "201", "204", "301", "302", "400", "401", "403", "404", "500", "502", "503"]

random.seed(42)

lines = []
base_time = datetime.datetime(2024, 1, 15, 9, 0, 0)

for i in range(847):
    timestamp = (base_time + datetime.timedelta(seconds=i*7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ip = f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    method = random.choice(methods)
    path = random.choice(paths)
    status = random.choice(statuses)
    bytes_sent = str(random.randint(100, 50000))
    line = f"{timestamp}\t{ip}\t{method}\t{path}\t{status}\t{bytes_sent}"
    lines.append(line)

with open("/home/user/logs/access.log", "w") as f:
    f.write("\n".join(lines) + "\n")
PYSCRIPT

RUN chmod 0644 /home/user/logs/access.log

WORKDIR /home/user

CMD ["/bin/bash"]
