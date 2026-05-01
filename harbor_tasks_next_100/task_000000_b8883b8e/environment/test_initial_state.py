# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the vulnerability scan task.
"""

import os
import sqlite3
import json
import pytest


# Base paths
PENTEST_DIR = "/home/user/pentest"
DATABASE_PATH = "/home/user/pentest/inventory.db"
APP_DIR = "/home/user/pentest/app"
FINDINGS_PATH = "/home/user/pentest/findings.txt"


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_pentest_directory_exists(self):
        """The /home/user/pentest directory must exist."""
        assert os.path.isdir(PENTEST_DIR), \
            f"Directory {PENTEST_DIR} does not exist"

    def test_pentest_directory_writable(self):
        """The /home/user/pentest directory must be writable."""
        assert os.access(PENTEST_DIR, os.W_OK), \
            f"Directory {PENTEST_DIR} is not writable"

    def test_app_directory_exists(self):
        """The /home/user/pentest/app directory must exist."""
        assert os.path.isdir(APP_DIR), \
            f"Directory {APP_DIR} does not exist"


class TestDatabaseExists:
    """Test that the SQLite database exists and is accessible."""

    def test_database_file_exists(self):
        """The inventory.db file must exist."""
        assert os.path.isfile(DATABASE_PATH), \
            f"Database file {DATABASE_PATH} does not exist"

    def test_database_is_sqlite3(self):
        """The inventory.db file must be a valid SQLite3 database."""
        # SQLite3 files start with "SQLite format 3"
        with open(DATABASE_PATH, 'rb') as f:
            header = f.read(16)
        assert header[:13] == b'SQLite format', \
            f"{DATABASE_PATH} is not a valid SQLite3 database"

    def test_database_readable(self):
        """The database must be readable."""
        assert os.access(DATABASE_PATH, os.R_OK), \
            f"Database {DATABASE_PATH} is not readable"


class TestDatabaseSchema:
    """Test that the database has the expected schema."""

    @pytest.fixture
    def db_connection(self):
        """Create a database connection for tests."""
        conn = sqlite3.connect(DATABASE_PATH)
        yield conn
        conn.close()

    def test_users_table_exists(self, db_connection):
        """The users table must exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = cursor.fetchone()
        assert result is not None, "Table 'users' does not exist in the database"

    def test_users_table_has_required_columns(self, db_connection):
        """The users table must have id, username, password_hash columns."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}
        required = {'id', 'username', 'password_hash'}
        assert required.issubset(columns), \
            f"users table missing columns. Has: {columns}, needs: {required}"

    def test_sessions_table_exists(self, db_connection):
        """The sessions table must exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        result = cursor.fetchone()
        assert result is not None, "Table 'sessions' does not exist"

    def test_api_keys_table_exists(self, db_connection):
        """The api_keys table must exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'"
        )
        result = cursor.fetchone()
        assert result is not None, "Table 'api_keys' does not exist"

    def test_audit_log_table_exists(self, db_connection):
        """The audit_log table must exist."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'"
        )
        result = cursor.fetchone()
        assert result is not None, "Table 'audit_log' does not exist"

    def test_legacy_auth_table_exists(self, db_connection):
        """The _legacy_auth table must exist (hidden table)."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='_legacy_auth'"
        )
        result = cursor.fetchone()
        assert result is not None, \
            "Table '_legacy_auth' does not exist - this is the hidden table with PINs"


class TestDatabaseContent:
    """Test that the database has the expected content."""

    @pytest.fixture
    def db_connection(self):
        """Create a database connection for tests."""
        conn = sqlite3.connect(DATABASE_PATH)
        yield conn
        conn.close()

    def test_users_table_has_expected_users(self, db_connection):
        """The users table must have alice, bob, charlie, admin."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT username FROM users")
        usernames = {row[0] for row in cursor.fetchall()}
        expected = {'alice', 'bob', 'charlie', 'admin'}
        assert expected == usernames, \
            f"users table has {usernames}, expected {expected}"

    def test_users_have_bcrypt_hashes(self, db_connection):
        """User passwords should be bcrypt hashes (start with $2)."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT username, password_hash FROM users")
        for username, password_hash in cursor.fetchall():
            assert password_hash.startswith('$2'), \
                f"User {username} does not have a bcrypt hash"

    def test_legacy_auth_has_pins(self, db_connection):
        """The _legacy_auth table must have cleartext PINs."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT username, pin FROM _legacy_auth")
        rows = cursor.fetchall()
        assert len(rows) >= 3, \
            f"_legacy_auth should have at least 3 entries, has {len(rows)}"

        # Check that PINs are 4-digit numbers
        for username, pin in rows:
            assert pin.isdigit() and len(pin) == 4, \
                f"PIN for {username} should be 4 digits, got: {pin}"

    def test_audit_log_has_api_key_entries(self, db_connection):
        """The audit_log must have api_key_generated entries with temp_key."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT details FROM audit_log WHERE action='api_key_generated'")
        rows = cursor.fetchall()
        assert len(rows) >= 3, \
            f"audit_log should have at least 3 api_key_generated entries, has {len(rows)}"

        # Verify each entry has temp_key in the JSON
        for (details,) in rows:
            data = json.loads(details)
            assert 'temp_key' in data, \
                f"audit_log entry missing temp_key field: {details}"


class TestAppSourceFiles:
    """Test that the application source files exist with expected content."""

    def test_config_py_exists(self):
        """config.py must exist in the app directory."""
        config_path = os.path.join(APP_DIR, "config.py")
        assert os.path.isfile(config_path), \
            f"File {config_path} does not exist"

    def test_config_py_has_legacy_auth_reference(self):
        """config.py must reference _legacy_auth table."""
        config_path = os.path.join(APP_DIR, "config.py")
        with open(config_path, 'r') as f:
            content = f.read()
        assert '_legacy_auth' in content, \
            "config.py does not contain reference to _legacy_auth table"

    def test_auth_py_exists(self):
        """auth.py must exist in the app directory."""
        auth_path = os.path.join(APP_DIR, "auth.py")
        assert os.path.isfile(auth_path), \
            f"File {auth_path} does not exist"

    def test_routes_py_exists(self):
        """routes.py must exist in the app directory."""
        routes_path = os.path.join(APP_DIR, "routes.py")
        assert os.path.isfile(routes_path), \
            f"File {routes_path} does not exist"

    def test_models_py_exists(self):
        """models.py must exist in the app directory."""
        models_path = os.path.join(APP_DIR, "models.py")
        assert os.path.isfile(models_path), \
            f"File {models_path} does not exist"


class TestOutputFileNotExists:
    """Test that the output file does not exist initially."""

    def test_findings_file_does_not_exist(self):
        """findings.txt should NOT exist before the task is performed."""
        assert not os.path.exists(FINDINGS_PATH), \
            f"Output file {FINDINGS_PATH} already exists - it should not exist initially"


class TestToolsAvailable:
    """Test that required tools are available."""

    def test_sqlite3_cli_available(self):
        """sqlite3 CLI must be available."""
        import subprocess
        result = subprocess.run(['which', 'sqlite3'], capture_output=True)
        assert result.returncode == 0, \
            "sqlite3 CLI is not available in PATH"

    def test_python3_available(self):
        """Python 3 must be available."""
        import subprocess
        result = subprocess.run(['which', 'python3'], capture_output=True)
        assert result.returncode == 0, \
            "python3 is not available in PATH"

    def test_python_sqlite3_module_available(self):
        """Python sqlite3 module must be importable."""
        try:
            import sqlite3
        except ImportError:
            pytest.fail("Python sqlite3 module is not available")
