FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    procps \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest flask requests

RUN mkdir -p /home/user/mesh && chmod 0777 /home/user && chmod 0777 /home/user/mesh

RUN cat > /home/user/mesh/requirements.txt << 'EOF'
flask
requests
EOF

RUN cat > /home/user/mesh/backend.py << 'EOF'
from flask import Flask, jsonify
import logging
import os

app = Flask(__name__)

# Set up logging to file
logging.basicConfig(level=logging.DEBUG)
log_path = '/home/user/mesh/backend.log'

@app.route('/fetch')
def fetch():
    # Log each request for verification
    with open(log_path, 'a') as f:
        f.write(f"Request received at /fetch\n")
    return jsonify({"status": "ok", "data": "secret_payload_42"})

@app.route('/')
def index():
    return jsonify({"service": "backend", "port": 8082})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=False, threaded=True)
EOF

RUN cat > /home/user/mesh/auth.py << 'EOF'
from flask import Flask, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/validate')
def validate():
    app.logger.debug("Auth received request at /validate")
    try:
        resp = requests.get('http://localhost:8082/fetch', timeout=10)
        app.logger.debug(f"Auth got response from backend: {resp.status_code}")
        # BUG: returning the requests.Response object directly instead of its content
        # This causes Flask to hang trying to serialize/iterate the response object
        return resp
    except Exception as e:
        app.logger.error(f"Auth error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({"service": "auth", "port": 8081})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
EOF

RUN cat > /home/user/mesh/gateway.py << 'EOF'
from flask import Flask, jsonify
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route('/data')
def data():
    app.logger.debug("Gateway received request at /data")
    try:
        resp = requests.get('http://localhost:8081/validate', timeout=30)
        app.logger.debug(f"Gateway got response from auth: {resp.status_code}")
        return resp.json()
    except requests.exceptions.Timeout:
        app.logger.error("Gateway timeout waiting for auth")
        return jsonify({"error": "Gateway timeout"}), 504
    except Exception as e:
        app.logger.error(f"Gateway error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return jsonify({"service": "gateway", "port": 8080})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
EOF

RUN cat > /home/user/mesh/start_mesh.sh << 'EOF'
#!/bin/bash
cd /home/user/mesh

# Kill any existing instances
pkill -f "python3.*gateway.py" 2>/dev/null || true
pkill -f "python3.*auth.py" 2>/dev/null || true
pkill -f "python3.*backend.py" 2>/dev/null || true

sleep 1

# Start backend first
python3 backend.py &
echo $! > backend.pid

# Start auth
python3 auth.py &
echo $! > auth.pid

# Start gateway
python3 gateway.py &
echo $! > gateway.pid

echo "All services started"
echo "Gateway PID: $(cat gateway.pid)"
echo "Auth PID: $(cat auth.pid)"
echo "Backend PID: $(cat backend.pid)"
EOF

RUN chmod +x /home/user/mesh/start_mesh.sh

RUN chmod 0666 /home/user/mesh/*.py /home/user/mesh/requirements.txt

RUN cat > /entrypoint.sh << 'EOF'
#!/bin/bash
cd /home/user/mesh

# Start backend
python3 backend.py &
sleep 0.5

# Start auth
python3 auth.py &
sleep 0.5

# Start gateway
python3 gateway.py &
sleep 0.5

# Wait for services to be ready
for i in {1..10}; do
    if curl -s --max-time 1 http://localhost:8080/ > /dev/null 2>&1 && \
       curl -s --max-time 1 http://localhost:8081/ > /dev/null 2>&1 && \
       curl -s --max-time 1 http://localhost:8082/ > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

exec "$@"
EOF

RUN chmod +x /entrypoint.sh

WORKDIR /home/user

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
