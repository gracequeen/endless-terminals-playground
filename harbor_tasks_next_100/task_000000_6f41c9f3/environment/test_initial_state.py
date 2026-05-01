# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the Python 2.7-era backup validation script.
"""

import os
import subprocess
import sqlite3
import pytest


# Base paths
HOME = "/home/user"
BACKUP_DIR = os.path.join(HOME, "backup")
VALIDATE_SCRIPT = os.path.join(BACKUP_DIR, "validate.py")
MANIFESTS_DIR = os.path.join(BACKUP_DIR, "manifests")
CHECKSUMS_DB = os.path.join(BACKUP_DIR, "checksums.db")
DATA_DIR = os.path.join(BACKUP_DIR, "data")


class TestPythonEnvironment:
    """Test that Python 3 is available and Python 2 is not."""

    def test_python3_installed(self):
        """Python 3 should be installed and accessible."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not installed or not accessible"
        assert "Python 3" in result.stdout or "Python 3" in result.stderr, \
            f"Expected Python 3, got: {result.stdout} {result.stderr}"

    def test_python3_is_version_3_11_or_compatible(self):
        """Python 3 should be a modern version (3.x)."""
        result = subprocess.run(
            ["python3", "-c", "import sys; print(sys.version_info.major, sys.version_info.minor)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get Python version info"
        major, minor = result.stdout.strip().split()
        assert int(major) == 3, f"Expected Python 3.x, got major version {major}"


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_backup_directory_exists(self):
        """The /home/user/backup directory should exist."""
        assert os.path.isdir(BACKUP_DIR), \
            f"Backup directory {BACKUP_DIR} does not exist"

    def test_manifests_directory_exists(self):
        """The /home/user/backup/manifests directory should exist."""
        assert os.path.isdir(MANIFESTS_DIR), \
            f"Manifests directory {MANIFESTS_DIR} does not exist"

    def test_data_directory_exists(self):
        """The /home/user/backup/data directory should exist."""
        assert os.path.isdir(DATA_DIR), \
            f"Data directory {DATA_DIR} does not exist"


class TestValidateScript:
    """Test that the validate.py script exists and has expected issues."""

    def test_validate_script_exists(self):
        """The validate.py script should exist."""
        assert os.path.isfile(VALIDATE_SCRIPT), \
            f"Validate script {VALIDATE_SCRIPT} does not exist"

    def test_validate_script_is_readable(self):
        """The validate.py script should be readable."""
        assert os.access(VALIDATE_SCRIPT, os.R_OK), \
            f"Validate script {VALIDATE_SCRIPT} is not readable"

    def test_validate_script_is_writable(self):
        """The validate.py script should be writable (so student can fix it)."""
        assert os.access(VALIDATE_SCRIPT, os.W_OK), \
            f"Validate script {VALIDATE_SCRIPT} is not writable"

    def test_validate_script_contains_hashlib_md5(self):
        """The script should use hashlib.md5 for checksumming."""
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()
        assert 'hashlib.md5' in content or 'hashlib' in content, \
            "Script does not appear to use hashlib for MD5 checksumming"

    def test_validate_script_has_python_code(self):
        """The script should contain Python code."""
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()
        # Check for common Python constructs
        assert 'import' in content or 'def ' in content or 'class ' in content, \
            "Script does not appear to contain Python code"


class TestManifestFiles:
    """Test that manifest files exist and have content."""

    def test_tape001_manifest_exists(self):
        """tape001.manifest should exist."""
        manifest_path = os.path.join(MANIFESTS_DIR, "tape001.manifest")
        assert os.path.isfile(manifest_path), \
            f"Manifest file {manifest_path} does not exist"

    def test_tape002_manifest_exists(self):
        """tape002.manifest should exist."""
        manifest_path = os.path.join(MANIFESTS_DIR, "tape002.manifest")
        assert os.path.isfile(manifest_path), \
            f"Manifest file {manifest_path} does not exist"

    def test_tape003_manifest_exists(self):
        """tape003.manifest should exist."""
        manifest_path = os.path.join(MANIFESTS_DIR, "tape003.manifest")
        assert os.path.isfile(manifest_path), \
            f"Manifest file {manifest_path} does not exist"

    def test_manifest_files_have_content(self):
        """Each manifest file should have content (file paths)."""
        for manifest_name in ["tape001.manifest", "tape002.manifest", "tape003.manifest"]:
            manifest_path = os.path.join(MANIFESTS_DIR, manifest_name)
            with open(manifest_path, 'r') as f:
                content = f.read().strip()
            assert len(content) > 0, \
                f"Manifest file {manifest_path} is empty"

    def test_exactly_three_manifest_files(self):
        """There should be exactly 3 manifest files."""
        manifest_files = [f for f in os.listdir(MANIFESTS_DIR) if f.endswith('.manifest')]
        assert len(manifest_files) == 3, \
            f"Expected 3 manifest files, found {len(manifest_files)}: {manifest_files}"


class TestChecksumsDatabase:
    """Test that the checksums database exists and has expected structure."""

    def test_checksums_db_exists(self):
        """The checksums.db file should exist."""
        assert os.path.isfile(CHECKSUMS_DB), \
            f"Checksums database {CHECKSUMS_DB} does not exist"

    def test_checksums_db_is_valid_sqlite(self):
        """The checksums.db should be a valid SQLite database."""
        try:
            conn = sqlite3.connect(CHECKSUMS_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            assert len(tables) > 0, "Database has no tables"
        except sqlite3.DatabaseError as e:
            pytest.fail(f"checksums.db is not a valid SQLite database: {e}")

    def test_checksums_table_exists(self):
        """The checksums table should exist in the database."""
        conn = sqlite3.connect(CHECKSUMS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checksums';")
        result = cursor.fetchone()
        conn.close()
        assert result is not None, \
            "Table 'checksums' does not exist in the database"

    def test_checksums_table_has_expected_columns(self):
        """The checksums table should have expected columns."""
        conn = sqlite3.connect(CHECKSUMS_DB)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(checksums);")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        expected_columns = {'manifest_id', 'filepath', 'md5sum'}
        assert expected_columns.issubset(columns), \
            f"Missing columns in checksums table. Expected {expected_columns}, found {columns}"

    def test_checksums_table_has_data(self):
        """The checksums table should have data entries."""
        conn = sqlite3.connect(CHECKSUMS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM checksums;")
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, "Checksums table is empty"


class TestDataFiles:
    """Test that data files referenced by manifests exist."""

    def test_data_directory_has_files(self):
        """The data directory should contain files."""
        files = os.listdir(DATA_DIR)
        assert len(files) > 0, \
            f"Data directory {DATA_DIR} is empty"

    def test_data_files_are_readable(self):
        """All files in data directory should be readable."""
        for filename in os.listdir(DATA_DIR):
            filepath = os.path.join(DATA_DIR, filename)
            if os.path.isfile(filepath):
                assert os.access(filepath, os.R_OK), \
                    f"Data file {filepath} is not readable"


class TestSqliteCLI:
    """Test that sqlite3 CLI tool is available."""

    def test_sqlite3_cli_available(self):
        """The sqlite3 CLI tool should be available."""
        result = subprocess.run(
            ["which", "sqlite3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "sqlite3 CLI tool is not available"


class TestScriptCurrentlyFails:
    """Test that the script currently fails with Python 3 (has issues to fix)."""

    def test_script_fails_with_python3(self):
        """The script should currently fail when run with Python 3."""
        result = subprocess.run(
            ["python3", VALIDATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        # The script should fail (non-zero exit code or error output)
        # due to Python 2/3 compatibility issues
        has_error = (
            result.returncode != 0 or
            'Error' in result.stderr or
            'error' in result.stderr or
            'Traceback' in result.stderr or
            'SyntaxError' in result.stderr or
            'AttributeError' in result.stderr or
            'TypeError' in result.stderr
        )
        assert has_error, \
            "Script should currently fail with Python 3 due to compatibility issues"
