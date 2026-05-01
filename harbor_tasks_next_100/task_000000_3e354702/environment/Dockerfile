FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    jq \
    python3 \
    python3-pip \
    gawk \
    sed \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/backups /home/user/data /home/user/verify

RUN chmod 0777 /home/user /home/user/backups /home/user/data /home/user/verify

RUN python3 << 'PYEOF'
import json
import random
import string
from datetime import datetime, timedelta

# Generate 50 unique customer IDs
random.seed(42)
customer_ids = random.sample(range(1000, 9999), 50)

# Generate customer data for JSON
customers_json = []
for cid in customer_ids:
    name = ''.join(random.choices(string.ascii_uppercase, k=1)) + ''.join(random.choices(string.ascii_lowercase, k=random.randint(4, 10))) + " " + random.choice(["Corp", "Inc", "LLC", "Ltd", "Co", "Industries", "Solutions"])
    email = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10))) + "@" + random.choice(["example.com", "test.org", "company.net", "mail.io"])
    created_at = (datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500))).strftime("%Y-%m-%d")
    customers_json.append({
        "id": cid,
        "name": name,
        "email": email,
        "created_at": created_at,
        "status": random.choice(["active", "inactive", "pending"]),
        "tier": random.choice(["bronze", "silver", "gold", "platinum"])
    })

# Write JSON file
with open("/home/user/backups/customers.json", "w") as f:
    json.dump(customers_json, f, indent=2)

# Write CSV file with same IDs
with open("/home/user/data/customers.csv", "w") as f:
    f.write("id,name,email,created_at\n")
    for customer in customers_json:
        # Escape name if it contains comma
        name = customer["name"]
        if "," in name:
            name = f'"{name}"'
        f.write(f'{customer["id"]},{name},{customer["email"]},{customer["created_at"]}\n')

print("Files created successfully")
PYEOF

RUN chmod 644 /home/user/backups/customers.json /home/user/data/customers.csv

CMD ["/bin/bash"]
