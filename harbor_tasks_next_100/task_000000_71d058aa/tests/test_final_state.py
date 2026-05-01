# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of extracting rows with status_code 500 from api_responses.csv.
"""

import os
import subprocess
import hashlib
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    INPUT_FILE = "/home/user/api_responses.csv"
    OUTPUT_FILE = "/home/user/failures.csv"
    EXPECTED_HEADER = "request_id,status_code,response_time_ms,endpoint"
    EXPECTED_OUTPUT_LINES = 13  # 1 header + 12 data rows
    EXPECTED_500_ROWS = 12

    @pytest.fixture(scope="class")
    def input_file_hash(self):
        """Compute hash of input file to verify it's unchanged."""
        with open(self.INPUT_FILE, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def test_output_file_exists(self):
        """Verify the output file /home/user/failures.csv exists."""
        assert os.path.isfile(self.OUTPUT_FILE), (
            f"Output file {self.OUTPUT_FILE} does not exist. "
            "The task requires creating this file with filtered 500 status rows."
        )

    def test_output_file_line_count(self):
        """Verify failures.csv has exactly 13 lines (1 header + 12 data rows)."""
        with open(self.OUTPUT_FILE, 'r') as f:
            line_count = sum(1 for _ in f)
        assert line_count == self.EXPECTED_OUTPUT_LINES, (
            f"Expected {self.EXPECTED_OUTPUT_LINES} lines in {self.OUTPUT_FILE}, "
            f"but found {line_count}. Should be 1 header + 12 data rows with status 500."
        )

    def test_output_file_line_count_via_wc(self):
        """Anti-shortcut guard: wc -l must output 13."""
        result = subprocess.run(
            ['wc', '-l'],
            stdin=open(self.OUTPUT_FILE, 'r'),
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"wc -l command failed: {result.stderr}"
        count = int(result.stdout.strip())
        assert count == self.EXPECTED_OUTPUT_LINES, (
            f"wc -l reports {count} lines, expected {self.EXPECTED_OUTPUT_LINES}"
        )

    def test_output_file_header(self):
        """Verify the first line of failures.csv is the correct header."""
        with open(self.OUTPUT_FILE, 'r') as f:
            header = f.readline().strip()
        assert header == self.EXPECTED_HEADER, (
            f"Expected header '{self.EXPECTED_HEADER}', but found '{header}'. "
            "The header must be preserved exactly as in the original file."
        )

    def test_output_file_header_via_head(self):
        """Anti-shortcut guard: head -1 must output exact header."""
        result = subprocess.run(
            ['head', '-1', self.OUTPUT_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"head command failed: {result.stderr}"
        header = result.stdout.strip()
        assert header == self.EXPECTED_HEADER, (
            f"head -1 returned '{header}', expected '{self.EXPECTED_HEADER}'"
        )

    def test_all_data_rows_have_status_500(self):
        """Verify every data row in failures.csv has status_code == 500."""
        with open(self.OUTPUT_FILE, 'r') as f:
            # Skip header
            next(f)
            for line_num, line in enumerate(f, 2):
                fields = line.strip().split(',')
                assert len(fields) >= 2, (
                    f"Line {line_num} in {self.OUTPUT_FILE} has fewer than 2 fields: {line.strip()}"
                )
                assert fields[1] == "500", (
                    f"Line {line_num} in {self.OUTPUT_FILE} has status_code '{fields[1]}', "
                    f"expected '500'. All data rows must have status 500."
                )

    def test_no_non_500_rows_via_awk(self):
        """Anti-shortcut guard: awk check for non-500 rows must return 0."""
        result = subprocess.run(
            ['awk', '-F,', 'NR>1 && $2!=500', self.OUTPUT_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"awk command failed: {result.stderr}"
        # Count non-empty lines in output
        non_500_lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(non_500_lines) == 0, (
            f"Found {len(non_500_lines)} rows with status != 500 in {self.OUTPUT_FILE}. "
            f"All data rows must have status_code 500. Non-500 rows: {non_500_lines[:3]}"
        )

    def test_output_has_exactly_12_data_rows(self):
        """Verify failures.csv contains exactly 12 data rows."""
        count_500 = 0
        with open(self.OUTPUT_FILE, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                if line.strip():
                    count_500 += 1
        assert count_500 == self.EXPECTED_500_ROWS, (
            f"Expected {self.EXPECTED_500_ROWS} data rows in {self.OUTPUT_FILE}, "
            f"but found {count_500}"
        )

    def test_output_rows_match_input_500_rows(self):
        """Verify all 12 rows with status 500 from original file are in failures.csv."""
        # Collect all 500 rows from input
        input_500_rows = set()
        with open(self.INPUT_FILE, 'r') as f:
            next(f)  # Skip header
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 2 and fields[1] == "500":
                    input_500_rows.add(line.strip())

        # Collect all data rows from output
        output_rows = set()
        with open(self.OUTPUT_FILE, 'r') as f:
            next(f)  # Skip header
            for line in f:
                if line.strip():
                    output_rows.add(line.strip())

        # Check that output contains all input 500 rows
        missing_rows = input_500_rows - output_rows
        assert len(missing_rows) == 0, (
            f"Missing {len(missing_rows)} rows from original file in {self.OUTPUT_FILE}. "
            f"Missing rows: {list(missing_rows)[:3]}..."
        )

        # Check that output doesn't have extra rows
        extra_rows = output_rows - input_500_rows
        assert len(extra_rows) == 0, (
            f"Found {len(extra_rows)} unexpected rows in {self.OUTPUT_FILE}. "
            f"Extra rows: {list(extra_rows)[:3]}..."
        )

    def test_input_file_unchanged(self):
        """Verify the input file /home/user/api_responses.csv is unchanged."""
        assert os.path.isfile(self.INPUT_FILE), (
            f"Input file {self.INPUT_FILE} no longer exists! It should remain unchanged."
        )

        # Check line count
        with open(self.INPUT_FILE, 'r') as f:
            line_count = sum(1 for _ in f)
        assert line_count == 847, (
            f"Input file {self.INPUT_FILE} has {line_count} lines, expected 847. "
            "The original file should not be modified."
        )

        # Check header
        with open(self.INPUT_FILE, 'r') as f:
            header = f.readline().strip()
        assert header == self.EXPECTED_HEADER, (
            f"Input file header changed to '{header}'. "
            "The original file should not be modified."
        )

        # Check that it still has exactly 12 rows with status 500
        count_500 = 0
        with open(self.INPUT_FILE, 'r') as f:
            next(f)
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 2 and fields[1] == "500":
                    count_500 += 1
        assert count_500 == 12, (
            f"Input file now has {count_500} rows with status 500, expected 12. "
            "The original file should not be modified."
        )

    def test_output_csv_well_formed(self):
        """Verify output CSV is well-formed with 4 fields per row."""
        with open(self.OUTPUT_FILE, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                fields = line.strip().split(',')
                assert len(fields) == 4, (
                    f"Line {line_num} in {self.OUTPUT_FILE} has {len(fields)} fields "
                    f"instead of 4: {line.strip()}"
                )
