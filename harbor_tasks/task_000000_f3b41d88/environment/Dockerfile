FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    iproute2 \
    procps \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest flask==3.0.0 python-dotenv==1.0.0

RUN mkdir -p /home/user/inventory && chmod 0777 /home/user && chmod 0777 /home/user/inventory

RUN cat <<'EOF' > /home/user/inventory/.env
API_KEY=inv-7f3a2b9c4d5e6f1a
DATABASE_URL=sqlite:///data.db
EOF

RUN cat <<'EOF' > /home/user/inventory/requirements.txt
flask==3.0.0
python-dotenv==1.0.0
EOF

RUN cat <<'EOF' > /home/user/inventory/app.py
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

API_KEY = os.getenv('API_KEY')

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'quantity': self.quantity
        }

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-Api-Key')
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/items', methods=['GET'])
@require_api_key
def get_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items', methods=['POST'])
@require_api_key
def create_item():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    sku = data.get('sku')
    name = data.get('name')
    quantity = data.get('quantity', 0)

    if not sku or not name:
        return jsonify({'error': 'sku and name are required'}), 400

    existing = Item.query.filter_by(sku=sku).first()
    if existing:
        return jsonify({'error': 'Item with this SKU already exists'}), 409

    item = Item(sku=sku, name=name, quantity=quantity)
    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF

RUN sqlite3 /home/user/inventory/data.db <<'SQLEOF'
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER DEFAULT 0
);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-001', 'Widget Alpha', 100);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-002', 'Widget Beta', 250);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-003', 'Gadget Pro', 75);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-004', 'Gadget Lite', 180);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-005', 'Component X1', 500);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-006', 'Component X2', 320);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-007', 'Assembly Kit A', 45);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-008', 'Assembly Kit B', 60);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-009', 'Connector Type C', 1000);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-010', 'Connector Type D', 850);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-011', 'Power Supply 12V', 200);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-012', 'Power Supply 24V', 150);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-013', 'Sensor Module', 90);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-014', 'Display Panel', 35);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-015', 'Control Board', 120);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-016', 'Enclosure Small', 200);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-017', 'Enclosure Large', 80);
INSERT INTO items (sku, name, quantity) VALUES ('SKU-018', 'Cable Bundle', 400);
SQLEOF

RUN chmod 0666 /home/user/inventory/data.db && \
    chmod 0666 /home/user/inventory/.env && \
    chmod 0666 /home/user/inventory/requirements.txt && \
    chmod 0666 /home/user/inventory/app.py

RUN useradd -m -d /home/user -s /bin/bash user || true

RUN chown -R user:user /home/user/inventory

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
