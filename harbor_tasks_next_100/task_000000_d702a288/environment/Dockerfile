FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest semgrep==1.45.0

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/project/.security \
    && mkdir -p /home/user/project/reports \
    && mkdir -p /home/user/project/src/config \
    && mkdir -p /home/user/project/src/db \
    && mkdir -p /home/user/project/src/utils

RUN cat > /home/user/project/.security/scanner-config.yaml << 'EOF'
# Semgrep scanner configuration
# This config is used by run_scan.sh

rules:
  - p/python

# Path to ignore file - relative to config location
ignore_file: .security/.semgrepignore

# Severity threshold - findings at this level or above cause nonzero exit
severity_threshold: warning

# Output settings
output:
  format: json
  file: reports/scan-results.json
EOF

RUN cat > /home/user/project/.security/.semgrepignore << 'EOF'
# Semgrep ignore patterns
# These patterns suppress known false positives

# False positive: hardcoded password in defaults.py is just a placeholder/example
src/config/defaults.py:python.lang.security.audit.hardcoded-password-default

# False positive: queries.py uses parameterized queries, not string concatenation
src/db/queries.py:python.lang.security.audit.sqli-injection-psycopg2
EOF

RUN cat > /home/user/project/.security/suppressions.yaml << 'EOF'
# Suppression records for audit trail
# These document why certain findings are suppressed

suppressions:
  - rule_id: python.lang.security.audit.hardcoded-password-default
    file: src/config/defaults.py
    reason: "This is a placeholder/example value, not a real credential"
    approved_by: security-team
    date: 2024-01-15

  - rule_id: python.lang.security.audit.sqli-injection-psycopg2
    file: src/db/queries.py
    reason: "False positive - code uses parameterized queries with %s placeholders"
    approved_by: security-team
    date: 2024-01-15
EOF

RUN cat > /home/user/project/src/config/__init__.py << 'EOF'
# Config module
EOF

RUN cat > /home/user/project/src/config/defaults.py << 'EOF'
"""Default configuration values for the application."""

# Database settings
DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_NAME = "myapp"

# This is a placeholder for local development only
# In production, this is overridden by environment variables
DEFAULT_PASSWORD = "changeme123"  # nosec - this is intentionally a placeholder

# API settings
API_TIMEOUT = 30
API_RETRY_COUNT = 3

# Feature flags
ENABLE_DEBUG_MODE = False
ENABLE_METRICS = True
EOF

RUN cat > /home/user/project/src/db/__init__.py << 'EOF'
# Database module
EOF

RUN cat > /home/user/project/src/db/queries.py << 'EOF'
"""Database query functions using parameterized queries."""

import psycopg2


def get_user_by_id(conn, user_id):
    """Fetch a user by their ID using parameterized query."""
    cursor = conn.cursor()
    # This is a parameterized query - %s is a placeholder, not string formatting
    query = "SELECT id, username, email FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()


def search_users_by_name(conn, name_pattern):
    """Search users by name pattern using parameterized query."""
    cursor = conn.cursor()
    # Using LIKE with parameterized query
    query = "SELECT id, username FROM users WHERE username LIKE %s"
    cursor.execute(query, (f"%{name_pattern}%",))
    return cursor.fetchall()


def get_user_orders(conn, user_id, status):
    """Get orders for a user with specific status."""
    cursor = conn.cursor()
    query = "SELECT * FROM orders WHERE user_id = %s AND status = %s"
    cursor.execute(query, (user_id, status))
    return cursor.fetchall()
EOF

RUN cat > /home/user/project/src/utils/__init__.py << 'EOF'
# Utils module
EOF

RUN cat > /home/user/project/src/utils/helpers.py << 'EOF'
"""Utility helper functions."""

import hashlib
import os


def generate_token():
    """Generate a random token."""
    return hashlib.sha256(os.urandom(32)).hexdigest()


def sanitize_input(user_input):
    """Basic input sanitization."""
    if not isinstance(user_input, str):
        return str(user_input)
    # Remove potentially dangerous characters
    return user_input.replace("<", "&lt;").replace(">", "&gt;")


def validate_email(email):
    """Simple email validation."""
    return "@" in email and "." in email
EOF

RUN cat > /home/user/project/src/utils/logging.py << 'EOF'
"""Logging utilities."""

import logging
import sys


def setup_logger(name, level=logging.INFO):
    """Set up a logger with standard formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# This looks like a secret but it's just a log format identifier
LOG_SECRET_MARKER = "AUDIT_LOG_12345"
EOF

RUN cat > /home/user/project/run_scan.sh << 'EOFSCRIPT'
#!/bin/bash
# SAST scan wrapper script
# Runs semgrep with our security configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIG_FILE=".security/scanner-config.yaml"
REPORT_FILE="reports/scan-results.json"

# Parse config file for settings
IGNORE_FILE=$(grep -E "^ignore_file:" "$CONFIG_FILE" | awk '{print $2}' | tr -d '"' | tr -d "'")
SEVERITY=$(grep -E "^severity_threshold:" "$CONFIG_FILE" | awk '{print $2}' | tr -d '"' | tr -d "'")

echo "Running SAST scan..."
echo "Config: $CONFIG_FILE"
echo "Ignore file: $IGNORE_FILE"
echo "Severity threshold: $SEVERITY"

# Build semgrep command
SEMGREP_CMD="semgrep --config p/python --json -o $REPORT_FILE"

# Add ignore file if specified
if [ -n "$IGNORE_FILE" ]; then
    SEMGREP_CMD="$SEMGREP_CMD --exclude-rules-file $IGNORE_FILE"
fi

# Add severity threshold
if [ -n "$SEVERITY" ]; then
    SEMGREP_CMD="$SEMGREP_CMD --severity $SEVERITY"
fi

# Add source directory
SEMGREP_CMD="$SEMGREP_CMD src/"

echo "Executing: $SEMGREP_CMD"
$SEMGREP_CMD

# Check results
FINDING_COUNT=$(jq '.results | length' "$REPORT_FILE")
echo "Scan complete. Found $FINDING_COUNT findings."

# Exit nonzero if there are WARNING or ERROR severity findings
WARNING_COUNT=$(jq '[.results[] | select(.extra.severity == "WARNING" or .extra.severity == "ERROR")] | length' "$REPORT_FILE")
if [ "$WARNING_COUNT" -gt 0 ]; then
    echo "ERROR: $WARNING_COUNT findings at WARNING level or above. Failing scan."
    exit 1
fi

echo "Scan passed."
exit 0
EOFSCRIPT

RUN chmod +x /home/user/project/run_scan.sh

RUN cat > /home/user/project/reports/scan-results.json << 'EOF'
{
  "results": [
    {
      "check_id": "python.lang.security.audit.hardcoded-password-default",
      "path": "src/config/defaults.py",
      "start": {"line": 12, "col": 1},
      "end": {"line": 12, "col": 32},
      "extra": {
        "message": "Hardcoded password detected",
        "severity": "WARNING",
        "metadata": {}
      }
    },
    {
      "check_id": "python.lang.security.audit.sqli-injection-psycopg2",
      "path": "src/db/queries.py",
      "start": {"line": 10, "col": 5},
      "end": {"line": 10, "col": 65},
      "extra": {
        "message": "Possible SQL injection with psycopg2",
        "severity": "WARNING",
        "metadata": {}
      }
    },
    {
      "check_id": "python.lang.security.audit.logging-sensitive-data",
      "path": "src/utils/logging.py",
      "start": {"line": 25, "col": 1},
      "end": {"line": 25, "col": 35},
      "extra": {
        "message": "Variable name suggests sensitive data in logs",
        "severity": "INFO",
        "metadata": {}
      }
    },
    {
      "check_id": "python.lang.best-practice.missing-type-hints",
      "path": "src/utils/helpers.py",
      "start": {"line": 8, "col": 1},
      "end": {"line": 10, "col": 50},
      "extra": {
        "message": "Function missing type hints",
        "severity": "INFO",
        "metadata": {}
      }
    }
  ],
  "errors": [],
  "version": "1.45.0"
}
EOF

RUN chmod -R 0777 /home/user/project

RUN useradd -m -d /home/user -s /bin/bash user || true

CMD ["/bin/bash"]
