FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/infra/output && chmod -R 0777 /home/user/infra

RUN printf 'DB_HOST=postgres.internal\nREDIS_URL=redis://cache:6379\nVAULT_ADDR=https://vault.internal:8200\r\nAPI_SECRET=sk-prod-29f8a3e1\r\nDEPLOY_KEY=dk-7721-beta\r\n' > /home/user/infra/.env

RUN cat > /home/user/infra/provision.sh << 'SCRIPT'
#!/bin/bash
set -euo pipefail

source /home/user/infra/.env

echo "Loaded DB_HOST=$DB_HOST"
echo "Loaded REDIS_URL=$REDIS_URL"

# Sensitive vars handled separately for security
unset VAULT_ADDR API_SECRET DEPLOY_KEY

if [[ -f /home/user/infra/.env.secrets ]]; then
    source /home/user/infra/.env.secrets
fi

# Validate
echo "Checking vault connectivity..."
curl -sf "${VAULT_ADDR}/v1/sys/health" > /dev/null || echo "Vault check skipped"

# Generate config
cat > /home/user/infra/output/config.json <<EOF
{
    "database": "${DB_HOST}",
    "cache": "${REDIS_URL}",
    "vault": "${VAULT_ADDR}",
    "api_key": "${API_SECRET}",
    "deploy": "${DEPLOY_KEY}"
}
EOF

echo "Provisioning complete"
SCRIPT

RUN chmod +x /home/user/infra/provision.sh

RUN chmod -R 0777 /home/user/infra

WORKDIR /home/user

CMD ["/bin/bash"]
