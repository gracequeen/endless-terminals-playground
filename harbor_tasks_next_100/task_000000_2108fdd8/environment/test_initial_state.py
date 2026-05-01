# test_initial_state.py
"""
Tests to validate the initial state of the system before the student
performs the timezone change task.
"""

import os
import subprocess
import pytest


class TestInitialTimezoneState:
    """Tests to verify the system is in the expected initial state for the timezone task."""

    def test_etc_localtime_exists(self):
        """Verify /etc/localtime exists."""
        assert os.path.exists("/etc/localtime"), \
            "/etc/localtime does not exist - it should be present"

    def test_etc_localtime_is_symlink_to_utc(self):
        """Verify /etc/localtime is a symlink pointing to UTC timezone."""
        assert os.path.islink("/etc/localtime"), \
            "/etc/localtime should be a symlink"
        target = os.readlink("/etc/localtime")
        assert "UTC" in target or "Etc/UTC" in target, \
            f"/etc/localtime should point to UTC, but points to: {target}"

    def test_etc_timezone_exists(self):
        """Verify /etc/timezone exists."""
        assert os.path.exists("/etc/timezone"), \
            "/etc/timezone does not exist - it should be present"

    def test_etc_timezone_contains_utc(self):
        """Verify /etc/timezone contains UTC."""
        with open("/etc/timezone", "r") as f:
            content = f.read().strip()
        assert content == "Etc/UTC" or content == "UTC", \
            f"/etc/timezone should contain 'Etc/UTC' or 'UTC', but contains: '{content}'"

    def test_chicago_zoneinfo_exists(self):
        """Verify the America/Chicago timezone file exists."""
        chicago_path = "/usr/share/zoneinfo/America/Chicago"
        assert os.path.exists(chicago_path), \
            f"{chicago_path} does not exist - it must be available for the task"

    def test_chicago_zoneinfo_is_file(self):
        """Verify the America/Chicago timezone is a valid file."""
        chicago_path = "/usr/share/zoneinfo/America/Chicago"
        assert os.path.isfile(chicago_path), \
            f"{chicago_path} should be a regular file"

    def test_current_timezone_is_utc(self):
        """Verify the current system timezone is UTC."""
        result = subprocess.run(
            ["date", "+%Z"],
            capture_output=True,
            text=True
        )
        timezone = result.stdout.strip()
        assert timezone == "UTC", \
            f"Current timezone should be 'UTC', but is: '{timezone}'"

    def test_tz_environment_not_set(self):
        """Verify TZ environment variable is not set."""
        tz_value = os.environ.get("TZ")
        assert tz_value is None, \
            f"TZ environment variable should not be set, but is set to: '{tz_value}'"

    def test_etc_localtime_is_writable(self):
        """Verify /etc/localtime can be modified."""
        # Check if we can write to /etc directory (needed to replace symlink)
        assert os.access("/etc", os.W_OK), \
            "/etc directory is not writable - cannot modify /etc/localtime"

    def test_etc_timezone_is_writable(self):
        """Verify /etc/timezone is writable."""
        assert os.access("/etc/timezone", os.W_OK), \
            "/etc/timezone is not writable"

    def test_ln_command_available(self):
        """Verify the ln command is available."""
        result = subprocess.run(
            ["which", "ln"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "ln command is not available"

    def test_date_command_available(self):
        """Verify the date command is available."""
        result = subprocess.run(
            ["which", "date"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "date command is not available"

    def test_timedatectl_available(self):
        """Verify timedatectl is available (even if it won't work without systemd)."""
        result = subprocess.run(
            ["which", "timedatectl"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "timedatectl command is not available"

    def test_zoneinfo_directory_exists(self):
        """Verify /usr/share/zoneinfo directory exists."""
        assert os.path.isdir("/usr/share/zoneinfo"), \
            "/usr/share/zoneinfo directory does not exist"
