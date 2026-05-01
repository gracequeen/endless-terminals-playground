# test_initial_state.py
"""
Tests to validate the initial state before the student applies the patch.
"""

import os
import pytest
import subprocess


class TestInitialState:
    """Validate the operating system state before the patch is applied."""

    def test_project_directory_exists(self):
        """Verify /home/user/project directory exists."""
        project_dir = "/home/user/project"
        assert os.path.isdir(project_dir), f"Project directory {project_dir} does not exist"

    def test_src_directory_exists(self):
        """Verify /home/user/project/src directory exists."""
        src_dir = "/home/user/project/src"
        assert os.path.isdir(src_dir), f"Source directory {src_dir} does not exist"

    def test_config_py_exists(self):
        """Verify /home/user/project/src/config.py exists."""
        config_file = "/home/user/project/src/config.py"
        assert os.path.isfile(config_file), f"Config file {config_file} does not exist"

    def test_config_py_content(self):
        """Verify /home/user/project/src/config.py has the expected initial content."""
        config_file = "/home/user/project/src/config.py"
        expected_content = '''DEBUG = False
MAX_CONNECTIONS = 100
TIMEOUT = 30
LOG_LEVEL = "INFO"
'''
        with open(config_file, 'r') as f:
            actual_content = f.read()

        assert actual_content == expected_content, (
            f"Config file content does not match expected.\n"
            f"Expected:\n{expected_content}\n"
            f"Actual:\n{actual_content}"
        )

    def test_config_py_has_debug_false(self):
        """Verify config.py has DEBUG = False (initial state before patch)."""
        config_file = "/home/user/project/src/config.py"
        with open(config_file, 'r') as f:
            first_line = f.readline().strip()

        assert first_line == "DEBUG = False", (
            f"First line of config.py should be 'DEBUG = False' but got '{first_line}'"
        )

    def test_patch_file_exists(self):
        """Verify /home/user/project/changes.patch exists."""
        patch_file = "/home/user/project/changes.patch"
        assert os.path.isfile(patch_file), f"Patch file {patch_file} does not exist"

    def test_patch_file_content(self):
        """Verify /home/user/project/changes.patch has the expected content."""
        patch_file = "/home/user/project/changes.patch"
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
            f"Patch file content does not match expected.\n"
            f"Expected:\n{expected_content}\n"
            f"Actual:\n{actual_content}"
        )

    def test_patch_has_src_prefix_in_paths(self):
        """Verify the patch file has paths starting with src/ (the cause of the issue)."""
        patch_file = "/home/user/project/changes.patch"
        with open(patch_file, 'r') as f:
            content = f.read()

        assert "--- src/config.py" in content, (
            "Patch file should have '--- src/config.py' path prefix"
        )
        assert "+++ src/config.py" in content, (
            "Patch file should have '+++ src/config.py' path prefix"
        )

    def test_patch_command_available(self):
        """Verify the patch command is available."""
        result = subprocess.run(
            ["which", "patch"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "patch command is not available"

    def test_diff_command_available(self):
        """Verify the diff command is available."""
        result = subprocess.run(
            ["which", "diff"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "diff command is not available"

    def test_project_directory_writable(self):
        """Verify /home/user/project is writable."""
        project_dir = "/home/user/project"
        assert os.access(project_dir, os.W_OK), f"Project directory {project_dir} is not writable"

    def test_src_directory_writable(self):
        """Verify /home/user/project/src is writable."""
        src_dir = "/home/user/project/src"
        assert os.access(src_dir, os.W_OK), f"Source directory {src_dir} is not writable"

    def test_config_py_writable(self):
        """Verify /home/user/project/src/config.py is writable."""
        config_file = "/home/user/project/src/config.py"
        assert os.access(config_file, os.W_OK), f"Config file {config_file} is not writable"
