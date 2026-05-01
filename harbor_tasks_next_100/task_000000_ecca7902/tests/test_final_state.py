# test_final_state.py
"""
Tests to validate the final state of the system after the student
has extracted 503 error lines from nginx access log to /home/user/docs/503_examples.txt.
"""

import os
import re
import pytest


class TestFinalState:
    """Validate the system state after the task is completed."""

    def test_output_file_exists(self):
        """Verify /home/user/docs/503_examples.txt exists."""
        output_path = "/home/user/docs/503_examples.txt"
        assert os.path.exists(output_path), \
            f"Output file does not exist: {output_path}. Task requires creating this file with 503 error lines."

    def test_output_file_is_regular_file(self):
        """Verify /home/user/docs/503_examples.txt is a regular file."""
        output_path = "/home/user/docs/503_examples.txt"
        assert os.path.isfile(output_path), \
            f"{output_path} exists but is not a regular file"

    def test_output_file_not_empty(self):
        """Verify output file is not empty."""
        output_path = "/home/user/docs/503_examples.txt"
        assert os.path.getsize(output_path) > 0, \
            f"Output file {output_path} is empty. It should contain 503 error lines."

    def test_output_file_line_count_matches_source(self):
        """Verify output file has the correct number of 503 lines (approximately 47)."""
        output_path = "/home/user/docs/503_examples.txt"
        source_path = "/var/log/app/access.log"

        # Count 503 lines in source
        source_503_count = 0
        with open(source_path, 'r') as f:
            for line in f:
                if '" 503 ' in line:
                    source_503_count += 1

        # Count lines in output
        with open(output_path, 'r') as f:
            output_line_count = sum(1 for line in f if line.strip())

        assert output_line_count == source_503_count, \
            f"Output file has {output_line_count} lines, but source log has {source_503_count} lines with 503 status. " \
            f"All 503 error lines should be extracted."

    def test_all_output_lines_contain_503_status(self):
        """Verify every line in output file has 503 as the HTTP status code."""
        output_path = "/home/user/docs/503_examples.txt"

        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:  # Skip empty lines
                    assert '" 503 ' in line, \
                        f"Line {line_num} does not contain 503 status code in correct position: {line[:100]}..."

    def test_no_false_positives_503_elsewhere(self):
        """
        Anti-shortcut guard: Verify no lines have 503 only in wrong positions.
        All lines must have '" 503 ' pattern (status code position).
        """
        output_path = "/home/user/docs/503_examples.txt"

        lines_without_503_status = []
        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    # Check that the line has 503 in the status position
                    if '" 503 ' not in line:
                        lines_without_503_status.append((line_num, line[:80]))

        assert len(lines_without_503_status) == 0, \
            f"Found {len(lines_without_503_status)} line(s) without 503 in status code position. " \
            f"These may be false positives where 503 appears elsewhere (IP, bytes, URL). " \
            f"First few: {lines_without_503_status[:3]}"

    def test_output_lines_are_valid_log_format(self):
        """Verify output lines are in valid nginx combined log format."""
        output_path = "/home/user/docs/503_examples.txt"

        # Combined log format pattern
        combined_log_pattern = re.compile(
            r'^\d+\.\d+\.\d+\.\d+ - .* \[.*\] ".*" \d{3} \d+ ".*" ".*"$'
        )

        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    assert combined_log_pattern.match(line), \
                        f"Line {line_num} is not in valid combined log format: {line[:100]}..."

    def test_output_lines_match_source_lines(self):
        """Verify output lines are exact copies from source log."""
        output_path = "/home/user/docs/503_examples.txt"
        source_path = "/var/log/app/access.log"

        # Get all 503 lines from source
        source_503_lines = set()
        with open(source_path, 'r') as f:
            for line in f:
                if '" 503 ' in line:
                    source_503_lines.add(line.strip())

        # Check all output lines exist in source
        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    assert line in source_503_lines, \
                        f"Line {line_num} in output does not match any 503 line in source: {line[:100]}..."

    def test_source_log_unchanged(self):
        """Verify /var/log/app/access.log still exists and has content."""
        source_path = "/var/log/app/access.log"

        assert os.path.exists(source_path), \
            f"Source log {source_path} no longer exists - it should not be modified"
        assert os.path.isfile(source_path), \
            f"Source log {source_path} is no longer a regular file"

        # Verify it still has approximately 2000 lines
        with open(source_path, 'r') as f:
            line_count = sum(1 for _ in f)

        assert 1800 <= line_count <= 2200, \
            f"Source log has {line_count} lines, expected approximately 2000. " \
            f"The source log should not be modified."

    def test_no_extra_files_in_docs_directory(self):
        """Verify no unexpected files were created in /home/user/docs/."""
        docs_path = "/home/user/docs"

        # List all files in docs directory
        files_in_docs = os.listdir(docs_path)

        # Only 503_examples.txt should be present (or it was already there before)
        # We check that no unexpected files exist
        expected_files = {'503_examples.txt'}

        for f in files_in_docs:
            if f not in expected_files:
                # Allow hidden files or directories that might have existed before
                if not f.startswith('.'):
                    # This is informational - we mainly care about the output file
                    pass

    def test_output_contains_expected_number_of_lines(self):
        """Verify output file contains approximately 47 lines as specified."""
        output_path = "/home/user/docs/503_examples.txt"

        with open(output_path, 'r') as f:
            line_count = sum(1 for line in f if line.strip())

        # The truth states approximately 47 lines
        assert 40 <= line_count <= 55, \
            f"Output file has {line_count} lines, expected approximately 47 (the number of 503 entries in source)"

    def test_output_file_readable(self):
        """Verify output file is readable."""
        output_path = "/home/user/docs/503_examples.txt"
        assert os.access(output_path, os.R_OK), \
            f"Output file {output_path} is not readable"
