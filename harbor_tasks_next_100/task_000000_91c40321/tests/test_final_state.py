# test_final_state.py
"""
Tests to validate the final state after the student has applied the patch.
"""

import os
import pytest


class TestFinalState:
    """Validate the operating system state after the patch is applied."""

    def test_config_py_exists(self):
        """Verify /home/user/project/src/config.py still exists."""
        config_file = "/home/user/project/src/config.py"
        assert os.path.isfile(config_file), f"Config file {config_file} does not exist"

    def test_config_py_has_debug_true(self):
        """Verify config.py has DEBUG = True on the first line (patch applied)."""
        config_file = "/home/user/project/src/config.py"
        with open(config_file, 'r') as f:
            first_line = f.readline().strip()

        assert first_line == "DEBUG = True", (
            f"First line of config.py should be 'DEBUG = True' after patch, "
            f"but got '{first_line}'. The patch was not applied correctly."
        )

    def test_config_py_line2_unchanged(self):
        """Verify line 2 of config.py is unchanged (MAX_CONNECTIONS = 100)."""
        config_file = "/home/user/project/src/config.py"
        with open(config_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 2, f"Config file should have at least 2 lines, got {len(lines)}"
        line2 = lines[1].strip()
        assert line2 == "MAX_CONNECTIONS = 100", (
            f"Line 2 should be 'MAX_CONNECTIONS = 100' but got '{line2}'"
        )

    def test_config_py_line3_unchanged(self):
        """Verify line 3 of config.py is unchanged (TIMEOUT = 30)."""
        config_file = "/home/user/project/src/config.py"
        with open(config_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 3, f"Config file should have at least 3 lines, got {len(lines)}"
        line3 = lines[2].strip()
        assert line3 == "TIMEOUT = 30", (
            f"Line 3 should be 'TIMEOUT = 30' but got '{line3}'"
        )

    def test_config_py_line4_unchanged(self):
        """Verify line 4 of config.py is unchanged (LOG_LEVEL = "INFO")."""
        config_file = "/home/user/project/src/config.py"
        with open(config_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 4, f"Config file should have at least 4 lines, got {len(lines)}"
        line4 = lines[3].strip()
        assert line4 == 'LOG_LEVEL = "INFO"', (
            f'Line 4 should be \'LOG_LEVEL = "INFO"\' but got \'{line4}\''
        )

    def test_config_py_full_content(self):
        """Verify /home/user/project/src/config.py has the expected final content."""
        config_file = "/home/user/project/src/config.py"
        expected_content = '''DEBUG = True
MAX_CONNECTIONS = 100
TIMEOUT = 30
LOG_LEVEL = "INFO"
'''
        with open(config_file, 'r') as f:
            actual_content = f.read()

        assert actual_content == expected_content, (
            f"Config file content does not match expected final state.\n"
            f"Expected:\n{expected_content}\n"
            f"Actual:\n{actual_content}\n"
            f"The patch may not have been applied correctly."
        )

    def test_patch_file_unchanged(self):
        """Verify /home/user/project/changes.patch is unchanged (invariant)."""
        patch_file = "/home/user/project/changes.patch"
        assert os.path.isfile(patch_file), f"Patch file {patch_file} should still exist"

        expected_content = '''--- src/config.py	2024-01-15 10:00:00.000000000 +0000
+++ src/config.py	2024-01-15 10:05:00.000000000 +0000
@@ -1,4 +1,4 @@
-DEBUG = False
+DEBUG = True
 MAX_CONNECTIONS = 100
 TIMEOUT = 30
 LOG_LEVEL = "INFO"
'''
        with open(patch_file, 'r') as f:
            actual_content = f.read()

        assert actual_content == expected_content, (
            f"Patch file should remain unchanged.\n"
            f"Expected:\n{expected_content}\n"
            f"Actual:\n{actual_content}"
        )

    def test_no_reject_files(self):
        """Verify no .rej files were created (indicating failed patch hunks)."""
        src_dir = "/home/user/project/src"
        project_dir = "/home/user/project"

        for directory in [src_dir, project_dir]:
            if os.path.isdir(directory):
                for filename in os.listdir(directory):
                    assert not filename.endswith('.rej'), (
                        f"Found reject file {os.path.join(directory, filename)} - "
                        f"patch was not applied cleanly"
                    )

    def test_no_orig_files(self):
        """Verify no .orig backup files were left behind (or if they exist, original was patched)."""
        config_orig = "/home/user/project/src/config.py.orig"
        # .orig files are acceptable as they're just backups, but we should verify
        # the main file was patched regardless
        config_file = "/home/user/project/src/config.py"
        with open(config_file, 'r') as f:
            content = f.read()

        assert "DEBUG = True" in content, (
            "config.py should contain 'DEBUG = True' after patch application"
        )
