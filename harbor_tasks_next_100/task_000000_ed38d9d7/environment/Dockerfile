FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/monitoring/templates /home/user/monitoring/rules

WORKDIR /tmp
RUN wget -q https://github.com/prometheus/alertmanager/releases/download/v0.27.0/alertmanager-0.27.0.linux-amd64.tar.gz && \
    tar xzf alertmanager-0.27.0.linux-amd64.tar.gz && \
    cp alertmanager-0.27.0.linux-amd64/alertmanager /home/user/monitoring/alertmanager && \
    chmod +x /home/user/monitoring/alertmanager && \
    rm -rf alertmanager-0.27.0.linux-amd64 alertmanager-0.27.0.linux-amd64.tar.gz

RUN cat > /home/user/monitoring/alertmanager.yml << 'ENDOFCONFIG'
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXX'

templates:
  - 'templates/*.tmpl'

route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'cluster']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
    - match:
        severity: warning
      receiver: 'slack-warnings'
    - match_re:
        service: ^(foo|bar)$
      receiver: 'team-backend'

receivers:
  - name: 'default-receiver'
    slack_configs:
      - channel: '#alerts-general'
        send_resolved: true

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'fake-pagerduty-key-12345'
        severity: critical

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#alerts-warnings'
        send_resolved: true

  - name: 'team-backend'
    slack_configs:
      - channel: '#team-backend-alerts'
        send_resolved:  true
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'

  - name: 'db-team'
    slack_configs:
      - channel: '#db-alerts'
ENDOFCONFIG

RUN printf '        \tsend_resolved: false\n' >> /home/user/monitoring/alertmanager.yml

RUN cat > /home/user/monitoring/templates/slack.tmpl << 'ENDOFTEMPLATE'
{{ define "slack.title" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .CommonLabels.alertname }}
{{ end }}

{{ define "slack.text" }}
{{ range .Alerts }}
*Alert:* {{ .Annotations.summary }}
*Description:* {{ .Annotations.description }}
*Severity:* {{ .Labels.severity }}
*Started:* {{ .StartsAt }}
{{ end }}
{{ end }}
ENDOFTEMPLATE

RUN cat > /home/user/monitoring/templates/pagerduty.tmpl << 'ENDOFTEMPLATE'
{{ define "pagerduty.default.description" }}
{{ .CommonAnnotations.summary }}
{{ end }}

{{ define "pagerduty.default.client" }}
Alertmanager
{{ end }}

{{ define "pagerduty.default.clientURL" }}
{{ template "__alertmanagerURL" . }}
{{ end }}

{{ define "pagerduty.default.instances" }}
{{ range .Alerts }}
  - {{ .Labels.instance }}
{{ end }}
{{ end }}
ENDOFTEMPLATE

RUN cat > /home/user/monitoring/receivers.yml << 'ENDOFRECEIVERS'
# Additional receivers configuration
# This file is not properly included in the main config

extra_receivers:
  - name: 'email-team'
    email_configs:
      - to: 'team@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
ENDOFRECEIVERS

RUN cat > /home/user/monitoring/rules/alerts.yml << 'ENDOFRULES'
groups:
  - name: example-alerts
    rules:
      - alert: HighErrorRate
        expr: job:request_errors:rate5m > 0.5
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} for {{ $labels.job }}"

      - alert: HighLatency
        expr: job:request_latency_seconds:mean5m > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "Latency is {{ $value }}s for {{ $labels.job }}"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."
ENDOFRULES

RUN cat > /home/user/monitoring/rules/database.yml << 'ENDOFRULES'
groups:
  - name: database-alerts
    rules:
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_activity_count > 100
        for: 5m
        labels:
          severity: warning
          service: database
        annotations:
          summary: "High number of database connections"
          description: "Database has {{ $value }} active connections"

      - alert: DatabaseReplicationLag
        expr: pg_replication_lag > 300
        for: 10m
        labels:
          severity: critical
          service: database
        annotations:
          summary: "Database replication lag is high"
          description: "Replication lag is {{ $value }} seconds"
ENDOFRULES

RUN chmod -R 0777 /home/user/monitoring

WORKDIR /home/user

CMD ["/bin/bash"]
