# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the disk inventory processing task.
"""

import os
import pytest


class TestReportsDirectoryExists:
    """Test that the reports directory was created."""

    def test_reports_directory_exists(self):
        """Verify that /home/user/reports/ directory exists."""
        reports_path = "/home/user/reports"
        assert os.path.isdir(reports_path), (
            f"Reports directory {reports_path} does not exist. "
            "The student should have created this directory."
        )

    def test_reports_directory_is_readable(self):
        """Verify that /home/user/reports/ is readable."""
        reports_path = "/home/user/reports"
        assert os.access(reports_path, os.R_OK), (
            f"Reports directory {reports_path} is not readable."
        )


class TestLargeFilesReport:
    """Test the large_files.txt report."""

    REPORT_PATH = "/home/user/reports/large_files.txt"

    EXPECTED_CONTENT = """100MB /var/data/archives/2023_archive.tar.gz
50MB /var/data/backups/full_backup.tar.gz
30MB /var/data/archives/2022_archive.tar.gz
20MB /var/data/cache/session_data.db
15MB /var/data/logs/app.log
15MB /var/data/uploads/presentation.pptx
10MB /var/data/backups/incremental.tar.gz
"""

    def test_large_files_report_exists(self):
        """Verify that /home/user/reports/large_files.txt exists."""
        assert os.path.isfile(self.REPORT_PATH), (
            f"Large files report {self.REPORT_PATH} does not exist. "
            "The student should have created this report."
        )

    def test_large_files_report_is_readable(self):
        """Verify that large_files.txt is readable."""
        assert os.access(self.REPORT_PATH, os.R_OK), (
            f"Large files report {self.REPORT_PATH} is not readable."
        )

    def test_large_files_report_not_empty(self):
        """Verify that large_files.txt is not empty."""
        file_size = os.path.getsize(self.REPORT_PATH)
        assert file_size > 0, (
            f"Large files report {self.REPORT_PATH} is empty."
        )

    def test_large_files_report_content(self):
        """Verify that large_files.txt contains exactly the expected content."""
        with open(self.REPORT_PATH, 'r') as f:
            actual_content = f.read()

        expected_lines = [line for line in self.EXPECTED_CONTENT.strip().split('\n') if line]
        actual_lines = [line for line in actual_content.strip().split('\n') if line]

        assert len(actual_lines) == len(expected_lines), (
            f"Large files report has {len(actual_lines)} lines, expected {len(expected_lines)}. "
            f"Expected lines:\n{self.EXPECTED_CONTENT.strip()}\n\n"
            f"Actual lines:\n{actual_content.strip()}"
        )

        for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines)):
            assert actual.strip() == expected.strip(), (
                f"Line {i+1} mismatch in large_files.txt.\n"
                f"Expected: '{expected}'\n"
                f"Actual:   '{actual}'"
            )

    def test_large_files_report_exact_content(self):
        """Verify exact content match for large_files.txt."""
        with open(self.REPORT_PATH, 'r') as f:
            actual_content = f.read()

        # Normalize line endings and trailing whitespace
        expected_normalized = self.EXPECTED_CONTENT.strip()
        actual_normalized = actual_content.strip()

        assert actual_normalized == expected_normalized, (
            f"Large files report content does not match exactly.\n"
            f"Expected:\n{expected_normalized}\n\n"
            f"Actual:\n{actual_normalized}"
        )

    def test_large_files_sorted_by_size_descending(self):
        """Verify that large_files.txt is sorted by size descending."""
        with open(self.REPORT_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        sizes = []
        for line in lines:
            parts = line.split()
            if parts:
                size_str = parts[0].replace('MB', '')
                sizes.append(int(size_str))

        for i in range(len(sizes) - 1):
            assert sizes[i] >= sizes[i+1], (
                f"Large files report is not sorted by size descending. "
                f"Size {sizes[i]}MB at line {i+1} should be >= {sizes[i+1]}MB at line {i+2}."
            )


class TestExtensionSummaryReport:
    """Test the extension_summary.csv report."""

    REPORT_PATH = "/home/user/reports/extension_summary.csv"

    EXPECTED_CONTENT = """extension,total_bytes
gz,198970880
db,20971520
log,20971520
pptx,15728640
xlsx,7340032
NO_EXTENSION,9437184
pdf,3145728
bak,2097152
jpg,1835008
txt,524288
"""

    def test_extension_summary_report_exists(self):
        """Verify that /home/user/reports/extension_summary.csv exists."""
        assert os.path.isfile(self.REPORT_PATH), (
            f"Extension summary report {self.REPORT_PATH} does not exist. "
            "The student should have created this report."
        )

    def test_extension_summary_report_is_readable(self):
        """Verify that extension_summary.csv is readable."""
        assert os.access(self.REPORT_PATH, os.R_OK), (
            f"Extension summary report {self.REPORT_PATH} is not readable."
        )

    def test_extension_summary_report_not_empty(self):
        """Verify that extension_summary.csv is not empty."""
        file_size = os.path.getsize(self.REPORT_PATH)
        assert file_size > 0, (
            f"Extension summary report {self.REPORT_PATH} is empty."
        )

    def test_extension_summary_has_header(self):
        """Verify that extension_summary.csv has the correct header."""
        with open(self.REPORT_PATH, 'r') as f:
            first_line = f.readline().strip()

        assert first_line == "extension,total_bytes", (
            f"Extension summary CSV header is incorrect.\n"
            f"Expected: 'extension,total_bytes'\n"
            f"Actual:   '{first_line}'"
        )

    def test_extension_summary_report_content(self):
        """Verify that extension_summary.csv contains exactly the expected content."""
        with open(self.REPORT_PATH, 'r') as f:
            actual_content = f.read()

        expected_lines = [line for line in self.EXPECTED_CONTENT.strip().split('\n') if line]
        actual_lines = [line for line in actual_content.strip().split('\n') if line]

        assert len(actual_lines) == len(expected_lines), (
            f"Extension summary report has {len(actual_lines)} lines, expected {len(expected_lines)}. "
            f"Expected lines:\n{self.EXPECTED_CONTENT.strip()}\n\n"
            f"Actual lines:\n{actual_content.strip()}"
        )

        for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines)):
            assert actual.strip() == expected.strip(), (
                f"Line {i+1} mismatch in extension_summary.csv.\n"
                f"Expected: '{expected}'\n"
                f"Actual:   '{actual}'"
            )

    def test_extension_summary_exact_content(self):
        """Verify exact content match for extension_summary.csv."""
        with open(self.REPORT_PATH, 'r') as f:
            actual_content = f.read()

        expected_normalized = self.EXPECTED_CONTENT.strip()
        actual_normalized = actual_content.strip()

        assert actual_normalized == expected_normalized, (
            f"Extension summary report content does not match exactly.\n"
            f"Expected:\n{expected_normalized}\n\n"
            f"Actual:\n{actual_normalized}"
        )

    def test_extension_summary_sorted_by_bytes_descending(self):
        """Verify that extension_summary.csv is sorted by total_bytes descending."""
        with open(self.REPORT_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        # Skip header
        data_lines = lines[1:]
        bytes_values = []
        for line in data_lines:
            parts = line.split(',')
            if len(parts) == 2:
                bytes_values.append(int(parts[1]))

        for i in range(len(bytes_values) - 1):
            assert bytes_values[i] >= bytes_values[i+1], (
                f"Extension summary is not sorted by total_bytes descending. "
                f"Value {bytes_values[i]} at line {i+2} should be >= {bytes_values[i+1]} at line {i+3}."
            )


class TestDirectoryRollupReport:
    """Test the directory_rollup.txt report."""

    REPORT_PATH = "/home/user/reports/directory_rollup.txt"

    EXPECTED_CONTENT = """archives 144703488 51.4%
backups 65011712 23.1%
uploads 27787264 9.9%
cache 22806528 8.1%
logs 20971520 7.5%
"""

    def test_directory_rollup_report_exists(self):
        """Verify that /home/user/reports/directory_rollup.txt exists."""
        assert os.path.isfile(self.REPORT_PATH), (
            f"Directory rollup report {self.REPORT_PATH} does not exist. "
            "The student should have created this report."
        )

    def test_directory_rollup_report_is_readable(self):
        """Verify that directory_rollup.txt is readable."""
        assert os.access(self.REPORT_PATH, os.R_OK), (
            f"Directory rollup report {self.REPORT_PATH} is not readable."
        )

    def test_directory_rollup_report_not_empty(self):
        """Verify that directory_rollup.txt is not empty."""
        file_size = os.path.getsize(self.REPORT_PATH)
        assert file_size > 0, (
            f"Directory rollup report {self.REPORT_PATH} is empty."
        )

    def test_directory_rollup_report_line_count(self):
        """Verify that directory_rollup.txt has exactly 5 lines (one per subdirectory)."""
        with open(self.REPORT_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) == 5, (
            f"Directory rollup report has {len(lines)} lines, expected 5. "
            f"There should be one line for each immediate subdirectory of /var/data."
        )

    def test_directory_rollup_report_content(self):
        """Verify that directory_rollup.txt contains exactly the expected content."""
        with open(self.REPORT_PATH, 'r') as f:
            actual_content = f.read()

        expected_lines = [line for line in self.EXPECTED_CONTENT.strip().split('\n') if line]
        actual_lines = [line for line in actual_content.strip().split('\n') if line]

        assert len(actual_lines) == len(expected_lines), (
            f"Directory rollup report has {len(actual_lines)} lines, expected {len(expected_lines)}. "
            f"Expected lines:\n{self.EXPECTED_CONTENT.strip()}\n\n"
            f"Actual lines:\n{actual_content.strip()}"
        )

        for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines)):
            assert actual.strip() == expected.strip(), (
                f"Line {i+1} mismatch in directory_rollup.txt.\n"
                f"Expected: '{expected}'\n"
                f"Actual:   '{actual}'"
            )

    def test_directory_rollup_exact_content(self):
        """Verify exact content match for directory_rollup.txt."""
        with open(self.REPORT_PATH, 'r') as f:
            actual_content = f.read()

        expected_normalized = self.EXPECTED_CONTENT.strip()
        actual_normalized = actual_content.strip()

        assert actual_normalized == expected_normalized, (
            f"Directory rollup report content does not match exactly.\n"
            f"Expected:\n{expected_normalized}\n\n"
            f"Actual:\n{actual_normalized}"
        )

    def test_directory_rollup_sorted_by_bytes_descending(self):
        """Verify that directory_rollup.txt is sorted by total_bytes descending."""
        with open(self.REPORT_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        bytes_values = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                bytes_values.append(int(parts[1]))

        for i in range(len(bytes_values) - 1):
            assert bytes_values[i] >= bytes_values[i+1], (
                f"Directory rollup is not sorted by total_bytes descending. "
                f"Value {bytes_values[i]} at line {i+1} should be >= {bytes_values[i+1]} at line {i+2}."
            )

    def test_directory_rollup_has_all_directories(self):
        """Verify that all expected directories are present in the rollup."""
        with open(self.REPORT_PATH, 'r') as f:
            content = f.read()

        expected_dirs = ['archives', 'backups', 'uploads', 'cache', 'logs']
        for dir_name in expected_dirs:
            assert dir_name in content, (
                f"Directory '{dir_name}' not found in directory_rollup.txt. "
                "All immediate subdirectories of /var/data should be included."
            )

    def test_directory_rollup_percentages_format(self):
        """Verify that percentages are formatted correctly with one decimal place."""
        with open(self.REPORT_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for i, line in enumerate(lines):
            parts = line.split()
            assert len(parts) == 3, (
                f"Line {i+1} in directory_rollup.txt has {len(parts)} parts, expected 3. "
                f"Format should be '<dirname> <total_bytes> <percentage>%'"
            )
            percentage = parts[2]
            assert percentage.endswith('%'), (
                f"Line {i+1} percentage '{percentage}' does not end with '%'."
            )
            # Check it has one decimal place
            pct_value = percentage.rstrip('%')
            assert '.' in pct_value, (
                f"Line {i+1} percentage '{percentage}' should have one decimal place."
            )
            decimal_part = pct_value.split('.')[1]
            assert len(decimal_part) == 1, (
                f"Line {i+1} percentage '{percentage}' should have exactly one decimal place."
            )


class TestOriginalFileUnchanged:
    """Test that the original inventory file is unchanged."""

    def test_disk_inventory_still_exists(self):
        """Verify that /home/user/disk_inventory.txt still exists."""
        inventory_path = "/home/user/disk_inventory.txt"
        assert os.path.isfile(inventory_path), (
            f"Original disk inventory file {inventory_path} no longer exists. "
            "The student should not have deleted or moved this file."
        )

    def test_disk_inventory_still_readable(self):
        """Verify that disk_inventory.txt is still readable."""
        inventory_path = "/home/user/disk_inventory.txt"
        assert os.access(inventory_path, os.R_OK), (
            f"Original disk inventory file {inventory_path} is no longer readable."
        )
