I'm an SRE and our monitoring stack just alerted me that several services need their configuration updated across two different config formats. We use a YAML file for our Prometheus alerting rules and a TOML file for our uptime checker daemon.

Here's what I need done:

**1. Prometheus Alerting Rules (YAML) at /etc/monitoring/alerts.yaml:**

The file currently has some alerting rules, but I need the following changes:
- Find the alert rule named `HighLatency` and change its `for` duration from whatever it currently is to `3m`
- Find the alert rule named `ServiceDown` and add a new label `escalation_level: critical` under its `labels` section (keep existing labels)
- Add a completely new alert rule in the same `rules` list with these exact specs:
  - alert: `DiskSpaceLow`
  - expr: `node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1`
  - for: `10m`
  - labels:
    - severity: `warning`
    - team: `infrastructure`
  - annotations:
    - summary: `Disk space below 10% on {{ $labels.instance }}`

**2. Uptime Checker Config (TOML) at /etc/monitoring/uptime.toml:**

This file configures which endpoints we check. I need:
- In the `[global]` section, change `check_interval` from its current value to `30`
- In the `[global]` section, add a new key `timeout = 10` if it doesn't exist
- Find the endpoint entry with `name = "api-gateway"` and change its `expected_status` to `200` and add `critical = true` to that same endpoint table
- Add a new endpoint to the `[[endpoints]]` array with:
  - name: `"payment-service"`
  - url: `"https://payments.internal.example.com/health"`
  - expected_status: `200`
  - critical: `true`
  - headers: a table containing `Authorization = "Bearer ${PAYMENTS_TOKEN}"`

**3. Validation Log:**

After making all changes, write a validation log to /home/user/config_changes.log with this exact format:
```
YAML_CHANGES:
- alerts.yaml: HighLatency for duration updated
- alerts.yaml: ServiceDown escalation_level added
- alerts.yaml: DiskSpaceLow alert added
TOML_CHANGES:
- uptime.toml: global.check_interval updated to 30
- uptime.toml: global.timeout added
- uptime.toml: api-gateway endpoint modified
- uptime.toml: payment-service endpoint added
VALIDATION: COMPLETE
```

Make sure both config files remain valid YAML and TOML respectively after your edits — I'll be loading them into our monitoring services. Preserve the overall structure and any comments in the files.
