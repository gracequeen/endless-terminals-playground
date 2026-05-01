# test_final_state.py
"""
Tests to validate the final state of the OS after the student has completed the cron job task.
Verifies that a user crontab entry exists to run /home/user/scripts/metrics_push.sh every 15 minutes.
"""

import os
import stat
import subprocess
import re
import pytest


class TestUserCrontabConfigured:
    """Tests for the user crontab configuration."""

    def test_crontab_has_entries(self):
        """Verify user crontab exists and has entries."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"User crontab does not exist or cannot be read. "
            f"stderr: {result.stderr}\n"
            "Expected a user crontab with the metrics_push.sh job scheduled."
        )

        # Filter out empty lines and comments
        lines = [line.strip() for line in result.stdout.strip().split('\n') 
                 if line.strip() and not line.strip().startswith('#')]
        assert len(lines) > 0, (
            "User crontab is empty (no non-comment entries). "
            "Expected a cron entry for metrics_push.sh every 15 minutes."
        )

    def test_metrics_push_in_crontab(self):
        """Verify metrics_push.sh is referenced in the crontab."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read crontab: {result.stderr}"

        assert "metrics_push.sh" in result.stdout, (
            f"metrics_push.sh not found in user crontab.\n"
            f"Current crontab contents:\n{result.stdout}\n"
            "Expected the crontab to contain an entry for metrics_push.sh"
        )

    def test_absolute_path_in_crontab(self):
        """Verify the crontab uses the absolute path to the script."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read crontab: {result.stderr}"

        assert "/home/user/scripts/metrics_push.sh" in result.stdout, (
            f"Absolute path /home/user/scripts/metrics_push.sh not found in crontab.\n"
            f"Current crontab contents:\n{result.stdout}\n"
            "Expected the crontab to use the full absolute path to the script."
        )

    def test_every_15_minutes_schedule(self):
        """Verify the cron schedule is every 15 minutes."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read crontab: {result.stderr}"

        crontab_content = result.stdout

        # Check for */15 * * * * pattern
        pattern_star_15 = r'\*/15\s+\*\s+\*\s+\*\s+\*'
        # Check for 0,15,30,45 * * * * pattern (equivalent)
        pattern_explicit = r'0,15,30,45\s+\*\s+\*\s+\*\s+\*'

        has_valid_schedule = (
            re.search(pattern_star_15, crontab_content) is not None or
            re.search(pattern_explicit, crontab_content) is not None
        )

        assert has_valid_schedule, (
            f"Cron schedule for every 15 minutes not found.\n"
            f"Expected '*/15 * * * *' or '0,15,30,45 * * * *'\n"
            f"Current crontab contents:\n{crontab_content}"
        )

    def test_schedule_and_script_on_same_line(self):
        """Verify the 15-minute schedule and metrics_push.sh are on the same cron line."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read crontab: {result.stderr}"

        # Use grep with extended regex to find both schedule and script
        grep_result = subprocess.run(
            ["grep", "-E", r"(\*/15|\b0,15,30,45\b).*metrics_push\.sh"],
            input=result.stdout,
            capture_output=True,
            text=True
        )

        assert grep_result.returncode == 0, (
            f"Could not find a crontab entry with both the 15-minute schedule "
            f"and metrics_push.sh on the same line.\n"
            f"Current crontab contents:\n{result.stdout}\n"
            "Expected a line like: */15 * * * * /home/user/scripts/metrics_push.sh"
        )

    def test_valid_crontab_entry_format(self):
        """Verify the crontab entry has valid format (5 time fields + command)."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read crontab: {result.stderr}"

        # Find lines containing metrics_push.sh
        for line in result.stdout.split('\n'):
            if 'metrics_push.sh' in line and not line.strip().startswith('#'):
                # Should have at least 6 fields (5 time fields + command)
                parts = line.split()
                assert len(parts) >= 6, (
                    f"Invalid crontab entry format. Expected at least 6 fields "
                    f"(5 time fields + command), got {len(parts)}.\n"
                    f"Line: {line}"
                )
                break


class TestScriptUnmodified:
    """Tests to verify the script remains unchanged."""

    def test_script_still_exists(self):
        """Verify /home/user/scripts/metrics_push.sh still exists."""
        script_path = "/home/user/scripts/metrics_push.sh"
        assert os.path.isfile(script_path), (
            f"Script file {script_path} no longer exists. "
            "The script should not be deleted or moved."
        )

    def test_script_content_unchanged(self):
        """Verify the script content is byte-identical to initial state."""
        script_path = "/home/user/scripts/metrics_push.sh"
        expected_content = '#!/bin/bash\necho "$(date -Iseconds) metrics pushed" >> /home/user/logs/metrics.log'

        with open(script_path, 'r') as f:
            actual_content = f.read().strip()

        assert actual_content == expected_content, (
            f"Script content has been modified.\n"
            f"Expected:\n{expected_content}\n"
            f"Actual:\n{actual_content}\n"
            "The script should remain unchanged."
        )

    def test_script_still_executable(self):
        """Verify the script is still executable."""
        script_path = "/home/user/scripts/metrics_push.sh"
        file_stat = os.stat(script_path)
        is_executable = file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        assert is_executable, (
            f"Script {script_path} is no longer executable. "
            "The script permissions should not be changed."
        )


class TestSystemCrontabsUnmodified:
    """Tests to verify system-wide crontabs were not modified."""

    def test_no_metrics_in_etc_cron_d(self):
        """Verify no metrics-related files were added to /etc/cron.d/."""
        cron_d_path = "/etc/cron.d"
        if os.path.isdir(cron_d_path):
            for filename in os.listdir(cron_d_path):
                filepath = os.path.join(cron_d_path, filename)
                if os.path.isfile(filepath):
                    # Check filename
                    assert "metrics" not in filename.lower(), (
                        f"Found metrics-related file in /etc/cron.d/: {filename}. "
                        "Task requires using user crontab, not system crontabs."
                    )
                    # Also check file contents
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        assert "metrics_push.sh" not in content, (
                            f"Found metrics_push.sh reference in /etc/cron.d/{filename}. "
                            "Task requires using user crontab, not system crontabs."
                        )
                    except (IOError, PermissionError):
                        pass  # Skip files we can't read

    def test_etc_crontab_no_metrics(self):
        """Verify /etc/crontab was not modified to include metrics_push.sh."""
        etc_crontab = "/etc/crontab"
        if os.path.isfile(etc_crontab):
            try:
                with open(etc_crontab, 'r') as f:
                    content = f.read()
                assert "metrics_push" not in content, (
                    f"Found metrics_push reference in /etc/crontab. "
                    "Task requires using user crontab, not system crontab."
                )
            except (IOError, PermissionError):
                pass  # Skip if we can't read


class TestCronServiceStillRunning:
    """Tests to verify cron service is still operational."""

    def test_cron_daemon_running(self):
        """Verify cron daemon is still running."""
        result = subprocess.run(
            ["pgrep", "-x", "cron"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["pgrep", "-x", "crond"],
                capture_output=True,
                text=True
            )

        assert result.returncode == 0, (
            "Cron daemon is not running. "
            "The cron service must remain active for scheduled jobs to execute."
        )
