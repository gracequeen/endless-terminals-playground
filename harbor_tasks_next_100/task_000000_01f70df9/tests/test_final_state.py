# test_final_state.py
"""
Tests to validate the final state of the system after the student
has completed the timezone change task to America/Denver.
"""

import os
import subprocess
import filecmp
import pytest


class TestFinalState:
    """Validate the OS state after the timezone change task is completed."""

    def test_etc_localtime_exists(self):
        """Verify /etc/localtime still exists after the change."""
        assert os.path.exists("/etc/localtime"), (
            "/etc/localtime does not exist. "
            "This file must exist and be configured for America/Denver timezone."
        )

    def test_etc_localtime_is_denver_timezone(self):
        """
        Verify /etc/localtime is a symlink to America/Denver OR is a 
        byte-identical copy of that file.
        """
        localtime_path = "/etc/localtime"
        denver_zoneinfo = "/usr/share/zoneinfo/America/Denver"

        assert os.path.exists(denver_zoneinfo), (
            f"{denver_zoneinfo} does not exist. Cannot verify timezone configuration."
        )

        # Check if it's a symlink pointing to America/Denver
        if os.path.islink(localtime_path):
            target = os.readlink(localtime_path)
            # Resolve to absolute path if relative
            if not os.path.isabs(target):
                target = os.path.normpath(os.path.join(os.path.dirname(localtime_path), target))

            # Check if target contains America/Denver or resolves to it
            is_denver_link = (
                "America/Denver" in target or
                target == denver_zoneinfo or
                os.path.realpath(localtime_path) == os.path.realpath(denver_zoneinfo)
            )
            assert is_denver_link, (
                f"/etc/localtime is a symlink pointing to '{target}', "
                f"but it should point to /usr/share/zoneinfo/America/Denver or equivalent."
            )
        else:
            # It's a regular file - check if it's byte-identical to America/Denver
            with open(localtime_path, "rb") as f1:
                localtime_content = f1.read()
            with open(denver_zoneinfo, "rb") as f2:
                denver_content = f2.read()
            assert localtime_content == denver_content, (
                "/etc/localtime exists as a regular file but is not "
                "byte-identical to /usr/share/zoneinfo/America/Denver. "
                "The file must be a symlink to or copy of the Denver timezone file."
            )

    def test_system_timezone_is_denver(self):
        """
        Verify the system timezone outputs MST or MDT (depending on DST status).
        Uses TZ= to ensure date reads from /etc/localtime, not environment.
        """
        # Run date with TZ unset to force reading from /etc/localtime
        env_without_tz = {k: v for k, v in os.environ.items() if k != "TZ"}
        result = subprocess.run(
            ["date", "+%Z"],
            capture_output=True,
            text=True,
            env=env_without_tz
        )
        assert result.returncode == 0, (
            f"date command failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

        timezone_abbrev = result.stdout.strip()
        valid_denver_abbrevs = {"MST", "MDT"}
        assert timezone_abbrev in valid_denver_abbrevs, (
            f"System timezone abbreviation is '{timezone_abbrev}', "
            f"but expected 'MST' or 'MDT' for America/Denver timezone. "
            "The /etc/localtime file must be properly configured."
        )

    def test_america_denver_zoneinfo_unchanged(self):
        """Verify /usr/share/zoneinfo/America/Denver still exists and is a file."""
        denver_path = "/usr/share/zoneinfo/America/Denver"
        assert os.path.exists(denver_path), (
            f"{denver_path} no longer exists. "
            "The zoneinfo file should not have been deleted or moved."
        )
        assert os.path.isfile(denver_path) or os.path.islink(denver_path), (
            f"{denver_path} is not a regular file or symlink. "
            "The zoneinfo file should not have been modified."
        )

    def test_timezone_not_just_env_variable(self):
        """
        Verify the fix is in /etc/localtime, not just a TZ environment variable.
        This ensures the system default is changed, not just the shell environment.
        """
        localtime_path = "/etc/localtime"
        denver_zoneinfo = "/usr/share/zoneinfo/America/Denver"
        utc_zoneinfo = "/usr/share/zoneinfo/UTC"

        # /etc/localtime must NOT be pointing to UTC anymore
        if os.path.islink(localtime_path):
            target = os.readlink(localtime_path)
            resolved = os.path.realpath(localtime_path)
            utc_resolved = os.path.realpath(utc_zoneinfo)

            assert resolved != utc_resolved, (
                f"/etc/localtime still points to UTC ({target}). "
                "The task requires changing /etc/localtime to America/Denver, "
                "not just setting TZ environment variable."
            )
        else:
            # It's a regular file - verify it's not identical to UTC
            if os.path.exists(utc_zoneinfo):
                with open(localtime_path, "rb") as f1:
                    localtime_content = f1.read()
                with open(utc_zoneinfo, "rb") as f2:
                    utc_content = f2.read()
                assert localtime_content != utc_content, (
                    "/etc/localtime is still byte-identical to UTC timezone file. "
                    "The task requires changing /etc/localtime to America/Denver."
                )

    def test_date_output_reflects_denver_offset(self):
        """
        Additional verification: check that date output reflects Mountain Time offset.
        America/Denver is UTC-7 (MST) or UTC-6 (MDT during daylight saving).
        """
        env_without_tz = {k: v for k, v in os.environ.items() if k != "TZ"}

        # Get the timezone offset
        result = subprocess.run(
            ["date", "+%z"],
            capture_output=True,
            text=True,
            env=env_without_tz
        )
        assert result.returncode == 0, (
            f"date command failed with return code {result.returncode}."
        )

        offset = result.stdout.strip()
        # America/Denver should be -0700 (MST) or -0600 (MDT)
        valid_offsets = {"-0700", "-0600"}
        assert offset in valid_offsets, (
            f"Timezone offset is '{offset}', but expected '-0700' (MST) or '-0600' (MDT) "
            "for America/Denver timezone."
        )
