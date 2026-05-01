FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/pg-backup-tool && chmod 0777 /home/user/pg-backup-tool

RUN cat <<'EOF' > /home/user/pg-backup-tool/package.json
{
  "name": "pg-backup-tool",
  "version": "2.3.1",
  "description": "A PostgreSQL backup utility with support for full and differential backups",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest",
    "lint": "eslint ."
  },
  "keywords": [
    "postgresql",
    "backup",
    "database",
    "utility"
  ],
  "author": "DevOps Team",
  "license": "MIT",
  "dependencies": {
    "pg": "^8.11.0",
    "commander": "^11.0.0",
    "winston": "^3.10.0",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "jest": "^29.6.0",
    "eslint": "^8.45.0"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/example/pg-backup-tool.git"
  }
}
EOF

RUN chmod 0666 /home/user/pg-backup-tool/package.json

RUN cat <<'EOF' > /home/user/pg-backup-tool/CHANGELOG.md
# Changelog

All notable changes to this project will be documented in this file.

## 2.3.1 - 2024-01-15

- Fixed connection timeout issue when backing up large databases
- Improved error messages for authentication failures
- Updated pg dependency to 8.11.0

## 2.3.0 - 2023-12-01

- Added support for differential backups
- New --compress flag for gzip compression
- Performance improvements for parallel backup operations

## 2.2.0 - 2023-10-15

- Added configuration file support
- New restore command with point-in-time recovery
- Improved logging with winston

## 2.1.0 - 2023-08-20

- Initial public release
- Full backup support for PostgreSQL databases
- Command-line interface with commander
- Basic scheduling support
EOF

RUN chmod 0666 /home/user/pg-backup-tool/CHANGELOG.md

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user/pg-backup-tool

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
