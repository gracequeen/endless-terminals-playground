FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/services && chmod 0777 /home/user && chmod 0777 /home/user/services

RUN cat <<'EOF' > /home/user/services/endpoints.conf
# Primary services
auth_endpoint=legacy-auth.internal:8080
cache_endpoint=legacy-redis.internal:6379
db_endpoint=legacy-postgres.internal:5432
session_endpoint=legacy-session.internal:8081

# Batch processing
queue_endpoint=legacy-rabbitmq.internal:5672
worker_endpoint=legacy-worker.internal:9000
scheduler_endpoint=legacy-scheduler.internal:9001
batch_endpoint=legacy-batch.internal:9002

# Storage services
storage_endpoint=legacy-minio.internal:9000
backup_endpoint=legacy-backup.internal:9003
archive_endpoint=legacy-archive.internal:9004

# Monitoring and logging
metrics_endpoint=legacy-prometheus.internal:9090
logging_endpoint=legacy-elasticsearch.internal:9200
tracing_endpoint=legacy-jaeger.internal:16686
alerting_endpoint=legacy-alertmanager.internal:9093

# API Gateway
gateway_endpoint=legacy-gateway.internal:8000
proxy_endpoint=legacy-proxy.internal:8001
loadbalancer_endpoint=legacy-lb.internal:8002

# Authentication and authorization
oauth_endpoint=legacy-oauth.internal:8082
ldap_endpoint=legacy-ldap.internal:389
sso_endpoint=legacy-sso.internal:8083

# Communication services
email_endpoint=legacy-smtp.internal:587
notification_endpoint=legacy-notify.internal:8084
websocket_endpoint=legacy-ws.internal:8085

# Data processing
etl_endpoint=legacy-etl.internal:9005
streaming_endpoint=legacy-kafka.internal:9092
analytics_endpoint=legacy-analytics.internal:9006

# Search and indexing
search_endpoint=legacy-solr.internal:8983
index_endpoint=legacy-indexer.internal:9007

# Configuration management
config_endpoint=legacy-consul.internal:8500
secrets_endpoint=legacy-vault.internal:8200

# Service mesh
mesh_endpoint=legacy-istio.internal:15000
sidecar_endpoint=legacy-envoy.internal:15001

# CI/CD
build_endpoint=legacy-jenkins.internal:8080
deploy_endpoint=legacy-argocd.internal:8081
registry_endpoint=legacy-harbor.internal:5000

# Miscellaneous
health_endpoint=legacy-health.internal:8086
status_endpoint=legacy-status.internal:8087
admin_endpoint=legacy-admin.internal:8088
debug_endpoint=legacy-debug.internal:8089
EOF

RUN chmod 0666 /home/user/services/endpoints.conf

CMD ["/bin/bash"]
