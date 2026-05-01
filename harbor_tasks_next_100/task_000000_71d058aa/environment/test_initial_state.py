# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting rows with status_code 500 from api_responses.csv.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    INPUT_FILE = "/home/user/api_responses.csv"
    OUTPUT_FILE = "/home/user/failures.csv"
    HOME_DIR = "/home/user"
    EXPECTED_HEADER = "request_id,status_code,response_time_ms,endpoint"
    EXPECTED_TOTAL_LINES = 847
    EXPECTED_500_ROWS = 12
    VALID_STATUS_CODES = {"200", "201", "400", "401", "404", "500", "502", "503"}

    def test_home_directory_exists(self):
        """Verify /home/user directory exists."""
        assert os.path.isdir(self.HOME_DIR), f"Home directory {self.HOME_DIR} does not exist"

    def test_home_directory_writable(self):
        """Verify /home/user is writable."""
        assert os.access(self.HOME_DIR, os.W_OK), f"Home directory {self.HOME_DIR} is not writable"

    def test_input_file_exists(self):
        """Verify the input CSV file exists."""
        assert os.path.isfile(self.INPUT_FILE), f"Input file {self.INPUT_FILE} does not exist"

    def test_input_file_readable(self):
        """Verify the input CSV file is readable."""
        assert os.access(self.INPUT_FILE, os.R_OK), f"Input file {self.INPUT_FILE} is not readable"

    def test_input_file_line_count(self):
        """Verify the input file has exactly 847 lines (1 header + 846 data rows)."""
        with open(self.INPUT_FILE, 'r') as f:
            line_count = sum(1 for _ in f)
        assert line_count == self.EXPECTED_TOTAL_LINES, (
            f"Expected {self.EXPECTED_TOTAL_LINES} lines in {self.INPUT_FILE}, "
            f"but found {line_count}"
        )

    def test_input_file_header(self):
        """Verify the header line is correct."""
        with open(self.INPUT_FILE, 'r') as f:
            header = f.readline().strip()
        assert header == self.EXPECTED_HEADER, (
            f"Expected header '{self.EXPECTED_HEADER}', but found '{header}'"
        )

    def test_csv_well_formed(self):
        """Verify CSV is well-formed with 4 fields per row."""
        with open(self.INPUT_FILE, 'r') as f:
            for line_num, line in enumerate(f, 1):
                fields = line.strip().split(',')
                assert len(fields) == 4, (
                    f"Line {line_num} has {len(fields)} fields instead of 4: {line.strip()}"
                )

    def test_exactly_12_rows_with_status_500(self):
        """Verify exactly 12 data rows have status_code == 500."""
        count_500 = 0
        with open(self.INPUT_FILE, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 2 and fields[1] == "500":
                    count_500 += 1
        assert count_500 == self.EXPECTED_500_ROWS, (
            f"Expected exactly {self.EXPECTED_500_ROWS} rows with status_code 500, "
            f"but found {count_500}"
        )

    def test_valid_status_codes_present(self):
        """Verify the expected status codes are present in the file."""
        found_codes = set()
        with open(self.INPUT_FILE, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 2:
                    found_codes.add(fields[1])

        # Check that all expected status codes are present
        for code in self.VALID_STATUS_CODES:
            assert code in found_codes, (
                f"Expected status code {code} not found in the data. "
                f"Found codes: {found_codes}"
            )

    def test_output_file_does_not_exist(self):
        """Verify the output file does not exist yet."""
        assert not os.path.exists(self.OUTPUT_FILE), (
            f"Output file {self.OUTPUT_FILE} already exists - it should not exist "
            "before the task is performed"
        )

    def test_awk_available(self):
        """Verify awk is available."""
        result = subprocess.run(['which', 'awk'], capture_output=True)
        assert result.returncode == 0, "awk is not available on the system"

    def test_sed_available(self):
        """Verify sed is available."""
        result = subprocess.run(['which', 'sed'], capture_output=True)
        assert result.returncode == 0, "sed is not available on the system"

    def test_grep_available(self):
        """Verify grep is available."""
        result = subprocess.run(['which', 'grep'], capture_output=True)
        assert result.returncode == 0, "grep is not available on the system"

    def test_awk_count_500_rows(self):
        """Verify awk can count exactly 12 rows with status 500."""
        result = subprocess.run(
            ['awk', '-F,', 'NR>1 && $2==500', self.INPUT_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"awk command failed: {result.stderr}"
        lines = [l for l in result.stdout.strip().split('\n') if l]
        assert len(lines) == self.EXPECTED_500_ROWS, (
            f"awk found {len(lines)} rows with status 500, expected {self.EXPECTED_500_ROWS}"
        )

    def test_no_embedded_commas_or_quotes(self):
        """Verify CSV has no embedded commas or quotes in fields."""
        with open(self.INPUT_FILE, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Check for quotes which would indicate complex CSV formatting
                assert '"' not in line, (
                    f"Line {line_num} contains quotes, indicating embedded commas or "
                    f"complex CSV formatting: {line.strip()}"
                )
                # Verify exactly 3 commas per line (4 fields)
                comma_count = line.count(',')
                assert comma_count == 3, (
                    f"Line {line_num} has {comma_count} commas instead of 3: {line.strip()}"
                )
