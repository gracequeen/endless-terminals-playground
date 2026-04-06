# test_final_state.py
"""
Tests to validate the final state of the filesystem after the student
has completed the security audit task.
"""

import os
import stat
import re
from datetime import datetime
import pytest


HOME_DIR = "/home/user"
REPORT_PATH = "/home/user/security_audit_report.txt"


def get_permission_string(mode):
    """Convert a file mode to a permission string like -rw-r--r--"""
    is_dir = stat.S_ISDIR(mode)
    prefix = 'd' if is_dir else '-'

    perms = ''
    for who in ['USR', 'GRP', 'OTH']:
        for what in ['R', 'W', 'X']:
            perm_bit = getattr(stat, f'S_I{what}{who}')
            if mode & perm_bit:
                perms += what.lower()
            else:
                perms += '-'

    return prefix + perms


def test_security_audit_report_exists():
    """Test that the security audit report file exists."""
    assert os.path.isfile(REPORT_PATH), (
        f"Security audit report file {REPORT_PATH} does not exist. "
        "The student should have created this file as part of the task."
    )


def test_report_is_not_world_writable():
    """Test that the report file itself does not have world-writable permissions."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    mode = os.stat(REPORT_PATH).st_mode
    perm_string = get_permission_string(mode)

    # Check if "other" has write permission (bit position for S_IWOTH)
    has_world_write = bool(mode & stat.S_IWOTH)

    assert not has_world_write, (
        f"Report file {REPORT_PATH} has world-writable permissions ({perm_string}). "
        "The report file itself should NOT have world-writable permissions for security reasons."
    )


def test_report_first_line_is_header():
    """Test that the first line of the report is exactly 'SECURITY AUDIT REPORT'."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        lines = f.readlines()

    assert len(lines) >= 1, (
        f"Report file {REPORT_PATH} is empty. "
        "The first line should be 'SECURITY AUDIT REPORT'."
    )

    first_line = lines[0].rstrip('\n\r')
    assert first_line == "SECURITY AUDIT REPORT", (
        f"First line of report is '{first_line}', "
        "but expected exactly 'SECURITY AUDIT REPORT'."
    )


def test_report_second_line_has_valid_date():
    """Test that the second line starts with 'Date: ' followed by YYYY-MM-DD format."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        lines = f.readlines()

    assert len(lines) >= 2, (
        f"Report file {REPORT_PATH} has fewer than 2 lines. "
        "The second line should be 'Date: YYYY-MM-DD'."
    )

    second_line = lines[1].rstrip('\n\r')
    assert second_line.startswith("Date: "), (
        f"Second line of report is '{second_line}', "
        "but expected it to start with 'Date: '."
    )

    # Extract the date part and validate format
    date_part = second_line[6:]  # Remove "Date: " prefix
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    assert re.match(date_pattern, date_part), (
        f"Date in report is '{date_part}', "
        "but expected YYYY-MM-DD format (e.g., 2024-01-15)."
    )

    # Validate it's a real date
    try:
        datetime.strptime(date_part, '%Y-%m-%d')
    except ValueError:
        pytest.fail(
            f"Date '{date_part}' is not a valid date. "
            "Expected a valid date in YYYY-MM-DD format."
        )


def test_report_third_line_is_blank():
    """Test that the third line of the report is blank."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        lines = f.readlines()

    assert len(lines) >= 3, (
        f"Report file {REPORT_PATH} has fewer than 3 lines. "
        "The third line should be blank."
    )

    third_line = lines[2].rstrip('\n\r')
    assert third_line == "", (
        f"Third line of report is '{third_line}', "
        "but expected it to be blank."
    )


def test_report_fourth_line_is_section_header():
    """Test that the fourth line is exactly 'WORLD-WRITABLE ITEMS FOUND:'."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        lines = f.readlines()

    assert len(lines) >= 4, (
        f"Report file {REPORT_PATH} has fewer than 4 lines. "
        "The fourth line should be 'WORLD-WRITABLE ITEMS FOUND:'."
    )

    fourth_line = lines[3].rstrip('\n\r')
    assert fourth_line == "WORLD-WRITABLE ITEMS FOUND:", (
        f"Fourth line of report is '{fourth_line}', "
        "but expected exactly 'WORLD-WRITABLE ITEMS FOUND:'."
    )


def test_report_contains_public_notes_entry():
    """Test that the report contains an entry for /home/user/public_notes.txt."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        content = f.read()

    # Check for the file path in the report
    assert "/home/user/public_notes.txt" in content, (
        f"Report does not contain entry for /home/user/public_notes.txt. "
        "This file has world-writable permissions (666) and should be listed."
    )

    # Check for proper permission string format (-rw-rw-rw-)
    # The pattern should match something like "-rw-rw-rw- /home/user/public_notes.txt"
    pattern = r'-rw-rw-rw-\s+/home/user/public_notes\.txt'
    assert re.search(pattern, content), (
        f"Report does not contain properly formatted entry for /home/user/public_notes.txt. "
        "Expected format: '-rw-rw-rw- /home/user/public_notes.txt'."
    )


def test_report_contains_shared_data_entry():
    """Test that the report contains an entry for /home/user/shared_data."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        content = f.read()

    # Check for the directory path in the report
    assert "/home/user/shared_data" in content, (
        f"Report does not contain entry for /home/user/shared_data. "
        "This directory has world-writable permissions (777) and should be listed."
    )

    # Check for proper permission string format (drwxrwxrwx)
    # The pattern should match something like "drwxrwxrwx /home/user/shared_data"
    pattern = r'drwxrwxrwx\s+/home/user/shared_data'
    assert re.search(pattern, content), (
        f"Report does not contain properly formatted entry for /home/user/shared_data. "
        "Expected format: 'drwxrwxrwx /home/user/shared_data'."
    )


def test_report_does_not_contain_normal_file():
    """Test that the report does NOT contain /home/user/normal_file.txt."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        content = f.read()

    # The normal_file.txt has permissions 644, which is NOT world-writable
    assert "/home/user/normal_file.txt" not in content, (
        f"Report incorrectly contains /home/user/normal_file.txt. "
        "This file has permissions 644 (-rw-r--r--) and is NOT world-writable, "
        "so it should NOT appear in the security audit report."
    )


def test_report_does_not_contain_private_dir():
    """Test that the report does NOT contain /home/user/private_dir."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        content = f.read()

    # The private_dir has permissions 755, which is NOT world-writable
    assert "/home/user/private_dir" not in content, (
        f"Report incorrectly contains /home/user/private_dir. "
        "This directory has permissions 755 (drwxr-xr-x) and is NOT world-writable, "
        "so it should NOT appear in the security audit report."
    )


def test_report_has_minimum_required_lines():
    """Test that the report has at least 5 lines (header + date + blank + section header + at least one item)."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        lines = f.readlines()

    assert len(lines) >= 5, (
        f"Report file has only {len(lines)} lines, but expected at least 5 lines: "
        "1) SECURITY AUDIT REPORT, 2) Date: YYYY-MM-DD, 3) blank line, "
        "4) WORLD-WRITABLE ITEMS FOUND:, 5) at least one world-writable item."
    )


def test_world_writable_items_listed_after_header():
    """Test that world-writable items are listed starting from line 5."""
    if not os.path.exists(REPORT_PATH):
        pytest.skip(f"Report file {REPORT_PATH} does not exist")

    with open(REPORT_PATH, 'r') as f:
        lines = f.readlines()

    if len(lines) < 5:
        pytest.skip("Report has fewer than 5 lines")

    # Get lines from position 4 onwards (5th line and beyond, 0-indexed)
    item_lines = [line.rstrip('\n\r') for line in lines[4:] if line.strip()]

    assert len(item_lines) >= 2, (
        f"Expected at least 2 world-writable items in the report "
        "(public_notes.txt and shared_data), but found {len(item_lines)} item(s)."
    )

    # Verify each item line has a valid permission string format
    perm_pattern = r'^[d-][rwx-]{9}\s+/'
    for item_line in item_lines:
        assert re.match(perm_pattern, item_line), (
            f"Item line '{item_line}' does not match expected format. "
            "Expected format: 'permission_string /absolute/path' "
            "(e.g., '-rw-rw-rw- /home/user/public_notes.txt')."
        )


def test_original_test_files_still_exist():
    """Test that the original test files still exist after the audit."""
    files_to_check = [
        ("/home/user/public_notes.txt", "file"),
        ("/home/user/shared_data", "directory"),
        ("/home/user/normal_file.txt", "file"),
        ("/home/user/private_dir", "directory"),
    ]

    for path, item_type in files_to_check:
        if item_type == "file":
            assert os.path.isfile(path), (
                f"File {path} no longer exists. "
                "The security audit should only report on files, not modify or delete them."
            )
        else:
            assert os.path.isdir(path), (
                f"Directory {path} no longer exists. "
                "The security audit should only report on directories, not modify or delete them."
            )