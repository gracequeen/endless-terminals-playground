# test_final_state.py
"""
Tests to validate the final state of the system after the student
has completed the timezone change task to America/Chicago.
"""

import os
import subprocess
import filecmp
import pytest


class TestFinalTimezoneState:
    """Tests to verify the system timezone has been correctly changed to America/Chicago."""

    def test_etc_localtime_exists(self):
        """Verify /etc/localtime exists."""
        assert os.path.exists("/etc/localtime"), \
            "/etc/localtime does not exist - it must be present for timezone to work"

    def test_etc_localtime_points_to_chicago_or_is_copy(self):
        """Verify /etc/localtime is a symlink to America/Chicago or a copy of it."""
        chicago_path = "/usr/share/zoneinfo/America/Chicago"
        localtime_path = "/etc/localtime"

        if os.path.islink(localtime_path):
            # It's a symlink - check where it points
            target = os.readlink(localtime_path)
            # Accept both absolute and relative paths that end up at America/Chicago
            assert "America/Chicago" in target or target.endswith("America/Chicago"), \
                f"/etc/localtime symlink should point to America/Chicago, but points to: {target}"
        else:
            # It's a regular file - should be identical to the Chicago timezone file
            assert os.path.isfile(localtime_path), \
                "/etc/localtime should be a file or symlink"
            assert filecmp.cmp(localtime_path, chicago_path, shallow=False), \
                "/etc/localtime should be identical to /usr/share/zoneinfo/America/Chicago"

    def test_etc_timezone_exists(self):
        """Verify /etc/timezone exists."""
        assert os.path.exists("/etc/timezone"), \
            "/etc/timezone does not exist - it should be present"

    def test_etc_timezone_contains_chicago(self):
        """Verify /etc/timezone contains America/Chicago."""
        with open("/etc/timezone", "r") as f:
            content = f.read().strip()
        assert content == "America/Chicago", \
            f"/etc/timezone should contain 'America/Chicago', but contains: '{content}'"

    def test_date_command_shows_chicago_timezone(self):
        """Verify date +%Z outputs CST or CDT (not UTC)."""
        # Run date in a fresh environment without TZ override
        result = subprocess.run(
            ["date", "+%Z"],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k != "TZ"}
        )
        timezone = result.stdout.strip()
        # America/Chicago uses CST (Central Standard Time) or CDT (Central Daylight Time)
        assert timezone in ("CST", "CDT"), \
            f"date +%Z should output 'CST' or 'CDT', but outputs: '{timezone}'. " \
            f"Timezone change may not have been applied correctly."

    def test_timezone_not_utc(self):
        """Verify the timezone is definitely not UTC anymore."""
        result = subprocess.run(
            ["date", "+%Z"],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k != "TZ"}
        )
        timezone = result.stdout.strip()
        assert timezone != "UTC", \
            f"Timezone is still UTC - the change was not applied correctly"

    def test_cat_etc_timezone_outputs_chicago(self):
        """Verify cat /etc/timezone outputs America/Chicago."""
        result = subprocess.run(
            ["cat", "/etc/timezone"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"cat /etc/timezone failed with return code {result.returncode}"
        content = result.stdout.strip()
        assert content == "America/Chicago", \
            f"cat /etc/timezone should output 'America/Chicago', but outputs: '{content}'"

    def test_chicago_zoneinfo_unchanged(self):
        """Verify /usr/share/zoneinfo/America/Chicago still exists and is valid."""
        chicago_path = "/usr/share/zoneinfo/America/Chicago"
        assert os.path.exists(chicago_path), \
            f"{chicago_path} should still exist"
        assert os.path.isfile(chicago_path), \
            f"{chicago_path} should be a regular file"
        # Check it has reasonable size (timezone files are typically a few KB)
        size = os.path.getsize(chicago_path)
        assert size > 100, \
            f"{chicago_path} seems too small ({size} bytes) - may be corrupted"

    def test_timezone_change_is_system_wide(self):
        """Verify the timezone change works in a fresh shell context."""
        # Use sh -c to simulate a fresh shell environment
        result = subprocess.run(
            ["sh", "-c", "date +%Z"],
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k != "TZ"}
        )
        timezone = result.stdout.strip()
        assert timezone in ("CST", "CDT"), \
            f"Timezone in fresh shell should be 'CST' or 'CDT', but is: '{timezone}'. " \
            f"The change may only be in the current session (TZ variable) not system-wide."

    def test_localtime_file_is_valid_timezone_data(self):
        """Verify /etc/localtime contains valid timezone data."""
        # Timezone files start with "TZif" magic bytes
        with open("/etc/localtime", "rb") as f:
            magic = f.read(4)
        assert magic == b"TZif", \
            f"/etc/localtime should start with 'TZif' magic bytes, but starts with: {magic}"
