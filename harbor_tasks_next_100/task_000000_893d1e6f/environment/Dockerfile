FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    findutils \
    file \
    diffutils \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/artifact-sync/cache && chmod -R 0777 /home/user/artifact-sync

RUN mkdir -p /var/repo/maven && chmod -R 0777 /var/repo

RUN mkdir -p /home/user/artifact-sync/cache/com/example/core/1.2.0 \
    && mkdir -p /home/user/artifact-sync/cache/com/example/utils/3.1.0 \
    && mkdir -p /home/user/artifact-sync/cache/com/example/web/2.0.0 \
    && mkdir -p /home/user/artifact-sync/cache/com/example/data/1.0.0 \
    && mkdir -p /home/user/artifact-sync/cache/org/internal/logging/2.0.0 \
    && mkdir -p /home/user/artifact-sync/cache/org/internal/config/1.5.2 \
    && mkdir -p /home/user/artifact-sync/cache/org/internal/security/3.0.0 \
    && mkdir -p /home/user/artifact-sync/cache/org/internal/metrics/1.1.0 \
    && mkdir -p /home/user/artifact-sync/cache/net/tools/parser/4.0.1 \
    && mkdir -p /home/user/artifact-sync/cache/net/tools/validator/2.2.0 \
    && mkdir -p /home/user/artifact-sync/cache/net/tools/formatter/1.3.0 \
    && mkdir -p /home/user/artifact-sync/cache/net/tools/converter/3.5.0

RUN dd if=/dev/urandom of=/home/user/artifact-sync/cache/com/example/core/1.2.0/core-1.2.0.jar bs=1024 count=75 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/com/example/utils/3.1.0/utils-3.1.0.jar bs=1024 count=120 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/com/example/web/2.0.0/web-2.0.0.jar bs=1024 count=200 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/com/example/data/1.0.0/data-1.0.0.jar bs=1024 count=95 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/org/internal/logging/2.0.0/logging-2.0.0.jar bs=1024 count=150 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/org/internal/config/1.5.2/config-1.5.2.jar bs=1024 count=80 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/org/internal/security/3.0.0/security-3.0.0.jar bs=1024 count=250 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/org/internal/metrics/1.1.0/metrics-1.1.0.jar bs=1024 count=110 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/net/tools/parser/4.0.1/parser-4.0.1.jar bs=1024 count=180 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/net/tools/validator/2.2.0/validator-2.2.0.jar bs=1024 count=90 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/net/tools/formatter/1.3.0/formatter-1.3.0.jar bs=1024 count=65 2>/dev/null \
    && dd if=/dev/urandom of=/home/user/artifact-sync/cache/net/tools/converter/3.5.0/converter-3.5.0.jar bs=1024 count=140 2>/dev/null

RUN mkdir -p /var/repo/maven/com/example/core/1.2.0 \
    && mkdir -p /var/repo/maven/com/example/utils/3.1.0 \
    && mkdir -p /var/repo/maven/com/example/web/2.0.0 \
    && mkdir -p /var/repo/maven/com/example/data/1.0.0 \
    && mkdir -p /var/repo/maven/org/internal/logging/2.0.0 \
    && mkdir -p /var/repo/maven/org/internal/config/1.5.2 \
    && mkdir -p /var/repo/maven/org/internal/security/3.0.0 \
    && mkdir -p /var/repo/maven/org/internal/metrics/1.1.0 \
    && mkdir -p /var/repo/maven/net/tools/parser/4.0.1 \
    && mkdir -p /var/repo/maven/net/tools/validator/2.2.0 \
    && mkdir -p /var/repo/maven/net/tools/formatter/1.3.0 \
    && mkdir -p /var/repo/maven/net/tools/converter/3.5.0

RUN sha1sum /home/user/artifact-sync/cache/com/example/core/1.2.0/core-1.2.0.jar | cut -d' ' -f1 > /var/repo/maven/com/example/core/1.2.0/core-1.2.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/com/example/utils/3.1.0/utils-3.1.0.jar | cut -d' ' -f1 > /var/repo/maven/com/example/utils/3.1.0/utils-3.1.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/com/example/web/2.0.0/web-2.0.0.jar | cut -d' ' -f1 > /var/repo/maven/com/example/web/2.0.0/web-2.0.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/com/example/data/1.0.0/data-1.0.0.jar | cut -d' ' -f1 > /var/repo/maven/com/example/data/1.0.0/data-1.0.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/org/internal/logging/2.0.0/logging-2.0.0.jar | cut -d' ' -f1 > /var/repo/maven/org/internal/logging/2.0.0/logging-2.0.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/org/internal/config/1.5.2/config-1.5.2.jar | cut -d' ' -f1 > /var/repo/maven/org/internal/config/1.5.2/config-1.5.2.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/org/internal/security/3.0.0/security-3.0.0.jar | cut -d' ' -f1 > /var/repo/maven/org/internal/security/3.0.0/security-3.0.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/org/internal/metrics/1.1.0/metrics-1.1.0.jar | cut -d' ' -f1 > /var/repo/maven/org/internal/metrics/1.1.0/metrics-1.1.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/net/tools/parser/4.0.1/parser-4.0.1.jar | cut -d' ' -f1 > /var/repo/maven/net/tools/parser/4.0.1/parser-4.0.1.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/net/tools/validator/2.2.0/validator-2.2.0.jar | cut -d' ' -f1 > /var/repo/maven/net/tools/validator/2.2.0/validator-2.2.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/net/tools/formatter/1.3.0/formatter-1.3.0.jar | cut -d' ' -f1 > /var/repo/maven/net/tools/formatter/1.3.0/formatter-1.3.0.jar.sha1 \
    && sha1sum /home/user/artifact-sync/cache/net/tools/converter/3.5.0/converter-3.5.0.jar | cut -d' ' -f1 > /var/repo/maven/net/tools/converter/3.5.0/converter-3.5.0.jar.sha1

RUN truncate -s 0 /var/repo/maven/com/example/core/1.2.0/core-1.2.0.jar \
    && truncate -s 0 /var/repo/maven/com/example/utils/3.1.0/utils-3.1.0.jar \
    && truncate -s 0 /var/repo/maven/org/internal/logging/2.0.0/logging-2.0.0.jar \
    && truncate -s 0 /var/repo/maven/org/internal/config/1.5.2/config-1.5.2.jar \
    && truncate -s 0 /var/repo/maven/net/tools/parser/4.0.1/parser-4.0.1.jar

RUN cp /home/user/artifact-sync/cache/com/example/web/2.0.0/web-2.0.0.jar /var/repo/maven/com/example/web/2.0.0/web-2.0.0.jar \
    && cp /home/user/artifact-sync/cache/com/example/data/1.0.0/data-1.0.0.jar /var/repo/maven/com/example/data/1.0.0/data-1.0.0.jar \
    && cp /home/user/artifact-sync/cache/org/internal/security/3.0.0/security-3.0.0.jar /var/repo/maven/org/internal/security/3.0.0/security-3.0.0.jar \
    && cp /home/user/artifact-sync/cache/org/internal/metrics/1.1.0/metrics-1.1.0.jar /var/repo/maven/org/internal/metrics/1.1.0/metrics-1.1.0.jar \
    && cp /home/user/artifact-sync/cache/net/tools/validator/2.2.0/validator-2.2.0.jar /var/repo/maven/net/tools/validator/2.2.0/validator-2.2.0.jar \
    && cp /home/user/artifact-sync/cache/net/tools/formatter/1.3.0/formatter-1.3.0.jar /var/repo/maven/net/tools/formatter/1.3.0/formatter-1.3.0.jar \
    && cp /home/user/artifact-sync/cache/net/tools/converter/3.5.0/converter-3.5.0.jar /var/repo/maven/net/tools/converter/3.5.0/converter-3.5.0.jar

RUN cat > /home/user/artifact-sync/artifacts.txt << 'EOF'
com.example:core:1.2.0
com.example:utils:3.1.0
com.example:web:2.0.0
com.example:data:1.0.0
org.internal:logging:2.0.0
org.internal:config:1.5.2
org.internal:security:3.0.0
org.internal:metrics:1.1.0
net.tools:parser:4.0.1
net.tools:validator:2.2.0
net.tools:formatter:1.3.0
net.tools:converter:3.5.0
EOF

RUN cat > /home/user/artifact-sync/sync.sh << 'EOFSCRIPT'
#!/bin/bash
#
# Maven artifact sync script
# Syncs artifacts from upstream to local repository
#

ARTIFACTS_FILE="/home/user/artifact-sync/artifacts.txt"
CACHE_DIR="/home/user/artifact-sync/cache"
REPO_DIR="/var/repo/maven"

# Convert GAV coordinate to path
# e.g., com.example:core:1.2.0 -> com/example/core/1.2.0/core-1.2.0.jar
gav_to_path() {
    local gav="$1"
    local group=$(echo "$gav" | cut -d: -f1 | tr '.' '/')
    local artifact=$(echo "$gav" | cut -d: -f2)
    local version=$(echo "$gav" | cut -d: -f3)
    echo "${group}/${artifact}/${version}/${artifact}-${version}.jar"
}

echo "Starting artifact sync at $(date)"
echo "Reading artifacts from $ARTIFACTS_FILE"

while IFS= read -r gav || [ -n "$gav" ]; do
    # Skip empty lines and comments
    [[ -z "$gav" || "$gav" =~ ^# ]] && continue

    echo "Processing: $gav"

    JAR_PATH=$(gav_to_path "$gav")
    CACHED_FILE="${CACHE_DIR}/${JAR_PATH}"
    REPO_FILE="${REPO_DIR}/${JAR_PATH}"
    REPO_DIR_PATH=$(dirname "$REPO_FILE")

    # Ensure repo directory exists
    mkdir -p "$REPO_DIR_PATH"

    # Check if cached file exists
    if [ ! -f "$CACHED_FILE" ]; then
        echo "  WARNING: Cache file not found: $CACHED_FILE"
        continue
    fi

    # Compute SHA1 of cached file and write to repo
    SHA1=$(sha1sum "$CACHED_FILE" | cut -d' ' -f1)
    echo "$SHA1" > "${REPO_FILE}.sha1"
    echo "  SHA1: $SHA1"

    # Copy jar to repo (BUG: typo in variable name - CACHE_FILE vs CACHED_FILE)
    cp "$CACHE_FILE" "$REPO_FILE"

    echo "  Synced to: $REPO_FILE"

done < "$ARTIFACTS_FILE"

echo "Sync completed at $(date)"
EOFSCRIPT

RUN chmod +x /home/user/artifact-sync/sync.sh

RUN chmod -R 0777 /home/user/artifact-sync \
    && chmod -R 0777 /var/repo/maven

WORKDIR /home/user

CMD ["/bin/bash"]
