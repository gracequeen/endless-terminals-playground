# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the vulnerability scan task.
"""

import os
import sqlite3
import json
import hashlib
import pytest


# Base paths
PENTEST_DIR = "/home/user/pentest"
DATABASE_PATH = "/home/user/pentest/inventory.db"
APP_DIR = "/home/user/pentest/app"
FINDINGS_PATH = "/home/user/pentest/findings.txt"


class TestFindingsFileExists:
    """Test that the findings file was created."""

    def test_findings_file_exists(self):
        """findings.txt must exist after the task is completed."""
        assert os.path.isfile(FINDINGS_PATH), \
            f"Output file {FINDINGS_PATH} does not exist - task not completed"

    def test_findings_file_not_empty(self):
        """findings.txt must not be empty."""
        assert os.path.getsize(FINDINGS_PATH) > 0, \
            f"Output file {FINDINGS_PATH} is empty"


class TestFindingsFileFormat:
    """Test that the findings file has the correct format."""

    @pytest.fixture
    def findings_content(self):
        """Read the findings file content."""
        with open(FINDINGS_PATH, 'r') as f:
            return f.read()

    @pytest.fixture
    def findings_lines(self, findings_content):
        """Get non-empty lines from findings file."""
        lines = [line.strip() for line in findings_content.strip().split('\n')]
        return [line for line in lines if line]  # Filter empty lines

    def test_findings_has_six_lines(self, findings_lines):
        """findings.txt should have exactly 6 credential lines."""
        assert len(findings_lines) == 6, \
            f"findings.txt should have 6 lines (3 PINs + 3 API keys), got {len(findings_lines)}"

    def test_all_lines_have_colon_format(self, findings_lines):
        """Each line must be in username:credential format."""
        for line in findings_lines:
            assert ':' in line, \
                f"Line '{line}' is not in username:credential format (missing colon)"
            parts = line.split(':', 1)
            assert len(parts) == 2, \
                f"Line '{line}' does not have exactly one colon separator"
            username, credential = parts
            assert username.strip(), \
                f"Line '{line}' has empty username"
            assert credential.strip(), \
                f"Line '{line}' has empty credential"

    def test_no_extra_whitespace(self, findings_lines):
        """Lines should not have extra whitespace."""
        for line in findings_lines:
            # Check for leading/trailing whitespace in username:credential parts
            parts = line.split(':', 1)
            username, credential = parts
            assert username == username.strip(), \
                f"Username '{username}' has extra whitespace"
            assert credential == credential.strip(), \
                f"Credential '{credential}' has extra whitespace"


class TestLegacyAuthPINsExtracted:
    """Test that the legacy auth PINs were extracted correctly."""

    @pytest.fixture
    def findings_credentials(self):
        """Parse findings file into a dict of username -> list of credentials."""
        creds = {}
        with open(FINDINGS_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username, credential = line.split(':', 1)
                    username = username.strip()
                    credential = credential.strip()
                    if username not in creds:
                        creds[username] = []
                    creds[username].append(credential)
        return creds

    @pytest.fixture
    def expected_pins(self):
        """Get expected PINs from the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, pin FROM _legacy_auth")
        pins = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return pins

    def test_alice_pin_extracted(self, findings_credentials, expected_pins):
        """Alice's PIN must be in findings."""
        assert 'alice' in findings_credentials, \
            "alice not found in findings.txt"
        assert expected_pins['alice'] in findings_credentials['alice'], \
            f"alice's PIN ({expected_pins['alice']}) not found in findings"

    def test_bob_pin_extracted(self, findings_credentials, expected_pins):
        """Bob's PIN must be in findings."""
        assert 'bob' in findings_credentials, \
            "bob not found in findings.txt"
        assert expected_pins['bob'] in findings_credentials['bob'], \
            f"bob's PIN ({expected_pins['bob']}) not found in findings"

    def test_admin_pin_extracted(self, findings_credentials, expected_pins):
        """Admin's PIN must be in findings."""
        assert 'admin' in findings_credentials, \
            "admin not found in findings.txt"
        assert expected_pins['admin'] in findings_credentials['admin'], \
            f"admin's PIN ({expected_pins['admin']}) not found in findings"


class TestAPIKeysExtracted:
    """Test that the leaked API keys were extracted correctly."""

    @pytest.fixture
    def findings_credentials(self):
        """Parse findings file into a dict of username -> list of credentials."""
        creds = {}
        with open(FINDINGS_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username, credential = line.split(':', 1)
                    username = username.strip()
                    credential = credential.strip()
                    if username not in creds:
                        creds[username] = []
                    creds[username].append(credential)
        return creds

    @pytest.fixture
    def expected_api_keys(self):
        """Get expected API keys from the audit_log in the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get user_id to username mapping
        cursor.execute("SELECT id, username FROM users")
        user_map = {row[0]: row[1] for row in cursor.fetchall()}

        # Get API keys from audit_log
        cursor.execute(
            "SELECT user_id, details FROM audit_log WHERE action='api_key_generated'"
        )
        api_keys = {}
        for user_id, details in cursor.fetchall():
            data = json.loads(details)
            if 'temp_key' in data:
                username = user_map.get(user_id)
                if username:
                    api_keys[username] = data['temp_key']

        conn.close()
        return api_keys

    def test_alice_api_key_extracted(self, findings_credentials, expected_api_keys):
        """Alice's leaked API key must be in findings."""
        if 'alice' not in expected_api_keys:
            pytest.skip("alice has no API key in audit_log")
        assert 'alice' in findings_credentials, \
            "alice not found in findings.txt"
        assert expected_api_keys['alice'] in findings_credentials['alice'], \
            f"alice's API key not found in findings"

    def test_bob_api_key_extracted(self, findings_credentials, expected_api_keys):
        """Bob's leaked API key must be in findings."""
        if 'bob' not in expected_api_keys:
            pytest.skip("bob has no API key in audit_log")
        assert 'bob' in findings_credentials, \
            "bob not found in findings.txt"
        assert expected_api_keys['bob'] in findings_credentials['bob'], \
            f"bob's API key not found in findings"

    def test_admin_api_key_extracted(self, findings_credentials, expected_api_keys):
        """Admin's leaked API key must be in findings."""
        if 'admin' not in expected_api_keys:
            pytest.skip("admin has no API key in audit_log")
        assert 'admin' in findings_credentials, \
            "admin not found in findings.txt"
        assert expected_api_keys['admin'] in findings_credentials['admin'], \
            f"admin's API key not found in findings"


class TestValidUsernames:
    """Test that only valid usernames appear in findings."""

    @pytest.fixture
    def valid_usernames(self):
        """Get valid usernames from the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        usernames = {row[0] for row in cursor.fetchall()}
        conn.close()
        return usernames

    @pytest.fixture
    def findings_usernames(self):
        """Get usernames from findings file."""
        usernames = set()
        with open(FINDINGS_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username = line.split(':', 1)[0].strip()
                    usernames.add(username)
        return usernames

    def test_all_usernames_valid(self, findings_usernames, valid_usernames):
        """All usernames in findings must be valid users from the database."""
        invalid = findings_usernames - valid_usernames
        assert not invalid, \
            f"Invalid usernames in findings.txt: {invalid}. Valid users are: {valid_usernames}"

    def test_charlie_not_in_findings(self, findings_usernames):
        """Charlie should NOT be in findings (has no legacy auth or leaked keys)."""
        assert 'charlie' not in findings_usernames, \
            "charlie should not be in findings.txt (no discoverable credentials)"


class TestDatabaseUnmodified:
    """Test that the database was not modified (read-only operation)."""

    @pytest.fixture
    def db_connection(self):
        """Create a database connection for tests."""
        conn = sqlite3.connect(DATABASE_PATH)
        yield conn
        conn.close()

    def test_users_table_unchanged(self, db_connection):
        """The users table should still have the same users."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT username FROM users ORDER BY username")
        usernames = [row[0] for row in cursor.fetchall()]
        expected = ['admin', 'alice', 'bob', 'charlie']
        assert usernames == expected, \
            f"users table was modified. Expected {expected}, got {usernames}"

    def test_legacy_auth_table_unchanged(self, db_connection):
        """The _legacy_auth table should still have the same entries."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT username, pin FROM _legacy_auth ORDER BY username")
        entries = cursor.fetchall()
        assert len(entries) == 3, \
            f"_legacy_auth table was modified. Expected 3 entries, got {len(entries)}"

    def test_audit_log_unchanged(self, db_connection):
        """The audit_log table should still have api_key_generated entries."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM audit_log WHERE action='api_key_generated'"
        )
        count = cursor.fetchone()[0]
        assert count >= 3, \
            f"audit_log table was modified. Expected at least 3 api_key_generated entries, got {count}"


class TestAppSourceUnchanged:
    """Test that the app source files were not modified."""

    def test_config_py_still_exists(self):
        """config.py must still exist."""
        config_path = os.path.join(APP_DIR, "config.py")
        assert os.path.isfile(config_path), \
            f"File {config_path} was deleted or moved"

    def test_auth_py_still_exists(self):
        """auth.py must still exist."""
        auth_path = os.path.join(APP_DIR, "auth.py")
        assert os.path.isfile(auth_path), \
            f"File {auth_path} was deleted or moved"

    def test_routes_py_still_exists(self):
        """routes.py must still exist."""
        routes_path = os.path.join(APP_DIR, "routes.py")
        assert os.path.isfile(routes_path), \
            f"File {routes_path} was deleted or moved"

    def test_models_py_still_exists(self):
        """models.py must still exist."""
        models_path = os.path.join(APP_DIR, "models.py")
        assert os.path.isfile(models_path), \
            f"File {models_path} was deleted or moved"


class TestCredentialCount:
    """Test the credential count using grep-like validation."""

    def test_colon_count_is_six(self):
        """There should be exactly 6 lines with colons (6 credentials)."""
        count = 0
        with open(FINDINGS_PATH, 'r') as f:
            for line in f:
                if ':' in line.strip():
                    count += 1
        assert count == 6, \
            f"Expected 6 credential lines (3 PINs + 3 API keys), found {count}"
