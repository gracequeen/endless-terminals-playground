FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sed \
    gawk \
    perl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml

RUN mkdir -p /home/user/services /home/user/rotation && chmod 0777 /home/user /home/user/services /home/user/rotation

RUN cat <<'EOF' > /home/user/services/config.yaml
# Service Configuration File
# Last updated: 2024-01-15
# Environment: production

application:
  name: "MyApp"
  version: "2.5.1"
  debug: false

services:
  # Payment Gateway Service
  payment_gateway:
    enabled: true
    timeout: 30
    api_key: "sk_live_a1b2c3d4e5f6"
    endpoint: "https://api.payments.example.com/v2"
    retry_count: 3

  # Email Service Provider
  email_service:
    provider: "sendgrid"
    api_key: "sk_live_g7h8i9j0k1l2"
    from_address: "noreply@example.com"
    templates_path: "/opt/templates/email"

  # Analytics Platform
  analytics:
    api_key: "sk_live_m3n4o5p6q7r8"
    tracking_id: "UA-12345678-1"
    enabled: true

  # Cloud Storage
  storage:
    provider: "aws-s3"
    bucket: "my-app-assets"
    api_key: "sk_live_s9t0u1v2w3x4"
    region: "us-east-1"

  # Search Engine
  search:
    engine: "elasticsearch"
    api_key: "sk_live_y5z6a7b8c9d0"
    index_prefix: "myapp_"
    timeout_ms: 5000

  # Notification Service
  notifications:
    push:
      api_key: "sk_live_e1f2g3h4i5j6"
      provider: "firebase"
    sms:
      api_key: "sk_live_k7l8m9n0o1p2"
      provider: "twilio"

  # Authentication Provider
  auth:
    oauth_enabled: true
    api_key: "sk_live_q3r4s5t6u7v8"
    token_expiry: 3600
    refresh_enabled: true

  # CDN Configuration
  cdn:
    provider: "cloudflare"
    api_key: "sk_live_w9x0y1z2a3b4"
    zone_id: "abc123def456"

  # Monitoring Service
  monitoring:
    api_key: "sk_live_c5d6e7f8g9h0"
    alert_threshold: 90
    check_interval: 60

  # Database Backup Service
  backup:
    schedule: "0 2 * * *"
    api_key: "sk_live_i1j2k3l4m5n6"
    retention_days: 30

  # Third-party Integration
  integration:
    partner_api:
      api_key: "sk_live_o7p8q9r0s1t2"
      webhook_url: "https://hooks.example.com/incoming"
      secret: "webhook_secret_123"

# Logging Configuration
logging:
  level: "info"
  format: "json"
  output: "/var/log/myapp/app.log"

# Feature Flags
features:
  new_dashboard: true
  beta_features: false
  maintenance_mode: false
EOF

RUN chmod 0666 /home/user/services/config.yaml

RUN cat <<'EOF' > /home/user/rotation/new_keys.csv
old_key,new_key
sk_live_a1b2c3d4e5f6,sk_live_NEW_001_xyz
sk_live_g7h8i9j0k1l2,sk_live_NEW_002_xyz
sk_live_m3n4o5p6q7r8,sk_live_NEW_003_xyz
sk_live_s9t0u1v2w3x4,sk_live_NEW_004_xyz
sk_live_y5z6a7b8c9d0,sk_live_NEW_005_xyz
sk_live_e1f2g3h4i5j6,sk_live_NEW_006_xyz
sk_live_k7l8m9n0o1p2,sk_live_NEW_007_xyz
sk_live_q3r4s5t6u7v8,sk_live_NEW_008_xyz
sk_live_w9x0y1z2a3b4,sk_live_NEW_009_xyz
sk_live_c5d6e7f8g9h0,sk_live_NEW_010_xyz
sk_live_i1j2k3l4m5n6,sk_live_NEW_011_xyz
sk_live_o7p8q9r0s1t2,sk_live_NEW_012_xyz
EOF

RUN chmod 0644 /home/user/rotation/new_keys.csv

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
