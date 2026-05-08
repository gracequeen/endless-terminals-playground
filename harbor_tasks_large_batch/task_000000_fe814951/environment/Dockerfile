FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    python3 \
    python3-pip \
    grep \
    findutils \
    coreutils \
    sed \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/scanner/rules && chmod -R 0777 /home/user/scanner

RUN cat > /home/user/scanner/scan.sh << 'SCANEOF'
#!/bin/bash
TARGET="${1:-.}"
RULES_DIR="$(dirname "$0")/rules"

find_violations() {
    local rule_file="$1"
    local glob_pattern=$(sed -n '1p' "$rule_file")
    local regex_pattern=$(sed -n '2p' "$rule_file")
    local severity=$(sed -n '3p' "$rule_file")

    find "$TARGET" -name "$glob_pattern" -print0 | xargs -0 -P 4 -I {} sh -c '
        if grep -qE "'"$regex_pattern"'" "{}"; then
            echo "['"$severity"'] {} matches '"$(basename "$rule_file" .rule)"'"
        fi
    '
}

for rule in "$RULES_DIR"/*.rule; do
    find_violations "$rule" &
done
wait
SCANEOF

RUN chmod +x /home/user/scanner/scan.sh

RUN printf '*.env\n(PASSWORD|SECRET|KEY)=.+\nHIGH\n' > /home/user/scanner/rules/secrets.rule

RUN printf '*.sh\nchmod 777\nMEDIUM\n' > /home/user/scanner/rules/perms.rule

RUN printf '*.txt\n=\\d+$\nLOW\n' > /home/user/scanner/rules/deps.rule

RUN printf '*ockerfile*\n\nUSER root|privileged:\\s*true\nHIGH\n' > /home/user/scanner/rules/docker.rule

RUN printf '*.yaml\nhostNetwork:\\s*true\nMEDIUM\n' > /home/user/scanner/rules/network.rule

RUN mkdir -p /home/user/test-repo/config \
    && mkdir -p /home/user/test-repo/scripts \
    && mkdir -p /home/user/test-repo/src \
    && mkdir -p /home/user/test-repo/k8s \
    && mkdir -p /home/user/test-repo/.git/objects/pack

RUN printf 'DB_HOST=localhost\nDB_PORT=5432\nDB_PASSWORD=hunter2\nDB_NAME=myapp\n' > /home/user/test-repo/config/db.env

RUN cat > /home/user/test-repo/scripts/deploy.sh << 'DEPLOYEOF'
#!/bin/bash
echo "Deploying application..."
cd /opt/app
./run.sh
DEPLOYEOF

RUN chmod 777 /home/user/test-repo/scripts/deploy.sh

RUN cat > /home/user/test-repo/src/setup.sh << 'SETUPEOF'
#!/bin/bash
echo "Setting up build environment"
mkdir -p /tmp/build
chmod 777 /tmp/build
echo "Build directory ready"
SETUPEOF

RUN cat > /home/user/test-repo/src/config.py << 'CONFIGPYEOF'
# Application configuration
DEBUG = False
API_KEY=sk-live-abc123
DATABASE_URL = "postgresql://localhost/myapp"
CONFIGPYEOF

RUN printf 'requests==2.25.1\nflask==1.0\nnumpy\npandas\n' > /home/user/test-repo/requirements.txt

RUN cat > /home/user/test-repo/Dockerfile << 'DOCKERFILEEOF'
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
USER root
CMD ["python", "app.py"]
DOCKERFILEEOF

RUN cat > /home/user/test-repo/docker-compose.yml << 'COMPOSEEOF'
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    privileged: true
    volumes:
      - ./data:/data
COMPOSEEOF

RUN cat > /home/user/test-repo/k8s/service.yaml << 'K8SEOF'
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  hostNetwork: true
  containers:
    - name: app
      image: myapp:latest
      ports:
        - containerPort: 8080
K8SEOF

RUN printf 'PACK\x00\x00\x00\x02\x00\x00\x00\x00' > /home/user/test-repo/.git/objects/pack/pack-abc123.pack

RUN cat > /home/user/test-repo/.git/config << 'GITCONFIGEOF'
[core]
    repositoryformatversion = 0
    filemode = true
    bare = false
[remote "origin"]
    url = git@github.com:example/test-repo.git
    fetch = +refs/heads/*:refs/remotes/origin/*
GITCONFIGEOF

RUN chmod -R 0777 /home/user

WORKDIR /home/user

CMD ["/bin/bash"]
