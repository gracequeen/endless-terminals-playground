FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest jsonschema

RUN mkdir -p /home/user/webhooks/test_payloads && \
    chmod 0777 /home/user && \
    chmod 0777 /home/user/webhooks && \
    chmod 0777 /home/user/webhooks/test_payloads

RUN cat <<'EOF' > /home/user/webhooks/validate.sh
#!/bin/bash
python3 /home/user/webhooks/validator.py "$1"
exit $?
EOF

RUN chmod +x /home/user/webhooks/validate.sh

RUN cat <<'EOF' > /home/user/webhooks/validator.py
#!/usr/bin/env python3
import json
import sys
import jsonschema
from jsonschema import validate, ValidationError

def main():
    if len(sys.argv) != 2:
        print("Usage: validator.py <json_file>", file=sys.stderr)
        sys.exit(1)

    json_file = sys.argv[1]
    schema_file = "/home/user/webhooks/schema.json"

    try:
        with open(schema_file, 'r') as f:
            schema = json.load(f)
    except Exception as e:
        print(f"Error loading schema: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        validate(instance=data, schema=schema)
        print("Validation successful")
        sys.exit(0)
    except ValidationError as e:
        print(f"Validation failed: {e.message}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

RUN chmod +x /home/user/webhooks/validator.py

RUN cat <<'EOF' > /home/user/webhooks/schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["event_type", "timestamp", "data"],
  "properties": {
    "event_type": {
      "type": "string",
      "pattern": "^[a-z]+\\.[a-z]+$"
    },
    "timestamp": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$"
    },
    "data": {
      "type": "object",
      "required": ["user_id", "email", "metadata"],
      "properties": {
        "user_id": {
          "type": "integer"
        },
        "email": {
          "type": "string",
          "format": "email"
        },
        "metadata": {
          "type": "object",
          "required": ["source"],
          "properties": {
            "source": {
              "type": "string"
            }
          },
          "additionalProperties": false
        }
      }
    }
  }
}
EOF

RUN cat <<'EOF' > /home/user/webhooks/transform.jq
{
  id: (.data.userid | tonumber),
  email: .data.email,
  event: .event_type,
  created_at: .timestamp,
  source: .data.metadata.source,
  api_version: .data.metadata.version
}
EOF

RUN cat <<'EOF' > /home/user/webhooks/test_payloads/event_01.json
{
  "event_type": "user.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "user_id": 4521,
    "email": "test@example.com",
    "metadata": {"source": "api", "version": "2.1"}
  }
}
EOF

RUN cat <<'EOF' > /home/user/webhooks/test_payloads/event_02.json
{
  "event_type": "user.updated",
  "timestamp": "2024-01-16T14:45:30Z",
  "data": {
    "user_id": 7832,
    "email": "another@example.org",
    "metadata": {"source": "web", "version": "2.1"}
  }
}
EOF

RUN cat <<'EOF' > /home/user/webhooks/test_payloads/event_03.json
{
  "event_type": "user.deleted",
  "timestamp": "2024-01-17T09:15:00Z",
  "data": {
    "user_id": 1234,
    "email": "third@example.net",
    "metadata": {"source": "mobile", "version": "3.0"}
  }
}
EOF

RUN chmod 0666 /home/user/webhooks/schema.json && \
    chmod 0666 /home/user/webhooks/transform.jq && \
    chmod 0666 /home/user/webhooks/validator.py && \
    chmod 0755 /home/user/webhooks/validate.sh && \
    chmod 0644 /home/user/webhooks/test_payloads/*.json

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
