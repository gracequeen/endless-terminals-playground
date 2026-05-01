FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    redis-server \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    curl \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest flask psycopg2-binary redis

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/devstack/config \
    /home/user/devstack/services \
    /home/user/devstack/app \
    /home/user/devstack/logs

RUN cat > /home/user/devstack/config/redis.conf << 'EOF'
bind 127.0.0.1
port 6379
daemonise yes
logfile /home/user/devstack/logs/redis-internal.log
EOF

RUN cat > /home/user/devstack/config/postgres.env << 'EOF'
export PGDATA=/home/user/devstack/pgdata
export PGPORT=5433
export PGHOST=127.0.0.1
export PGUSER=devuser
export PGDATABASE=devdb
EOF

RUN cat > /home/user/devstack/config/api.env << 'EOF'
export REDIS_URL=redis://127.0.0.1:6379/0
export DATABASE_URL=postgresql://devuser@localhost:5432/devdb
export API_PORT=8080
export FLASK_APP=/home/user/devstack/app/api.py
EOF

RUN cat > /home/user/devstack/services/start_redis.sh << 'EOF'
#!/bin/bash
cd /home/user/devstack
redis-server /home/user/devstack/config/redis.conf
sleep 1
if pgrep -f "redis-server" > /dev/null; then
    echo "Redis started successfully"
    exit 0
else
    echo "Redis failed to start"
    exit 1
fi
EOF

RUN chmod +x /home/user/devstack/services/start_redis.sh

RUN cat > /home/user/devstack/services/start_postgres.sh << 'EOF'
#!/bin/bash
source /home/user/devstack/config/postgres.env
cd /home/user/devstack

pg_ctl -D "$PGDATA" -l /home/user/devstack/logs/postgres-internal.log start -w
sleep 2

if pgrep -f "postgres" > /dev/null; then
    echo "Postgres started successfully"
    exit 0
else
    echo "Postgres failed to start"
    exit 1
fi
EOF

RUN chmod +x /home/user/devstack/services/start_postgres.sh

RUN cat > /home/user/devstack/services/start_api.sh << 'EOF'
#!/bin/bash
source /home/user/devstack/config/api.env
cd /home/user/devstack/app

python3 -u api.py > /home/user/devstack/logs/api-internal.log 2>&1 &
sleep 2

if pgrep -f "api.py" > /dev/null; then
    echo "API started successfully"
    exit 0
else
    echo "API failed to start"
    exit 1
fi
EOF

RUN chmod +x /home/user/devstack/services/start_api.sh

RUN cat > /home/user/devstack/start.sh << 'EOF'
#!/bin/bash
cd /home/user/devstack

echo "Starting Redis..."
./services/start_redis.sh > logs/redis.log 2>/dev/null
if [ $? -ne 0 ]; then
    exit 1
fi

echo "Starting Postgres..."
./services/start_postgres.sh > logs/postgres.log 2>/dev/null
if [ $? -ne 0 ]; then
    exit 1
fi

echo "Starting API..."
./services/start_api.sh > logs/api.log 2>/dev/null
if [ $? -ne 0 ]; then
    exit 1
fi

echo "All services started successfully"
exit 0
EOF

RUN chmod +x /home/user/devstack/start.sh

RUN cat > /home/user/devstack/app/api.py << 'PYEOF'
import os
from flask import Flask, jsonify
import redis
import psycopg2

app = Flask(__name__)

@app.route('/health')
def health():
    try:
        # Check Redis
        redis_url = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
        r = redis.from_url(redis_url)
        r.ping()

        # Check Postgres
        database_url = os.environ['DATABASE_URL']
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()

        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return jsonify({"message": "DevStack API"})

if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 8080))
    app.run(host='0.0.0.0', port=port)
PYEOF

RUN chown -R nobody:nogroup /home/user/devstack && \
    chmod -R 0777 /home/user/devstack

ENV PATH="/usr/lib/postgresql/14/bin:${PATH}"

CMD ["/bin/bash"]
