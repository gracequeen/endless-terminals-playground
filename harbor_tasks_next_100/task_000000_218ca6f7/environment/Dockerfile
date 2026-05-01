FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/api /home/user/docs

RUN cat <<'EOF' > /home/user/api/routes.json
[
  {"method": "GET", "path": "/users", "description": "List all users"},
  {"method": "POST", "path": "/users", "description": "Create a new user"},
  {"method": "GET", "path": "/users/{id}", "description": "Get user by ID"}
]
EOF

RUN chmod 0777 /home/user && \
    chmod 0777 /home/user/api && \
    chmod 0777 /home/user/docs && \
    chmod 0644 /home/user/api/routes.json

WORKDIR /home/user
