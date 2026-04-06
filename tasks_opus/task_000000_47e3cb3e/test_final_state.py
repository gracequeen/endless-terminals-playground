# test_final_state.py
"""
Tests to validate the final state of the operating system after the student
has completed the disk I/O benchmark task.
"""

import pytest
import os
import re
from pathlib import Path


HOME_DIR = "/home/user"
ARTIFACT_STORAGE_DIR = "/home/user/artifact_storage"
BENCHMARK_FILE = "/home/user/artifact_storage/benchmark_test.dat"
BENCHMARK_LOG = "/home/user/artifact_storage/benchmark_results.log"
EXPECTED_FILE_SIZE = 104857600  # 100 MB in bytes


class TestDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_artifact_storage_directory_exists(self):
        """Verify that /home/user/artifact_storage directory exists."""
        assert os.path.exists(ARTIFACT_STORAGE_DIR), (
            f"Directory {ARTIFACT_STORAGE_DIR} does not exist. "
            "The task requires creating this directory."
        )
        assert os.path.isdir(ARTIFACT_STORAGE_DIR), (
            f"{ARTIFACT_STORAGE_DIR} exists but is not a directory. "
            "It should be a directory, not a file."
        )


class TestBenchmarkTestFile:
    """Test the benchmark test file (benchmark_test.dat)."""

    def test_benchmark_file_exists(self):
        """Verify that the benchmark test file exists."""
        assert os.path.exists(BENCHMARK_FILE), (
            f"Benchmark file {BENCHMARK_FILE} does not exist. "
            "The dd command should create this file during the benchmark."
        )

    def test_benchmark_file_is_regular_file(self):
        """Verify that the benchmark test file is a regular file."""
        assert os.path.isfile(BENCHMARK_FILE), (
            f"{BENCHMARK_FILE} exists but is not a regular file. "
            "It should be a regular file created by dd."
        )

    def test_benchmark_file_size_is_100mb(self):
        """Verify that the benchmark test file is exactly 100 MB (104857600 bytes)."""
        if not os.path.exists(BENCHMARK_FILE):
            pytest.fail(f"Benchmark file {BENCHMARK_FILE} does not exist.")

        actual_size = os.path.getsize(BENCHMARK_FILE)
        assert actual_size == EXPECTED_FILE_SIZE, (
            f"Benchmark file size is {actual_size} bytes, but expected {EXPECTED_FILE_SIZE} bytes (100 MB). "
            f"The dd command should use bs=1M count=100 to create a 100 MB file."
        )


class TestBenchmarkLogFile:
    """Test the benchmark results log file (benchmark_results.log)."""

    def test_log_file_exists(self):
        """Verify that the benchmark results log file exists."""
        assert os.path.exists(BENCHMARK_LOG), (
            f"Log file {BENCHMARK_LOG} does not exist. "
            "The task requires creating this log file with benchmark results."
        )

    def test_log_file_is_regular_file(self):
        """Verify that the log file is a regular file."""
        assert os.path.isfile(BENCHMARK_LOG), (
            f"{BENCHMARK_LOG} exists but is not a regular file."
        )

    def test_log_file_has_exactly_six_lines(self):
        """Verify that the log file contains exactly 6 lines."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = f.readlines()

        # Remove trailing empty lines if any, but count actual content lines
        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) == 6, (
            f"Log file has {len(non_empty_lines)} non-empty lines, but expected exactly 6 lines. "
            f"Lines found: {non_empty_lines}"
        )

    def test_log_line_1_benchmark_type(self):
        """Verify that line 1 is 'BENCHMARK_TYPE: disk_write'."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 1:
            pytest.fail("Log file is empty or has no content on line 1.")

        expected = "BENCHMARK_TYPE: disk_write"
        assert lines[0] == expected, (
            f"Line 1 is '{lines[0]}', but expected '{expected}'."
        )

    def test_log_line_2_file_size(self):
        """Verify that line 2 is 'FILE_SIZE_MB: 100'."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 2:
            pytest.fail("Log file does not have content on line 2.")

        expected = "FILE_SIZE_MB: 100"
        assert lines[1] == expected, (
            f"Line 2 is '{lines[1]}', but expected '{expected}'."
        )

    def test_log_line_3_block_size(self):
        """Verify that line 3 is 'BLOCK_SIZE: 1M'."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 3:
            pytest.fail("Log file does not have content on line 3.")

        expected = "BLOCK_SIZE: 1M"
        assert lines[2] == expected, (
            f"Line 3 is '{lines[2]}', but expected '{expected}'."
        )

    def test_log_line_4_block_count(self):
        """Verify that line 4 is 'BLOCK_COUNT: 100'."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 4:
            pytest.fail("Log file does not have content on line 4.")

        expected = "BLOCK_COUNT: 100"
        assert lines[3] == expected, (
            f"Line 4 is '{lines[3]}', but expected '{expected}'."
        )

    def test_log_line_5_throughput_format(self):
        """Verify that line 5 matches 'THROUGHPUT_MB_S: <numeric_value>'."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 5:
            pytest.fail("Log file does not have content on line 5.")

        # Pattern: THROUGHPUT_MB_S: followed by a numeric value (integer or decimal)
        pattern = r'^THROUGHPUT_MB_S: [0-9]+\.?[0-9]*$'
        assert re.match(pattern, lines[4]), (
            f"Line 5 is '{lines[4]}', but expected format 'THROUGHPUT_MB_S: <numeric_value>' "
            f"where <numeric_value> is a positive number (e.g., 'THROUGHPUT_MB_S: 150.5')."
        )

    def test_log_line_5_throughput_positive_value(self):
        """Verify that the throughput value is a positive number greater than 0."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 5:
            pytest.fail("Log file does not have content on line 5.")

        # Extract the numeric value
        match = re.match(r'^THROUGHPUT_MB_S: ([0-9]+\.?[0-9]*)$', lines[4])
        if not match:
            pytest.fail(f"Line 5 '{lines[4]}' does not match expected format.")

        throughput_value = float(match.group(1))
        assert throughput_value > 0, (
            f"Throughput value is {throughput_value}, but it should be a positive number greater than 0. "
            "The benchmark should have measured some write speed."
        )

    def test_log_line_6_status(self):
        """Verify that line 6 is 'STATUS: COMPLETED'."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 6:
            pytest.fail("Log file does not have content on line 6.")

        expected = "STATUS: COMPLETED"
        assert lines[5] == expected, (
            f"Line 6 is '{lines[5]}', but expected '{expected}'."
        )


class TestLogFileCompleteValidation:
    """Complete validation of the log file format."""

    def test_log_file_complete_format(self):
        """Verify the complete format of the log file with all 6 lines."""
        if not os.path.exists(BENCHMARK_LOG):
            pytest.fail(f"Log file {BENCHMARK_LOG} does not exist.")

        with open(BENCHMARK_LOG, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        errors = []

        if len(lines) != 6:
            errors.append(f"Expected 6 lines, found {len(lines)}")

        if len(lines) >= 1 and lines[0] != "BENCHMARK_TYPE: disk_write":
            errors.append(f"Line 1 mismatch: got '{lines[0]}'")

        if len(lines) >= 2 and lines[1] != "FILE_SIZE_MB: 100":
            errors.append(f"Line 2 mismatch: got '{lines[1]}'")

        if len(lines) >= 3 and lines[2] != "BLOCK_SIZE: 1M":
            errors.append(f"Line 3 mismatch: got '{lines[2]}'")

        if len(lines) >= 4 and lines[3] != "BLOCK_COUNT: 100":
            errors.append(f"Line 4 mismatch: got '{lines[3]}'")

        if len(lines) >= 5:
            if not re.match(r'^THROUGHPUT_MB_S: [0-9]+\.?[0-9]*$', lines[4]):
                errors.append(f"Line 5 format mismatch: got '{lines[4]}'")

        if len(lines) >= 6 and lines[5] != "STATUS: COMPLETED":
            errors.append(f"Line 6 mismatch: got '{lines[5]}'")

        assert not errors, (
            "Log file format validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )