FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sed \
    gawk \
    grep \
    jq \
    vim \
    nano \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/pg-backup-tool && chmod 0777 /home/user/pg-backup-tool

RUN cat <<'EOF' > /home/user/pg-backup-tool/package.json
{
  "name": "pg-backup-tool",
  "version": "2.3.1",
  "description": "PostgreSQL backup utility with support for incremental backups",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "test": "jest",
    "lint": "eslint ."
  },
  "keywords": [
    "postgresql",
    "backup",
    "database"
  ],
  "author": "DevOps Team",
  "license": "MIT",
  "dependencies": {
    "pg": "^8.11.0",
    "winston": "^3.8.0"
  },
  "devDependencies": {
    "jest": "^29.5.0",
    "eslint": "^8.40.0"
  }
}
EOF

RUN chmod 0666 /home/user/pg-backup-tool/package.json

RUN cat <<'EOF' > /home/user/pg-backup-tool/CHANGELOG.md
# Changelog

## [Unreleased]

## [2.3.1] - 2024-01-15
### Fixed
- Connection timeout handling for replicas

## [2.3.0] - 2024-01-02
### Added
- Support for PostgreSQL 16
EOF

RUN chmod 0666 /home/user/pg-backup-tool/CHANGELOG.md

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user/pg-backup-tool

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
