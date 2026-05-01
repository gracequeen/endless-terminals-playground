FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/backup/manifests \
    && mkdir -p /home/user/backup/data \
    && chmod -R 0777 /home/user/backup

RUN echo "file1.txt" > /home/user/backup/manifests/tape001.manifest \
    && echo "file2.txt" >> /home/user/backup/manifests/tape001.manifest \
    && echo "file3.txt" >> /home/user/backup/manifests/tape001.manifest \
    && echo "file4.txt" > /home/user/backup/manifests/tape002.manifest \
    && echo "file5.txt" >> /home/user/backup/manifests/tape002.manifest \
    && echo "file6.txt" >> /home/user/backup/manifests/tape002.manifest \
    && echo "file7.txt" > /home/user/backup/manifests/tape003.manifest \
    && echo "file8.txt" >> /home/user/backup/manifests/tape003.manifest \
    && echo "file9.txt" >> /home/user/backup/manifests/tape003.manifest

RUN echo "Content of file 1 for tape backup" > /home/user/backup/data/file1.txt \
    && echo "Content of file 2 for tape backup" > /home/user/backup/data/file2.txt \
    && echo "Content of file 3 for tape backup" > /home/user/backup/data/file3.txt \
    && echo "Content of file 4 for tape backup" > /home/user/backup/data/file4.txt \
    && echo "Content of file 5 for tape backup" > /home/user/backup/data/file5.txt \
    && echo "Content of file 6 for tape backup" > /home/user/backup/data/file6.txt \
    && echo "Content of file 7 for tape backup" > /home/user/backup/data/file7.txt \
    && echo "Content of file 8 for tape backup" > /home/user/backup/data/file8.txt \
    && echo "Content of file 9 for tape backup" > /home/user/backup/data/file9.txt

RUN cd /home/user/backup/data && \
    sqlite3 /home/user/backup/checksums.db "CREATE TABLE checksums (manifest_id TEXT, filepath TEXT, md5sum TEXT);" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape001', 'file1.txt', '$(md5sum file1.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape001', 'file2.txt', '$(md5sum file2.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape001', 'file3.txt', '$(md5sum file3.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape002', 'file4.txt', '$(md5sum file4.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape002', 'file5.txt', '$(md5sum file5.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape002', 'file6.txt', '$(md5sum file6.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape003', 'file7.txt', '$(md5sum file7.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape003', 'file8.txt', '$(md5sum file8.txt | cut -d' ' -f1)');" && \
    sqlite3 /home/user/backup/checksums.db "INSERT INTO checksums VALUES ('tape003', 'file9.txt', '$(md5sum file9.txt | cut -d' ' -f1)');"

RUN cat > /home/user/backup/validate.py << 'ENDOFSCRIPT'
#!/usr/bin/env python
"""
Tape Archive Validation Script
Originally written 2019 for Python 2.7
Validates manifest files against stored checksums
"""

import os
import sys
import hashlib
import sqlite3

print("Loading manifests...")

MANIFEST_DIR = "manifests"
DATA_DIR = "data"
DB_PATH = "checksums.db"

def get_manifest_id(manifest_file):
    """Extract manifest ID from filename."""
    return os.path.splitext(os.path.basename(manifest_file))[0]

def compute_file_hash(fpath):
    """Compute MD5 hash of a file."""
    file_hash = hashlib.md5(open(fpath).read()).hexdigest()
    return file_hash

def load_manifests():
    """Load all manifest files from the manifest directory."""
    manifests = {}
    for fname in os.listdir(MANIFEST_DIR):
        if fname.endswith('.manifest'):
            manifest_path = os.path.join(MANIFEST_DIR, fname)
            manifest_id = get_manifest_id(fname)
            with open(manifest_path, 'r') as f:
                files = [line.strip() for line in f if line.strip()]
            manifests[manifest_id] = files
    return manifests

def validate_checksums(manifests):
    """Validate file checksums against the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    all_valid = True

    for manifest_id, files in manifests.items():
        print("Checking manifest: %s" % manifest_id)
        for filepath in files:
            full_path = os.path.join(DATA_DIR, filepath)

            cursor.execute(
                "SELECT md5sum FROM checksums WHERE manifest_id=? AND filepath=?",
                (manifest_id, filepath)
            )
            for row in cursor.fetchall():
                stored = row[0]
                checksum = compute_file_hash(full_path)
                if checksum <> stored:
                    print("  %s: MISMATCH (expected %s, got %s)" % (filepath, stored, checksum))
                    all_valid = False
                else:
                    print("  %s: VALID" % filepath)

    conn.close()
    return all_valid

def main():
    """Main entry point."""
    try:
        manifests = load_manifests()
        if not manifests:
            print("No manifests found!")
            sys.exit(1)

        print("Found %d manifests" % len(manifests))

        if validate_checksums(manifests):
            print("All checksums validated successfully!")
            sys.exit(0)
        else:
            print("Some checksums failed validation!")
            sys.exit(1)
    except IOError, e:
        print("IO Error: %s" % str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
ENDOFSCRIPT

RUN chmod 0777 /home/user/backup/validate.py \
    && chmod 0777 /home/user/backup/checksums.db \
    && chmod -R 0777 /home/user/backup/manifests \
    && chmod -R 0777 /home/user/backup/data

WORKDIR /home/user

CMD ["/bin/bash"]
