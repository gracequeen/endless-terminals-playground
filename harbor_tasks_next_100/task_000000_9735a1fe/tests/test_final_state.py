# test_final_state.py
"""
Post-validation tests for the nginx 5xx log extraction task.
Validates the final state after the student has completed the action.
"""

import os
import pytest
import subprocess
import hashlib


class TestFinalState:
    """Tests to verify the final state after task execution."""

    def test_output_file_exists(self):
        """Verify that /home/user/5xx.log exists."""
        output_path = "/home/user/5xx.log"
        assert os.path.exists(output_path), (
            f"Output file {output_path} does not exist. "
            "You need to extract 5xx error lines from /var/log/app/access.log "
            "and save them to /home/user/5xx.log"
        )
        assert os.path.isfile(output_path), (
            f"{output_path} exists but is not a regular file"
        )

    def test_output_file_not_empty(self):
        """Verify that /home/user/5xx.log is not empty."""
        output_path = "/home/user/5xx.log"
        assert os.path.exists(output_path), f"Output file {output_path} does not exist"
        file_size = os.path.getsize(output_path)
        assert file_size > 0, (
            f"{output_path} is empty. It should contain the 5xx error lines."
        )

    def test_output_line_count(self):
        """Verify that /home/user/5xx.log contains exactly 847 lines."""
        output_path = "/home/user/5xx.log"
        result = subprocess.run(
            ["wc", "-l", output_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to count lines in {output_path}"
        line_count = int(result.stdout.split()[0])
        assert line_count == 847, (
            f"Expected exactly 847 lines in {output_path}, but found {line_count}. "
            "Make sure you're extracting lines where field 9 (1-indexed) is a 5xx status code."
        )

    def test_all_lines_have_5xx_status(self):
        """Verify that every line in the output has a 5xx status code in field 9."""
        output_path = "/home/user/5xx.log"
        assert os.path.exists(output_path), f"Output file {output_path} does not exist"

        invalid_lines = []
        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')
                if not line:
                    continue
                fields = line.split()
                if len(fields) < 9:
                    invalid_lines.append((line_num, f"Less than 9 fields: {line[:80]}..."))
                    continue
                status_code = fields[8]  # 0-indexed, field 9 is index 8
                if not (status_code.isdigit() and len(status_code) == 3 and status_code.startswith('5')):
                    invalid_lines.append((line_num, f"Field 9 is '{status_code}', not a 5xx code"))

        assert not invalid_lines, (
            f"Found {len(invalid_lines)} lines without valid 5xx status in field 9:\n" +
            "\n".join(f"  Line {ln}: {msg}" for ln, msg in invalid_lines[:10]) +
            ("\n  ..." if len(invalid_lines) > 10 else "")
        )

    def test_lines_are_complete(self):
        """Verify that output lines are complete (not just status codes or partial fields)."""
        output_path = "/home/user/5xx.log"
        assert os.path.exists(output_path), f"Output file {output_path} does not exist"

        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip('\n')
                if not line:
                    continue
                fields = line.split()
                # A complete combined log line should have at least 10 fields
                # (IP, ident, user, [date], "request", status, size, "referer", "user-agent")
                assert len(fields) >= 10, (
                    f"Line {line_num} appears truncated or incomplete. "
                    f"Only {len(fields)} fields found. Lines must be complete original lines. "
                    f"Line content: {line[:100]}..."
                )
                # First field should look like an IP address
                first_field = fields[0]
                assert '.' in first_field or ':' in first_field, (
                    f"Line {line_num} doesn't start with an IP address. "
                    "Output must contain complete original lines, not just extracted fields."
                )
                if line_num >= 20:  # Only check first 20 lines for performance
                    break

    def test_output_lines_match_source(self):
        """Verify that output lines exist byte-identical in the source log."""
        output_path = "/home/user/5xx.log"
        source_path = "/var/log/app/access.log"

        assert os.path.exists(output_path), f"Output file {output_path} does not exist"

        # Build a set of all 5xx lines from source
        source_5xx_lines = set()
        with open(source_path, 'r') as f:
            for line in f:
                fields = line.split()
                if len(fields) >= 9:
                    status = fields[8]
                    if status.isdigit() and len(status) == 3 and status.startswith('5'):
                        source_5xx_lines.add(line)

        # Check that all output lines are in source
        mismatched_lines = []
        with open(output_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line not in source_5xx_lines:
                    # Also check without trailing newline in case of formatting differences
                    if line.rstrip('\n') + '\n' not in source_5xx_lines:
                        mismatched_lines.append(line_num)

        assert not mismatched_lines, (
            f"Found {len(mismatched_lines)} lines in output that don't match source 5xx lines. "
            f"First mismatched line numbers: {mismatched_lines[:5]}"
        )

    def test_all_5xx_lines_captured(self):
        """Verify that all 5xx lines from source are in the output."""
        output_path = "/home/user/5xx.log"
        source_path = "/var/log/app/access.log"

        assert os.path.exists(output_path), f"Output file {output_path} does not exist"

        # Count 5xx lines in source
        result = subprocess.run(
            ["awk", '$9 ~ /^5[0-9][0-9]$/ {count++} END {print count}', source_path],
            capture_output=True,
            text=True
        )
        source_5xx_count = int(result.stdout.strip())

        # Count lines in output
        result = subprocess.run(
            ["wc", "-l", output_path],
            capture_output=True,
            text=True
        )
        output_count = int(result.stdout.split()[0])

        assert output_count == source_5xx_count, (
            f"Output has {output_count} lines but source has {source_5xx_count} 5xx lines. "
            "All 5xx lines should be captured."
        )

    def test_source_log_unchanged(self):
        """Verify that /var/log/app/access.log still exists and has expected line count."""
        source_path = "/var/log/app/access.log"

        assert os.path.exists(source_path), (
            f"Source log {source_path} no longer exists! It should not be modified or deleted."
        )

        result = subprocess.run(
            ["wc", "-l", source_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to count lines in {source_path}"
        line_count = int(result.stdout.split()[0])

        # Should still have approximately 200,000 lines
        assert 190000 <= line_count <= 210000, (
            f"Source log {source_path} has {line_count} lines, expected ~200,000. "
            "The source log should not be modified."
        )

    def test_5xx_status_codes_variety(self):
        """Verify that output contains actual 5xx codes (500, 502, 503, 504, etc.)."""
        output_path = "/home/user/5xx.log"
        assert os.path.exists(output_path), f"Output file {output_path} does not exist"

        status_codes = set()
        with open(output_path, 'r') as f:
            for line in f:
                fields = line.split()
                if len(fields) >= 9:
                    status = fields[8]
                    if status.isdigit() and status.startswith('5'):
                        status_codes.add(status)

        # Should have at least some variety of 5xx codes
        assert len(status_codes) >= 1, (
            "No valid 5xx status codes found in output"
        )

        # All found codes should be valid 5xx
        for code in status_codes:
            assert 500 <= int(code) <= 599, (
                f"Found invalid status code {code} in output - expected 5xx codes only"
            )

    def test_no_non_5xx_lines(self):
        """Verify that output contains no 2xx, 3xx, or 4xx status codes."""
        output_path = "/home/user/5xx.log"
        assert os.path.exists(output_path), f"Output file {output_path} does not exist"

        # Use awk to find any non-5xx lines
        result = subprocess.run(
            ["awk", '$9 !~ /^5[0-9][0-9]$/ {print NR": "$9}', output_path],
            capture_output=True,
            text=True
        )

        non_5xx_output = result.stdout.strip()
        assert not non_5xx_output, (
            f"Found lines with non-5xx status codes in output:\n{non_5xx_output[:500]}"
        )
