# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies the broken Flask inventory API setup that needs to be fixed.
"""

import os
import sqlite3
import subprocess
import pytest


class TestInventoryDirectoryStructure:
    """Test that the inventory directory and files exist."""

    def test_inventory_directory_exists(self):
        """The /home/user/inventory directory must exist."""
        path = "/home/user/inventory"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_app_py_exists(self):
        """The Flask application file must exist."""
        path = "/home/user/inventory/app.py"
        assert os.path.isfile(path), f"Flask app file {path} does not exist"

    def test_data_db_exists(self):
        """The SQLite database file must exist."""
        path = "/home/user/inventory/data.db"
        assert os.path.isfile(path), f"Database file {path} does not exist"

    def test_env_file_exists(self):
        """The .env file must exist."""
        path = "/home/user/inventory/.env"
        assert os.path.isfile(path), f"Environment file {path} does not exist"

    def test_requirements_txt_exists(self):
        """The requirements.txt file must exist."""
        path = "/home/user/inventory/requirements.txt"
        assert os.path.isfile(path), f"Requirements file {path} does not exist"

    def test_inventory_directory_is_writable(self):
        """The inventory directory must be writable."""
        path = "/home/user/inventory"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestEnvFileContents:
    """Test the contents of the .env file."""

    def test_env_contains_api_key(self):
        """The .env file must contain the API_KEY."""
        path = "/home/user/inventory/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "API_KEY=inv-7f3a2b9c4d5e6f1a" in content, \
            f".env file does not contain expected API_KEY. Content: {content}"

    def test_env_contains_database_url(self):
        """The .env file must contain DATABASE_URL."""
        path = "/home/user/inventory/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "DATABASE_URL" in content, \
            f".env file does not contain DATABASE_URL. Content: {content}"


class TestRequirementsTxt:
    """Test the contents of requirements.txt."""

    def test_requirements_contains_flask(self):
        """requirements.txt must contain flask."""
        path = "/home/user/inventory/requirements.txt"
        with open(path, "r") as f:
            content = f.read().lower()
        assert "flask" in content, \
            f"requirements.txt does not contain flask. Content: {content}"

    def test_requirements_contains_python_dotenv(self):
        """requirements.txt must contain python-dotenv."""
        path = "/home/user/inventory/requirements.txt"
        with open(path, "r") as f:
            content = f.read().lower()
        assert "python-dotenv" in content or "dotenv" in content, \
            f"requirements.txt does not contain python-dotenv. Content: {content}"

    def test_requirements_missing_flask_sqlalchemy(self):
        """requirements.txt should NOT contain flask-sqlalchemy (this is the bug)."""
        path = "/home/user/inventory/requirements.txt"
        with open(path, "r") as f:
            content = f.read().lower()
        assert "flask-sqlalchemy" not in content, \
            f"requirements.txt unexpectedly contains flask-sqlalchemy - the bug may already be fixed"


class TestAppPyContents:
    """Test the contents of app.py to verify the expected broken state."""

    def test_app_imports_flask_sqlalchemy(self):
        """app.py must import flask_sqlalchemy (which will cause the import error)."""
        path = "/home/user/inventory/app.py"
        with open(path, "r") as f:
            content = f.read()
        assert "flask_sqlalchemy" in content or "SQLAlchemy" in content, \
            f"app.py does not appear to use flask_sqlalchemy. This is unexpected."

    def test_app_imports_load_dotenv(self):
        """app.py must use load_dotenv for environment variables."""
        path = "/home/user/inventory/app.py"
        with open(path, "r") as f:
            content = f.read()
        assert "load_dotenv" in content or "dotenv" in content, \
            f"app.py does not appear to use dotenv for environment variables."

    def test_app_uses_api_key_header(self):
        """app.py must reference X-Api-Key header for authentication."""
        path = "/home/user/inventory/app.py"
        with open(path, "r") as f:
            content = f.read()
        assert "X-Api-Key" in content or "X-API-Key" in content or "x-api-key" in content.lower(), \
            f"app.py does not appear to use X-Api-Key header for authentication."


class TestDatabase:
    """Test the SQLite database contents."""

    def test_database_is_valid_sqlite(self):
        """data.db must be a valid SQLite database."""
        path = "/home/user/inventory/data.db"
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            conn.close()
        except sqlite3.Error as e:
            pytest.fail(f"data.db is not a valid SQLite database: {e}")

    def test_database_has_items_table(self):
        """data.db must have an 'items' table."""
        path = "/home/user/inventory/data.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, "Database does not have an 'items' table"

    def test_items_table_has_correct_columns(self):
        """items table must have id, sku, name, quantity columns."""
        path = "/home/user/inventory/data.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(items)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required_columns = {"id", "sku", "name", "quantity"}
        missing = required_columns - columns
        assert not missing, f"items table is missing columns: {missing}. Found: {columns}"

    def test_items_table_has_18_rows(self):
        """items table must have exactly 18 rows."""
        path = "/home/user/inventory/data.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 18, f"items table has {count} rows, expected 18"

    def test_no_test_restore_item_exists(self):
        """The TEST-RESTORE-001 item should NOT exist yet (will be added by student)."""
        path = "/home/user/inventory/data.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items WHERE sku = 'TEST-RESTORE-001'")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 0, "TEST-RESTORE-001 item already exists - this should be added by the student"


class TestSystemState:
    """Test the system state (Python, pip, port availability)."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"
        assert "Python 3" in result.stdout, f"Unexpected Python version: {result.stdout}"

    def test_pip_available(self):
        """pip must be available."""
        result = subprocess.run(
            ["pip3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "pip3 is not available"

    def test_venv_available(self):
        """venv module must be available."""
        result = subprocess.run(
            ["python3", "-c", "import venv"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python venv module is not available"

    def test_port_8080_available(self):
        """Port 8080 must be available (not in use)."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if port 8080 is NOT being listened on
        assert ":8080" not in result.stdout, \
            f"Port 8080 is already in use. Something is already listening on it."

    def test_no_flask_app_running(self):
        """No Flask app should be running on port 8080 initially."""
        result = subprocess.run(
            ["pgrep", "-f", "python.*app.py"],
            capture_output=True,
            text=True
        )
        # pgrep returns 1 if no processes found, 0 if found
        # We want no processes to be found
        if result.returncode == 0:
            pytest.fail(f"A Python app.py process is already running: {result.stdout}")


class TestFlaskSqlalchemyNotInstalled:
    """Verify that flask-sqlalchemy is NOT installed (this is the bug)."""

    def test_flask_sqlalchemy_not_installed(self):
        """flask-sqlalchemy should NOT be installed system-wide."""
        result = subprocess.run(
            ["pip3", "show", "flask-sqlalchemy"],
            capture_output=True,
            text=True
        )
        # pip show returns 1 if package not found
        assert result.returncode != 0, \
            "flask-sqlalchemy is already installed - the import error bug may not exist"

    def test_flask_is_installed(self):
        """Flask should be installed."""
        result = subprocess.run(
            ["pip3", "show", "flask"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Flask is not installed"

    def test_python_dotenv_is_installed(self):
        """python-dotenv should be installed."""
        result = subprocess.run(
            ["pip3", "show", "python-dotenv"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "python-dotenv is not installed"


class TestAppWillFailToStart:
    """Verify that the app will fail to start due to import error."""

    def test_app_fails_with_import_error(self):
        """Running app.py should fail with an import error."""
        result = subprocess.run(
            ["python3", "/home/user/inventory/app.py"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd="/home/user/inventory"
        )
        # The app should fail to start
        assert result.returncode != 0, \
            "app.py started successfully - expected it to fail with import error"

        # Check for import-related error
        error_output = result.stderr.lower()
        assert "import" in error_output or "module" in error_output or "no module" in error_output, \
            f"Expected import error, but got: {result.stderr}"
