# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the backup verification task.
"""

import pytest
import os
import json
import subprocess


class TestFinalState:
    """Test suite to validate final state after the task is performed."""

    # --- Tests for json_ids.txt ---

    def test_json_ids_file_exists(self):
        """Verify /home/user/verify/json_ids.txt exists."""
        assert os.path.isfile("/home/user/verify/json_ids.txt"), \
            "File /home/user/verify/json_ids.txt does not exist"

    def test_json_ids_has_exactly_50_lines(self):
        """Verify json_ids.txt has exactly 50 lines."""
        file_path = "/home/user/verify/json_ids.txt"
        with open(file_path, 'r') as f:
            lines = f.readlines()
        # Count non-empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) == 50, \
            f"json_ids.txt should have exactly 50 lines, got {len(non_empty_lines)}"

    def test_json_ids_all_integers(self):
        """Verify all lines in json_ids.txt are valid integers only."""
        file_path = "/home/user/verify/json_ids.txt"
        with open(file_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:  # Skip empty lines for this check
                assert stripped.isdigit() or (stripped.startswith('-') and stripped[1:].isdigit()), \
                    f"Line {i+1} in json_ids.txt is not a valid integer: '{stripped}'"

    def test_json_ids_no_blank_lines(self):
        """Verify json_ids.txt has no blank lines."""
        file_path = "/home/user/verify/json_ids.txt"
        with open(file_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        # Remove trailing empty string from split if file ends with newline
        if lines and lines[-1] == '':
            lines = lines[:-1]

        for i, line in enumerate(lines):
            assert line.strip() != '' or i == len(lines), \
                f"json_ids.txt has a blank line at line {i+1}"

    def test_json_ids_sorted_numerically(self):
        """Verify json_ids.txt is sorted numerically ascending."""
        file_path = "/home/user/verify/json_ids.txt"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        ids = [int(line) for line in lines]
        sorted_ids = sorted(ids)
        assert ids == sorted_ids, \
            f"json_ids.txt is not sorted numerically ascending"

    def test_json_ids_no_duplicates(self):
        """Verify json_ids.txt has no duplicate IDs."""
        file_path = "/home/user/verify/json_ids.txt"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        ids = [int(line) for line in lines]
        assert len(ids) == len(set(ids)), \
            f"json_ids.txt contains duplicate IDs"

    # --- Tests for csv_ids.txt ---

    def test_csv_ids_file_exists(self):
        """Verify /home/user/verify/csv_ids.txt exists."""
        assert os.path.isfile("/home/user/verify/csv_ids.txt"), \
            "File /home/user/verify/csv_ids.txt does not exist"

    def test_csv_ids_has_exactly_50_lines(self):
        """Verify csv_ids.txt has exactly 50 lines."""
        file_path = "/home/user/verify/csv_ids.txt"
        with open(file_path, 'r') as f:
            lines = f.readlines()
        # Count non-empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) == 50, \
            f"csv_ids.txt should have exactly 50 lines, got {len(non_empty_lines)}"

    def test_csv_ids_all_integers(self):
        """Verify all lines in csv_ids.txt are valid integers only."""
        file_path = "/home/user/verify/csv_ids.txt"
        with open(file_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped:  # Skip empty lines for this check
                assert stripped.isdigit() or (stripped.startswith('-') and stripped[1:].isdigit()), \
                    f"Line {i+1} in csv_ids.txt is not a valid integer: '{stripped}'"

    def test_csv_ids_no_blank_lines(self):
        """Verify csv_ids.txt has no blank lines."""
        file_path = "/home/user/verify/csv_ids.txt"
        with open(file_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        # Remove trailing empty string from split if file ends with newline
        if lines and lines[-1] == '':
            lines = lines[:-1]

        for i, line in enumerate(lines):
            assert line.strip() != '' or i == len(lines), \
                f"csv_ids.txt has a blank line at line {i+1}"

    def test_csv_ids_sorted_numerically(self):
        """Verify csv_ids.txt is sorted numerically ascending."""
        file_path = "/home/user/verify/csv_ids.txt"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        ids = [int(line) for line in lines]
        sorted_ids = sorted(ids)
        assert ids == sorted_ids, \
            f"csv_ids.txt is not sorted numerically ascending"

    def test_csv_ids_no_duplicates(self):
        """Verify csv_ids.txt has no duplicate IDs."""
        file_path = "/home/user/verify/csv_ids.txt"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        ids = [int(line) for line in lines]
        assert len(ids) == len(set(ids)), \
            f"csv_ids.txt contains duplicate IDs"

    # --- Tests for matching content ---

    def test_json_and_csv_ids_match(self):
        """Verify json_ids.txt and csv_ids.txt contain the same IDs."""
        json_path = "/home/user/verify/json_ids.txt"
        csv_path = "/home/user/verify/csv_ids.txt"

        with open(json_path, 'r') as f:
            json_ids = set(int(line.strip()) for line in f.readlines() if line.strip())

        with open(csv_path, 'r') as f:
            csv_ids = set(int(line.strip()) for line in f.readlines() if line.strip())

        assert json_ids == csv_ids, \
            f"json_ids.txt and csv_ids.txt do not contain the same IDs. " \
            f"In JSON only: {json_ids - csv_ids}, In CSV only: {csv_ids - json_ids}"

    # --- Tests for correct extraction from source files ---

    def test_json_ids_match_source(self):
        """Verify json_ids.txt contains the correct IDs from customers.json."""
        source_path = "/home/user/backups/customers.json"
        output_path = "/home/user/verify/json_ids.txt"

        with open(source_path, 'r') as f:
            json_data = json.load(f)
        source_ids = set(record['id'] for record in json_data)

        with open(output_path, 'r') as f:
            output_ids = set(int(line.strip()) for line in f.readlines() if line.strip())

        assert source_ids == output_ids, \
            f"json_ids.txt does not contain the correct IDs from customers.json. " \
            f"Missing: {source_ids - output_ids}, Extra: {output_ids - source_ids}"

    def test_csv_ids_match_source(self):
        """Verify csv_ids.txt contains the correct IDs from customers.csv."""
        source_path = "/home/user/data/customers.csv"
        output_path = "/home/user/verify/csv_ids.txt"

        source_ids = set()
        with open(source_path, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                if line.strip():
                    id_value = line.split(',')[0].strip()
                    source_ids.add(int(id_value))

        with open(output_path, 'r') as f:
            output_ids = set(int(line.strip()) for line in f.readlines() if line.strip())

        assert source_ids == output_ids, \
            f"csv_ids.txt does not contain the correct IDs from customers.csv. " \
            f"Missing: {source_ids - output_ids}, Extra: {output_ids - source_ids}"

    # --- Invariant tests: source files unchanged ---

    def test_customers_json_still_exists(self):
        """Verify /home/user/backups/customers.json still exists."""
        assert os.path.isfile("/home/user/backups/customers.json"), \
            "File /home/user/backups/customers.json no longer exists"

    def test_customers_json_still_valid(self):
        """Verify customers.json is still valid JSON with 50 records."""
        json_path = "/home/user/backups/customers.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), \
            "customers.json is no longer a JSON array"
        assert len(data) == 50, \
            f"customers.json should still have 50 records, got {len(data)}"

    def test_customers_csv_still_exists(self):
        """Verify /home/user/data/customers.csv still exists."""
        assert os.path.isfile("/home/user/data/customers.csv"), \
            "File /home/user/data/customers.csv no longer exists"

    def test_customers_csv_still_has_correct_structure(self):
        """Verify customers.csv still has correct structure with 50 data rows."""
        csv_path = "/home/user/data/customers.csv"
        with open(csv_path, 'r') as f:
            lines = f.readlines()

        # Check header
        header = lines[0].strip()
        assert header.startswith('id,'), \
            "customers.csv header is corrupted"

        # Check data rows
        data_rows = len(lines) - 1
        assert data_rows == 50, \
            f"customers.csv should still have 50 data rows, got {data_rows}"

    # --- Anti-shortcut guards using shell commands ---

    def test_json_ids_line_count_via_wc(self):
        """Verify wc -l returns 50 for json_ids.txt."""
        result = subprocess.run(
            ['wc', '-l'],
            stdin=open('/home/user/verify/json_ids.txt', 'r'),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip().split()[0])
        assert line_count == 50, \
            f"wc -l for json_ids.txt should return 50, got {line_count}"

    def test_csv_ids_line_count_via_wc(self):
        """Verify wc -l returns 50 for csv_ids.txt."""
        result = subprocess.run(
            ['wc', '-l'],
            stdin=open('/home/user/verify/csv_ids.txt', 'r'),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip().split()[0])
        assert line_count == 50, \
            f"wc -l for csv_ids.txt should return 50, got {line_count}"

    def test_json_ids_sorted_via_sort_diff(self):
        """Verify json_ids.txt is sorted using sort -n and diff."""
        result = subprocess.run(
            'sort -n /home/user/verify/json_ids.txt | diff - /home/user/verify/json_ids.txt',
            shell=True,
            capture_output=True
        )
        assert result.returncode == 0, \
            f"json_ids.txt is not properly sorted numerically"

    def test_csv_ids_sorted_via_sort_diff(self):
        """Verify csv_ids.txt is sorted using sort -n and diff."""
        result = subprocess.run(
            'sort -n /home/user/verify/csv_ids.txt | diff - /home/user/verify/csv_ids.txt',
            shell=True,
            capture_output=True
        )
        assert result.returncode == 0, \
            f"csv_ids.txt is not properly sorted numerically"

    def test_json_ids_integers_only_via_grep(self):
        """Verify json_ids.txt contains only integer lines using grep."""
        result = subprocess.run(
            "grep -E '^[0-9]+$' /home/user/verify/json_ids.txt | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        assert count == 50, \
            f"json_ids.txt should have 50 lines matching integer pattern, got {count}"

    def test_csv_ids_integers_only_via_grep(self):
        """Verify csv_ids.txt contains only integer lines using grep."""
        result = subprocess.run(
            "grep -E '^[0-9]+$' /home/user/verify/csv_ids.txt | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        assert count == 50, \
            f"csv_ids.txt should have 50 lines matching integer pattern, got {count}"
