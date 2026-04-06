# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student
performs the security audit task.
"""

import os
import stat
import pytest


HOME_DIR = "/home/user"


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


def test_home_directory_exists():
    """Test that the home directory exists."""
    assert os.path.isdir(HOME_DIR), f"Home directory {HOME_DIR} does not exist"


def test_public_notes_file_exists():
    """Test that public_notes.txt exists."""
    filepath = os.path.join(HOME_DIR, "public_notes.txt")
    assert os.path.isfile(filepath), (
        f"File {filepath} does not exist. "
        "This file should be created with world-writable permissions (666) for the security audit task."
    )


def test_public_notes_has_world_writable_permissions():
    """Test that public_notes.txt has permissions 666 (-rw-rw-rw-)."""
    filepath = os.path.join(HOME_DIR, "public_notes.txt")
    if not os.path.exists(filepath):
        pytest.skip(f"File {filepath} does not exist")

    mode = os.stat(filepath).st_mode
    perm_string = get_permission_string(mode)

    # Check for 666 permissions (rw-rw-rw-)
    expected_perms = 0o666
    actual_perms = stat.S_IMODE(mode)

    assert actual_perms == expected_perms, (
        f"File {filepath} has permissions {oct(actual_perms)} ({perm_string}), "
        f"but expected 0o666 (-rw-rw-rw-). "
        "This file should be world-writable for the security audit to find it."
    )


def test_shared_data_directory_exists():
    """Test that shared_data directory exists."""
    dirpath = os.path.join(HOME_DIR, "shared_data")
    assert os.path.isdir(dirpath), (
        f"Directory {dirpath} does not exist. "
        "This directory should be created with world-writable permissions (777) for the security audit task."
    )


def test_shared_data_has_world_writable_permissions():
    """Test that shared_data directory has permissions 777 (drwxrwxrwx)."""
    dirpath = os.path.join(HOME_DIR, "shared_data")
    if not os.path.exists(dirpath):
        pytest.skip(f"Directory {dirpath} does not exist")

    mode = os.stat(dirpath).st_mode
    perm_string = get_permission_string(mode)

    # Check for 777 permissions (rwxrwxrwx)
    expected_perms = 0o777
    actual_perms = stat.S_IMODE(mode)

    assert actual_perms == expected_perms, (
        f"Directory {dirpath} has permissions {oct(actual_perms)} ({perm_string}), "
        f"but expected 0o777 (drwxrwxrwx). "
        "This directory should be world-writable for the security audit to find it."
    )


def test_normal_file_exists():
    """Test that normal_file.txt exists."""
    filepath = os.path.join(HOME_DIR, "normal_file.txt")
    assert os.path.isfile(filepath), (
        f"File {filepath} does not exist. "
        "This file should be created with permissions 644 (-rw-r--r--) as a control file "
        "that should NOT appear in the security audit report."
    )


def test_normal_file_has_correct_permissions():
    """Test that normal_file.txt has permissions 644 (-rw-r--r--)."""
    filepath = os.path.join(HOME_DIR, "normal_file.txt")
    if not os.path.exists(filepath):
        pytest.skip(f"File {filepath} does not exist")

    mode = os.stat(filepath).st_mode
    perm_string = get_permission_string(mode)

    # Check for 644 permissions (rw-r--r--)
    expected_perms = 0o644
    actual_perms = stat.S_IMODE(mode)

    assert actual_perms == expected_perms, (
        f"File {filepath} has permissions {oct(actual_perms)} ({perm_string}), "
        f"but expected 0o644 (-rw-r--r--). "
        "This file should NOT be world-writable (it's a control file)."
    )


def test_private_dir_exists():
    """Test that private_dir directory exists."""
    dirpath = os.path.join(HOME_DIR, "private_dir")
    assert os.path.isdir(dirpath), (
        f"Directory {dirpath} does not exist. "
        "This directory should be created with permissions 755 (drwxr-xr-x) as a control directory "
        "that should NOT appear in the security audit report."
    )


def test_private_dir_has_correct_permissions():
    """Test that private_dir has permissions 755 (drwxr-xr-x)."""
    dirpath = os.path.join(HOME_DIR, "private_dir")
    if not os.path.exists(dirpath):
        pytest.skip(f"Directory {dirpath} does not exist")

    mode = os.stat(dirpath).st_mode
    perm_string = get_permission_string(mode)

    # Check for 755 permissions (rwxr-xr-x)
    expected_perms = 0o755
    actual_perms = stat.S_IMODE(mode)

    assert actual_perms == expected_perms, (
        f"Directory {dirpath} has permissions {oct(actual_perms)} ({perm_string}), "
        f"but expected 0o755 (drwxr-xr-x). "
        "This directory should NOT be world-writable (it's a control directory)."
    )


def test_security_audit_report_does_not_exist_yet():
    """Test that the output file does not exist yet (student needs to create it)."""
    filepath = os.path.join(HOME_DIR, "security_audit_report.txt")
    assert not os.path.exists(filepath), (
        f"File {filepath} already exists. "
        "This is the output file that the student should create as part of the task. "
        "It should not exist before the task begins."
    )