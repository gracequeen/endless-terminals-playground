# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the config registry migration task (legacy- to svc- prefix change).
"""

import os
import pytest
import subprocess
import re


class TestFinalState:
    """Validate the final state after the migration task is completed."""

    ENDPOINTS_FILE = "/home/user/services/endpoints.conf"
    SERVICES_DIR = "/home/user/services"

    def test_endpoints_file_still_exists(self):
        """Verify /home/user/services/endpoints.conf still exists after migration."""
        assert os.path.isfile(self.ENDPOINTS_FILE), (
            f"File {self.ENDPOINTS_FILE} does not exist. "
            "The file may have been accidentally deleted during the migration."
        )

    def test_no_legacy_prefix_remaining(self):
        """Verify all 'legacy-' prefixes have been replaced (count should be 0)."""
        result = subprocess.run(
            ["grep", "-c", "legacy-", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        # grep returns exit code 1 if no matches found, which is what we want
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 0, (
            f"File {self.ENDPOINTS_FILE} still contains {count} occurrences of 'legacy-'. "
            "All 'legacy-' prefixes should be replaced with 'svc-'."
        )

    def test_svc_prefix_count_is_40(self):
        """Verify there are exactly 40 occurrences of 'svc-' prefix."""
        result = subprocess.run(
            ["grep", "-c", "svc-", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 40, (
            f"File {self.ENDPOINTS_FILE} contains {count} occurrences of 'svc-', "
            "expected exactly 40 occurrences after migration."
        )

    def test_40_endpoint_definitions_with_svc_prefix(self):
        """Verify there are 40 properly formatted endpoint definitions with svc- prefix."""
        result = subprocess.run(
            ["grep", "-cE", r"^[a-z_]+_endpoint=svc-", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 40, (
            f"File {self.ENDPOINTS_FILE} contains {count} endpoint definitions with 'svc-' prefix, "
            "expected exactly 40 endpoint definitions in format 'name_endpoint=svc-...'."
        )

    def test_file_line_count_preserved(self):
        """Verify the file still has approximately 60 lines (structure preserved)."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            lines = f.readlines()
        line_count = len(lines)
        assert 55 <= line_count <= 65, (
            f"File {self.ENDPOINTS_FILE} has {line_count} lines, expected approximately 60 lines. "
            "The file structure may have been altered during migration."
        )

    def test_file_not_empty_or_truncated(self):
        """Verify the file has substantial content (not emptied or truncated)."""
        file_size = os.path.getsize(self.ENDPOINTS_FILE)
        # With 40 endpoint lines plus comments, file should be at least 1KB
        assert file_size > 1000, (
            f"File {self.ENDPOINTS_FILE} is only {file_size} bytes. "
            "The file appears to have been truncated or emptied."
        )

    def test_comment_lines_preserved(self):
        """Verify comment lines are still present in the file."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()
        comment_lines = [line for line in content.splitlines() if line.strip().startswith('#')]
        assert len(comment_lines) > 0, (
            f"File {self.ENDPOINTS_FILE} no longer contains comment lines. "
            "Comment lines should be preserved during migration."
        )

    def test_internal_domain_preserved(self):
        """Verify .internal domain is still present in endpoint definitions."""
        result = subprocess.run(
            ["grep", "-c", r"\.internal:", self.ENDPOINTS_FILE],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 40, (
            f"File {self.ENDPOINTS_FILE} contains {count} occurrences of '.internal:' domain, "
            "expected at least 40. The domain names may have been corrupted during migration."
        )

    def test_port_numbers_preserved(self):
        """Verify port numbers are still present in endpoint definitions."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()

        # Check for pattern like :8080, :5432, etc. at end of lines
        port_pattern = re.compile(r':\d{2,5}$', re.MULTILINE)
        matches = port_pattern.findall(content)
        assert len(matches) >= 40, (
            f"File {self.ENDPOINTS_FILE} contains {len(matches)} lines with port numbers, "
            "expected at least 40. Port numbers may have been corrupted during migration."
        )

    def test_service_names_properly_migrated(self):
        """Verify service names follow the new svc- naming pattern correctly."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()

        # Check that svc- is followed by valid service name (alphanumeric and hyphens)
        # Pattern: svc-<servicename>.internal:<port>
        svc_pattern = re.compile(r'svc-[a-z0-9-]+\.internal:\d+')
        matches = svc_pattern.findall(content)
        assert len(matches) >= 40, (
            f"File {self.ENDPOINTS_FILE} contains {len(matches)} properly formatted 'svc-' endpoints, "
            "expected at least 40. Service names may have been mangled during migration."
        )

    def test_endpoint_format_intact(self):
        """Verify the endpoint definition format is intact (key=value structure)."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()

        # Pattern: word_endpoint=svc-something.internal:port
        endpoint_pattern = re.compile(r'^[a-z_]+_endpoint=svc-[a-z0-9-]+\.internal:\d+$', re.MULTILINE)
        matches = endpoint_pattern.findall(content)
        assert len(matches) == 40, (
            f"File {self.ENDPOINTS_FILE} contains {len(matches)} properly formatted endpoint definitions, "
            "expected exactly 40. The endpoint format may have been corrupted."
        )

    def test_no_double_prefix(self):
        """Verify no accidental double prefixes like 'svc-svc-' or 'svc-legacy-'."""
        with open(self.ENDPOINTS_FILE, 'r') as f:
            content = f.read()

        assert 'svc-svc-' not in content, (
            f"File {self.ENDPOINTS_FILE} contains 'svc-svc-' which indicates "
            "the migration was run multiple times or incorrectly."
        )
        assert 'svc-legacy-' not in content, (
            f"File {self.ENDPOINTS_FILE} contains 'svc-legacy-' which indicates "
            "an incorrect or partial migration."
        )
        assert 'legacy-svc-' not in content, (
            f"File {self.ENDPOINTS_FILE} contains 'legacy-svc-' which indicates "
            "an incorrect migration."
        )

    def test_file_readable_after_migration(self):
        """Verify the file is still readable after migration."""
        try:
            with open(self.ENDPOINTS_FILE, 'r') as f:
                content = f.read()
            assert len(content) > 0, "File is empty after migration."
        except Exception as e:
            pytest.fail(f"Failed to read {self.ENDPOINTS_FILE} after migration: {e}")
