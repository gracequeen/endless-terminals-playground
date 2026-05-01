FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyyaml jinja2 jsonschema

RUN npm install -g markdownlint-cli

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/auditgen/data \
    && mkdir -p /home/user/auditgen/templates \
    && mkdir -p /home/user/auditgen/output \
    && chmod -R 0777 /home/user/auditgen

RUN cat <<'EOF' > /home/user/auditgen/generate.py
#!/usr/bin/env python3
"""
Audit Report Generator
Reads audit records from data/records.yaml, validates against schema.yaml,
and renders output to output/audit_report.md using Jinja2 template.
"""

import os
import yaml
import json
from jinja2 import Environment, FileSystemLoader, Undefined
from jsonschema import validate, ValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "records.yaml")
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.yaml")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_FILE = os.path.join(BASE_DIR, "output", "audit_report.md")


class SilentUndefined(Undefined):
    """Custom undefined that returns empty string instead of raising error."""
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ""

    def __str__(self):
        return ""


def load_yaml(filepath):
    """Load YAML file and return data."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


def validate_records(records, schema):
    """Validate each record against the schema."""
    item_schema = schema.get("items", schema)
    for i, record in enumerate(records):
        try:
            validate(instance=record, schema=item_schema)
        except ValidationError as e:
            raise ValidationError(f"Record {i} validation failed: {e.message}")


def render_report(records, template_dir, output_file):
    """Render the audit report using Jinja2 template."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=SilentUndefined
    )
    template = env.get_template("report.md.j2")

    output = template.render(records=records)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(output)

    print(f"Report generated: {output_file}")


def main():
    # Load data
    records = load_yaml(DATA_FILE)
    schema = load_yaml(SCHEMA_FILE)

    # Validate
    validate_records(records, schema)

    # Render
    render_report(records, TEMPLATE_DIR, OUTPUT_FILE)


if __name__ == "__main__":
    main()
EOF

RUN cat <<'EOF' > /home/user/auditgen/schema.yaml
type: array
items:
  type: object
  properties:
    record_id:
      type: string
      pattern: "^AUD-[0-9]{6}$"
    timestamp:
      type: string
      format: date-time
    actor:
      type: string
      minLength: 1
    action:
      type: string
      enum:
        - create
        - read
        - update
        - delete
        - login
        - logout
        - export
        - import
        - approve
        - reject
    resource:
      type: string
      minLength: 1
    outcome:
      type: string
      enum:
        - success
        - failure
        - partial
    notes:
      type: string
  required:
    - record_id
    - timestamp
    - actor
    - resource
    - outcome
EOF

RUN cat <<'EOF' > /home/user/auditgen/templates/report.md.j2
# Audit Report

Generated compliance audit report containing all recorded actions.

## Summary

Total records: {{ records | length }}

## Audit Records

| Record ID | Timestamp | Actor | Action | Resource | Outcome | Notes |
|-----------|-----------|-------|--------|----------|---------|-------|
{% for record in records %}
| {{ record.record_id }} | {{ record.timestamp }} | {{ record.actor }} | {{ record.action }} | {{ record.resource }} | {{ record.outcome }} | {{ record.notes | default('-', true) }} |
{% endfor %}

## Compliance Notes

- All actions have been logged according to policy requirements
- Records are retained for the mandatory 7-year period
- Access to this report is restricted to authorized personnel

### Action Categories

The following action types are tracked:

- create: Resource creation events
- read: Resource access events
- update: Resource modification events
- delete: Resource removal events
- login: Authentication events
- logout: Session termination events
- export: Data export events
- import: Data import events
- approve: Approval workflow events
- reject: Rejection workflow events

## Footer

Report generated automatically by auditgen compliance system.
EOF

RUN cat <<'EOF' > /home/user/auditgen/.markdownlint.json
{
  "MD013": {
    "line_length": 120
  },
  "MD032": true,
  "MD047": true,
  "MD009": true
}
EOF

RUN cat <<'EOF' > /home/user/auditgen/data/records.yaml
- record_id: "AUD-000001"
  timestamp: "2024-03-01T08:15:22Z"
  actor: "jsmith"
  action: "login"
  resource: "/auth/session"
  outcome: "success"
  notes: "Morning login from office IP"

- record_id: "AUD-000002"
  timestamp: "2024-03-01T08:17:45Z"
  actor: "jsmith"
  action: "read"
  resource: "/data/customers"
  outcome: "success"

- record_id: "AUD-000003"
  timestamp: "2024-03-01T09:00:00Z"
  actor: "awhite"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000004"
  timestamp: "2024-03-01T09:05:12Z"
  actor: "awhite"
  action: "create"
  resource: "/data/reports/q1-2024"
  outcome: "success"
  notes: "Quarterly report creation"

- record_id: "AUD-000005"
  timestamp: "2024-03-01T09:30:00Z"
  actor: "bgreen"
  action: "login"
  resource: "/auth/session"
  outcome: "failure"
  notes: "Invalid password attempt"

- record_id: "AUD-000006"
  timestamp: "2024-03-01T09:31:15Z"
  actor: "bgreen"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000007"
  timestamp: "2024-03-01T10:00:00Z"
  actor: "jsmith"
  action: "update"
  resource: "/data/customers/C-1001"
  outcome: "success"
  notes: "Address update per customer request"

- record_id: "AUD-000008"
  timestamp: "2024-03-01T10:15:00Z"
  actor: "cdavis"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000009"
  timestamp: "2024-03-01T10:20:30Z"
  actor: "cdavis"
  action: "export"
  resource: "/data/reports/annual-2023"
  outcome: "success"
  notes: "PDF export for board meeting"

- record_id: "AUD-000010"
  timestamp: "2024-03-01T11:00:00Z"
  actor: "awhite"
  action: "approve"
  resource: "/workflow/expense/EXP-2024-0142"
  outcome: "success"

- record_id: "AUD-000011"
  timestamp: "2024-03-01T11:30:00Z"
  actor: "jsmith"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000012"
  timestamp: "2024-03-01T12:00:00Z"
  actor: "eblack"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000013"
  timestamp: "2024-03-01T12:05:00Z"
  actor: "eblack"
  action: "read"
  resource: "/data/inventory"
  outcome: "success"

- record_id: "AUD-000014"
  timestamp: "2024-03-01T13:00:00Z"
  actor: "bgreen"
  action: "create"
  resource: "/data/orders/ORD-2024-0891"
  outcome: "success"

- record_id: "AUD-000015"
  timestamp: "2024-03-01T13:15:00Z"
  actor: "awhite"
  action: "reject"
  resource: "/workflow/expense/EXP-2024-0143"
  outcome: "success"
  notes: "Missing receipts"

- record_id: "AUD-000016"
  timestamp: "2024-03-01T14:00:00Z"
  actor: "cdavis"
  action: "update"
  resource: "/config/system/backup-schedule"
  outcome: "success"

- record_id: "AUD-000017"
  timestamp: "2024-03-01T14:30:00Z"
  actor: "eblack"
  action: "delete"
  resource: "/data/temp/staging-files"
  outcome: "success"
  notes: "Cleanup of staging area"

- record_id: "AUD-000018"
  timestamp: "2024-03-01T15:00:00Z"
  actor: "bgreen"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000019"
  timestamp: "2024-03-02T08:00:00Z"
  actor: "fwilson"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000020"
  timestamp: "2024-03-02T08:10:00Z"
  actor: "fwilson"
  action: "import"
  resource: "/data/vendors/batch-update"
  outcome: "partial"
  notes: "3 of 50 records failed validation"

- record_id: "AUD-000021"
  timestamp: "2024-03-02T09:00:00Z"
  actor: "jsmith"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000022"
  timestamp: "2024-03-02T09:15:00Z"
  actor: "jsmith"
  action: "read"
  resource: "/data/analytics/dashboard"
  outcome: "success"

- record_id: "AUD-000023"
  timestamp: "2024-03-02T10:00:00Z"
  actor: "awhite"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000024"
  timestamp: "2024-03-02T10:30:00Z"
  actor: "awhite"
  action: "approve"
  resource: "/workflow/purchase/PO-2024-0567"
  outcome: "success"

- record_id: "AUD-000025"
  timestamp: "2024-03-02T11:00:00Z"
  actor: "gmartin"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000026"
  timestamp: "2024-03-02T11:15:00Z"
  actor: "gmartin"
  action: "create"
  resource: "/data/customers/C-1089"
  outcome: "success"
  notes: "New enterprise customer onboarding"

- record_id: "AUD-000027"
  timestamp: "2024-03-02T12:00:00Z"
  actor: "fwilson"
  action: "update"
  resource: "/data/vendors/V-0234"
  outcome: "success"

- record_id: "AUD-000028"
  timestamp: "2024-03-02T13:00:00Z"
  actor: "cdavis"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000029"
  timestamp: "2024-03-02T13:30:00Z"
  actor: "cdavis"
  action: "read"
  resource: "/data/logs/security"
  outcome: "success"

- record_id: "AUD-000030"
  timestamp: "2024-03-02T14:00:00Z"
  actor: "eblack"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000031"
  timestamp: "2024-03-02T14:15:00Z"
  actor: "eblack"
  action: "export"
  resource: "/data/inventory/full-catalog"
  outcome: "success"

- record_id: "AUD-000032"
  timestamp: "2024-03-15T09:00:00Z"
  actor: "jsmith"
  action_type: "read"
  resource: "/data/customers"
  outcome: "success"
  notes: "Bulk customer data review"

- record_id: "AUD-000033"
  timestamp: "2024-03-15T10:00:00Z"
  actor: "hlee"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000034"
  timestamp: "2024-03-15T10:30:00Z"
  actor: "hlee"
  action: "create"
  resource: "/data/projects/PRJ-2024-0089"
  outcome: "success"

- record_id: "AUD-000035"
  timestamp: "2024-03-15T11:00:00Z"
  actor: "awhite"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000036"
  timestamp: "2024-03-15T11:30:00Z"
  actor: "awhite"
  action: "approve"
  resource: "/workflow/budget/BUD-2024-Q2"
  outcome: "success"
  notes: "Q2 budget approval"

- record_id: "AUD-000037"
  timestamp: "2024-03-15T12:00:00Z"
  actor: "gmartin"
  action: "update"
  resource: "/data/customers/C-1089"
  outcome: "success"

- record_id: "AUD-000038"
  timestamp: "2024-03-15T13:00:00Z"
  actor: "bgreen"
  action: "login"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000039"
  timestamp: "2024-03-15T13:15:00Z"
  actor: "bgreen"
  action: "read"
  resource: "/data/orders"
  outcome: "success"

- record_id: "AUD-000040"
  timestamp: "2024-03-15T14:00:00Z"
  actor: "fwilson"
  action: "delete"
  resource: "/data/vendors/V-0012"
  outcome: "success"
  notes: "Vendor deactivation per contract end"

- record_id: "AUD-000041"
  timestamp: "2024-03-15T14:30:00Z"
  actor: "cdavis"
  action: "export"
  resource: "/data/logs/audit-march"
  outcome: "success"

- record_id: "AUD-000042"
  timestamp: "2024-03-15T15:00:00Z"
  actor: "hlee"
  action: "update"
  resource: "/data/projects/PRJ-2024-0089"
  outcome: "success"

- record_id: "AUD-000043"
  timestamp: "2024-03-15T15:30:00Z"
  actor: "eblack"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000044"
  timestamp: "2024-03-15T16:00:00Z"
  actor: "jsmith"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000045"
  timestamp: "2024-03-15T16:30:00Z"
  actor: "awhite"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000046"
  timestamp: "2024-03-15T17:00:00Z"
  actor: "gmartin"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"

- record_id: "AUD-000047"
  timestamp: "2024-03-15T17:30:00Z"
  actor: "hlee"
  action: "logout"
  resource: "/auth/session"
  outcome: "success"
EOF

RUN chmod -R 0777 /home/user/auditgen

WORKDIR /home/user

CMD ["/bin/bash"]
