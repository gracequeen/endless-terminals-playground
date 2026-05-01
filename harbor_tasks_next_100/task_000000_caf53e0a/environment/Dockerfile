FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    patch \
    diffutils \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/policygate/baseline/etc/nginx \
    && mkdir -p /home/user/policygate/baseline/etc/app \
    && mkdir -p /home/user/policygate/baseline/var/log \
    && mkdir -p /home/user/policygate/baseline/usr/local/bin \
    && mkdir -p /home/user/policygate/incoming \
    && mkdir -p /home/user/policygate/lib

RUN cat > /home/user/policygate/baseline/etc/nginx/nginx.conf << 'EOF'
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    server {
        listen 80;
        server_name localhost;
        root /var/www/html;
        index index.html;
    }
}
EOF

RUN cat > /home/user/policygate/baseline/etc/app/config.yaml << 'EOF'
app:
  name: myapp
  version: 1.0.0
  debug: false

database:
  host: localhost
  port: 5432
  name: appdb

logging:
  level: INFO
  format: json
EOF

RUN cat > /home/user/policygate/baseline/etc/shadow << 'EOF'
root:$6$rounds=4096$saltsalt$hashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhash:18000:0:99999:7:::
daemon:*:18000:0:99999:7:::
bin:*:18000:0:99999:7:::
sys:*:18000:0:99999:7:::
nobody:*:18000:0:99999:7:::
EOF

RUN touch /home/user/policygate/baseline/var/log/.keep

RUN cat > /home/user/policygate/baseline/usr/local/bin/app << 'EOF'
#!/bin/bash
echo "Application v1.0.0"
EOF

RUN chmod +x /home/user/policygate/baseline/usr/local/bin/app

RUN cat > /home/user/policygate/allowlist.txt << 'EOF'
etc/nginx/*
etc/app/*
usr/local/bin/*
EOF

RUN cat > /home/user/policygate/policy.md << 'EOF'
# Policy-as-Code Validation

## Overview
This system validates vendor patches against an allowlist of permitted modifications.

## Allowlist Format
The allowlist.txt file contains glob patterns, one per line:
- `etc/nginx/*` - allows modifications to any file under etc/nginx/
- `etc/app/*` - allows modifications to any file under etc/app/
- `usr/local/bin/*` - allows modifications to any file under usr/local/bin/

## Validation Process
1. Each patch in incoming/ is applied to a copy of baseline/
2. Modified files are detected using diff
3. Each modified file path is checked against allowlist patterns
4. Patches that only modify allowed paths PASS
5. Patches that modify disallowed paths FAIL

## Pattern Matching
Patterns use glob-style matching:
- `*` matches any characters within a path component
- Patterns are matched against relative paths from baseline root
EOF

RUN printf 'diff --git a/etc/nginx/nginx.conf b/etc/nginx/nginx.conf\n--- a/etc/nginx/nginx.conf\n+++ b/etc/nginx/nginx.conf\n@@ -7,7 +7,7 @@ events {\n }\n \n http {\n-    include /etc/nginx/mime.types;\n+    include /etc/nginx/mime.types;\r\n     default_type application/octet-stream;\n-    sendfile on;\n+    sendfile on;\r\n     keepalive_timeout 65;\n \n     server {\n' > /home/user/policygate/incoming/vendor-nginx-fix.patch

RUN printf 'diff --git a/etc/app/config.yaml b/etc/app/config.yaml\n--- a/etc/app/config.yaml\n+++ b/etc/app/config.yaml\n@@ -1,7 +1,7 @@\n app:\n   name: myapp\n-  version: 1.0.0\n-  debug: false\n+  version: 1.0.1\r\n+  debug: false\r\n \n database:\n   host: localhost\n' > /home/user/policygate/incoming/vendor-config-update.patch

RUN cat > /home/user/policygate/incoming/vendor-backdoor.patch << 'EOF'
diff --git a/etc/shadow b/etc/shadow
--- a/etc/shadow
+++ b/etc/shadow
@@ -1,5 +1,6 @@
 root:$6$rounds=4096$saltsalt$hashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhashhash:18000:0:99999:7:::
 daemon:*:18000:0:99999:7:::
 bin:*:18000:0:99999:7:::
 sys:*:18000:0:99999:7:::
 nobody:*:18000:0:99999:7:::
+backdoor:$6$evil$backdoorhash:18000:0:99999:7:::
EOF

RUN cat > /home/user/policygate/lib/diff_check.py << 'PYEOF'
#!/usr/bin/env python3
"""
Diff checker for policy validation.
Compares patched directory against baseline and validates against allowlist.
"""

import sys
import os
import subprocess
import fnmatch


def load_allowlist(allowlist_path):
    """Load allowlist patterns from file."""
    patterns = []
    with open(allowlist_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                patterns.append(line)
    return patterns


def path_matches_allowlist(path, patterns):
    """Check if path matches any allowlist pattern."""
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
        # Also check if path starts with pattern directory
        pattern_dir = pattern.rstrip('*').rstrip('/')
        if path.startswith(pattern_dir + '/') or path == pattern_dir:
            return True
    return False


def find_modified_files(workdir, baseline):
    """Find files that differ between workdir and baseline."""
    result = subprocess.run(
        ['diff', '-rq', workdir, baseline],
        capture_output=True,
        text=True
    )

    modified = []
    for line in result.stdout.splitlines():
        if line.startswith('Files ') and ' differ' in line:
            # Parse "Files /path/a and /path/b differ"
            parts = line.split(' and ')
            if len(parts) >= 1:
                file_path = parts[0].replace('Files ', '').strip()
                # Get relative path from workdir
                if file_path.startswith(workdir):
                    rel_path = file_path[len(workdir):].lstrip('/')
                    modified.append(rel_path)
        elif 'Only in' in line:
            # Handle new or deleted files
            # "Only in /path/dir: filename"
            if workdir in line:
                parts = line.split(': ')
                if len(parts) == 2:
                    dir_part = parts[0].replace('Only in ', '')
                    filename = parts[1]
                    if dir_part.startswith(workdir):
                        rel_dir = dir_part[len(workdir):].lstrip('/')
                        rel_path = os.path.join(rel_dir, filename) if rel_dir else filename
                        modified.append(rel_path)

    return modified


def is_modification_allowed(workdir, baseline, modified_files, patterns):
    """
    Check if all modifications are allowed.
    Returns (success, message).
    """
    unauthorized = []

    for filepath in modified_files:
        if not path_matches_allowlist(filepath, patterns):
            unauthorized.append(filepath)
            continue

        # For allowed paths, verify the diff is expected
        # This does a byte-exact comparison to catch any unexpected changes
        workfile = os.path.join(workdir, filepath)
        basefile = os.path.join(baseline, filepath)

        if os.path.exists(workfile) and os.path.exists(basefile):
            diff_result = subprocess.run(
                ['diff', workfile, basefile],
                capture_output=True,
                text=True
            )
            # BUG: This comparison against empty string means any diff output
            # causes failure, even for legitimately modified allowed files
            expected_diff = ""
            if diff_result.stdout != expected_diff:
                unauthorized.append(filepath)

    if unauthorized:
        return False, f"unauthorized modification detected: {', '.join(unauthorized)}"

    return True, "all modifications allowed"


def main():
    if len(sys.argv) != 4:
        print("Usage: diff_check.py <workdir> <baseline> <allowlist>", file=sys.stderr)
        sys.exit(2)

    workdir = sys.argv[1]
    baseline = sys.argv[2]
    allowlist_path = sys.argv[3]

    patterns = load_allowlist(allowlist_path)
    modified_files = find_modified_files(workdir, baseline)

    if not modified_files:
        print("no modifications detected")
        sys.exit(0)

    success, message = is_modification_allowed(workdir, baseline, modified_files, patterns)
    print(message)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
PYEOF

RUN chmod +x /home/user/policygate/lib/diff_check.py

RUN cat > /home/user/policygate/validate.sh << 'SHEOF'
#!/bin/bash
#
# Policy validation script
# Applies patches from incoming/ and validates against allowlist
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASELINE_DIR="$SCRIPT_DIR/baseline"
INCOMING_DIR="$SCRIPT_DIR/incoming"
ALLOWLIST="$SCRIPT_DIR/allowlist.txt"
LIB_DIR="$SCRIPT_DIR/lib"

# Track overall result
OVERALL_RESULT=0
PASS_COUNT=0
FAIL_COUNT=0

echo "=========================================="
echo "Policy-as-Code Validation"
echo "=========================================="
echo ""

# Process each patch
for patch_file in "$INCOMING_DIR"/*.patch; do
    if [ ! -f "$patch_file" ]; then
        echo "No patch files found in $INCOMING_DIR"
        exit 0
    fi

    patch_name=$(basename "$patch_file")
    echo "Processing: $patch_name"

    # Create temporary working directory
    WORKDIR=$(mktemp -d)
    trap "rm -rf $WORKDIR" EXIT

    # Copy baseline to working directory
    cp -r "$BASELINE_DIR"/* "$WORKDIR/"

    # Apply the patch
    cd "$WORKDIR"
    if ! patch -p1 < "$patch_file" > /dev/null 2>&1; then
        echo "  Status: FAIL (patch failed to apply)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        OVERALL_RESULT=1
        rm -rf "$WORKDIR"
        trap - EXIT
        echo ""
        continue
    fi
    cd "$SCRIPT_DIR"

    # Run diff check
    if python3 "$LIB_DIR/diff_check.py" "$WORKDIR" "$BASELINE_DIR" "$ALLOWLIST" 2>&1; then
        echo "  Status: PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "  Status: FAIL (unauthorized modification detected)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        OVERALL_RESULT=1
    fi

    # Cleanup
    rm -rf "$WORKDIR"
    trap - EXIT
    echo ""
done

echo "=========================================="
echo "Summary: $PASS_COUNT passed, $FAIL_COUNT failed"
echo "=========================================="

exit $OVERALL_RESULT
SHEOF

RUN chmod +x /home/user/policygate/validate.sh

RUN chown -R 1000:1000 /home/user/policygate && chmod -R 0755 /home/user/policygate

RUN chmod 0666 /home/user/policygate/validate.sh \
    && chmod 0666 /home/user/policygate/lib/diff_check.py \
    && chmod 0666 /home/user/policygate/policy.md \
    && chmod 0666 /home/user/policygate/allowlist.txt

RUN find /home/user/policygate/baseline -type f -exec chmod 0666 {} \;
RUN find /home/user/policygate/incoming -type f -exec chmod 0666 {} \;

RUN chmod 0777 /home/user/policygate \
    && chmod 0777 /home/user/policygate/lib \
    && chmod 0777 /home/user/policygate/baseline \
    && chmod 0777 /home/user/policygate/incoming \
    && find /home/user/policygate/baseline -type d -exec chmod 0777 {} \;

RUN chmod +x /home/user/policygate/validate.sh

WORKDIR /home/user

USER 1000

CMD ["/bin/bash"]
