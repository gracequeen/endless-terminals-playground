FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/deploy/base \
    && mkdir -p /home/user/deploy/environments \
    && mkdir -p /home/user/deploy/services \
    && mkdir -p /home/user/deploy/overrides/staging \
    && mkdir -p /home/user/deploy/overrides/production \
    && mkdir -p /home/user/deploy/overrides/.legacy

RUN cat <<'EOF' > /home/user/deploy/base/defaults.yaml
database:
  host: db-dev.internal
  port: 5432
  pool_size: 5
cache:
  host: redis-dev.internal
  ttl: 300
logging:
  level: INFO
EOF

RUN cat <<'EOF' > /home/user/deploy/environments/staging.yaml
database:
  host: db-staging.internal
  pool_size: 10
cache:
  host: redis-staging.internal
EOF

RUN cat <<'EOF' > /home/user/deploy/environments/production.yaml
database:
  host: db-prod.internal
  pool_size: 50
cache:
  host: redis-prod.internal
logging:
  level: WARNING
EOF

RUN cat <<'EOF' > /home/user/deploy/services/web-api.yaml
database:
  pool_size: 20
  timeout: 30
cache:
  ttl: 600
features:
  rate_limiting: true
EOF

RUN cat <<'EOF' > /home/user/deploy/overrides/staging/web-api.yaml
database:
  pool_size: 15
features:
  debug_mode: true
EOF

RUN cat <<'EOF' > /home/user/deploy/overrides/production/web-api.yaml
database:
  host: db-prod.internal
  pool_size: 100
EOF

RUN cat <<'EOF' > /home/user/deploy/overrides/.legacy/web-api.yaml
database:
  host: db-prod.internal
EOF

RUN cat <<'EOF' > /home/user/deploy/render.py
#!/usr/bin/env python3
import sys
import yaml
from pathlib import Path

def deep_merge(base, override):
    """Recursively merge override into base."""
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    result = base.copy()
    for key, value in override.items():
        if key in result:
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_yaml(path):
    if path.exists():
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return {}

def render_config(environment, service):
    base_dir = Path(__file__).parent

    # Load layers
    base = load_yaml(base_dir / "base" / "defaults.yaml")
    env = load_yaml(base_dir / "environments" / f"{environment}.yaml")
    svc = load_yaml(base_dir / "services" / f"{service}.yaml")
    override = load_yaml(base_dir / "overrides" / environment / f"{service}.yaml")

    # Merge in order: base → env → svc → override
    # BUG: The variable name reuse causes issues with evaluation order
    config = deep_merge(base, env)
    config = deep_merge(config, svc)

    # This is where staging breaks: there's a hidden file being loaded
    # Check for legacy compatibility layer
    legacy_path = base_dir / "overrides" / ".legacy" / f"{service}.yaml"
    if legacy_path.exists():
        legacy = load_yaml(legacy_path)
        config = deep_merge(config, legacy)

    config = deep_merge(config, override)

    return config

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: render.py <environment> <service>", file=sys.stderr)
        sys.exit(1)

    env, svc = sys.argv[1], sys.argv[2]
    config = render_config(env, svc)
    print(yaml.dump(config, default_flow_style=False))
EOF

RUN chmod +x /home/user/deploy/render.py

RUN chmod -R 0777 /home/user/deploy

WORKDIR /home/user

CMD ["/bin/bash"]
