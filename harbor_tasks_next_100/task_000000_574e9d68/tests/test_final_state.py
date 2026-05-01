# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of extracting ip and status columns from access.log.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Tests for validating the final state after the task is performed."""

    LOG_DIR = "/home/user/logs"
    ACCESS_LOG = "/home/user/logs/access.log"
    OUTPUT_FILE = "/home/user/logs/ip_status.tsv"

    def test_output_file_exists(self):
        """Verify that /home/user/logs/ip_status.tsv exists."""
        assert os.path.isfile(self.OUTPUT_FILE), (
            f"File {self.OUTPUT_FILE} does not exist. "
            "The output file must be created with the extracted ip and status columns."
        )

    def test_output_file_has_847_lines(self):
        """Verify that ip_status.tsv contains exactly 847 lines."""
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(self.OUTPUT_FILE, "r"),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip())
        assert line_count == 847, (
            f"File {self.OUTPUT_FILE} has {line_count} lines, expected 847. "
            "The output file must have the same number of lines as the input file."
        )

    def test_output_file_has_exactly_2_tab_separated_fields_per_line(self):
        """Verify that each line in ip_status.tsv has exactly 2 tab-separated fields."""
        result = subprocess.run(
            ["awk", "-F\t", "NF != 2 { exit 1 }"],
            stdin=open(self.OUTPUT_FILE, "r"),
            capture_output=True
        )
        assert result.returncode == 0, (
            f"File {self.OUTPUT_FILE} does not have exactly 2 tab-separated fields on every line. "
            "Each line must have exactly 2 fields: ip and status, separated by a single tab."
        )

    def test_first_line_ip_matches_input(self):
        """Verify that the ip field in line 1 of output matches field 2 of input."""
        with open(self.ACCESS_LOG, "r") as f:
            input_first_line = f.readline().rstrip("\n")

        with open(self.OUTPUT_FILE, "r") as f:
            output_first_line = f.readline().rstrip("\n")

        input_fields = input_first_line.split("\t")
        output_fields = output_first_line.split("\t")

        expected_ip = input_fields[1]  # Column 2 (0-indexed: 1)
        actual_ip = output_fields[0]   # First field in output

        assert actual_ip == expected_ip, (
            f"IP field mismatch on line 1. "
            f"Expected '{expected_ip}' (from column 2 of input), got '{actual_ip}'."
        )

    def test_first_line_status_matches_input(self):
        """Verify that the status field in line 1 of output matches field 5 of input."""
        with open(self.ACCESS_LOG, "r") as f:
            input_first_line = f.readline().rstrip("\n")

        with open(self.OUTPUT_FILE, "r") as f:
            output_first_line = f.readline().rstrip("\n")

        input_fields = input_first_line.split("\t")
        output_fields = output_first_line.split("\t")

        expected_status = input_fields[4]  # Column 5 (0-indexed: 4)
        actual_status = output_fields[1]   # Second field in output

        assert actual_status == expected_status, (
            f"Status field mismatch on line 1. "
            f"Expected '{expected_status}' (from column 5 of input), got '{actual_status}'."
        )

    def test_all_lines_ip_and_status_match_input(self):
        """Verify that all lines have correct ip and status extracted from input."""
        with open(self.ACCESS_LOG, "r") as f:
            input_lines = f.readlines()

        with open(self.OUTPUT_FILE, "r") as f:
            output_lines = f.readlines()

        assert len(output_lines) == len(input_lines), (
            f"Line count mismatch: input has {len(input_lines)} lines, "
            f"output has {len(output_lines)} lines."
        )

        # Check a sample of lines (first, last, and some in the middle)
        sample_indices = [0, 1, 100, 400, 845, 846]

        for idx in sample_indices:
            if idx >= len(input_lines):
                continue

            input_line = input_lines[idx].rstrip("\n")
            output_line = output_lines[idx].rstrip("\n")

            input_fields = input_line.split("\t")
            output_fields = output_line.split("\t")

            expected_ip = input_fields[1]      # Column 2
            expected_status = input_fields[4]  # Column 5

            assert len(output_fields) == 2, (
                f"Line {idx + 1}: expected 2 fields, got {len(output_fields)}. "
                f"Output line: {output_line!r}"
            )

            actual_ip = output_fields[0]
            actual_status = output_fields[1]

            assert actual_ip == expected_ip, (
                f"Line {idx + 1}: IP mismatch. "
                f"Expected '{expected_ip}', got '{actual_ip}'."
            )

            assert actual_status == expected_status, (
                f"Line {idx + 1}: Status mismatch. "
                f"Expected '{expected_status}', got '{actual_status}'."
            )

    def test_access_log_unchanged(self):
        """Verify that the original access.log file is unchanged."""
        # Check it still exists
        assert os.path.isfile(self.ACCESS_LOG), (
            f"File {self.ACCESS_LOG} no longer exists. "
            "The original access log should not be modified or deleted."
        )

        # Check it still has 847 lines
        result = subprocess.run(
            ["wc", "-l"],
            stdin=open(self.ACCESS_LOG, "r"),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip())
        assert line_count == 847, (
            f"File {self.ACCESS_LOG} now has {line_count} lines, expected 847. "
            "The original access log should not be modified."
        )

        # Check it still has 6 columns
        result = subprocess.run(
            ["awk", "-F\t", "NF != 6 { exit 1 }"],
            stdin=open(self.ACCESS_LOG, "r"),
            capture_output=True
        )
        assert result.returncode == 0, (
            f"File {self.ACCESS_LOG} no longer has 6 tab-separated columns on every line. "
            "The original access log should not be modified."
        )

    def test_output_uses_tab_separator(self):
        """Verify that the output file uses tab as the field separator."""
        with open(self.OUTPUT_FILE, "r") as f:
            first_line = f.readline().rstrip("\n")

        # Check that there's exactly one tab in the line
        tab_count = first_line.count("\t")
        assert tab_count == 1, (
            f"First line of output has {tab_count} tab characters, expected 1. "
            f"Line content: {first_line!r}"
        )

    def test_no_extra_whitespace_in_output(self):
        """Verify that output fields don't have leading/trailing whitespace."""
        with open(self.OUTPUT_FILE, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip("\n")
                fields = line.split("\t")

                if len(fields) != 2:
                    continue  # Already caught by other tests

                for i, field in enumerate(fields):
                    stripped = field.strip()
                    assert field == stripped, (
                        f"Line {line_num}, field {i + 1} has extra whitespace. "
                        f"Original: {field!r}, Stripped: {stripped!r}"
                    )

                # Only check first few lines to keep test fast
                if line_num >= 10:
                    break
