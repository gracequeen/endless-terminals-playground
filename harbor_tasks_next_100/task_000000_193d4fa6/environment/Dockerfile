FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    make \
    coreutils \
    bash \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/webapp/src/frontend \
    && mkdir -p /home/user/webapp/src/backend \
    && mkdir -p /home/user/webapp/scripts

RUN echo "2.4.1" > /home/user/webapp/VERSION

RUN cat > /home/user/webapp/src/frontend/index.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>WebApp</title>
</head>
<body>
    <div id="app"></div>
</body>
</html>
HTMLEOF

RUN cat > /home/user/webapp/src/frontend/app.js << 'JSEOF'
// WebApp Frontend Application
(function() {
    console.log("WebApp initialized");
    document.getElementById('app').innerHTML = '<h1>Welcome to WebApp</h1>';
})();
JSEOF

RUN cat > /home/user/webapp/src/backend/main.py << 'PYEOF'
#!/usr/bin/env python3
"""WebApp Backend Server"""

def main():
    print("Starting WebApp backend server...")
    # Server logic here

if __name__ == "__main__":
    main()
PYEOF

RUN cat > /home/user/webapp/scripts/checksum.sh << 'SHEOF'
#!/bin/bash
echo "{"
echo "  \"version\": \"$(cat VERSION)\","
echo "  \"checksums\": {"
first=true
for f in "$@"; do
    if [ "$first" = true ]; then
        first=false
    else
        echo ","
    fi
    base=$(basename "$f")
    sha=$(sha256sum "$f" | cut -d' ' -f1)
    printf "    \"%s\": \"%s\"" "$base" "$sha"
done
echo ""
echo "  }"
echo "}"
SHEOF

RUN chmod +x /home/user/webapp/scripts/checksum.sh

RUN cat > /home/user/webapp/Makefile << 'MAKEEOF'
.PHONY: frontend backend bundle manifest tag release clean

frontend:
	@echo "Building frontend..."
	@mkdir -p build/frontend
	@cat src/frontend/index.html src/frontend/app.js > build/frontend/bundle.js
	@echo "Frontend done"

backend:
	@echo "Building backend..."
	@mkdir -p build/backend
	@cp src/backend/main.py build/backend/server.py
	@echo "Backend done"

bundle: frontend backend
	@echo "Bundling artifacts..."
	@mkdir -p dist
	@cp build/frontend/bundle.js dist/
	@cp build/backend/app.py dist/server.py
	@echo "Bundle done"

manifest: bundle
	@echo "Generating manifest..."
	@./scripts/checksum.sh dist/bundle.js dist/server.py > dist/manifest.json
	@echo "Manifest done"

tag: manifest
	@echo "Would tag $(shell cat VERSION)"

release: clean tag
	@echo "Release complete"

clean:
	@rm -rf build dist
MAKEEOF

RUN chown -R 1000:1000 /home/user/webapp && chmod -R 0755 /home/user/webapp

WORKDIR /home/user
