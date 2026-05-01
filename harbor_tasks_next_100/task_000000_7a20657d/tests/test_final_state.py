# test_final_state.py
"""
Tests to validate the final state of the operating system / filesystem
after the student has completed the user-audit scan debugging task.
"""

import os
import sqlite3
import subprocess
import tempfile
import shutil
import pytest


AUDIT_DIR = "/home/user/audit"
SCAN_PY = os.path.join(AUDIT_DIR, "scan.py")
USERS_DB = os.path.join(AUDIT_DIR, "users.db")
BREACH_HASHES = os.path.join(AUDIT_DIR, "breach_hashes.txt")
COMPROMISED_UIDS_FILE = os.path.join(AUDIT_DIR, "compromised_uids.txt")

# Expected compromised UIDs based on the truth value
EXPECTED_COMPROMISED_UIDS = {23, 89, 156, 234, 312, 401, 478}


class TestScanPyRunsSuccessfully:
    """Test that scan.py runs without errors."""

    def test_scan_py_exits_zero(self):
        result = subprocess.run(
            ["python3", SCAN_PY],
            capture_output=True,
            text=True,
            cwd=AUDIT_DIR
        )
        assert result.returncode == 0, f"scan.py should exit with code 0, got {result.returncode}. stderr: {result.stderr}"

    def test_scan_py_reports_7_compromised(self):
        result = subprocess.run(
            ["python3", SCAN_PY],
            capture_output=True,
            text=True,
            cwd=AUDIT_DIR
        )
        assert "Found 7 compromised accounts" in result.stdout, \
            f"scan.py should report 'Found 7 compromised accounts', got: {result.stdout}"


class TestCompromisedUidsFileExists:
    """Test that the compromised_uids.txt file exists and has correct content."""

    def test_compromised_uids_file_exists(self):
        # First run scan.py to ensure the file is created
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)
        assert os.path.isfile(COMPROMISED_UIDS_FILE), \
            f"Compromised UIDs file {COMPROMISED_UIDS_FILE} does not exist"

    def test_compromised_uids_file_has_7_lines(self):
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)

        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(COMPROMISED_UIDS_FILE, 'r'),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip().split()[0])
        assert line_count == 7, f"compromised_uids.txt should have 7 lines, found {line_count}"

    def test_compromised_uids_contains_expected_uids(self):
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)

        with open(COMPROMISED_UIDS_FILE, 'r') as f:
            uids = set()
            for line in f:
                stripped = line.strip()
                if stripped:
                    uids.add(int(stripped))

        assert uids == EXPECTED_COMPROMISED_UIDS, \
            f"compromised_uids.txt contains {uids}, expected {EXPECTED_COMPROMISED_UIDS}"

    def test_compromised_uids_sorted_output(self):
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)

        result = subprocess.run(
            ["sort", "-n", COMPROMISED_UIDS_FILE],
            capture_output=True,
            text=True
        )
        lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        expected_sorted = ['23', '89', '156', '234', '312', '401', '478']

        assert lines == expected_sorted, \
            f"Sorted UIDs should be {expected_sorted}, got {lines}"

    def test_no_duplicate_uids(self):
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)

        with open(COMPROMISED_UIDS_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        assert len(lines) == len(set(lines)), \
            f"compromised_uids.txt contains duplicates: {lines}"

    def test_no_extra_whitespace_in_uids(self):
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)

        with open(COMPROMISED_UIDS_FILE, 'r') as f:
            for i, line in enumerate(f, 1):
                # Each line should be just a number followed by newline
                content = line.rstrip('\n')
                assert content == content.strip(), \
                    f"Line {i} has extra whitespace: '{repr(line)}'"
                # Should be a valid integer
                try:
                    int(content)
                except ValueError:
                    pytest.fail(f"Line {i} is not a valid integer: '{content}'")


class TestDatabaseUnmodified:
    """Test that users.db remains unmodified."""

    def test_users_db_still_has_500_accounts(self):
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM accounts")
        count = cur.fetchone()[0]
        conn.close()
        assert count == 500, f"users.db should still have 500 accounts, found {count}"

    def test_users_db_hashes_unchanged(self):
        # Verify the expected compromised accounts still have hashes that match breach file
        with open(BREACH_HASHES, 'r') as f:
            breach_set = {line.strip() for line in f}

        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT uid, password_hash FROM accounts")
        rows = cur.fetchall()
        conn.close()

        compromised = {uid for uid, pw_hash in rows if pw_hash in breach_set}
        assert compromised == EXPECTED_COMPROMISED_UIDS, \
            f"Database appears modified. Compromised UIDs now: {compromised}, expected: {EXPECTED_COMPROMISED_UIDS}"


class TestBreachHashesUnmodified:
    """Test that breach_hashes.txt remains unmodified."""

    def test_breach_hashes_still_has_10000_lines(self):
        with open(BREACH_HASHES, 'r') as f:
            line_count = sum(1 for _ in f)
        assert line_count == 10000, f"breach_hashes.txt should still have 10000 lines, found {line_count}"


class TestNoHardcodedUids:
    """Test that scan.py does not hardcode the expected UIDs."""

    def test_scan_py_does_not_contain_hardcoded_uids(self):
        result = subprocess.run(
            ["grep", "-E", r"^\s*(23|89|156|234|312|401|478)\s*$", SCAN_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            f"scan.py appears to contain hardcoded UIDs: {result.stdout}"

    def test_scan_py_does_not_have_uid_list_literal(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        # Check for suspicious patterns that might indicate hardcoding
        suspicious_patterns = [
            "[23, 89, 156, 234, 312, 401, 478]",
            "[23,89,156,234,312,401,478]",
            "{23, 89, 156, 234, 312, 401, 478}",
            "{23,89,156,234,312,401,478}",
            "(23, 89, 156, 234, 312, 401, 478)",
            "(23,89,156,234,312,401,478)",
        ]

        for pattern in suspicious_patterns:
            assert pattern not in content, \
                f"scan.py appears to contain hardcoded UID list: {pattern}"


class TestDynamicDetection:
    """Test that scan.py dynamically detects compromised accounts."""

    def test_scan_detects_new_compromised_account(self):
        """
        Add a new compromised account (uid 499) and verify scan.py detects it.
        This tests that the solution is dynamic, not hardcoded.
        """
        # Get a hash from the breach file to use for the new account
        with open(BREACH_HASHES, 'r') as f:
            # Get a hash that's not already used by the 7 compromised accounts
            breach_hashes = [line.strip() for line in f]

        # Get existing compromised hashes
        conn = sqlite3.connect(USERS_DB)
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM accounts WHERE uid IN (23, 89, 156, 234, 312, 401, 478)")
        existing_compromised_hashes = {row[0] for row in cur.fetchall()}

        # Find a breach hash not already in use
        new_hash = None
        for h in breach_hashes:
            if h not in existing_compromised_hashes:
                new_hash = h
                break

        assert new_hash is not None, "Could not find an unused breach hash for testing"

        # Check if uid 499 exists
        cur.execute("SELECT uid FROM accounts WHERE uid = 499")
        uid_499_exists = cur.fetchone() is not None

        if uid_499_exists:
            # Update existing account
            cur.execute("UPDATE accounts SET password_hash = ? WHERE uid = 499", (new_hash,))
        else:
            # Insert new account
            cur.execute("INSERT INTO accounts (uid, email, password_hash) VALUES (499, 'test499@example.com', ?)", (new_hash,))

        conn.commit()
        conn.close()

        try:
            # Run scan.py
            result = subprocess.run(
                ["python3", SCAN_PY],
                capture_output=True,
                text=True,
                cwd=AUDIT_DIR
            )

            assert result.returncode == 0, f"scan.py failed after adding new compromised account: {result.stderr}"

            # Check that 8 accounts are now reported
            assert "Found 8 compromised accounts" in result.stdout, \
                f"scan.py should report 8 compromised accounts after adding uid 499, got: {result.stdout}"

            # Check that uid 499 is in the output file
            with open(COMPROMISED_UIDS_FILE, 'r') as f:
                uids = {int(line.strip()) for line in f if line.strip()}

            assert 499 in uids, f"uid 499 should be in compromised_uids.txt, got: {uids}"
            assert len(uids) == 8, f"Should have 8 compromised UIDs, got {len(uids)}: {uids}"

        finally:
            # Restore the database to original state
            conn = sqlite3.connect(USERS_DB)
            cur = conn.cursor()
            if uid_499_exists:
                # Restore original hash (we don't know it, so set to a non-breach hash)
                cur.execute("UPDATE accounts SET password_hash = '$2b$12$notabreachedhashxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' WHERE uid = 499")
            else:
                # Remove the added account
                cur.execute("DELETE FROM accounts WHERE uid = 499")
            conn.commit()
            conn.close()

            # Re-run scan.py to restore compromised_uids.txt
            subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)


class TestScanPyStillReadsFromFiles:
    """Test that scan.py still reads from the actual files and database."""

    def test_scan_py_references_breach_hashes_file(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        assert 'breach_hashes.txt' in content, \
            "scan.py should reference breach_hashes.txt"

    def test_scan_py_references_users_db(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        assert 'users.db' in content, \
            "scan.py should reference users.db"

    def test_scan_py_uses_sqlite3(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        assert 'sqlite3' in content, \
            "scan.py should use sqlite3 module"

    def test_scan_py_opens_and_reads_files(self):
        with open(SCAN_PY, 'r') as f:
            content = f.read()

        # Should have file open operations
        assert 'open(' in content, \
            "scan.py should open files"


class TestBugIsFix:
    """Test that the original bug (trailing newlines) has been fixed."""

    def test_breach_hashes_loaded_without_newlines(self):
        """
        Verify that the fix properly strips newlines from breach hashes.
        We do this by checking that the comparison now works.
        """
        subprocess.run(["python3", SCAN_PY], cwd=AUDIT_DIR, capture_output=True)

        with open(COMPROMISED_UIDS_FILE, 'r') as f:
            uids = {int(line.strip()) for line in f if line.strip()}

        # If the bug is fixed, we should have exactly 7 UIDs
        assert len(uids) == 7, \
            f"Bug may not be fully fixed. Expected 7 compromised UIDs, got {len(uids)}: {uids}"

        assert uids == EXPECTED_COMPROMISED_UIDS, \
            f"Bug may not be fully fixed. Got UIDs {uids}, expected {EXPECTED_COMPROMISED_UIDS}"
