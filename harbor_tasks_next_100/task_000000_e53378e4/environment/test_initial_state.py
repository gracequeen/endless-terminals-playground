# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the crontab scheduling task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the student performs the task."""

    def test_etl_directory_exists(self):
        """Verify /home/user/etl directory exists."""
        etl_dir = "/home/user/etl"
        assert os.path.isdir(etl_dir), f"Directory {etl_dir} does not exist"

    def test_daily_ingest_script_exists(self):
        """Verify /home/user/etl/daily_ingest.sh exists."""
        script_path = "/home/user/etl/daily_ingest.sh"
        assert os.path.isfile(script_path), f"Script {script_path} does not exist"

    def test_daily_ingest_script_is_executable(self):
        """Verify /home/user/etl/daily_ingest.sh is executable."""
        script_path = "/home/user/etl/daily_ingest.sh"
        assert os.access(script_path, os.X_OK), f"Script {script_path} is not executable"

    def test_daily_ingest_script_content(self):
        """Verify the script contains expected content (echoes timestamp and 'ingest complete')."""
        script_path = "/home/user/etl/daily_ingest.sh"
        with open(script_path, 'r') as f:
            content = f.read()
        # Check that it's a shell script with echo statements
        assert "ingest complete" in content.lower() or "ingest" in content.lower(), \
            f"Script {script_path} does not contain expected 'ingest complete' output"

    def test_logs_directory_exists(self):
        """Verify /home/user/etl/logs directory exists."""
        logs_dir = "/home/user/etl/logs"
        assert os.path.isdir(logs_dir), f"Directory {logs_dir} does not exist"

    def test_logs_directory_is_writable(self):
        """Verify /home/user/etl/logs directory is writable."""
        logs_dir = "/home/user/etl/logs"
        assert os.access(logs_dir, os.W_OK), f"Directory {logs_dir} is not writable"

    def test_cron_log_does_not_exist_initially(self):
        """Verify /home/user/etl/logs/cron.log does not exist initially."""
        cron_log = "/home/user/etl/logs/cron.log"
        assert not os.path.exists(cron_log), \
            f"File {cron_log} should not exist initially but it does"

    def test_cron_daemon_is_running(self):
        """Verify cron daemon is installed and running."""
        # Try to find cron process - could be 'cron' or 'crond' depending on distro
        result = subprocess.run(
            ["pgrep", "-x", "cron"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            # Try crond (used on some systems like CentOS/RHEL)
            result = subprocess.run(
                ["pgrep", "-x", "crond"],
                capture_output=True,
                text=True
            )

        assert result.returncode == 0, \
            "Cron daemon is not running. Expected 'cron' or 'crond' process to be active."

    def test_user_crontab_is_empty(self):
        """Verify user crontab for 'user' is empty initially."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        # crontab -l returns non-zero if no crontab exists, or returns empty/comment-only content
        if result.returncode != 0:
            # "no crontab for user" message indicates empty crontab - this is expected
            assert "no crontab" in result.stderr.lower(), \
                f"Unexpected error checking crontab: {result.stderr}"
        else:
            # If it returns successfully, the content should be empty or only comments
            content = result.stdout.strip()
            # Filter out comment lines and empty lines
            non_comment_lines = [
                line for line in content.split('\n')
                if line.strip() and not line.strip().startswith('#')
            ]
            assert len(non_comment_lines) == 0, \
                f"User crontab should be empty initially, but found entries: {non_comment_lines}"

    def test_no_existing_daily_ingest_cron_entry(self):
        """Verify there's no existing cron entry for daily_ingest.sh."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Check that daily_ingest.sh is not already scheduled
            assert "daily_ingest.sh" not in result.stdout, \
                "A cron entry for daily_ingest.sh already exists - should not be present initially"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
