FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    bash \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/ci/scripts \
    && mkdir -p /home/user/ci/artifacts/frontend/dist \
    && mkdir -p /home/user/ci/build_output

RUN cat <<'EOF' > /home/user/ci/frontend.yaml
build:
  stage: build
  script:
    - ./scripts/build-frontend.sh

artifacts:
  paths:
    - artifacts/frontend/*.js
    - artifacts/frontend/*.css
    - artifacts/frontend/*.html
  expire_in: 7 days
EOF

RUN cat <<'EOF' > /home/user/ci/scripts/build-frontend.sh
#!/bin/bash
set -e
BUILD_DIR="/home/user/ci/build_output"
ARTIFACT_DIR="/home/user/ci/artifacts/frontend"

mkdir -p "$BUILD_DIR" "$ARTIFACT_DIR"

# Simulate build
echo "console.log('app');" > "$BUILD_DIR/app.bundle.js"
echo "body { margin: 0; }" > "$BUILD_DIR/styles.bundle.css"
echo "<!DOCTYPE html><html><head></head><body></body></html>" > "$BUILD_DIR/index.html"

# Stage artifacts
cp "$BUILD_DIR"/* "$ARTIFACT_DIR/dist/"

echo "Build complete"
EOF

RUN cat <<'EOF' > /home/user/ci/scripts/check-artifacts.sh
#!/bin/bash
cd /home/user/ci
count=$(ls -1 artifacts/frontend/*.js artifacts/frontend/*.css artifacts/frontend/*.html 2>/dev/null | wc -l)
if [ "$count" -eq 0 ]; then
    echo "ERROR: no matching files in artifacts/frontend/"
    exit 1
fi
echo "Found $count artifact(s) ready for upload"
exit 0
EOF

RUN chmod +x /home/user/ci/scripts/build-frontend.sh \
    && chmod +x /home/user/ci/scripts/check-artifacts.sh

RUN echo "console.log('app');" > /home/user/ci/build_output/app.bundle.js \
    && echo "body { margin: 0; }" > /home/user/ci/build_output/styles.bundle.css \
    && echo "<!DOCTYPE html><html><head></head><body></body></html>" > /home/user/ci/build_output/index.html

RUN echo "console.log('app');" > /home/user/ci/artifacts/frontend/dist/app.bundle.js \
    && echo "body { margin: 0; }" > /home/user/ci/artifacts/frontend/dist/styles.bundle.css \
    && echo "<!DOCTYPE html><html><head></head><body></body></html>" > /home/user/ci/artifacts/frontend/dist/index.html

RUN chmod -R 0777 /home/user/ci

RUN useradd -m -d /home/user -s /bin/bash user || true

WORKDIR /home/user

USER user
