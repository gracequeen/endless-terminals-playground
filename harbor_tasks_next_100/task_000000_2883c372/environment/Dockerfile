FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    nginx \
    curl \
    wget \
    python3 \
    python3-pip \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/mirror/staging \
    && mkdir -p /home/user/mirror/archive \
    && chmod -R 0777 /home/user/mirror

RUN mkdir -p /var/www/repo/com/example/core/1.2.0 \
    && mkdir -p /var/www/repo/com/example/utils/2.0.1 \
    && mkdir -p /var/www/repo/com/example/auth/1.5.3 \
    && mkdir -p /var/www/repo/com/example/data/3.1.0 \
    && mkdir -p /var/www/repo/com/example/web/2.2.0 \
    && mkdir -p /var/www/repo/com/example/cache/1.0.4 \
    && mkdir -p /var/www/repo/com/example/logging/1.1.0 \
    && mkdir -p /var/www/repo/com/example/metrics/0.9.2

RUN echo "core-1.2.0 jar content version 1" > /var/www/repo/com/example/core/1.2.0/core-1.2.0.jar \
    && echo "utils-2.0.1 jar content version 1" > /var/www/repo/com/example/utils/2.0.1/utils-2.0.1.jar \
    && echo "auth-1.5.3 jar content version 2 updated" > /var/www/repo/com/example/auth/1.5.3/auth-1.5.3.jar \
    && echo "data-3.1.0 jar content version 1" > /var/www/repo/com/example/data/3.1.0/data-3.1.0.jar \
    && echo "web-2.2.0 jar content version 1" > /var/www/repo/com/example/web/2.2.0/web-2.2.0.jar \
    && echo "cache-1.0.4 jar content version 2 updated" > /var/www/repo/com/example/cache/1.0.4/cache-1.0.4.jar \
    && echo "logging-1.1.0 jar content version 1" > /var/www/repo/com/example/logging/1.1.0/logging-1.1.0.jar \
    && echo "metrics-0.9.2 jar content version 2 updated" > /var/www/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar

RUN cd /var/www/repo/com/example/core/1.2.0 && sha1sum core-1.2.0.jar | awk '{print $1}' > core-1.2.0.jar.sha1 \
    && cd /var/www/repo/com/example/utils/2.0.1 && sha1sum utils-2.0.1.jar | awk '{print $1}' > utils-2.0.1.jar.sha1 \
    && cd /var/www/repo/com/example/auth/1.5.3 && sha1sum auth-1.5.3.jar | awk '{print $1}' > auth-1.5.3.jar.sha1 \
    && cd /var/www/repo/com/example/data/3.1.0 && sha1sum data-3.1.0.jar | awk '{print $1}' > data-3.1.0.jar.sha1 \
    && cd /var/www/repo/com/example/web/2.2.0 && sha1sum web-2.2.0.jar | awk '{print $1}' > web-2.2.0.jar.sha1 \
    && cd /var/www/repo/com/example/cache/1.0.4 && sha1sum cache-1.0.4.jar | awk '{print $1}' > cache-1.0.4.jar.sha1 \
    && cd /var/www/repo/com/example/logging/1.1.0 && sha1sum logging-1.1.0.jar | awk '{print $1}' > logging-1.1.0.jar.sha1 \
    && cd /var/www/repo/com/example/metrics/0.9.2 && sha1sum metrics-0.9.2.jar | awk '{print $1}' > metrics-0.9.2.jar.sha1

RUN CORE_HASH=$(sha1sum /var/www/repo/com/example/core/1.2.0/core-1.2.0.jar | awk '{print $1}') && \
    UTILS_HASH=$(sha1sum /var/www/repo/com/example/utils/2.0.1/utils-2.0.1.jar | awk '{print $1}') && \
    DATA_HASH=$(sha1sum /var/www/repo/com/example/data/3.1.0/data-3.1.0.jar | awk '{print $1}') && \
    WEB_HASH=$(sha1sum /var/www/repo/com/example/web/2.2.0/web-2.2.0.jar | awk '{print $1}') && \
    LOGGING_HASH=$(sha1sum /var/www/repo/com/example/logging/1.1.0/logging-1.1.0.jar | awk '{print $1}') && \
    echo "${CORE_HASH}  core-1.2.0.jar" > /home/user/mirror/manifest.sha1 && \
    echo "${UTILS_HASH}  utils-2.0.1.jar" >> /home/user/mirror/manifest.sha1 && \
    echo "0000000000000000000000000000000000000001  auth-1.5.3.jar" >> /home/user/mirror/manifest.sha1 && \
    echo "${DATA_HASH}  data-3.1.0.jar" >> /home/user/mirror/manifest.sha1 && \
    echo "${WEB_HASH}  web-2.2.0.jar" >> /home/user/mirror/manifest.sha1 && \
    echo "0000000000000000000000000000000000000002  cache-1.0.4.jar" >> /home/user/mirror/manifest.sha1 && \
    echo "${LOGGING_HASH}  logging-1.1.0.jar" >> /home/user/mirror/manifest.sha1 && \
    echo "0000000000000000000000000000000000000003  metrics-0.9.2.jar" >> /home/user/mirror/manifest.sha1

RUN cat <<'EOF' > /home/user/mirror/artifacts.list
http://127.0.0.1:8080/repo/com/example/core/1.2.0/core-1.2.0.jar
http://127.0.0.1:8080/repo/com/example/utils/2.0.1/utils-2.0.1.jar
http://127.0.0.1:8080/repo/com/example/auth/1.5.3/auth-1.5.3.jar
http://127.0.0.1:8080/repo/com/example/data/3.1.0/data-3.1.0.jar
http://127.0.0.1:8080/repo/com/example/web/2.2.0/web-2.2.0.jar
http://127.0.0.1:8080/repo/com/example/cache/1.0.4/cache-1.0.4.jar
http://127.0.0.1:8080/repo/com/example/logging/1.1.0/logging-1.1.0.jar
http://127.0.0.1:8080/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar
EOF

RUN cat <<'EOF' > /home/user/mirror/sync.sh
#!/bin/bash

set -e

MIRROR_DIR="/home/user/mirror"
ARTIFACTS_LIST="${MIRROR_DIR}/artifacts.list"
MANIFEST_FILE="${MIRROR_DIR}/manifest.sha1"
STAGING_DIR="${MIRROR_DIR}/staging"
ARCHIVE_DIR="${MIRROR_DIR}/archive"

# Clean staging directory
rm -f "${STAGING_DIR}"/*

# Read each artifact URL and process
while IFS= read -r url; do
    if [ -z "$url" ]; then
        continue
    fi

    # Extract filename from URL
    filename=$(basename "$url")

    echo "Downloading ${filename}..."
    curl -s -o "${STAGING_DIR}/${filename}" "$url"

    # Compute sha1sum of downloaded file
    computed_hash=$(sha1sum "${STAGING_DIR}/${filename}" | awk '{print $1}')

    # Get expected hash from manifest
    expected_hash=$(grep "  ${filename}$" "${MANIFEST_FILE}" | awk '{print $1}')

    if [ -z "$expected_hash" ]; then
        echo "ERROR: No manifest entry for ${filename}"
        exit 1
    fi

    # Compare checksums
    if [ "$computed_hash" != "$expected_hash" ]; then
        echo "ERROR: Checksum mismatch for ${filename}"
        echo "  Expected: ${expected_hash}"
        echo "  Got:      ${computed_hash}"
        exit 1
    fi

    echo "Checksum verified for ${filename}"

    # Move to archive
    mv "${STAGING_DIR}/${filename}" "${ARCHIVE_DIR}/"
    echo "Archived ${filename}"

done < "${ARTIFACTS_LIST}"

echo "Sync completed successfully!"
exit 0
EOF

RUN chmod +x /home/user/mirror/sync.sh

RUN echo "old-artifact-1.0.0 jar content" > /home/user/mirror/archive/old-artifact-1.0.0.jar \
    && echo "legacy-lib-2.3.1 jar content" > /home/user/mirror/archive/legacy-lib-2.3.1.jar

RUN chmod -R 0777 /home/user/mirror

RUN rm /etc/nginx/sites-enabled/default

RUN cat <<'EOF' > /etc/nginx/sites-available/repo
server {
    listen 8080;
    server_name localhost;

    location /repo/ {
        alias /var/www/repo/;
        autoindex on;
    }
}
EOF

RUN ln -s /etc/nginx/sites-available/repo /etc/nginx/sites-enabled/repo

RUN cat <<'EOF' > /entrypoint.sh
#!/bin/bash
nginx
exec "$@"
EOF

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
