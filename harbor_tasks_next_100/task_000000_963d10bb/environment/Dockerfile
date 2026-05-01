FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    tar \
    gzip \
    findutils \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /data/projects && chmod 0777 /data/projects
RUN mkdir -p /backup && chmod 0777 /backup

RUN cat << 'SCRIPT' > /tmp/generate_files.py
import os
import random
import string

random.seed(42)

base_dir = "/data/projects"

# Create 12 top-level directories
top_dirs = [
    "analytics", "backend", "frontend", "database", "reports",
    "logs", "configs", "exports", "imports", "archives", "temp", "cache"
]

# Create nested structure
all_dirs = []
for top in top_dirs:
    top_path = os.path.join(base_dir, top)
    all_dirs.append(top_path)
    # Create 2-5 levels of nesting
    depth = random.randint(2, 5)
    current = top_path
    for level in range(depth):
        subdir_count = random.randint(1, 3)
        for i in range(subdir_count):
            subdir_name = f"level{level}_sub{i}"
            subdir_path = os.path.join(current, subdir_name)
            all_dirs.append(subdir_path)
        current = os.path.join(current, f"level{level}_sub0")

# Create all directories
for d in all_dirs:
    os.makedirs(d, exist_ok=True)

# Get all leaf and intermediate directories for file placement
all_created_dirs = []
for root, dirs, files in os.walk(base_dir):
    all_created_dirs.append(root)

extensions = [".txt", ".log", ".dat", ".csv", ".json"]

def random_content(size_kb):
    size = size_kb * 1024
    return ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=size))

# Track files created
files_created = 0
files_with_spaces = 0
files_with_quotes = 0

# We need exactly 847 files, at least 40 with spaces, at least 15 with quotes
target_total = 847
target_spaces = 45
target_quotes = 18

file_names = []

# Generate file names
for i in range(target_total):
    ext = random.choice(extensions)
    base_name = f"file_{i:04d}"

    # Add spaces to some files
    if files_with_spaces < target_spaces:
        base_name = f"file {i:04d} data"
        files_with_spaces += 1
    # Add quotes to some files (different from space files)
    elif files_with_quotes < target_quotes:
        base_name = f"file_{i:04d}'s_data"
        files_with_quotes += 1

    file_names.append(base_name + ext)

# Distribute files across directories
random.shuffle(file_names)
random.shuffle(all_created_dirs)

for i, fname in enumerate(file_names):
    dir_idx = i % len(all_created_dirs)
    target_dir = all_created_dirs[dir_idx]
    fpath = os.path.join(target_dir, fname)

    # Random size between 1KB and 500KB, but keep total around 120MB
    # 847 files * avg 145KB = ~123MB
    size_kb = random.randint(50, 250)

    with open(fpath, 'w') as f:
        f.write(random_content(size_kb))

    files_created += 1

print(f"Created {files_created} files")
print(f"Files with spaces: {files_with_spaces}")
print(f"Files with quotes: {files_with_quotes}")
SCRIPT

RUN python3 /tmp/generate_files.py && rm /tmp/generate_files.py

RUN chmod -R 0755 /data/projects
RUN find /data/projects -type f -exec chmod 0644 {} \;
RUN find /data/projects -type d -exec chmod 0755 {} \;

RUN chown -R root:root /data/projects
RUN chmod 0777 /data/projects
RUN chmod 0777 /backup

WORKDIR /home/user

USER root
RUN chmod -R a+rX /data/projects

CMD ["/bin/bash"]
