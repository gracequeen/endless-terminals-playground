# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the backup integrity verification task.
"""

import os
import gzip
import hashlib
import re
import pytest
from pathlib import Path


class TestFinalState:
    """Test the final state after the backup integrity verification task is completed."""

    # Constants
    BACKUP_FILE = Path("/home/user/backups/database_dump.sql.gz")
    LOG_FILE = Path("/home/user/backups/integrity_check.log")
    EXPECTED_EQUALS_SIGNS = 23

    def test_backup_file_still_exists(self):
        """Verify that the original backup file still exists (wasn't deleted)."""
        assert self.BACKUP_FILE.exists(), (
            f"Backup file no longer exists at {self.BACKUP_FILE}. "
            "The original backup file should not be deleted during verification."
        )
        assert self.BACKUP_FILE.is_file(), (
            f"{self.BACKUP_FILE} exists but is not a regular file."
        )

    def test_integrity_log_file_exists(self):
        """Verify that the integrity check log file was created."""
        assert self.LOG_FILE.exists(), (
            f"Integrity check log file does not exist at {self.LOG_FILE}. "
            "Please create the verification log file as specified in the task."
        )
        assert self.LOG_FILE.is_file(), (
            f"{self.LOG_FILE} exists but is not a regular file."
        )

    def test_integrity_log_file_is_readable(self):
        """Verify that the integrity check log file is readable."""
        assert os.path.isfile(self.LOG_FILE), (
            f"Integrity check log file at {self.LOG_FILE} is not readable."
        )

    def test_integrity_log_has_exactly_six_lines(self):
        """Verify that the log file has exactly 6 lines."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        # Count non-empty lines or all lines depending on interpretation
        # The task says "exactly 6 lines" so we count all lines
        assert len(lines) == 6, (
            f"Integrity log file should have exactly 6 lines, but has {len(lines)} lines. "
            f"Expected format:\n"
            f"Line 1: BACKUP INTEGRITY REPORT\n"
            f"Line 2: ======================= (23 equals signs)\n"
            f"Line 3: File: /home/user/backups/database_dump.sql.gz\n"
            f"Line 4: Compressed MD5: <32 hex chars>\n"
            f"Line 5: Uncompressed MD5: <32 hex chars>\n"
            f"Line 6: Status: VERIFIED"
        )

    def test_line_1_is_header(self):
        """Verify that line 1 is 'BACKUP INTEGRITY REPORT'."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line1 = lines[0].rstrip('\n\r')
        expected = "BACKUP INTEGRITY REPORT"
        assert line1 == expected, (
            f"Line 1 should be '{expected}', but got '{line1}'."
        )

    def test_line_2_is_separator(self):
        """Verify that line 2 is exactly 23 equals signs."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line2 = lines[1].rstrip('\n\r')
        expected = "=" * self.EXPECTED_EQUALS_SIGNS
        assert line2 == expected, (
            f"Line 2 should be exactly {self.EXPECTED_EQUALS_SIGNS} equals signs ('{expected}'), "
            f"but got '{line2}' ({len(line2)} characters)."
        )

    def test_line_3_contains_correct_file_path(self):
        """Verify that line 3 contains the correct file path."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line3 = lines[2].rstrip('\n\r')
        expected = f"File: {self.BACKUP_FILE}"
        assert line3 == expected, (
            f"Line 3 should be '{expected}', but got '{line3}'."
        )

    def test_line_4_has_valid_compressed_md5_format(self):
        """Verify that line 4 has a valid MD5 hash format."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line4 = lines[3].rstrip('\n\r')

        # Check format: "Compressed MD5: " followed by 32 hex chars
        pattern = r'^Compressed MD5: ([a-f0-9]{32})$'
        match = re.match(pattern, line4)
        assert match is not None, (
            f"Line 4 should be 'Compressed MD5: ' followed by exactly 32 lowercase hex characters. "
            f"Got: '{line4}'."
        )

    def test_line_5_has_valid_uncompressed_md5_format(self):
        """Verify that line 5 has a valid MD5 hash format."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line5 = lines[4].rstrip('\n\r')

        # Check format: "Uncompressed MD5: " followed by 32 hex chars
        pattern = r'^Uncompressed MD5: ([a-f0-9]{32})$'
        match = re.match(pattern, line5)
        assert match is not None, (
            f"Line 5 should be 'Uncompressed MD5: ' followed by exactly 32 lowercase hex characters. "
            f"Got: '{line5}'."
        )

    def test_line_6_is_status_verified(self):
        """Verify that line 6 is 'Status: VERIFIED'."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line6 = lines[5].rstrip('\n\r')
        expected = "Status: VERIFIED"
        assert line6 == expected, (
            f"Line 6 should be '{expected}', but got '{line6}'."
        )

    def test_compressed_md5_matches_actual_file(self):
        """Verify that the compressed MD5 in the log matches the actual MD5 of the .gz file."""
        # Calculate actual MD5 of compressed file
        with open(self.BACKUP_FILE, 'rb') as f:
            actual_md5 = hashlib.md5(f.read()).hexdigest()

        # Extract MD5 from log file
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line4 = lines[3].rstrip('\n\r')
        pattern = r'^Compressed MD5: ([a-f0-9]{32})$'
        match = re.match(pattern, line4)

        assert match is not None, (
            f"Could not extract compressed MD5 from line 4: '{line4}'"
        )

        logged_md5 = match.group(1)
        assert logged_md5 == actual_md5, (
            f"Compressed MD5 in log does not match actual file MD5.\n"
            f"Logged MD5:  {logged_md5}\n"
            f"Actual MD5:  {actual_md5}\n"
            f"Please recalculate the MD5 of {self.BACKUP_FILE}."
        )

    def test_uncompressed_md5_matches_actual_content(self):
        """Verify that the uncompressed MD5 in the log matches the MD5 of decompressed content."""
        # Calculate actual MD5 of uncompressed content
        with gzip.open(self.BACKUP_FILE, 'rb') as f:
            actual_md5 = hashlib.md5(f.read()).hexdigest()

        # Extract MD5 from log file
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line5 = lines[4].rstrip('\n\r')
        pattern = r'^Uncompressed MD5: ([a-f0-9]{32})$'
        match = re.match(pattern, line5)

        assert match is not None, (
            f"Could not extract uncompressed MD5 from line 5: '{line5}'"
        )

        logged_md5 = match.group(1)
        assert logged_md5 == actual_md5, (
            f"Uncompressed MD5 in log does not match actual decompressed content MD5.\n"
            f"Logged MD5:  {logged_md5}\n"
            f"Actual MD5:  {actual_md5}\n"
            f"Please recalculate the MD5 of the decompressed content of {self.BACKUP_FILE}."
        )

    def test_compressed_and_uncompressed_md5_are_different(self):
        """Verify that the compressed and uncompressed MD5 values are different."""
        with open(self.LOG_FILE, 'r') as f:
            lines = f.readlines()

        line4 = lines[3].rstrip('\n\r')
        line5 = lines[4].rstrip('\n\r')

        compressed_pattern = r'^Compressed MD5: ([a-f0-9]{32})$'
        uncompressed_pattern = r'^Uncompressed MD5: ([a-f0-9]{32})$'

        compressed_match = re.match(compressed_pattern, line4)
        uncompressed_match = re.match(uncompressed_pattern, line5)

        if compressed_match and uncompressed_match:
            compressed_md5 = compressed_match.group(1)
            uncompressed_md5 = uncompressed_match.group(1)

            assert compressed_md5 != uncompressed_md5, (
                f"Compressed and uncompressed MD5 values should be different.\n"
                f"Both are: {compressed_md5}\n"
                f"This suggests the same content was hashed twice instead of "
                f"hashing compressed vs uncompressed content."
            )

    def test_log_file_complete_format(self):
        """Verify the complete format of the log file matches expectations."""
        with open(self.LOG_FILE, 'r') as f:
            content = f.read()

        # Build expected pattern
        pattern = (
            r'^BACKUP INTEGRITY REPORT\n'
            r'={23}\n'
            r'File: /home/user/backups/database_dump\.sql\.gz\n'
            r'Compressed MD5: [a-f0-9]{32}\n'
            r'Uncompressed MD5: [a-f0-9]{32}\n'
            r'Status: VERIFIED\n?$'
        )

        assert re.match(pattern, content), (
            f"Log file format does not match expected format.\n"
            f"Expected format:\n"
            f"BACKUP INTEGRITY REPORT\n"
            f"=======================\n"
            f"File: /home/user/backups/database_dump.sql.gz\n"
            f"Compressed MD5: <32 hex chars>\n"
            f"Uncompressed MD5: <32 hex chars>\n"
            f"Status: VERIFIED\n\n"
            f"Actual content:\n{content}"
        )