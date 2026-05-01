# test_initial_state.py
"""
Tests to validate the initial state before the student performs the cron job commenting task.
"""

import os
import pytest


CRONTAB_PATH = "/var/spool/cron/crontabs/user"


class TestCrontabFileExists:
    """Test that the crontab file exists and is accessible."""

    def test_crontab_file_exists(self):
        """The crontab file must exist at the expected path."""
        assert os.path.exists(CRONTAB_PATH), (
            f"Crontab file does not exist at {CRONTAB_PATH}. "
            "The file must be present before the task can be performed."
        )

    def test_crontab_file_is_regular_file(self):
        """The crontab path must be a regular file, not a directory or symlink."""
        assert os.path.isfile(CRONTAB_PATH), (
            f"{CRONTAB_PATH} exists but is not a regular file. "
            "It must be a regular file containing cron job definitions."
        )

    def test_crontab_file_is_writable(self):
        """The crontab file must be writable by the current user/agent."""
        assert os.access(CRONTAB_PATH, os.W_OK), (
            f"{CRONTAB_PATH} is not writable. "
            "The agent must have write permissions to modify the crontab."
        )

    def test_crontab_file_is_readable(self):
        """The crontab file must be readable."""
        assert os.access(CRONTAB_PATH, os.R_OK), (
            f"{CRONTAB_PATH} is not readable. "
            "The agent must have read permissions to view the crontab contents."
        )


class TestCrontabContents:
    """Test that the crontab file has the expected initial contents."""

    @pytest.fixture
    def crontab_contents(self):
        """Read and return the crontab file contents."""
        with open(CRONTAB_PATH, 'r') as f:
            return f.read()

    @pytest.fixture
    def crontab_lines(self, crontab_contents):
        """Return non-empty lines from the crontab."""
        return [line for line in crontab_contents.splitlines() if line.strip()]

    def test_backup_job_exists(self, crontab_contents):
        """The backup.sh cron job must exist in the crontab."""
        assert "backup.sh" in crontab_contents, (
            "The backup.sh job is not found in the crontab. "
            "Expected a line containing '/home/user/scripts/backup.sh'."
        )

    def test_backup_job_is_uncommented(self, crontab_contents):
        """The backup.sh job must be uncommented (active) initially."""
        lines = crontab_contents.splitlines()
        backup_lines = [line for line in lines if "backup.sh" in line]

        assert len(backup_lines) > 0, "No backup.sh line found in crontab."

        # Check that at least one backup.sh line is uncommented
        uncommented_backup = [line for line in backup_lines 
                             if not line.strip().startswith('#')]
        assert len(uncommented_backup) > 0, (
            "The backup.sh job is already commented out. "
            "Initial state requires the backup job to be active (uncommented)."
        )

    def test_backup_job_schedule(self, crontab_contents):
        """The backup.sh job should be scheduled at 2am daily."""
        lines = crontab_contents.splitlines()
        backup_line = None
        for line in lines:
            if "backup.sh" in line and not line.strip().startswith('#'):
                backup_line = line
                break

        assert backup_line is not None, "No uncommented backup.sh line found."
        assert "0 2 * * *" in backup_line, (
            f"The backup.sh job is not scheduled at 2am daily (0 2 * * *). "
            f"Found line: {backup_line}"
        )

    def test_weekly_report_job_exists(self, crontab_contents):
        """The weekly_report.sh cron job must exist in the crontab."""
        assert "weekly_report.sh" in crontab_contents, (
            "The weekly_report.sh job is not found in the crontab. "
            "Expected a line containing '/home/user/scripts/weekly_report.sh'."
        )

    def test_weekly_report_job_is_uncommented(self, crontab_contents):
        """The weekly_report.sh job must be uncommented (active)."""
        lines = crontab_contents.splitlines()
        report_lines = [line for line in lines 
                       if "weekly_report.sh" in line and not line.strip().startswith('#')]

        assert len(report_lines) > 0, (
            "The weekly_report.sh job is commented out or missing. "
            "It should be active in the initial state."
        )

    def test_healthcheck_job_exists(self, crontab_contents):
        """The healthcheck.sh cron job must exist in the crontab."""
        assert "healthcheck.sh" in crontab_contents, (
            "The healthcheck.sh job is not found in the crontab. "
            "Expected a line containing '/home/user/scripts/healthcheck.sh'."
        )

    def test_healthcheck_job_is_uncommented(self, crontab_contents):
        """The healthcheck.sh job must be uncommented (active)."""
        lines = crontab_contents.splitlines()
        health_lines = [line for line in lines 
                       if "healthcheck.sh" in line and not line.strip().startswith('#')]

        assert len(health_lines) > 0, (
            "The healthcheck.sh job is commented out or missing. "
            "It should be active in the initial state."
        )

    def test_three_script_jobs_exist(self, crontab_contents):
        """There should be exactly 3 .sh script references in the crontab."""
        import re
        # Count lines containing .sh (job definitions)
        sh_matches = re.findall(r'\.sh', crontab_contents)
        assert len(sh_matches) == 3, (
            f"Expected exactly 3 .sh script jobs in the crontab, found {len(sh_matches)}. "
            "The crontab should contain backup.sh, weekly_report.sh, and healthcheck.sh jobs."
        )

    def test_has_header_comment(self, crontab_contents):
        """The crontab should have the standard header comment."""
        assert "# m h dom mon dow command" in crontab_contents, (
            "The standard crontab header comment '# m h dom mon dow command' is missing. "
            "This is expected in the initial state."
        )


class TestCrontabStructure:
    """Test the overall structure of the crontab file."""

    def test_file_not_empty(self):
        """The crontab file must not be empty."""
        size = os.path.getsize(CRONTAB_PATH)
        assert size > 0, (
            f"The crontab file at {CRONTAB_PATH} is empty. "
            "It should contain cron job definitions."
        )

    def test_file_has_reasonable_size(self):
        """The crontab file should have a reasonable size (not corrupted/truncated)."""
        size = os.path.getsize(CRONTAB_PATH)
        # The expected content is roughly 200 bytes
        assert size >= 100, (
            f"The crontab file seems too small ({size} bytes). "
            "It may be corrupted or missing content."
        )
        assert size < 10000, (
            f"The crontab file seems unusually large ({size} bytes). "
            "This may indicate unexpected content."
        )
