FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest bcrypt

RUN mkdir -p /home/user/pentest/app && chmod 0777 /home/user && chmod 0777 /home/user/pentest && chmod 0777 /home/user/pentest/app

RUN cat <<'EOF' > /home/user/pentest/app/config.py
# Application Configuration

DATABASE_PATH = "/home/user/pentest/inventory.db"
SECRET_KEY = "super-secret-key-change-in-production"

# Authentication settings
SESSION_TIMEOUT = 3600
MAX_LOGIN_ATTEMPTS = 5

# Legacy authentication table
# TODO: migrate users off PIN auth
LEGACY_AUTH_TABLE = "_legacy_auth"

# API settings
API_KEY_LENGTH = 32
EOF

RUN cat <<'EOF' > /home/user/pentest/app/auth.py
"""Authentication module for the inventory application."""

import sqlite3
import hashlib
from config import DATABASE_PATH, LEGACY_AUTH_TABLE


def get_db_connection():
    """Get a database connection."""
    return sqlite3.connect(DATABASE_PATH)


def check_password(username, password_hash_input):
    """Check bcrypt password hash against stored hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?",
        (username,)
    )
    result = cursor.fetchone()
    conn.close()

    if result:
        # In production, use bcrypt.checkpw()
        return result[0] == password_hash_input
    return False


def check_legacy_pin(username, pin):
    """
    Check legacy 4-digit PIN for quick login.
    This is the old authentication method - should be deprecated.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query the legacy auth table directly
    query = f"SELECT pin FROM {LEGACY_AUTH_TABLE} WHERE username = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0] == pin
    return False


def validate_api_key(key):
    """Validate an API key by checking its SHA256 hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    cursor.execute(
        "SELECT user_id FROM api_keys WHERE key_hash = ?",
        (key_hash,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None
EOF

RUN cat <<'EOF' > /home/user/pentest/app/routes.py
"""Flask routes for the inventory application."""

from flask import Flask, request, jsonify
from auth import check_password, check_legacy_pin, validate_api_key

app = Flask(__name__)


@app.route('/api/login', methods=['POST'])
def login():
    """Standard login endpoint using username and password."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if check_password(username, password):
        return jsonify({"status": "success", "message": "Logged in"})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route('/api/quick-login', methods=['POST'])
def quick_login():
    """
    Quick login endpoint using 4-digit PIN.
    Legacy feature for mobile app compatibility.
    Accepts username and 4-digit PIN.
    """
    data = request.get_json()
    username = data.get('username')
    pin = data.get('pin')

    if not pin or len(pin) != 4 or not pin.isdigit():
        return jsonify({"status": "error", "message": "PIN must be 4 digits"}), 400

    if check_legacy_pin(username, pin):
        return jsonify({"status": "success", "message": "Quick login successful"})
    return jsonify({"status": "error", "message": "Invalid PIN"}), 401


@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get inventory items. Requires API key."""
    api_key = request.headers.get('X-API-Key')
    if not api_key or not validate_api_key(api_key):
        return jsonify({"status": "error", "message": "Invalid API key"}), 401

    # Return inventory data
    return jsonify({"status": "success", "items": []})


if __name__ == '__main__':
    app.run(debug=True)
EOF

RUN cat <<'EOF' > /home/user/pentest/app/models.py
"""ORM models for the inventory application."""

# Note: Using raw SQL for some legacy tables that don't fit the ORM pattern

class User:
    """User model - maps to 'users' table."""

    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def table_name():
        return 'users'


class Session:
    """Session model - maps to 'sessions' table."""

    def __init__(self, id, user_id, session_token, created_at):
        self.id = id
        self.user_id = user_id
        self.session_token = session_token
        self.created_at = created_at

    @staticmethod
    def table_name():
        return 'sessions'


class ApiKey:
    """API Key model - maps to 'api_keys' table."""

    def __init__(self, id, user_id, key_hash):
        self.id = id
        self.user_id = user_id
        self.key_hash = key_hash

    @staticmethod
    def table_name():
        return 'api_keys'


class AuditLog:
    """Audit log model - maps to 'audit_log' table."""

    def __init__(self, id, user_id, action, details, timestamp):
        self.id = id
        self.user_id = user_id
        self.action = action
        self.details = details
        self.timestamp = timestamp

    @staticmethod
    def table_name():
        return 'audit_log'


# Note: _legacy_auth table is not represented here as it's being phased out
# and uses raw SQL queries in auth.py for backward compatibility
EOF

RUN python3 <<'PYEOF'
import sqlite3
import hashlib
import json

conn = sqlite3.connect('/home/user/pentest/inventory.db')
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')

# Create sessions table
cursor.execute('''
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# Create api_keys table
cursor.execute('''
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    key_hash TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# Create audit_log table
cursor.execute('''
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

# Create hidden _legacy_auth table
cursor.execute('''
CREATE TABLE _legacy_auth (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    pin TEXT NOT NULL
)
''')

# Insert users with bcrypt hashes
users = [
    (1, 'alice', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA/Cq/Ky.Pu'),
    (2, 'bob', '$2b$12$WZaxWsLXlD.iyfFwJfAQpOQF8Fz3v0MhpX5/nHJKvLMjUgBnJvemu'),
    (3, 'charlie', '$2b$12$kXzRzerq.P" "Yd5FvN1O.uLJ8vHgKZwe6Q4Y.JqF5TmBnMvKHi'),
    (4, 'admin', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi')
]
cursor.executemany('INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)', users)

# Insert legacy auth PINs (cleartext - the vulnerability!)
legacy_auth = [
    (1, 'alice', '1234'),
    (2, 'bob', '5678'),
    (3, 'admin', '0000')
]
cursor.executemany('INSERT INTO _legacy_auth (id, username, pin) VALUES (?, ?, ?)', legacy_auth)

# Insert some sessions
sessions = [
    (1, 1, 'sess_abc123def456', '2024-01-15 10:30:00'),
    (2, 2, 'sess_xyz789uvw012', '2024-01-15 11:45:00'),
]
cursor.executemany('INSERT INTO sessions (id, user_id, session_token, created_at) VALUES (?, ?, ?, ?)', sessions)

# API keys - stored as SHA256 hashes
api_keys_data = [
    (1, 1, hashlib.sha256('a]f8c2e1b9d4a7f3e6c0b5d2a8f1e4c7b0d3'.encode()).hexdigest()),
    (2, 2, hashlib.sha256('b9e7d1c4a8f2e5b0c3d6a9f0e2b5c8d1a4f7'.encode()).hexdigest()),
    (3, 4, hashlib.sha256('c0d4e8f2a6b1c5d9e3f7a0b4c8d2e6f1a5b9'.encode()).hexdigest()),
]
cursor.executemany('INSERT INTO api_keys (id, user_id, key_hash) VALUES (?, ?, ?)', api_keys_data)

# Audit log entries - including the vulnerability (temp_key logged in cleartext!)
audit_entries = [
    (1, 1, 'login', '{"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"}', '2024-01-10 09:00:00'),
    (2, 1, 'api_key_generated', json.dumps({"temp_key": "a]f8c2e1b9d4a7f3e6c0b5d2a8f1e4c7b0d3", "purpose": "inventory_access"}), '2024-01-11 14:30:00'),
    (3, 2, 'login', '{"ip": "192.168.1.101", "user_agent": "curl/7.68.0"}', '2024-01-12 08:15:00'),
    (4, 2, 'api_key_generated', json.dumps({"temp_key": "b9e7d1c4a8f2e5b0c3d6a9f0e2b5c8d1a4f7", "purpose": "mobile_app"}), '2024-01-12 08:20:00'),
    (5, 3, 'login', '{"ip": "192.168.1.102", "user_agent": "Python-requests/2.28.0"}', '2024-01-13 16:45:00'),
    (6, 4, 'login', '{"ip": "10.0.0.1", "user_agent": "AdminPanel/1.0"}', '2024-01-14 07:00:00'),
    (7, 4, 'api_key_generated', json.dumps({"temp_key": "c0d4e8f2a6b1c5d9e3f7a0b4c8d2e6f1a5b9", "purpose": "admin_tools"}), '2024-01-14 07:05:00'),
    (8, 1, 'inventory_view', '{"items_viewed": 15}', '2024-01-15 10:35:00'),
    (9, 2, 'inventory_update', '{"item_id": 42, "field": "quantity", "old": 10, "new": 8}', '2024-01-15 11:50:00'),
]
cursor.executemany('INSERT INTO audit_log (id, user_id, action, details, timestamp) VALUES (?, ?, ?, ?, ?)', audit_entries)

conn.commit()
conn.close()
PYEOF

RUN chmod 644 /home/user/pentest/inventory.db && \
    chmod 644 /home/user/pentest/app/config.py && \
    chmod 644 /home/user/pentest/app/auth.py && \
    chmod 644 /home/user/pentest/app/routes.py && \
    chmod 644 /home/user/pentest/app/models.py

RUN useradd -m -d /home/user -s /bin/bash user

RUN chown -R user:user /home/user

USER user
WORKDIR /home/user
