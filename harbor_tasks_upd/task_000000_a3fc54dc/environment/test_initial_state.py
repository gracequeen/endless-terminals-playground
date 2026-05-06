# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the action to fix the dashboard checksum verification issues.
"""

import os
import re
import pytest
import hashlib


HOME = "/home/user"
MONITOR_DIR = os.path.join(HOME, "monitor")
CONFIG_DIR = os.path.join(MONITOR_DIR, "config")
DASHBOARD_PATH = os.path.join(MONITOR_DIR, "dashboard.py")
CHECKSUMS_PATH = os.path.join(CONFIG_DIR, "checksums.sha256")
MANIFEST_PATH = os.path.join(CONFIG_DIR, "manifest.json")
SCHEMA_METRICS_PATH = os.path.join(CONFIG_DIR, "schema_metrics.json")
SCHEMA_LOGS_PATH = os.path.join(CONFIG_DIR, "schema_logs.json")
SCHEMA_TRACES_PATH = os.path.join(CONFIG_DIR, "schema_traces.json")


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_monitor_directory_exists(self):
        assert os.path.isdir(MONITOR_DIR), (
            f"Monitor directory does not exist at {MONITOR_DIR}"
        )

    def test_config_directory_exists(self):
        assert os.path.isdir(CONFIG_DIR), (
            f"Config directory does not exist at {CONFIG_DIR}"
        )

    def test_monitor_directory_is_writable(self):
        assert os.access(MONITOR_DIR, os.W_OK), (
            f"Monitor directory {MONITOR_DIR} is not writable"
        )

    def test_config_directory_is_writable(self):
        assert os.access(CONFIG_DIR, os.W_OK), (
            f"Config directory {CONFIG_DIR} is not writable"
        )


class TestRequiredFilesExist:
    """Test that all required files exist."""

    def test_dashboard_script_exists(self):
        assert os.path.isfile(DASHBOARD_PATH), (
            f"Dashboard script does not exist at {DASHBOARD_PATH}"
        )

    def test_checksums_file_exists(self):
        assert os.path.isfile(CHECKSUMS_PATH), (
            f"Checksums file does not exist at {CHECKSUMS_PATH}"
        )

    def test_manifest_json_exists(self):
        assert os.path.isfile(MANIFEST_PATH), (
            f"Manifest file does not exist at {MANIFEST_PATH}"
        )

    def test_schema_metrics_exists(self):
        assert os.path.isfile(SCHEMA_METRICS_PATH), (
            f"Schema metrics file does not exist at {SCHEMA_METRICS_PATH}"
        )

    def test_schema_logs_exists(self):
        assert os.path.isfile(SCHEMA_LOGS_PATH), (
            f"Schema logs file does not exist at {SCHEMA_LOGS_PATH}"
        )

    def test_schema_traces_exists(self):
        assert os.path.isfile(SCHEMA_TRACES_PATH), (
            f"Schema traces file does not exist at {SCHEMA_TRACES_PATH}"
        )


class TestDashboardScript:
    """Test that dashboard.py has the expected verification logic."""

    def test_dashboard_is_readable(self):
        assert os.access(DASHBOARD_PATH, os.R_OK), (
            f"Dashboard script {DASHBOARD_PATH} is not readable"
        )

    def test_dashboard_contains_verification_logic(self):
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        # Check for checksum-related keywords
        checksum_keywords = ['verify_checksums', 'SHA256', 'checksum', 'hashlib']
        found_keywords = [kw for kw in checksum_keywords if kw in content]

        assert len(found_keywords) >= 2, (
            f"Dashboard script should contain checksum verification logic. "
            f"Expected at least 2 of {checksum_keywords}, found: {found_keywords}"
        )

    def test_dashboard_has_verify_checksums_function(self):
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        assert 'def verify_checksums' in content, (
            "Dashboard script should contain a verify_checksums function"
        )

    def test_dashboard_has_buggy_regex_pattern(self):
        """Verify the bug exists: regex uses .+ which captures trailing whitespace."""
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        # The buggy pattern uses .+ at the end which captures trailing spaces
        # Looking for pattern like: r'SHA256 \(([^)]+)\) = (.+)'
        assert re.search(r"re\.match\(['\"].*\(\.\+\).*['\"]", content) or \
               re.search(r"\.match\(.*\.\+.*\)", content), (
            "Dashboard script should contain the buggy regex pattern that uses .+ "
            "which captures trailing whitespace"
        )


class TestChecksumsFile:
    """Test the checksums.sha256 file format and content."""

    def test_checksums_file_is_readable(self):
        assert os.access(CHECKSUMS_PATH, os.R_OK), (
            f"Checksums file {CHECKSUMS_PATH} is not readable"
        )

    def test_checksums_file_has_bsd_format(self):
        """Verify checksums file uses BSD-style format."""
        with open(CHECKSUMS_PATH, 'r') as f:
            content = f.read()

        # BSD format: SHA256 (filename) = hash
        bsd_pattern = r'SHA256 \([^)]+\) = [a-f0-9]+'
        matches = re.findall(bsd_pattern, content)

        assert len(matches) >= 4, (
            f"Checksums file should contain at least 4 BSD-format entries, "
            f"found {len(matches)}"
        )

    def test_checksums_file_lists_all_config_files(self):
        """Verify all config files are listed in checksums."""
        with open(CHECKSUMS_PATH, 'r') as f:
            content = f.read()

        expected_files = ['manifest.json', 'schema_metrics.json', 
                         'schema_logs.json', 'schema_traces.json']

        for filename in expected_files:
            assert filename in content, (
                f"Checksums file should list {filename}"
            )

    def test_schema_traces_line_has_trailing_space(self):
        """Verify the bug: schema_traces.json line has trailing space."""
        with open(CHECKSUMS_PATH, 'r') as f:
            lines = f.readlines()

        traces_line = None
        for line in lines:
            if 'schema_traces.json' in line:
                traces_line = line
                break

        assert traces_line is not None, (
            "Checksums file should contain a line for schema_traces.json"
        )

        # Check for trailing space before newline (the bug)
        # The line should end with "hash " or "hash \n" (space before newline)
        stripped_of_newline = traces_line.rstrip('\n')
        assert stripped_of_newline.endswith(' '), (
            f"Bug setup: schema_traces.json line should have trailing space. "
            f"Line: {repr(traces_line)}"
        )

    def test_schema_logs_has_wrong_checksum(self):
        """Verify the bug: schema_logs.json has outdated checksum."""
        with open(CHECKSUMS_PATH, 'r') as f:
            content = f.read()

        # Extract the stored hash for schema_logs.json
        match = re.search(r'SHA256 \(schema_logs\.json\) = ([a-f0-9]+)', content)
        assert match, "Could not find schema_logs.json entry in checksums file"

        stored_hash = match.group(1)

        # Compute actual hash
        with open(SCHEMA_LOGS_PATH, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()

        assert stored_hash != actual_hash, (
            f"Bug setup: schema_logs.json should have WRONG checksum in checksums.sha256. "
            f"Stored: {stored_hash}, Actual: {actual_hash}"
        )


class TestSchemaFiles:
    """Test the schema files exist and are readable."""

    def test_manifest_json_is_valid_json(self):
        import json
        with open(MANIFEST_PATH, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"manifest.json is not valid JSON: {e}")

        # Should define three services
        assert isinstance(data, dict), "manifest.json should be a JSON object"

    def test_schema_files_are_readable(self):
        for path in [SCHEMA_METRICS_PATH, SCHEMA_LOGS_PATH, SCHEMA_TRACES_PATH]:
            assert os.access(path, os.R_OK), (
                f"Schema file {path} is not readable"
            )


class TestDashboardCurrentlyFails:
    """Test that the dashboard currently fails with integrity errors."""

    def test_dashboard_fails_on_execution(self):
        import subprocess

        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        assert result.returncode != 0, (
            "Bug setup: Dashboard should currently fail (exit non-zero) due to "
            f"checksum errors. Got exit code {result.returncode}. "
            f"stdout: {result.stdout}, stderr: {result.stderr}"
        )

    def test_dashboard_shows_integrity_error(self):
        import subprocess

        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        combined_output = result.stdout + result.stderr
        assert 'Integrity error' in combined_output or 'checksum' in combined_output.lower(), (
            "Bug setup: Dashboard should show integrity/checksum error message. "
            f"Output: {combined_output}"
        )
