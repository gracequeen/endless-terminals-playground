# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the disk usage audit task.
"""

import os
import re
import pytest


class TestOutputFileExists:
    """Tests for the existence and basic properties of the output file."""

    def test_top5_file_exists(self):
        """Verify /home/user/audit/top5.txt exists."""
        assert os.path.exists("/home/user/audit/top5.txt"), (
            "/home/user/audit/top5.txt does not exist. "
            "The task requires creating this file with the top 5 largest files."
        )

    def test_top5_file_is_regular_file(self):
        """Verify /home/user/audit/top5.txt is a regular file."""
        assert os.path.isfile("/home/user/audit/top5.txt"), (
            "/home/user/audit/top5.txt exists but is not a regular file."
        )

    def test_top5_file_is_readable(self):
        """Verify /home/user/audit/top5.txt is readable."""
        assert os.access("/home/user/audit/top5.txt", os.R_OK), (
            "/home/user/audit/top5.txt is not readable."
        )

    def test_top5_file_is_not_empty(self):
        """Verify /home/user/audit/top5.txt is not empty."""
        size = os.path.getsize("/home/user/audit/top5.txt")
        assert size > 0, "/home/user/audit/top5.txt is empty."


class TestOutputFileContent:
    """Tests for the content of the output file."""

    EXPECTED_FILES_ORDERED = [
        "/var/data/archives/backup_2024_q1.tar.gz",
        "/var/data/logs/access_full.log",
        "/var/data/dumps/postgres_main.sql",
        "/var/data/media/training_video.mp4",
        "/var/data/exports/customer_data.csv",
    ]

    @pytest.fixture
    def file_lines(self):
        """Read and return non-empty lines from the output file."""
        with open("/home/user/audit/top5.txt", "r") as f:
            content = f.read()
        # Split into lines and filter out empty lines
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
        return lines

    def test_exactly_five_lines(self, file_lines):
        """Verify the file contains exactly 5 lines."""
        assert len(file_lines) == 5, (
            f"Expected exactly 5 lines in top5.txt, but found {len(file_lines)} lines. "
            f"Lines found: {file_lines}"
        )

    def test_all_expected_files_present(self, file_lines):
        """Verify all 5 expected files are mentioned in the output."""
        content = "\n".join(file_lines)
        missing_files = []
        for expected_file in self.EXPECTED_FILES_ORDERED:
            if expected_file not in content:
                missing_files.append(expected_file)

        assert not missing_files, (
            f"The following expected files are missing from top5.txt: {missing_files}. "
            f"Content found:\n{content}"
        )

    def test_files_in_correct_order(self, file_lines):
        """Verify files are listed in descending size order (largest first)."""
        # Find which expected file appears in each line
        found_order = []
        for line in file_lines:
            for expected_file in self.EXPECTED_FILES_ORDERED:
                if expected_file in line:
                    found_order.append(expected_file)
                    break

        assert found_order == self.EXPECTED_FILES_ORDERED, (
            f"Files are not in the correct order (largest first). "
            f"Expected order: {self.EXPECTED_FILES_ORDERED}. "
            f"Found order: {found_order}"
        )

    def test_human_readable_sizes(self, file_lines):
        """Verify sizes are in human-readable format (not raw bytes)."""
        # Human-readable sizes should contain K, M, G, or similar suffixes
        # Common patterns: 489M, 256M, 128M, 100M, 50M or 489MB, 256MB, etc.
        # Also accept formats like 489 M, 489Mi, 489MiB
        human_readable_pattern = re.compile(r'\d+\.?\d*\s*[KMGT]i?B?', re.IGNORECASE)

        # Also check that raw byte counts are NOT present (the exact expected sizes)
        raw_byte_sizes = ["512000000", "268435456", "134217728", "104857600", "52428800"]

        for line in file_lines:
            # Check that line doesn't contain raw byte values
            for raw_size in raw_byte_sizes:
                assert raw_size not in line, (
                    f"Line appears to contain raw byte size ({raw_size}) instead of "
                    f"human-readable format: {line}"
                )

            # Check that line contains a human-readable size indicator
            assert human_readable_pattern.search(line), (
                f"Line does not appear to contain a human-readable size "
                f"(expected K, M, G suffix): {line}"
            )

    def test_each_line_has_size_and_path(self, file_lines):
        """Verify each line contains both a size and a file path."""
        for i, line in enumerate(file_lines):
            # Check for a path (should start with /var/data)
            assert "/var/data" in line, (
                f"Line {i+1} does not contain a path under /var/data: {line}"
            )

            # Check for some numeric content (the size)
            assert re.search(r'\d+', line), (
                f"Line {i+1} does not contain any numeric size value: {line}"
            )


class TestVarDataUnchanged:
    """Tests to verify /var/data contents remain unchanged."""

    EXPECTED_FILES = {
        "/var/data/archives/backup_2024_q1.tar.gz": 512000000,
        "/var/data/logs/access_full.log": 268435456,
        "/var/data/dumps/postgres_main.sql": 134217728,
        "/var/data/media/training_video.mp4": 104857600,
        "/var/data/exports/customer_data.csv": 52428800,
    }

    @pytest.mark.parametrize("filepath,expected_size", EXPECTED_FILES.items())
    def test_original_files_still_exist(self, filepath, expected_size):
        """Verify original files under /var/data still exist."""
        assert os.path.exists(filepath), (
            f"Original file was deleted or moved: {filepath}"
        )

    @pytest.mark.parametrize("filepath,expected_size", EXPECTED_FILES.items())
    def test_original_files_unchanged_size(self, filepath, expected_size):
        """Verify original files under /var/data have unchanged sizes."""
        actual_size = os.path.getsize(filepath)
        assert actual_size == expected_size, (
            f"File {filepath} was modified. "
            f"Expected size: {expected_size} bytes, Actual: {actual_size} bytes"
        )

    def test_var_data_directory_exists(self):
        """Verify /var/data directory still exists."""
        assert os.path.isdir("/var/data"), "/var/data directory no longer exists"


class TestReportAccuracy:
    """Tests to verify the report reflects actual filesystem state."""

    def test_reported_sizes_match_filesystem(self):
        """Verify reported sizes approximately match actual file sizes."""
        if not os.path.exists("/home/user/audit/top5.txt"):
            pytest.skip("Output file does not exist")

        with open("/home/user/audit/top5.txt", "r") as f:
            content = f.read()

        # Map of expected files to their actual sizes in bytes
        expected_files = {
            "/var/data/archives/backup_2024_q1.tar.gz": 512000000,
            "/var/data/logs/access_full.log": 268435456,
            "/var/data/dumps/postgres_main.sql": 134217728,
            "/var/data/media/training_video.mp4": 104857600,
            "/var/data/exports/customer_data.csv": 52428800,
        }

        # For each expected file, verify it appears in the output
        # and that the size mentioned is reasonable
        for filepath, expected_bytes in expected_files.items():
            assert filepath in content, (
                f"File {filepath} (size: {expected_bytes} bytes) "
                f"should appear in the report but was not found."
            )

            # Get actual size from filesystem to ensure report is based on real data
            actual_size = os.path.getsize(filepath)
            assert actual_size == expected_bytes, (
                f"Filesystem shows {filepath} has {actual_size} bytes, "
                f"but expected {expected_bytes} bytes. "
                f"This suggests the test environment may have been modified."
            )
