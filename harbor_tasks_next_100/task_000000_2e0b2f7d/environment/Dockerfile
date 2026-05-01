FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    tar \
    time \
    strace \
    coreutils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/release/conf.d \
    && mkdir -p /home/user/release/checks \
    && mkdir -p /home/user/release/app \
    && mkdir -p /home/user/release/staging

RUN cat <<'EOF' > /home/user/release/conf.d/00-base.conf
# Base configuration
APP_NAME="myapp"
VERSION="1.2.3"
DEPLOY_ENV="production"
EOF

RUN cat <<'EOF' > /home/user/release/conf.d/10-paths.conf
# Path configuration
APP_ROOT="/home/user/release/app"
STAGING_ROOT="/home/user/release/staging"
LOG_DIR="/var/log/myapp"
TMP_DIR="/tmp/deploy"
EOF

RUN cat <<'EOF' > /home/user/release/conf.d/20-services.conf
# Service configuration
SERVICE_LIST=("web" "api" "worker" "scheduler")
PRIMARY_SERVICE="web"
RESTART_ORDER="scheduler worker api web"
EOF

RUN cat <<'EOF' > /home/user/release/conf.d/30-validators.conf
# Validator functions
validate_config() {
    if [ -z "$APP_NAME" ]; then
        echo "ERROR: APP_NAME not set"
        return 1
    fi
    if [ -z "$VERSION" ]; then
        echo "ERROR: VERSION not set"
        return 1
    fi
    return 0
}

validate_paths() {
    if [ ! -d "$APP_ROOT" ]; then
        echo "ERROR: APP_ROOT does not exist"
        return 1
    fi
    return 0
}
EOF

RUN cat <<'EOF' > /home/user/release/conf.d/40-health.conf
# Health check configuration - added last sprint
HEALTH_CHECK_ENABLED=true
HEALTH_TIMEOUT=2

# Build list of health endpoints for all service ports
HEALTH_ENDPOINTS=$(for i in $(seq 1 50); do echo "http://localhost:808$i/health"; done)

# Pre-warm health check connections to reduce deploy-time latency
for endpoint in $HEALTH_ENDPOINTS; do
    curl --connect-timeout 2 -s "$endpoint" >/dev/null 2>&1 || true
done

HEALTH_STATUS="initialized"
EOF

RUN cat <<'EOF' > /home/user/release/conf.d/50-notify.conf
# Notification configuration
NOTIFY_WEBHOOK_URL="https://hooks.example.com/deploy"
NOTIFY_CHANNEL="#deployments"
NOTIFY_ON_SUCCESS=true
NOTIFY_ON_FAILURE=true
EOF

RUN cat <<'EOF' > /home/user/release/checks/disk_space.sh
#!/bin/bash
# Check available disk space
MIN_SPACE_MB=100
AVAILABLE=$(df -m /home/user | tail -1 | awk '{print $4}')
if [ "$AVAILABLE" -lt "$MIN_SPACE_MB" ]; then
    echo "ERROR: Insufficient disk space. Need ${MIN_SPACE_MB}MB, have ${AVAILABLE}MB"
    exit 1
fi
echo "Disk space check passed: ${AVAILABLE}MB available"
exit 0
EOF

RUN cat <<'EOF' > /home/user/release/checks/permissions.sh
#!/bin/bash
# Check write permissions
DIRS_TO_CHECK="/home/user/release/staging /home/user/release"
for dir in $DIRS_TO_CHECK; do
    if [ ! -w "$dir" ]; then
        echo "ERROR: Cannot write to $dir"
        exit 1
    fi
done
echo "Permission check passed"
exit 0
EOF

RUN cat <<'EOF' > /home/user/release/checks/syntax_check.sh
#!/bin/bash
# Validate config syntax
for conf in /home/user/release/conf.d/*.conf; do
    bash -n "$conf" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "ERROR: Syntax error in $conf"
        exit 1
    fi
done
echo "Syntax check passed"
exit 0
EOF

RUN cat <<'EOF' > /home/user/release/deploy.sh
#!/bin/bash
# Deploy script for myapp
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_DIR="${SCRIPT_DIR}/conf.d"
CHECKS_DIR="${SCRIPT_DIR}/checks"

echo "=== Starting deployment ==="
echo "Loading configuration..."

# Source all config files in order
for conf in "${CONF_DIR}"/*.conf; do
    if [ -f "$conf" ]; then
        echo "  Sourcing $(basename "$conf")..."
        source "$conf"
    fi
done

echo "Configuration loaded."
echo "  APP_NAME: $APP_NAME"
echo "  VERSION: $VERSION"

echo ""
echo "Running preflight checks..."

# Run all check scripts
for check in "${CHECKS_DIR}"/*.sh; do
    if [ -f "$check" ]; then
        echo "  Running $(basename "$check")..."
        bash "$check"
    fi
done

echo "Preflight checks complete."
echo ""
echo "Creating deployment package..."

# Create tarball
TARBALL="/tmp/deploy-${APP_NAME}-${VERSION}.tar.gz"
tar -czf "$TARBALL" -C "${SCRIPT_DIR}" app/

echo "  Created: $TARBALL"

echo ""
echo "Deploying to staging..."

# Copy to staging
mkdir -p "${SCRIPT_DIR}/staging"
cp "$TARBALL" "${SCRIPT_DIR}/staging/"
tar -xzf "${SCRIPT_DIR}/staging/$(basename "$TARBALL")" -C "${SCRIPT_DIR}/staging/"

echo "  Copied to staging"

echo ""
echo "Writing manifest..."

# Write manifest
MANIFEST="${SCRIPT_DIR}/staging/manifest.txt"
cat > "$MANIFEST" <<MANIFEST_EOF
APP_NAME: ${APP_NAME}
VERSION: ${VERSION}
DEPLOYED_AT: $(date -Iseconds)
DEPLOYED_BY: ${USER:-unknown}
SERVICES: ${SERVICE_LIST[*]}
MANIFEST_EOF

echo "  Manifest written to $MANIFEST"

# Cleanup
rm -f "$TARBALL"

echo ""
echo "=== Deployment complete ==="
exit 0
EOF

RUN echo '{"name": "myapp", "version": "1.2.3"}' > /home/user/release/app/package.json

RUN cat <<'EOF' > /home/user/release/app/main.py
#!/usr/bin/env python3
"""Main application entry point."""

def main():
    print("Hello from myapp!")

if __name__ == "__main__":
    main()
EOF

RUN cat <<'EOF' > /home/user/release/app/config.yaml
app:
  name: myapp
  debug: false
  workers: 4
EOF

RUN mkdir -p /home/user/release/app/lib

RUN cat <<'EOF' > /home/user/release/app/lib/utils.py
"""Utility functions."""

def format_output(msg):
    return f"[myapp] {msg}"
EOF

RUN chmod +x /home/user/release/deploy.sh \
    && chmod +x /home/user/release/checks/*.sh

RUN chown -R 1000:1000 /home/user/release \
    && chmod -R 0777 /home/user/release

USER 1000

WORKDIR /home/user

CMD ["/bin/bash"]
