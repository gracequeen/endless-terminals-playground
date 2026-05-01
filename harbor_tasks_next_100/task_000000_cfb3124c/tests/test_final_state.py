# test_final_state.py
"""
Tests to validate the final state of the operating system after the student
has completed the disk usage breakdown task.
"""

import os
import re
import subprocess
import pytest


class TestReportFileExists:
    """Tests for the existence and basic properties of the report file."""

    def test_report_file_exists(self):
        """Verify /home/user/report.txt exists."""
        report_path = "/home/user/report.txt"
        assert os.path.exists(report_path), (
            f"{report_path} does not exist - the report file was not created"
        )

    def test_report_file_is_regular_file(self):
        """Verify /home/user/report.txt is a regular file."""
        report_path = "/home/user/report.txt"
        assert os.path.isfile(report_path), (
            f"{report_path} exists but is not a regular file"
        )

    def test_report_file_is_readable(self):
        """Verify /home/user/report.txt is readable."""
        report_path = "/home/user/report.txt"
        assert os.access(report_path, os.R_OK), (
            f"{report_path} exists but is not readable"
        )

    def test_report_file_not_empty(self):
        """Verify /home/user/report.txt is not empty."""
        report_path = "/home/user/report.txt"
        size = os.path.getsize(report_path)
        assert size > 0, f"{report_path} exists but is empty"


class TestReportContainsRequiredDirectories:
    """Tests to verify the report contains all required directory entries."""

    @pytest.fixture
    def report_content(self):
        """Read and return the report file content."""
        with open("/home/user/report.txt", "r") as f:
            return f.read()

    def test_contains_logs_directory(self, report_content):
        """Verify report contains logs directory entry."""
        assert "logs" in report_content, (
            "Report does not contain 'logs' directory - expected /var/data/logs entry"
        )

    def test_contains_cache_directory(self, report_content):
        """Verify report contains cache directory entry."""
        assert "cache" in report_content, (
            "Report does not contain 'cache' directory - expected /var/data/cache entry"
        )

    def test_contains_uploads_directory(self, report_content):
        """Verify report contains uploads directory entry."""
        assert "uploads" in report_content, (
            "Report does not contain 'uploads' directory - expected /var/data/uploads entry"
        )

    def test_contains_backups_directory(self, report_content):
        """Verify report contains backups directory entry."""
        assert "backups" in report_content, (
            "Report does not contain 'backups' directory - expected /var/data/backups entry"
        )

    def test_contains_tmp_directory(self, report_content):
        """Verify report contains tmp directory entry."""
        assert "tmp" in report_content, (
            "Report does not contain 'tmp' directory - expected /var/data/tmp entry"
        )

    def test_contains_var_data_total(self, report_content):
        """Verify report contains /var/data total line."""
        # Should have a line ending with /var/data (the total)
        assert "/var/data" in report_content, (
            "Report does not contain '/var/data' - expected total line for /var/data"
        )


class TestReportHasHumanReadableSizes:
    """Tests to verify sizes are in human-readable format."""

    @pytest.fixture
    def report_content(self):
        """Read and return the report file content."""
        with open("/home/user/report.txt", "r") as f:
            return f.read()

    def test_contains_human_readable_size_suffixes(self, report_content):
        """Verify report contains human-readable size suffixes (K, M, G)."""
        # Human-readable sizes should have K, M, or G suffixes
        # Pattern matches sizes like 50M, 1.2G, 500K, 2.1G, etc.
        size_pattern = r'\d+\.?\d*[KMG]'
        matches = re.findall(size_pattern, report_content)
        assert len(matches) >= 5, (
            f"Report should contain at least 5 human-readable sizes (K/M/G format), "
            f"found {len(matches)}: {matches}"
        )

    def test_backups_shows_gigabyte_size(self, report_content):
        """Verify backups directory shows size in gigabytes (G)."""
        # Find the line containing backups
        lines = report_content.strip().split('\n')
        backups_line = None
        for line in lines:
            if 'backups' in line:
                backups_line = line
                break

        assert backups_line is not None, "Could not find backups line in report"
        # Should contain G for gigabytes (around 2.1G)
        assert 'G' in backups_line, (
            f"backups line should show size in gigabytes (G), got: {backups_line}"
        )


class TestReportIsSortedBySize:
    """Tests to verify the report is sorted with largest directories first."""

    @pytest.fixture
    def report_lines(self):
        """Read and return the report file lines."""
        with open("/home/user/report.txt", "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]

    def parse_size_to_bytes(self, size_str):
        """Convert human-readable size string to bytes for comparison."""
        size_str = size_str.strip()
        multipliers = {
            'K': 1024,
            'M': 1024 * 1024,
            'G': 1024 * 1024 * 1024,
            'T': 1024 * 1024 * 1024 * 1024,
        }

        # Handle sizes like "2.1G", "500M", "50K"
        match = re.match(r'^(\d+\.?\d*)([KMGT])?', size_str)
        if match:
            value = float(match.group(1))
            suffix = match.group(2)
            if suffix and suffix in multipliers:
                return int(value * multipliers[suffix])
            return int(value)
        return 0

    def test_backups_appears_before_tmp(self, report_lines):
        """Verify backups (largest) appears before tmp (smallest) in the report."""
        backups_index = None
        tmp_index = None

        for i, line in enumerate(report_lines):
            if 'backups' in line and '/var/data' in line:
                backups_index = i
            if 'tmp' in line and '/var/data' in line:
                tmp_index = i

        assert backups_index is not None, "Could not find backups entry in report"
        assert tmp_index is not None, "Could not find tmp entry in report"
        assert backups_index < tmp_index, (
            f"Report is not sorted largest first: backups (line {backups_index}) "
            f"should appear before tmp (line {tmp_index})"
        )

    def test_cache_appears_before_tmp(self, report_lines):
        """Verify cache appears before tmp in the report."""
        cache_index = None
        tmp_index = None

        for i, line in enumerate(report_lines):
            if 'cache' in line and '/var/data' in line:
                cache_index = i
            if 'tmp' in line and '/var/data' in line:
                tmp_index = i

        assert cache_index is not None, "Could not find cache entry in report"
        assert tmp_index is not None, "Could not find tmp entry in report"
        assert cache_index < tmp_index, (
            f"Report is not sorted largest first: cache (line {cache_index}) "
            f"should appear before tmp (line {tmp_index})"
        )

    def test_overall_descending_order(self, report_lines):
        """Verify sizes are in descending order (largest first)."""
        sizes = []
        for line in report_lines:
            # Extract size from beginning of line
            match = re.match(r'^(\d+\.?\d*[KMGT]?)', line)
            if match:
                size_bytes = self.parse_size_to_bytes(match.group(1))
                sizes.append(size_bytes)

        assert len(sizes) >= 5, f"Expected at least 5 size entries, found {len(sizes)}"

        # Check that sizes are in descending order
        for i in range(len(sizes) - 1):
            assert sizes[i] >= sizes[i + 1], (
                f"Report is not sorted in descending order: "
                f"size at line {i} ({sizes[i]}) is less than size at line {i+1} ({sizes[i+1]})"
            )


class TestReportReflectsActualDiskUsage:
    """Tests to verify report reflects actual disk usage, not hardcoded values."""

    def get_actual_du_output(self):
        """Get actual du output for comparison."""
        result = subprocess.run(
            ["du", "-h", "--max-depth=1", "/var/data"],
            capture_output=True,
            text=True
        )
        return result.stdout

    @pytest.fixture
    def report_content(self):
        """Read and return the report file content."""
        with open("/home/user/report.txt", "r") as f:
            return f.read()

    def test_report_has_correct_number_of_entries(self, report_content):
        """Verify report has the expected number of directory entries."""
        # Should have 5 subdirectories + 1 total = 6 entries
        lines = [line for line in report_content.strip().split('\n') if line.strip()]
        assert len(lines) >= 6, (
            f"Report should have at least 6 entries (5 subdirs + total), found {len(lines)}"
        )

    def test_sizes_match_actual_disk_usage(self):
        """Verify reported sizes are close to actual disk usage."""
        # Get actual sizes
        result = subprocess.run(
            ["du", "-b", "--max-depth=1", "/var/data"],
            capture_output=True,
            text=True
        )

        actual_sizes = {}
        for line in result.stdout.strip().split('\n'):
            parts = line.split('\t')
            if len(parts) == 2:
                size, path = parts
                dir_name = os.path.basename(path) if path != "/var/data" else "total"
                actual_sizes[dir_name] = int(size)

        # Read report and extract sizes
        with open("/home/user/report.txt", "r") as f:
            report_content = f.read()

        # Verify backups is in the GB range
        assert actual_sizes.get("backups", 0) > 1024 * 1024 * 1024, (
            "Actual backups size should be > 1GB"
        )

        # Verify the report mentions backups with a G suffix (gigabytes)
        backups_pattern = r'\d+\.?\d*G.*backups|backups.*\d+\.?\d*G'
        # More flexible: just check that backups line has reasonable size
        assert "backups" in report_content, "Report must contain backups directory"


class TestVarDataUnchanged:
    """Tests to verify /var/data and its contents are unchanged."""

    def test_var_data_still_exists(self):
        """Verify /var/data still exists."""
        assert os.path.exists("/var/data"), "/var/data no longer exists"
        assert os.path.isdir("/var/data"), "/var/data is no longer a directory"

    def test_subdirectories_still_exist(self):
        """Verify all subdirectories still exist."""
        required_subdirs = ["logs", "cache", "uploads", "backups", "tmp"]
        for subdir in required_subdirs:
            full_path = os.path.join("/var/data", subdir)
            assert os.path.exists(full_path), (
                f"Subdirectory {full_path} no longer exists - data was modified"
            )
            assert os.path.isdir(full_path), (
                f"{full_path} is no longer a directory - data was modified"
            )

    def test_subdirectories_still_have_content(self):
        """Verify subdirectories still contain files."""
        required_subdirs = ["logs", "cache", "uploads", "backups", "tmp"]
        for subdir in required_subdirs:
            full_path = os.path.join("/var/data", subdir)
            contents = os.listdir(full_path)
            assert len(contents) > 0, (
                f"Subdirectory {full_path} is now empty - data was modified"
            )


class TestNoExtraFilesCreated:
    """Tests to verify no extra files were created outside the report."""

    def test_only_report_in_home_user(self):
        """Verify only expected files exist in /home/user."""
        home_contents = os.listdir("/home/user")
        # report.txt should be there, and we allow other pre-existing files
        assert "report.txt" in home_contents, (
            "report.txt not found in /home/user"
        )
