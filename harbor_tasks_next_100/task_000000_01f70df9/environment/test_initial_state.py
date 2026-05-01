# test_initial_state.py
"""
Tests to validate the initial state of the system before the student
performs the timezone change task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the OS state before the timezone change task."""

    def test_etc_localtime_exists(self):
        """Verify /etc/localtime exists."""
        assert os.path.exists("/etc/localtime"), (
            "/etc/localtime does not exist. "
            "This file must exist for the timezone task."
        )

    def test_etc_localtime_points_to_utc(self):
        """Verify /etc/localtime is a symlink to UTC or is a copy of UTC zone file."""
        localtime_path = "/etc/localtime"
        utc_zoneinfo = "/usr/share/zoneinfo/UTC"

        # Check if it's a symlink pointing to UTC
        if os.path.islink(localtime_path):
            target = os.readlink(localtime_path)
            # The symlink might be absolute or relative
            assert "UTC" in target or target.endswith("Etc/UTC"), (
                f"/etc/localtime is a symlink but points to '{target}', "
                f"expected it to point to UTC timezone file."
            )
        else:
            # It's a regular file - check if it's byte-identical to UTC
            assert os.path.exists(utc_zoneinfo), (
                f"{utc_zoneinfo} does not exist to compare against."
            )
            with open(localtime_path, "rb") as f1:
                localtime_content = f1.read()
            with open(utc_zoneinfo, "rb") as f2:
                utc_content = f2.read()
            assert localtime_content == utc_content, (
                "/etc/localtime exists as a regular file but is not "
                "byte-identical to /usr/share/zoneinfo/UTC."
            )

    def test_america_denver_zoneinfo_exists(self):
        """Verify /usr/share/zoneinfo/America/Denver exists."""
        denver_path = "/usr/share/zoneinfo/America/Denver"
        assert os.path.exists(denver_path), (
            f"{denver_path} does not exist. "
            "The America/Denver timezone file is required for this task."
        )
        assert os.path.isfile(denver_path), (
            f"{denver_path} exists but is not a regular file."
        )

    def test_etc_localtime_is_writable(self):
        """Verify /etc/localtime is writable by the current user."""
        localtime_path = "/etc/localtime"
        # Check if we can write to it (or its parent directory if it's a symlink)
        assert os.access(localtime_path, os.W_OK) or os.access("/etc", os.W_OK), (
            "/etc/localtime is not writable by the current user. "
            "The agent needs write access to complete the task."
        )

    def test_etc_timezone_exists_and_contains_utc(self):
        """Verify /etc/timezone exists and contains 'UTC'."""
        timezone_path = "/etc/timezone"
        assert os.path.exists(timezone_path), (
            f"{timezone_path} does not exist. "
            "This file should exist and contain 'UTC'."
        )
        with open(timezone_path, "r") as f:
            content = f.read().strip()
        assert content == "UTC", (
            f"/etc/timezone contains '{content}', expected 'UTC'."
        )

    def test_etc_timezone_is_writable(self):
        """Verify /etc/timezone is writable by the current user."""
        timezone_path = "/etc/timezone"
        if os.path.exists(timezone_path):
            assert os.access(timezone_path, os.W_OK), (
                "/etc/timezone is not writable by the current user."
            )

    def test_tz_environment_variable_unset(self):
        """Verify TZ environment variable is not set."""
        tz_value = os.environ.get("TZ")
        assert tz_value is None, (
            f"TZ environment variable is set to '{tz_value}'. "
            "It should be unset for this task."
        )

    def test_timedatectl_not_available(self):
        """Verify timedatectl is NOT available (no systemd)."""
        result = subprocess.run(
            ["which", "timedatectl"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "timedatectl is available on this system. "
            "This task expects a non-systemd environment where timedatectl is not available."
        )

    def test_ln_command_available(self):
        """Verify ln command is available."""
        result = subprocess.run(
            ["which", "ln"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "ln command is not available. "
            "Standard tools (ln, cp, cat, date, readlink) should be available."
        )

    def test_cp_command_available(self):
        """Verify cp command is available."""
        result = subprocess.run(
            ["which", "cp"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "cp command is not available. "
            "Standard tools (ln, cp, cat, date, readlink) should be available."
        )

    def test_date_command_available(self):
        """Verify date command is available."""
        result = subprocess.run(
            ["which", "date"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "date command is not available. "
            "Standard tools (ln, cp, cat, date, readlink) should be available."
        )

    def test_readlink_command_available(self):
        """Verify readlink command is available."""
        result = subprocess.run(
            ["which", "readlink"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "readlink command is not available. "
            "Standard tools (ln, cp, cat, date, readlink) should be available."
        )

    def test_current_timezone_is_utc(self):
        """Verify the current system timezone is UTC."""
        # Use TZ= to ensure we read from /etc/localtime, not environment
        result = subprocess.run(
            ["date", "+%Z"],
            capture_output=True,
            text=True,
            env={**os.environ, "TZ": ""}
        )
        # Remove TZ from env to read /etc/localtime
        env_without_tz = {k: v for k, v in os.environ.items() if k != "TZ"}
        result = subprocess.run(
            ["date", "+%Z"],
            capture_output=True,
            text=True,
            env=env_without_tz
        )
        timezone_abbrev = result.stdout.strip()
        assert timezone_abbrev == "UTC", (
            f"Current system timezone is '{timezone_abbrev}', expected 'UTC'. "
            "The initial state should have UTC as the system timezone."
        )
