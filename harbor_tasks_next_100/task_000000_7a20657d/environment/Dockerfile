FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/audit && chmod 0777 /home/user && chmod 0777 /home/user/audit

RUN cat << 'EOF' > /home/user/audit/scan.py
#!/usr/bin/env python3
import sqlite3

def load_breach_hashes(path):
    with open(path, 'r') as f:
        return set(f.readlines())  # BUG: readlines() preserves \n

def scan_users(db_path, breach_set):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT uid, email, password_hash FROM accounts")
    compromised = []
    for uid, email, pw_hash in cur.fetchall():
        # normalize email for domain check (case insensitive)
        email_lower = email.lower()
        if pw_hash in breach_set:
            compromised.append(uid)
    conn.close()
    return compromised

def main():
    breach_set = load_breach_hashes('/home/user/audit/breach_hashes.txt')
    print(f"Checking {len(breach_set)} hashes...")
    compromised = scan_users('/home/user/audit/users.db', breach_set)
    print(f"Found {len(compromised)} compromised accounts")
    with open('/home/user/audit/compromised_uids.txt', 'w') as f:
        for uid in compromised:
            f.write(f"{uid}\n")

if __name__ == '__main__':
    main()
EOF

RUN chmod +x /home/user/audit/scan.py

RUN python3 << 'PYSCRIPT'
import sqlite3
import hashlib
import random
import string
import os

random.seed(42)

def generate_bcrypt_like_hash():
    salt = ''.join(random.choices(string.ascii_letters + string.digits + './', k=22))
    hash_part = ''.join(random.choices(string.ascii_letters + string.digits + './', k=31))
    return f"$2b$12${salt}{hash_part}"

compromised_uids = [23, 89, 156, 234, 312, 401, 478]

compromised_hashes = []
for _ in compromised_uids:
    compromised_hashes.append(generate_bcrypt_like_hash())

uid_to_hash = dict(zip(compromised_uids, compromised_hashes))

breach_hashes = set(compromised_hashes)
while len(breach_hashes) < 10000:
    breach_hashes.add(generate_bcrypt_like_hash())

breach_hashes = list(breach_hashes)
random.shuffle(breach_hashes)

with open('/home/user/audit/breach_hashes.txt', 'w') as f:
    for h in breach_hashes:
        f.write(h + '\n')

conn = sqlite3.connect('/home/user/audit/users.db')
cur = conn.cursor()
cur.execute('''
    CREATE TABLE accounts (
        uid INTEGER PRIMARY KEY,
        email TEXT,
        password_hash TEXT
    )
''')

domains = ['example.com', 'test.org', 'company.net', 'mail.io', 'service.co']

for uid in range(1, 501):
    username = ''.join(random.choices(string.ascii_lowercase, k=8))
    domain = random.choice(domains)
    email = f"{username}@{domain}"

    if uid in uid_to_hash:
        pw_hash = uid_to_hash[uid]
    else:
        pw_hash = generate_bcrypt_like_hash()
        while pw_hash in breach_hashes:
            pw_hash = generate_bcrypt_like_hash()

    cur.execute("INSERT INTO accounts (uid, email, password_hash) VALUES (?, ?, ?)",
                (uid, email, pw_hash))

conn.commit()
conn.close()
PYSCRIPT

RUN chmod 0666 /home/user/audit/users.db && \
    chmod 0666 /home/user/audit/breach_hashes.txt && \
    chmod 0755 /home/user/audit/scan.py

WORKDIR /home/user

CMD ["/bin/bash"]
