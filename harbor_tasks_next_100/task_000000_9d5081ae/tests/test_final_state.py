# test_final_state.py
"""
Tests to validate the final state after the student has commented out the backup.sh cron job.
"""

import os
import re
import subprocess
import pytest


CRONTAB_PATH = "/var/spool/cron/crontabs/user"


class TestCrontabFileExists:
    """Test that the crontab file still exists and is accessible."""

    def test_crontab_file_exists(self):
        """The crontab file must still exist at the expected path."""
        assert os.path.exists(CRONTAB_PATH), (
            f"Crontab file does not exist at {CRONTAB_PATH}. "
            "The file should not have been deleted, only modified."
        )

    def test_crontab_file_is_regular_file(self):
        """The crontab path must still be a regular file."""
        assert os.path.isfile(CRONTAB_PATH), (
            f"{CRONTAB_PATH} is not a regular file. "
            "The crontab should remain a regular file after modification."
        )


class TestBackupJobCommentedOut:
    """Test that the backup.sh job has been properly commented out."""

    @pytest.fixture
    def crontab_contents(self):
        """Read and return the crontab file contents."""
        with open(CRONTAB_PATH, 'r') as f:
            return f.read()

    def test_backup_job_line_still_exists(self, crontab_contents):
        """The backup.sh line must still exist in the file (not deleted)."""
        assert "backup.sh" in crontab_contents, (
            "The backup.sh line has been deleted from the crontab. "
            "The task requires commenting out the line, not deleting it."
        )

    def test_backup_job_is_commented_out(self, crontab_contents):
        """The backup.sh job must be commented out (line starts with #)."""
        lines = crontab_contents.splitlines()
        backup_lines = [line for line in lines if "backup.sh" in line]

        assert len(backup_lines) > 0, "No backup.sh line found in crontab."

        # All backup.sh lines should be commented
        for line in backup_lines:
            stripped = line.lstrip()
            assert stripped.startswith('#'), (
                f"The backup.sh job is not commented out. "
                f"Found uncommented line: '{line}'. "
                "The line should start with '#' to disable the cron job."
            )

    def test_no_active_backup_job_via_grep(self):
        """Verify no uncommented backup.sh line exists using grep pattern."""
        # grep -E '^[^#]*backup\.sh' should return exit code 1 (no match)
        result = subprocess.run(
            ["grep", "-E", "^[^#]*backup\\.sh", CRONTAB_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1, (
            f"Found an uncommented backup.sh line in the crontab. "
            f"Matching line(s): {result.stdout.strip()}. "
            "The backup.sh job should be commented out."
        )

    def test_backup_line_exists_via_grep(self):
        """Verify the backup.sh line still exists (commented or not) using grep."""
        # grep 'backup.sh' should return exit code 0 (found)
        result = subprocess.run(
            ["grep", "backup.sh", CRONTAB_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The backup.sh line was deleted from the crontab. "
            "The task requires commenting out the line, not removing it entirely."
        )


class TestOtherJobsUnchanged:
    """Test that the other cron jobs remain uncommented and unchanged."""

    @pytest.fixture
    def crontab_contents(self):
        """Read and return the crontab file contents."""
        with open(CRONTAB_PATH, 'r') as f:
            return f.read()

    def test_weekly_report_job_still_active(self, crontab_contents):
        """The weekly_report.sh job must remain uncommented and active."""
        lines = crontab_contents.splitlines()
        active_report_lines = [
            line for line in lines 
            if "weekly_report.sh" in line and not line.lstrip().startswith('#')
        ]

        assert len(active_report_lines) > 0, (
            "The weekly_report.sh job has been commented out or removed. "
            "Only the backup.sh job should have been commented out."
        )

    def test_weekly_report_schedule_unchanged(self, crontab_contents):
        """The weekly_report.sh job should still have its original schedule."""
        lines = crontab_contents.splitlines()
        for line in lines:
            if "weekly_report.sh" in line and not line.lstrip().startswith('#'):
                assert "30 6 * * 1" in line, (
                    f"The weekly_report.sh schedule appears to have been modified. "
                    f"Found: '{line}'. Expected schedule: '30 6 * * 1'."
                )
                break

    def test_healthcheck_job_still_active(self, crontab_contents):
        """The healthcheck.sh job must remain uncommented and active."""
        lines = crontab_contents.splitlines()
        active_health_lines = [
            line for line in lines 
            if "healthcheck.sh" in line and not line.lstrip().startswith('#')
        ]

        assert len(active_health_lines) > 0, (
            "The healthcheck.sh job has been commented out or removed. "
            "Only the backup.sh job should have been commented out."
        )

    def test_healthcheck_schedule_unchanged(self, crontab_contents):
        """The healthcheck.sh job should still have its original schedule."""
        lines = crontab_contents.splitlines()
        for line in lines:
            if "healthcheck.sh" in line and not line.lstrip().startswith('#'):
                assert "*/15 * * * *" in line, (
                    f"The healthcheck.sh schedule appears to have been modified. "
                    f"Found: '{line}'. Expected schedule: '*/15 * * * *'."
                )
                break


class TestAllJobsPresent:
    """Test that all three original jobs are still present in the file."""

    @pytest.fixture
    def crontab_contents(self):
        """Read and return the crontab file contents."""
        with open(CRONTAB_PATH, 'r') as f:
            return f.read()

    def test_three_script_jobs_still_exist(self, crontab_contents):
        """All three .sh script jobs must still exist in the crontab."""
        # Count occurrences of .sh in the file
        sh_count = len(re.findall(r'\.sh', crontab_contents))
        assert sh_count == 3, (
            f"Expected exactly 3 .sh script references in the crontab, found {sh_count}. "
            "All three jobs (backup.sh, weekly_report.sh, healthcheck.sh) must remain in the file."
        )

    def test_three_script_jobs_via_grep(self):
        """Verify all three .sh jobs exist using grep -c."""
        result = subprocess.run(
            ["grep", "-c", "\\.sh", CRONTAB_PATH],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 3, (
            f"Expected grep to find 3 lines containing '.sh', found {count}. "
            "All three original jobs must still be present in the file."
        )

    def test_backup_job_present(self, crontab_contents):
        """The backup.sh reference must exist."""
        assert "backup.sh" in crontab_contents, (
            "backup.sh is missing from the crontab."
        )

    def test_weekly_report_job_present(self, crontab_contents):
        """The weekly_report.sh reference must exist."""
        assert "weekly_report.sh" in crontab_contents, (
            "weekly_report.sh is missing from the crontab."
        )

    def test_healthcheck_job_present(self, crontab_contents):
        """The healthcheck.sh reference must exist."""
        assert "healthcheck.sh" in crontab_contents, (
            "healthcheck.sh is missing from the crontab."
        )


class TestFileIntegrity:
    """Test that the file wasn't corrupted or improperly modified."""

    def test_file_not_empty(self):
        """The crontab file must not be empty."""
        size = os.path.getsize(CRONTAB_PATH)
        assert size > 0, (
            f"The crontab file at {CRONTAB_PATH} is empty. "
            "The file should still contain all cron job definitions."
        )

    def test_file_has_reasonable_size(self):
        """The crontab file should have a reasonable size."""
        size = os.path.getsize(CRONTAB_PATH)
        # The content with one commented line should be roughly 200-250 bytes
        assert size >= 100, (
            f"The crontab file seems too small ({size} bytes). "
            "It may have lost content during modification."
        )
        assert size < 10000, (
            f"The crontab file seems unusually large ({size} bytes). "
            "Unexpected content may have been added."
        )

    def test_header_comment_preserved(self):
        """The standard crontab header comment should still be present."""
        with open(CRONTAB_PATH, 'r') as f:
            contents = f.read()

        # Check for the header comment (allowing for minor variations)
        assert "m h dom mon dow" in contents.lower() or "# m h" in contents, (
            "The crontab header comment appears to have been removed or corrupted."
        )
