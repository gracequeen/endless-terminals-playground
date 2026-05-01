# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the config registry migration task.
"""

import os
import pytest
import subprocess


class TestInitialState:
    """Validate the initial state before the migration task."""

    ENDPOINTS_FILE = "/home/user/services/endpoints.conf"
    SERVICES_DIR = "/home/user/services"

    def test_services_directory_exists(self):
        """Verify /home/user/services/ directory exists."""
        assert os.path.isdir(self.SERVICES_DIR), (
            f"Directory {self.SERVICES_DIR} does not exist. "
            "The services directory must exist before performing the migration."
        )

    def test_services_directory_is_writable(self):
        """Verify /home/user/services/ directory is writable."""
        assert os.access(self.SERVICES_DIR, os.W_OK), (
            f"Directory {self.SERVICES_DIR} is not writable. "
            "The services directory must be writable for in-place editing."
        )

    def test_endpoints_file_exists(self):
        """Verify /home/user/services/endpoints.conf exists."""
        assert os.path.isfile(self.ENDPOINTS_FILE), (
            f"File {self.ENDPOINTS_FILE} does not exist. "
            "The endpoints.conf file must exist before performing the migration."
        )

    def test_endpoints_file_is_readable(self):
        """Verify /home/user/services/endpoints.conf is readable."""
        assert os.access(self.ENDPOINTS_FILE, os.R_OK), (
            f"File {self.ENDPOINTS_FILE} is not readable. "
            "The endpoints.conf file must be readable."
        )

    def test_endpoints_file_is_writable(self):
        """Verify /home/user/services/endpoints.conf is writable."""
        assert os.access(self.ENDPOINTS_FILE, os.W_OK), (
            f"File {self.ENDPOINTS_FILE} is not writable. "
            "The endpoints.conf file must be writable for in-place editing."
        )

    def test_file_has_approximately_60_lines(self):
        """Verify the file has approximately 60 lines (40 endpoints + comments/blanks)."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            lines = f.readlines()
        line_count = len(lines)
        assert 55 <= line_count <= 65, (
            f"File {self.ENDPOINTS_FILE} has {line_count} lines, expected approximately 60 lines "
            "(40 endpoint definitions plus comments and blank lines)."
        )

    def test_file_contains_40_legacy_prefixes(self):
        """Verify the file contains exactly 40 occurrences of 'legacy-' prefix."""
        result = subprocess.run(
            ["grep", "-c", "legacy-", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        # grep -c returns the count as a string
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 40, (
            f"File {self.ENDPOINTS_FILE} contains {count} occurrences of 'legacy-', "
            "expected exactly 40 occurrences to migrate."
        )

    def test_file_contains_40_endpoint_definitions_with_legacy(self):
        """Verify there are 40 endpoint definitions with legacy- prefix."""
        result = subprocess.run(
            ["grep", "-cE", r"^[a-z_]+_endpoint=legacy-", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 40, (
            f"File {self.ENDPOINTS_FILE} contains {count} endpoint definitions with 'legacy-' prefix, "
            "expected exactly 40 endpoint definitions in format 'name_endpoint=legacy-...'."
        )

    def test_file_contains_no_svc_prefix_initially(self):
        """Verify the file does not already contain 'svc-' prefix (migration not done)."""
        result = subprocess.run(
            ["grep", "-c", "svc-", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        # grep returns exit code 1 if no matches found
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 0, (
            f"File {self.ENDPOINTS_FILE} already contains {count} occurrences of 'svc-'. "
            "The migration appears to have already been partially or fully completed."
        )

    def test_file_contains_comment_lines(self):
        """Verify the file contains comment lines (lines starting with #)."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()
        comment_lines = [line for line in content.splitlines() if line.strip().startswith('#')]
        assert len(comment_lines) > 0, (
            f"File {self.ENDPOINTS_FILE} does not contain any comment lines. "
            "Expected comment lines starting with '#'."
        )

    def test_file_contains_internal_domain(self):
        """Verify endpoint definitions use .internal domain."""
        result = subprocess.run(
            ["grep", "-c", r"\.internal:", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 40, (
            f"File {self.ENDPOINTS_FILE} contains {count} occurrences of '.internal:' domain, "
            "expected at least 40 (one per endpoint definition)."
        )

    def test_file_format_has_port_numbers(self):
        """Verify endpoint definitions include port numbers."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()

        # Check for pattern like :8080, :5432, etc.
        import re
        port_pattern = re.compile(r':\d{2,5}$', re.MULTILINE)
        matches = port_pattern.findall(content)
        assert len(matches) >= 40, (
            f"File {self.ENDPOINTS_FILE} contains {len(matches)} lines with port numbers, "
            "expected at least 40 endpoint definitions with ports."
        )

    def test_sample_endpoint_formats_exist(self):
        """Verify some expected endpoint types exist in the file."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()

        # Check for some common endpoint patterns mentioned in the task
        expected_patterns = [
            "legacy-",
            "_endpoint=",
            ".internal:"
        ]

        for pattern in expected_patterns:
            assert pattern in content, (
                f"File {self.ENDPOINTS_FILE} does not contain expected pattern '{pattern}'. "
                "The file format may not match the expected endpoint configuration format."
            )
