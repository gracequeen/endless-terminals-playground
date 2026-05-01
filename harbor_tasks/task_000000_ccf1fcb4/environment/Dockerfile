FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    curl \
    net-tools \
    iproute2 \
    procps \
    lsof \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/labeler/app && \
    mkdir -p /home/user/labeler/config

RUN python3.11 -m venv /home/user/labeler/venv

RUN /home/user/labeler/venv/bin/pip install flask gunicorn configparser

RUN cat > /home/user/labeler/app/__init__.py << 'EOF'
from flask import Flask


def create_app():
    app = Flask(__name__)

    from . import routes
    app.register_blueprint(routes.bp)

    return app
EOF

RUN cat > /home/user/labeler/app/routes.py << 'EOF'
from flask import Blueprint

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return "Labeler v2.1 running"


@bp.route('/health')
def health():
    return {"status": "ok"}
EOF

RUN cat > /home/user/labeler/config/settings.ini << 'EOF'
[sevrer]
host=127.0.0.1
port=5000
workers=2
EOF

RUN cat > /home/user/labeler/config/gunicorn.conf.py << 'EOF'
import configparser
import os

# Read configuration from settings.ini
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'settings.ini')
config.read(config_path)

# Get settings with fallbacks
host = config.get('server', 'host', fallback='127.0.0.1')
port = config.get('server', 'port', fallback='8000')
workers_count = config.get('server', 'workers', fallback='2')

# Gunicorn configuration
bind = f"{host}:{port}"
workers = int(workers_count)
daemon = False
EOF

RUN cat > /home/user/labeler/start.sh << 'EOF'
#!/bin/bash
echo "Starting labeler service..."
cd /home/user/labeler
source venv/bin/activate
gunicorn -c config/gunicorn.conf.py "app:create_app()" --daemon
EOF

RUN chmod +x /home/user/labeler/start.sh

RUN cat > /home/user/labeler/requirements.txt << 'EOF'
flask
gunicorn
configparser
EOF

RUN chmod -R 0777 /home/user/labeler

CMD ["/bin/bash"]
