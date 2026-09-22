#!/usr/bin/env bash
# Install docker compose plugin and buildx on Amazon Linux 2023.

set -euo pipefail

sudo mkdir -p /usr/libexec/docker/cli-plugins

# Docker Compose
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
    -o /usr/libexec/docker/cli-plugins/docker-compose
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-compose

# Docker Buildx v0.34.1
sudo curl -fsSL https://github.com/docker/buildx/releases/download/v0.34.1/buildx-v0.34.1.linux-amd64 \
    -o /usr/libexec/docker/cli-plugins/docker-buildx
sudo chmod +x /usr/libexec/docker/cli-plugins/docker-buildx

echo "docker compose: $(docker compose version)"
echo "docker buildx:  $(docker buildx version)"
