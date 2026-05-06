FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user && chmod 0777 /home/user

WORKDIR /home/user

RUN mkdir -p /home/user/docs-site && \
    cd /home/user/docs-site && \
    git init && \
    git config user.email "test@example.com" && \
    git config user.name "Test User"

RUN mkdir -p /home/user/docs-site/docs/getting-started && \
    mkdir -p /home/user/docs-site/docs/api && \
    mkdir -p /home/user/docs-site/docs/tutorials

RUN cat <<'EOF' > /home/user/docs-site/mkdocs.yml
site_name: Acme Docs
docs_dir: docs
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/install.md
    - Quick Start: getting-started/quickstart.md
    - Migration Guide: getting-started/migration.md
  - API Reference:
    - Overview: api/overview.md
    - Authentication: api/auth.md
    - Endpoints: api/endpoints.md
    - Legacy API: api/legacy-v1.md
  - Tutorials:
    - Basic Usage: tutorials/basic.md
    - Advanced Patterns: tutorials/advanced.md
    - Integrations: tutorials/integrations.md
  - Contributing: contributing.md
  - Changelog: changelog.md
EOF

RUN echo "# Welcome to Acme Docs" > /home/user/docs-site/docs/index.md && \
    echo "# Installation Guide" > /home/user/docs-site/docs/getting-started/install.md && \
    echo "# Quick Start" > /home/user/docs-site/docs/getting-started/quickstart.md && \
    echo "# Migration Guide" > /home/user/docs-site/docs/getting-started/migration.md && \
    echo "# API Overview" > /home/user/docs-site/docs/api/overview.md && \
    echo "# Authentication" > /home/user/docs-site/docs/api/auth.md && \
    echo "# API Endpoints" > /home/user/docs-site/docs/api/endpoints.md && \
    echo "# Legacy API v1" > /home/user/docs-site/docs/api/legacy-v1.md && \
    echo "# Basic Tutorial" > /home/user/docs-site/docs/tutorials/basic.md && \
    echo "# Advanced Patterns" > /home/user/docs-site/docs/tutorials/advanced.md && \
    echo "# Integrations" > /home/user/docs-site/docs/tutorials/integrations.md && \
    echo "# Contributing" > /home/user/docs-site/docs/contributing.md && \
    echo "# Changelog" > /home/user/docs-site/docs/changelog.md

RUN cd /home/user/docs-site && \
    git add -A && \
    git commit -m "Initial commit with all documentation files"

RUN cd /home/user/docs-site && \
    git rm docs/getting-started/migration.md && \
    git commit -m "Remove outdated migration guide"

RUN cd /home/user/docs-site && \
    git rm docs/api/endpoints.md && \
    git commit -m "Remove endpoints doc during API restructure"

RUN cd /home/user/docs-site && \
    git rm docs/api/legacy-v1.md && \
    git commit -m "Deprecate legacy API documentation"

RUN cd /home/user/docs-site && \
    git rm docs/tutorials/integrations.md && \
    git commit -m "Remove integrations tutorial - needs rewrite"

RUN chmod -R 0777 /home/user/docs-site

WORKDIR /home/user

CMD ["/bin/bash"]
