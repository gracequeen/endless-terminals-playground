# test_final_state.py
"""
Tests to validate the final state after the student has fixed the Python 2.7-era
backup validation script to work with Python 3.
"""

import os
import subprocess
import sqlite3
import re
import pytest


# Base paths
HOME = "/home/user"
BACKUP_DIR = os.path.join(HOME, "backup")
VALIDATE_SCRIPT = os.path.join(BACKUP_DIR, "validate.py")
MANIFESTS_DIR = os.path.join(BACKUP_DIR, "manifests")
CHECKSUMS_DB = os.path.join(BACKUP_DIR, "checksums.db")
DATA_DIR = os.path.join(BACKUP_DIR, "data")


class TestScriptRunsSuccessfully:
    """Test that the fixed script runs without errors."""

    def test_script_runs_without_python_errors(self):
        """The script should run to completion without Python errors."""
        result = subprocess.run(
            ["python3", VALIDATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        # Check for common Python error indicators in stderr
        error_indicators = ['Traceback', 'SyntaxError', 'AttributeError', 
                           'TypeError', 'NameError', 'ValueError']
        for indicator in error_indicators:
            assert indicator not in result.stderr, \
                f"Script failed with Python error ({indicator}): {result.stderr}"

    def test_script_exits_with_code_zero(self):
        """The script should exit with code 0 (all checksums valid)."""
        result = subprocess.run(
            ["python3", VALIDATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        assert result.returncode == 0, \
            f"Script exited with code {result.returncode}. " \
            f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_script_outputs_valid_for_all_files(self):
        """The script should output 'VALID' at least 9 times (for 9 files)."""
        result = subprocess.run(
            ["python3", VALIDATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        valid_count = result.stdout.upper().count('VALID')
        assert valid_count >= 9, \
            f"Expected at least 9 'VALID' outputs, found {valid_count}. " \
            f"stdout: {result.stdout}"


class TestScriptStillPerformsValidation:
    """Test that the script still performs actual MD5 validation."""

    def test_script_uses_hashlib_md5(self):
        """The script must still use hashlib.md5 for checksumming."""
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()
        assert 'hashlib.md5' in content or 'hashlib' in content and 'md5' in content, \
            "Script no longer uses hashlib.md5 for checksumming"

    def test_script_uses_binary_read_mode_with_md5(self):
        """The script must read files in binary mode for MD5 hashing."""
        result = subprocess.run(
            ["grep", "-E", r"hashlib\.md5.*open.*rb|open.*rb.*hashlib\.md5|open\([^)]*,\s*['\"]rb['\"]|'rb'|\"rb\"",
             VALIDATE_SCRIPT],
            capture_output=True,
            text=True
        )
        # Also check the file content directly for more flexible matching
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()

        # Check for binary read mode in various patterns
        has_binary_read = (
            "'rb'" in content or
            '"rb"' in content or
            "rb'" in content or
            'rb"' in content
        )
        assert has_binary_read, \
            "Script does not appear to use binary read mode ('rb') for file hashing. " \
            "This is required for hashlib.md5 to work correctly in Python 3."

    def test_script_queries_database(self):
        """The script must query the checksums database."""
        result = subprocess.run(
            ["grep", "-E", r"SELECT.*FROM.*checksums|cursor\.(execute|fetchall)",
             VALIDATE_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0 and result.stdout.strip(), \
            "Script does not appear to query the checksums database"


class TestInvariantsPreserved:
    """Test that invariant files were not modified."""

    def test_manifest_files_exist(self):
        """All manifest files should still exist."""
        expected_manifests = ["tape001.manifest", "tape002.manifest", "tape003.manifest"]
        for manifest in expected_manifests:
            manifest_path = os.path.join(MANIFESTS_DIR, manifest)
            assert os.path.isfile(manifest_path), \
                f"Manifest file {manifest_path} is missing"

    def test_checksums_db_exists(self):
        """The checksums database should still exist."""
        assert os.path.isfile(CHECKSUMS_DB), \
            f"Checksums database {CHECKSUMS_DB} is missing"

    def test_checksums_db_is_valid(self):
        """The checksums database should still be valid SQLite."""
        try:
            conn = sqlite3.connect(CHECKSUMS_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM checksums;")
            count = cursor.fetchone()[0]
            conn.close()
            assert count > 0, "Checksums table is empty"
        except sqlite3.DatabaseError as e:
            pytest.fail(f"checksums.db is not a valid SQLite database: {e}")

    def test_data_directory_has_files(self):
        """The data directory should still contain files."""
        assert os.path.isdir(DATA_DIR), f"Data directory {DATA_DIR} is missing"
        files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
        assert len(files) > 0, f"Data directory {DATA_DIR} has no files"


class TestPython3CompatibilityFixes:
    """Test that specific Python 2 to 3 compatibility issues were fixed."""

    def test_no_old_comparison_operator(self):
        """The script should not use the <> comparison operator (Python 2 only)."""
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()
        # Look for <> that's not inside a string
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Skip comments
            code_part = line.split('#')[0] if '#' in line else line
            # Check for <> operator (but not inside strings)
            if '<>' in code_part:
                # Simple check - if it's in code context
                # Remove string literals for checking
                stripped = re.sub(r'["\'][^"\']*["\']', '', code_part)
                assert '<>' not in stripped, \
                    f"Line {i} still uses Python 2 '<>' operator: {line}"

    def test_no_old_except_syntax(self):
        """The script should not use old except syntax (except X, e:)."""
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()
        # Pattern for old except syntax: except SomeError, variable:
        old_except_pattern = re.compile(r'except\s+\w+\s*,\s*\w+\s*:')
        match = old_except_pattern.search(content)
        assert match is None, \
            f"Script still uses old except syntax: {match.group() if match else ''}"

    def test_print_is_function_call(self):
        """Print statements should use function call syntax."""
        with open(VALIDATE_SCRIPT, 'r') as f:
            content = f.read()
        # Look for print without parentheses (Python 2 style)
        # Pattern: print followed by space and something that's not (
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comments and empty lines
            if stripped.startswith('#') or not stripped:
                continue
            # Check for print statement without parentheses
            if re.match(r'^print\s+[^(]', stripped):
                pytest.fail(f"Line {i} uses Python 2 print statement: {line}")


class TestScriptFunctionality:
    """Test the actual functionality of the fixed script."""

    def test_script_processes_all_manifests(self):
        """The script should process all 3 manifest files."""
        result = subprocess.run(
            ["python3", VALIDATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        output = result.stdout + result.stderr
        # The script should mention or process all manifests
        # At minimum, it should produce output for files from all manifests
        assert result.returncode == 0, \
            f"Script failed: {result.stderr}"

    def test_script_validates_checksums_correctly(self):
        """The script should correctly validate file checksums."""
        result = subprocess.run(
            ["python3", VALIDATE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        # Should not report any mismatches (test data is valid)
        output_upper = result.stdout.upper()
        mismatch_count = output_upper.count('MISMATCH')
        assert mismatch_count == 0, \
            f"Script reported {mismatch_count} mismatches but all checksums should be valid. " \
            f"stdout: {result.stdout}"
