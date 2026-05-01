FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install flask pytest

RUN mkdir -p /home/user/healthcheck && chmod 0777 /home/user && chmod 0777 /home/user/healthcheck

RUN cat <<'EOF' > /home/user/healthcheck/app.py
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

RUN chmod 0644 /home/user/healthcheck/app.py

WORKDIR /home/user

CMD ["/bin/bash"]
