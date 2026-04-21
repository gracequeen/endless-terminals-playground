# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the documentation workspace setup task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Tests to verify the system is in the correct initial state."""

    def test_home_user_exists(self):
        """Verify /home/user directory exists."""
        home_path = "/home/user"
        assert os.path.isdir(home_path), (
            f"Directory {home_path} does not exist. "
            "The home directory must exist before starting the task."
        )

    def test_home_user_is_writable(self):
        """Verify /home/user is writable by the current user."""
        home_path = "/home/user"
        assert os.access(home_path, os.W_OK), (
            f"Directory {home_path} is not writable. "
            "The user must have write permissions to their home directory."
        )

    def test_docs_workspace_does_not_exist(self):
        """Verify /home/user/docs_workspace does not exist yet."""
        workspace_path = "/home/user/docs_workspace"
        assert not os.path.exists(workspace_path), (
            f"Directory {workspace_path} already exists. "
            "The docs_workspace directory should not exist before starting the task. "
            "Please remove it first."
        )

    def test_mkdir_available(self):
        """Verify mkdir command is available."""
        result = subprocess.run(
            ["which", "mkdir"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'mkdir' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_chmod_available(self):
        """Verify chmod command is available."""
        result = subprocess.run(
            ["which", "chmod"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'chmod' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_touch_available(self):
        """Verify touch command is available."""
        result = subprocess.run(
            ["which", "touch"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'touch' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_cat_available(self):
        """Verify cat command is available."""
        result = subprocess.run(
            ["which", "cat"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'cat' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_stat_available(self):
        """Verify stat command is available."""
        result = subprocess.run(
            ["which", "stat"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'stat' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_bash_available(self):
        """Verify bash is available at /bin/bash."""
        bash_path = "/bin/bash"
        assert os.path.isfile(bash_path), (
            f"Bash shell not found at {bash_path}. "
            "Bash must be available for the verification script."
        )
        assert os.access(bash_path, os.X_OK), (
            f"Bash at {bash_path} is not executable. "
            "Bash must be executable."
        )

    def test_user_is_not_root(self):
        """Verify the current user is not root (has normal permissions)."""
        assert os.getuid() != 0, (
            "Current user is root. "
            "The task should be performed with normal (non-root) user permissions."
        )

    def test_diff_available(self):
        """Verify diff command is available (needed for verification)."""
        result = subprocess.run(
            ["which", "diff"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'diff' command is not available. "
            "This is needed for verification purposes."
        )
