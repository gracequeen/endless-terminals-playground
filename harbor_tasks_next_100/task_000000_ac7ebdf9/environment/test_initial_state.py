# test_initial_state.py
"""
Tests to validate the initial state of the OS before the student performs the cron job task.
"""

import os
import stat
import subprocess
import pytest


class TestScriptExists:
    """Tests for the metrics_push.sh script."""

    def test_script_file_exists(self):
        """Verify /home/user/scripts/metrics_push.sh exists."""
        script_path = "/home/user/scripts/metrics_push.sh"
        assert os.path.isfile(script_path), (
            f"Script file {script_path} does not exist. "
            "The metrics_push.sh script should be present before scheduling."
        )

    def test_script_is_executable(self):
        """Verify the script has executable permissions."""
        script_path = "/home/user/scripts/metrics_push.sh"
        assert os.path.isfile(script_path), f"Script {script_path} does not exist"

        file_stat = os.stat(script_path)
        is_executable = file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        assert is_executable, (
            f"Script {script_path} is not executable. "
            "Expected chmod +x to have been applied."
        )

    def test_script_content(self):
        """Verify the script contains the expected content."""
        script_path = "/home/user/scripts/metrics_push.sh"
        expected_content = '#!/bin/bash\necho "$(date -Iseconds) metrics pushed" >> /home/user/logs/metrics.log'

        with open(script_path, 'r') as f:
            actual_content = f.read().strip()

        assert actual_content == expected_content, (
            f"Script content does not match expected.\n"
            f"Expected:\n{expected_content}\n"
            f"Actual:\n{actual_content}"
        )

    def test_script_runs_manually(self):
        """Verify the script can be executed manually without errors."""
        script_path = "/home/user/scripts/metrics_push.sh"
        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"Script {script_path} failed to run manually. "
            f"Return code: {result.returncode}, stderr: {result.stderr}"
        )


class TestDirectories:
    """Tests for required directories."""

    def test_scripts_directory_exists(self):
        """Verify /home/user/scripts/ directory exists."""
        scripts_dir = "/home/user/scripts"
        assert os.path.isdir(scripts_dir), (
            f"Directory {scripts_dir} does not exist. "
            "The scripts directory should be present."
        )

    def test_scripts_directory_writable(self):
        """Verify /home/user/scripts/ is writable by user."""
        scripts_dir = "/home/user/scripts"
        assert os.access(scripts_dir, os.W_OK), (
            f"Directory {scripts_dir} is not writable. "
            "User should have write access to the scripts directory."
        )

    def test_logs_directory_exists(self):
        """Verify /home/user/logs/ directory exists."""
        logs_dir = "/home/user/logs"
        assert os.path.isdir(logs_dir), (
            f"Directory {logs_dir} does not exist. "
            "The logs directory should be present for the script to write to."
        )

    def test_logs_directory_writable(self):
        """Verify /home/user/logs/ is writable by user."""
        logs_dir = "/home/user/logs"
        assert os.access(logs_dir, os.W_OK), (
            f"Directory {logs_dir} is not writable. "
            "User should have write access to the logs directory."
        )


class TestCronService:
    """Tests for cron daemon status."""

    def test_cron_daemon_running(self):
        """Verify cron daemon is running."""
        # Try multiple common cron process names
        result = subprocess.run(
            ["pgrep", "-x", "cron"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            # Try crond (used on some systems)
            result = subprocess.run(
                ["pgrep", "-x", "crond"],
                capture_output=True,
                text=True
            )

        assert result.returncode == 0, (
            "Cron daemon is not running. "
            "The cron service must be active for scheduled jobs to execute."
        )

    def test_crontab_command_available(self):
        """Verify crontab command is available."""
        result = subprocess.run(
            ["which", "crontab"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "crontab command not found. "
            "Cron must be installed for user crontab functionality."
        )


class TestUserCrontab:
    """Tests for user crontab state."""

    def test_user_crontab_empty(self):
        """Verify user crontab is currently empty."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        # crontab -l returns non-zero if no crontab exists, or returns empty/comments only
        if result.returncode != 0:
            # No crontab for user - this is acceptable (empty state)
            assert "no crontab" in result.stderr.lower(), (
                f"Unexpected error checking crontab: {result.stderr}"
            )
        else:
            # Crontab exists - check it's empty (or only comments)
            lines = [line.strip() for line in result.stdout.strip().split('\n') 
                     if line.strip() and not line.strip().startswith('#')]
            assert len(lines) == 0, (
                f"User crontab is not empty. Found existing entries:\n{result.stdout}\n"
                "Expected the user crontab to be empty before adding the metrics job."
            )

    def test_no_metrics_push_in_crontab(self):
        """Verify metrics_push.sh is not already scheduled."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            assert "metrics_push" not in result.stdout, (
                "metrics_push.sh is already in the crontab. "
                "Expected the crontab to not contain this entry initially."
            )


class TestSystemCrontabUnmodified:
    """Tests to verify system crontabs are in expected state."""

    def test_etc_cron_d_no_metrics(self):
        """Verify no metrics-related files in /etc/cron.d/."""
        cron_d_path = "/etc/cron.d"
        if os.path.isdir(cron_d_path):
            for filename in os.listdir(cron_d_path):
                assert "metrics" not in filename.lower(), (
                    f"Found metrics-related file in /etc/cron.d/: {filename}. "
                    "System crontabs should not be modified for this task."
                )
