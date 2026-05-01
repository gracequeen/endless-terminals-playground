FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/exports && chmod 0777 /home/user && chmod 0777 /home/user/exports

RUN python3 << 'PYSCRIPT'
import json
import random

first_names = ["Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah", "Ivan", "Julia",
               "Kevin", "Laura", "Michael", "Nancy", "Oscar", "Patricia", "Quentin", "Rachel", "Steven", "Tina",
               "Ulysses", "Victoria", "William", "Xena", "Yolanda", "Zachary", "Aaron", "Brenda", "Carlos", "Deborah",
               "Eric", "Felicia", "Gary", "Helen", "Isaac", "Jennifer", "Kyle", "Linda", "Marcus", "Nicole",
               "Oliver", "Pamela", "Raymond", "Sandra", "Thomas", "Uma", "Vincent", "Wendy", "Xavier", "Yvonne"]

last_names = ["Chen", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
              "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson",
              "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis",
              "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
              "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter"]

domains = ["example.com", "mail.com", "test.org", "company.net", "work.io", "email.com", "inbox.org", "post.net"]

streets = ["Main St", "Oak Ave", "Elm Blvd", "Pine Rd", "Maple Dr", "Cedar Ln", "Birch Way", "Walnut Ct"]
cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA"]
countries = ["USA", "USA", "USA", "USA", "USA", "USA", "USA", "USA"]

customers = []
random.seed(42)

for i in range(1, 501):
    if i == 1:
        first_name = "Alice"
        last_name = "Chen"
    else:
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

    name = f"{first_name} {last_name}"
    email = f"{first_name.lower()}@{random.choice(domains)}"

    customer = {
        "id": i,
        "name": name,
        "email": email,
        "address": {
            "street": f"{random.randint(100, 9999)} {random.choice(streets)}",
            "city": random.choice(cities),
            "state": random.choice(states),
            "zip": f"{random.randint(10000, 99999)}",
            "country": random.choice(countries)
        },
        "metadata": {
            "created_at": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}Z",
            "updated_at": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}Z",
            "status": random.choice(["active", "inactive", "pending"]),
            "tier": random.choice(["bronze", "silver", "gold", "platinum"]),
            "preferences": {
                "newsletter": random.choice([True, False]),
                "notifications": random.choice([True, False]),
                "language": random.choice(["en", "es", "fr", "de"])
            }
        },
        "phone": f"+1-{random.randint(200,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
        "company": random.choice(["Acme Corp", "TechStart Inc", "Global Solutions", "DataFlow LLC", "CloudBase", "InnovateTech", None])
    }
    customers.append(customer)

data = {
    "data": customers,
    "pagination": {
        "total": 500,
        "page": 1,
        "per_page": 500,
        "total_pages": 1
    }
}

with open("/home/user/exports/customers.json", "w") as f:
    json.dump(data, f, indent=2)
PYSCRIPT

RUN chmod 0644 /home/user/exports/customers.json
