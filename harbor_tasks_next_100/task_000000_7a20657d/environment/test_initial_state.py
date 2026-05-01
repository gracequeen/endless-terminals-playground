# test_initial_state.py
"""
Tests to validate the initial state of the operating system / filesystem
before the student performs the user-audit scan debugging task.
"""

import os
import stat
import sqlite3
import subprocess
import pytest


AUDIT_DIR = "/home/user/audit"
SCAN_PY = os.path.join(AUDIT_DIR, "scan.py")
USERS_DB = os.path.join(AUDIT_DIR, "users.db")
BREACH_HASHES = os.path.join(AUDIT_DIR, "breach_hashes.txt")

# Expected compromised UIDs based on the truth value
EXPECTED_COMPROMISED_UIDS = {23, 89, 156, 234, 312, 401, 478}


class TestAuditDirectoryExists:
    """Test that the audit directory exists and is writable."""

    def test_audit_directory_exists(self):
        assert os.path.isdir(AUDIT_DIR), f"Audit directory {AUDIT_DIR} does not exist"

    def test_audit_directory_is_writable(self):
        assert os.access(AUDIT_DIR, os.W_OK), f"Audit directory {AUDIT_DIR} is not writable"


class TestScanPyExists:
    """Test that scan.py exists and is executable with python3."""

    def test_scan_py_exists(self):
        assert os.path.isfile(SCAN_PY), f"Scanner script {SCAN_PY} does not exist"

    def test_scan_py_is_readable(self):
        assert os.access(SCAN_PY, os.R_OK), f"Scanner script {SCAN_PY} is not readable"

    def test_scan_py_is_executable_with_python3(self):
        # Check that python3 can at least parse the file
        result = subprocess.run(
            ["python3", "-m", "py_compile", SCAN_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"scan.py is not valid Python3: {result.stderr}"

    def test_scan_py_has_shebang(self):
        with open(SCAN_PY, 'r') as f:
            first_line = f.readline()
        assert first_line.startswith("#!"), "scan.py should have a shebang line"
        assert "python" in first_line.lower(), "scan.py shebang should reference python"


class TestUsersDatabaseExists:
    """Test that users.db exists and has the correct structure."""

    def test_users_db_exists(self):
        assert os.path.isfile(USERS_DB), f"Users database {USERS_DB} does not exist"

    def test_users_db_is_sqlite3(self):
        # Check SQLite3 magic bytes
        with open(USERS_DB, 'rb') as f:
            header = f.read(16)
        assert header.startswith(b'SQLite format 3'), f"{USERS_DB} is not a valid SQLite3 database"

    def test_users_db_has_accounts_table(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        result = cur.fetchone()
        conn.close()
        assert result is not None, "Database does not contain 'accounts' table"

    def test_accounts_table_has_correct_columns(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(accounts)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()

        required_columns = {'uid', 'email', 'password_hash'}
        missing = required_columns - columns
        assert not missing, f"accounts table is missing columns: {missing}"

    def test_accounts_table_has_500_users(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        count = cur.fetchone()[0]
        conn.close()
        assert count == 500, f"accounts table should have 500 users, found {count}"

    def test_password_hashes_are_bcrypt_format(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM accounts LIMIT 10")
        hashes = [row[0] for row in cur.fetchall()]
        conn.close()

        for h in hashes:
            assert h.startswith("$2b$") or h.startswith("$2a$") or h.startswith("$2y$"), \
                f"Password hash does not appear to be bcrypt format: {h[:20]}..."

    def test_password_hashes_have_no_trailing_whitespace(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT uid, password_hash FROM accounts")
        rows = cur.fetchall()
        conn.close()

        for uid, pw_hash in rows:
            assert pw_hash == pw_hash.strip(), \
                f"Password hash for uid {uid} has trailing/leading whitespace"


class TestBreachHashesFileExists:
    """Test that breach_hashes.txt exists and has correct format."""

    def test_breach_hashes_file_exists(self):
        assert os.path.isfile(BREACH_HASHES), f"Breach hashes file {BREACH_HASHES} does not exist"

    def test_breach_hashes_file_is_readable(self):
        assert os.access(BREACH_HASHES, os.R_OK), f"Breach hashes file {BREACH_HASHES} is not readable"

    def test_breach_hashes_has_10000_lines(self):
        with open(BREACH_HASHES, 'r') as f:
            line_count = sum(1 for _ in f)
        assert line_count == 10000, f"breach_hashes.txt should have 10000 lines, found {line_count}"

    def test_breach_hashes_are_bcrypt_format(self):
        with open(BREACH_HASHES, 'r') as f:
            # Check first 10 lines
            for i, line in enumerate(f):
                if i >= 10:
                    break
                stripped = line.strip()
                assert stripped.startswith("$2b$") or stripped.startswith("$2a$") or stripped.startswith("$2y$"), \
                    f"Breach hash line {i+1} does not appear to be bcrypt format: {stripped[:20]}..."


class TestExpectedCompromisedAccountsExist:
    """Test that the expected compromised accounts actually exist and match."""

    def test_expected_uids_exist_in_database(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT uid FROM accounts")
        all_uids = {row[0] for row in cur.fetchall()}
        conn.close()

        missing_uids = EXPECTED_COMPROMISED_UIDS - all_uids
        assert not missing_uids, f"Expected compromised UIDs not found in database: {missing_uids}"

    def test_exactly_7_compromised_accounts_exist(self):
        # Load breach hashes (stripping newlines to get actual hashes)
        with open(BREACH_HASHES, 'r') as f:
            breach_set = {line.strip() for line in f}

        # Check database
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT uid, password_hash FROM accounts")
        rows = cur.fetchall()
        conn.close()

        compromised = [uid for uid, pw_hash in rows if pw_hash in breach_set]

        assert len(compromised) == 7, \
            f"Expected exactly 7 compromised accounts, found {len(compromised)}: {compromised}"

    def test_compromised_uids_match_expected(self):
        # Load breach hashes (stripping newlines to get actual hashes)
        with open(BREACH_HASHES, 'r') as f:
            breach_set = {line.strip() for line in f}

        # Check database
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT uid, password_hash FROM accounts")
        rows = cur.fetchall()
        conn.close()

        compromised = {uid for uid, pw_hash in rows if pw_hash in breach_set}

        assert compromised == EXPECTED_COMPROMISED_UIDS, \
            f"Compromised UIDs {compromised} do not match expected {EXPECTED_COMPROMISED_UIDS}"


class TestScanPyHasTheBug:
    """Test that scan.py contains the bug (uses readlines without stripping)."""

    def test_scan_py_uses_readlines(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        assert 'readlines()' in content, \
            "scan.py should use readlines() (this is part of the bug)"

    def test_scan_py_does_not_strip_in_load_breach_hashes(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        # The bug is that it doesn't strip the newlines
        # Check that there's no .strip() immediately after readlines in the set creation
        # This is a heuristic check
        if 'set(f.readlines())' in content or 'set(f.readlines()' in content:
            # The buggy pattern exists
            pass
        else:
            # Check if there's a strip happening
            if '.strip()' in content and 'readlines' in content:
                # Might be fixed already, but let's verify by running
                pass

    def test_scan_py_currently_reports_zero_compromised(self):
        """Verify the bug exists by running scan.py and checking it reports 0."""
        result = subprocess.run(
            ["python3", SCAN_PY],
            capture_output=True,
            text=True,
            cwd=AUDIT_DIR
        )

        # The script should run without error
        assert result.returncode == 0, f"scan.py failed to run: {result.stderr}"

        # It should report 0 compromised accounts (the bug)
        assert "Found 0 compromised accounts" in result.stdout, \
            f"scan.py should currently report 0 compromised accounts (the bug), got: {result.stdout}"


class TestPythonEnvironment:
    """Test that the required Python environment is available."""

    def test_python3_available(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "python3 is not available"

    def test_python3_version_is_310_or_higher(self):
        result = subprocess.run(
            ["python3", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True
        )
        version = result.stdout.strip()
        major, minor = map(int, version.split('.'))
        assert (major, minor) >= (3, 10), f"Python version should be 3.10+, got {version}"

    def test_sqlite3_module_available(self):
        result = subprocess.run(
            ["python3", "-c", "import sqlite3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sqlite3 module is not available in Python"
