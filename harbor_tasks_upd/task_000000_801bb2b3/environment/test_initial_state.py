# test_initial_state.py
"""
Tests to validate the initial state of the system before the student creates
the diskmon.sh script.
"""

import os
import subprocess
import pytest


class TestDirectoryStructure:
    """Test that required directories exist and have correct permissions."""

    def test_bin_directory_exists(self):
        """Verify /home/user/bin/ directory exists."""
        bin_dir = "/home/user/bin"
        assert os.path.isdir(bin_dir), (
            f"Directory {bin_dir} does not exist. "
            "The bin directory must exist before creating the script."
        )

    def test_bin_directory_is_writable(self):
        """Verify /home/user/bin/ directory is writable."""
        bin_dir = "/home/user/bin"
        assert os.access(bin_dir, os.W_OK), (
            f"Directory {bin_dir} is not writable. "
            "You need write permissions to create the script."
        )


class TestScriptDoesNotExist:
    """Test that the target script does not already exist."""

    def test_diskmon_script_does_not_exist(self):
        """Verify /home/user/bin/diskmon.sh does not exist yet."""
        script_path = "/home/user/bin/diskmon.sh"
        assert not os.path.exists(script_path), (
            f"Script {script_path} already exists. "
            "The initial state requires this file to not exist."
        )


class TestCoreutilsAvailable:
    """Test that required coreutils are available."""

    def test_df_command_available(self):
        """Verify df command is available."""
        result = subprocess.run(
            ["which", "df"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'df' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_awk_command_available(self):
        """Verify awk command is available."""
        result = subprocess.run(
            ["which", "awk"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'awk' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_grep_command_available(self):
        """Verify grep command is available."""
        result = subprocess.run(
            ["which", "grep"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'grep' command is not available. "
            "Standard coreutils must be installed."
        )

    def test_bash_available(self):
        """Verify bash is available for script execution."""
        result = subprocess.run(
            ["which", "bash"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'bash' shell is not available. "
            "Bash must be installed to run the script."
        )


class TestFilesystemsMounted:
    """Test that the system has mounted filesystems to check."""

    def test_at_least_one_filesystem_mounted(self):
        """Verify at least one filesystem is mounted."""
        result = subprocess.run(
            ["df", "-P"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'df' command failed to execute. "
            "Cannot verify mounted filesystems."
        )

        # df -P output has header line, so we need at least 2 lines
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 2, (
            "No mounted filesystems found. "
            "At least one filesystem must be mounted for the script to check."
        )

    def test_root_filesystem_mounted(self):
        """Verify root filesystem (/) is mounted."""
        result = subprocess.run(
            ["df", "-P", "/"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Cannot check root filesystem. "
            "The root filesystem (/) must be mounted."
        )

        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 2, (
            "Root filesystem (/) does not appear in df output. "
            "The root filesystem must be mounted."
        )

    def test_df_produces_parseable_output(self):
        """Verify df produces output that can be parsed for usage percentage."""
        result = subprocess.run(
            ["df", "-P"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "df command failed"

        lines = result.stdout.strip().split('\n')
        # Skip header, check at least one data line has percentage
        found_percentage = False
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 5:
                # The 5th column should be the usage percentage (e.g., "45%")
                usage = parts[4]
                if '%' in usage:
                    found_percentage = True
                    break

        assert found_percentage, (
            "df output does not contain parseable usage percentages. "
            "The df -P output must include usage percentage column."
        )
