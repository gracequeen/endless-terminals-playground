FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gawk \
    sed \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN python3 << 'PYSCRIPT'
import random

random.seed(42)

endpoints = [
    "/api/v1/users",
    "/api/v1/orders",
    "/api/v1/products",
    "/api/v1/auth",
    "/api/v1/payments",
    "/api/v1/inventory",
    "/api/v1/shipping",
    "/api/v1/reviews",
    "/api/v1/cart",
    "/api/v1/search"
]

status_codes = [200, 201, 400, 401, 404, 500, 502, 503]
status_weights = [50, 10, 5, 5, 10, 0, 5, 5]

rows = []

for i in range(1, 847):
    request_id = f"req-{i:04d}"
    status = random.choices(status_codes, weights=status_weights, k=1)[0]
    response_time = random.randint(50, 3000)
    endpoint = random.choice(endpoints)
    rows.append((request_id, status, response_time, endpoint))

indices_for_500 = random.sample(range(len(rows)), 12)
for idx in indices_for_500:
    req_id, _, resp_time, ep = rows[idx]
    rows[idx] = (req_id, 500, resp_time, ep)

with open("/home/user/api_responses.csv", "w") as f:
    f.write("request_id,status_code,response_time_ms,endpoint\n")
    for req_id, status, resp_time, endpoint in rows:
        f.write(f"{req_id},{status},{resp_time},{endpoint}\n")
PYSCRIPT

RUN chmod 644 /home/user/api_responses.csv

CMD ["/bin/bash"]
