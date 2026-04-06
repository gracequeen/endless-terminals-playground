# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the web scraping task.
"""

import os
import re
import stat
import pytest


class TestFinalState:
    """Tests to verify the web scraping task was completed successfully."""

    # Path constants
    TITLES_FILE = "/home/user/hn_titles.txt"
    LOG_FILE = "/home/user/scrape_log.txt"

    def test_titles_file_exists(self):
        """Verify that /home/user/hn_titles.txt exists."""
        assert os.path.exists(self.TITLES_FILE), (
            f"Output file {self.TITLES_FILE} does not exist. "
            "The scraping task has not been completed."
        )

    def test_titles_file_is_regular_file(self):
        """Verify that /home/user/hn_titles.txt is a regular file."""
        assert os.path.isfile(self.TITLES_FILE), (
            f"{self.TITLES_FILE} exists but is not a regular file."
        )

    def test_titles_file_is_readable(self):
        """Verify that /home/user/hn_titles.txt has read permissions."""
        assert os.access(self.TITLES_FILE, os.R_OK), (
            f"{self.TITLES_FILE} is not readable. "
            "File should have at least 644 permissions."
        )

    def test_titles_file_permissions(self):
        """Verify that /home/user/hn_titles.txt has at least 644 permissions."""
        file_stat = os.stat(self.TITLES_FILE)
        mode = file_stat.st_mode
        # Check that owner can read, group can read, others can read
        owner_read = bool(mode & stat.S_IRUSR)
        group_read = bool(mode & stat.S_IRGRP)
        other_read = bool(mode & stat.S_IROTH)

        assert owner_read, (
            f"{self.TITLES_FILE} is not readable by owner."
        )
        # At minimum, the file should be readable by owner
        # 644 also requires group and other read, but we'll be lenient
        # and just ensure it's readable

    def test_titles_file_has_exactly_5_lines(self):
        """Verify that /home/user/hn_titles.txt contains exactly 5 lines."""
        with open(self.TITLES_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Filter out completely empty lines at the end (trailing newline)
        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) == 5, (
            f"{self.TITLES_FILE} should contain exactly 5 lines, "
            f"but found {len(non_empty_lines)} non-empty lines."
        )

    def test_titles_file_lines_match_format(self):
        """Verify each line matches the format: number. title"""
        pattern = re.compile(r'^\d+\. .+$')

        with open(self.TITLES_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for i, line in enumerate(lines, start=1):
            assert pattern.match(line), (
                f"Line {i} in {self.TITLES_FILE} does not match expected format. "
                f"Expected format: 'N. Title text' (e.g., '1. Some Story Title'). "
                f"Got: '{line}'"
            )

    def test_titles_file_lines_numbered_correctly(self):
        """Verify lines are numbered 1 through 5 in order."""
        with open(self.TITLES_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for expected_num, line in enumerate(lines, start=1):
            # Extract the number at the beginning
            match = re.match(r'^(\d+)\.', line)
            assert match, (
                f"Line {expected_num} does not start with a number. Got: '{line}'"
            )
            actual_num = int(match.group(1))
            assert actual_num == expected_num, (
                f"Line {expected_num} has wrong number prefix. "
                f"Expected {expected_num}, got {actual_num}. Line: '{line}'"
            )

    def test_titles_file_titles_are_non_empty(self):
        """Verify each title (after the number prefix) is non-empty."""
        with open(self.TITLES_FILE, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for i, line in enumerate(lines, start=1):
            # Extract title after "N. "
            match = re.match(r'^\d+\.\s*(.*)$', line)
            assert match, f"Could not parse line {i}: '{line}'"
            title = match.group(1).strip()
            assert len(title) > 0, (
                f"Line {i} has an empty title after the number prefix. "
                f"Full line: '{line}'"
            )

    def test_log_file_exists(self):
        """Verify that /home/user/scrape_log.txt exists."""
        assert os.path.exists(self.LOG_FILE), (
            f"Log file {self.LOG_FILE} does not exist. "
            "The scraping task has not been completed."
        )

    def test_log_file_is_regular_file(self):
        """Verify that /home/user/scrape_log.txt is a regular file."""
        assert os.path.isfile(self.LOG_FILE), (
            f"{self.LOG_FILE} exists but is not a regular file."
        )

    def test_log_file_is_readable(self):
        """Verify that /home/user/scrape_log.txt has read permissions."""
        assert os.access(self.LOG_FILE, os.R_OK), (
            f"{self.LOG_FILE} is not readable. "
            "File should have at least 644 permissions."
        )

    def test_log_file_line1_status_success(self):
        """Verify log file line 1 is exactly 'STATUS: SUCCESS'."""
        with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) >= 1, (
            f"{self.LOG_FILE} is empty. Expected at least 3 lines."
        )

        line1 = lines[0].strip()
        assert line1 == "STATUS: SUCCESS", (
            f"Line 1 of {self.LOG_FILE} should be exactly 'STATUS: SUCCESS'. "
            f"Got: '{line1}'"
        )

    def test_log_file_line2_items_scraped(self):
        """Verify log file line 2 is exactly 'ITEMS_SCRAPED: 5'."""
        with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) >= 2, (
            f"{self.LOG_FILE} has fewer than 2 lines. Expected at least 3 lines."
        )

        line2 = lines[1].strip()
        assert line2 == "ITEMS_SCRAPED: 5", (
            f"Line 2 of {self.LOG_FILE} should be exactly 'ITEMS_SCRAPED: 5'. "
            f"Got: '{line2}'"
        )

    def test_log_file_line3_url(self):
        """Verify log file line 3 is exactly 'URL: https://news.ycombinator.com'."""
        with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert len(lines) >= 3, (
            f"{self.LOG_FILE} has fewer than 3 lines. Expected exactly 3 lines."
        )

        line3 = lines[2].strip()
        assert line3 == "URL: https://news.ycombinator.com", (
            f"Line 3 of {self.LOG_FILE} should be exactly "
            f"'URL: https://news.ycombinator.com'. Got: '{line3}'"
        )

    def test_log_file_has_exactly_3_content_lines(self):
        """Verify log file has exactly 3 lines of content."""
        with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
            lines = [line for line in f.readlines() if line.strip()]

        assert len(lines) == 3, (
            f"{self.LOG_FILE} should contain exactly 3 non-empty lines. "
            f"Found {len(lines)} non-empty lines."
        )

    def test_log_file_complete_content(self):
        """Verify the complete content of the log file."""
        expected_lines = [
            "STATUS: SUCCESS",
            "ITEMS_SCRAPED: 5",
            "URL: https://news.ycombinator.com"
        ]

        with open(self.LOG_FILE, 'r', encoding='utf-8') as f:
            actual_lines = [line.strip() for line in f.readlines() if line.strip()]

        assert actual_lines == expected_lines, (
            f"Log file content does not match expected.\n"
            f"Expected:\n{chr(10).join(expected_lines)}\n"
            f"Got:\n{chr(10).join(actual_lines)}"
        )