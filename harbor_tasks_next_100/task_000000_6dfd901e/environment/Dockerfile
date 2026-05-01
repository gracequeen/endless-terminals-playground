FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gzip \
    xxd \
    bsdmainutils \
    file \
    binwalk \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/backup/tables && chmod -R 0777 /home/user

RUN cat << 'PYSCRIPT' > /tmp/generate_backup.py
import gzip
import os
import random
import zlib
import io

TABLES_DIR = "/home/user/backup/tables"
LOG_FILE = "/home/user/backup/backup.log"

table_names = [
    "users", "accounts", "orders", "products", "inventory", "transactions",
    "customers", "suppliers", "shipments", "payments", "invoices", "categories",
    "reviews", "ratings", "comments", "posts", "tags", "sessions", "logs",
    "audit_trail", "permissions", "roles", "user_roles", "settings", "configs",
    "notifications", "messages", "attachments", "files", "images", "thumbnails",
    "cache_entries", "job_queue", "scheduled_tasks", "reports", "analytics",
    "metrics", "events", "subscriptions", "plans", "billing", "credits",
    "discounts", "coupons", "promotions", "campaigns", "addresses"
]

assert len(table_names) == 47

random.seed(42)
random.shuffle(table_names)

corrupted_tables = set(table_names[:16])
valid_tables = set(table_names[16:])

def generate_sql_dump(table_name, num_rows=None):
    if num_rows is None:
        num_rows = random.randint(100, 500)

    lines = []
    lines.append(f"-- PostgreSQL dump")
    lines.append(f"-- Dumped from database version 14.5")
    lines.append(f"-- Dumped by pg_dump version 14.5")
    lines.append("")
    lines.append("SET statement_timeout = 0;")
    lines.append("SET lock_timeout = 0;")
    lines.append("SET idle_in_transaction_session_timeout = 0;")
    lines.append("SET client_encoding = 'UTF8';")
    lines.append("SET standard_conforming_strings = on;")
    lines.append("SET check_function_bodies = false;")
    lines.append("SET xmloption = content;")
    lines.append("SET client_min_messages = warning;")
    lines.append("SET row_security = off;")
    lines.append("")
    lines.append(f"DROP TABLE IF EXISTS public.{table_name};")
    lines.append("")
    lines.append(f"CREATE TABLE public.{table_name} (")
    lines.append(f"    id integer NOT NULL,")
    lines.append(f"    name character varying(255),")
    lines.append(f"    description text,")
    lines.append(f"    created_at timestamp without time zone DEFAULT now(),")
    lines.append(f"    updated_at timestamp without time zone DEFAULT now(),")
    lines.append(f"    status character varying(50) DEFAULT 'active'::character varying,")
    lines.append(f"    metadata jsonb")
    lines.append(f");")
    lines.append("")
    lines.append(f"ALTER TABLE public.{table_name} OWNER TO postgres;")
    lines.append("")
    lines.append(f"COPY public.{table_name} (id, name, description, created_at, updated_at, status, metadata) FROM stdin;")

    for i in range(1, num_rows + 1):
        name = f"item_{i}_{random.randint(1000, 9999)}"
        desc = f"Description for {name} with some additional text to make it longer and more realistic"
        created = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        updated = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        status = random.choice(["active", "inactive", "pending", "archived"])
        metadata = '{"key": "value", "count": ' + str(random.randint(1, 1000)) + '}'
        lines.append(f"{i}\t{name}\t{desc}\t{created}\t{updated}\t{status}\t{metadata}")

    lines.append("\\.")
    lines.append("")
    lines.append(f"ALTER TABLE ONLY public.{table_name}")
    lines.append(f"    ADD CONSTRAINT {table_name}_pkey PRIMARY KEY (id);")
    lines.append("")
    lines.append(f"CREATE INDEX idx_{table_name}_name ON public.{table_name} USING btree (name);")
    lines.append(f"CREATE INDEX idx_{table_name}_status ON public.{table_name} USING btree (status);")
    lines.append("")
    lines.append("-- Dump complete")
    lines.append("")

    return "\n".join(lines)

def generate_progress_data(table_name):
    lines = []
    lines.append(f"PROGRESS CHECKPOINT: {table_name}")
    lines.append(f"Rows processed: {random.randint(10, 50)}")
    lines.append(f"Bytes written: {random.randint(1000, 5000)}")
    lines.append(f"Timestamp: 2024-01-15 03:{random.randint(10,59):02d}:{random.randint(0,59):02d}")
    return "\n".join(lines)

def create_valid_gzip(content):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb') as f:
        f.write(content.encode('utf-8'))
    return buf.getvalue()

def create_corrupted_gzip(main_content, progress_content):
    valid_stream = create_valid_gzip(main_content)

    progress_compressed = create_valid_gzip(progress_content)
    truncate_at = len(progress_compressed) * 2 // 3
    truncated_stream = progress_compressed[:truncate_at]

    return valid_stream + truncated_stream

log_entries = []

for table_name in table_names:
    timestamp_base = random.randint(0, 3600)
    log_entries.append((timestamp_base, f"2024-01-15 03:{timestamp_base//60:02d}:{timestamp_base%60:02d} DUMP: {table_name} started"))

    if table_name in corrupted_tables:
        progress_time = timestamp_base + random.randint(5, 30)
        log_entries.append((progress_time, f"2024-01-15 03:{progress_time//60:02d}:{progress_time%60:02d} PROGRESS: {table_name} checkpoint"))

    complete_time = timestamp_base + random.randint(30, 120)
    log_entries.append((complete_time, f"2024-01-15 03:{complete_time//60:02d}:{complete_time%60:02d} DUMP: {table_name} complete"))

log_entries.sort(key=lambda x: x[0])

with open(LOG_FILE, 'w') as f:
    f.write("=== PostgreSQL Backup Job Started ===\n")
    f.write("2024-01-15 03:00:00 Starting backup of 47 tables\n")
    f.write("2024-01-15 03:00:00 Target directory: /home/user/backup/tables/\n")
    f.write("\n")
    for _, entry in log_entries:
        f.write(entry + "\n")
    f.write("\n")
    f.write("2024-01-15 04:05:32 === Backup Job Completed Successfully ===\n")
    f.write("2024-01-15 04:05:32 Total tables: 47\n")
    f.write("2024-01-15 04:05:32 Exit code: 0\n")

for table_name in table_names:
    filepath = os.path.join(TABLES_DIR, f"{table_name}.sql.gz")
    sql_content = generate_sql_dump(table_name)

    if table_name in corrupted_tables:
        progress_content = generate_progress_data(table_name)
        file_data = create_corrupted_gzip(sql_content, progress_content)
    else:
        file_data = create_valid_gzip(sql_content)

    with open(filepath, 'wb') as f:
        f.write(file_data)

print(f"Generated {len(valid_tables)} valid files and {len(corrupted_tables)} corrupted files")
print(f"Corrupted tables: {sorted(corrupted_tables)}")
PYSCRIPT

RUN python3 /tmp/generate_backup.py && rm /tmp/generate_backup.py

RUN chmod -R 0777 /home/user/backup

WORKDIR /home/user

CMD ["/bin/bash"]
