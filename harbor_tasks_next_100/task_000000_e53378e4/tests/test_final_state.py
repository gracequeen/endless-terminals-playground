# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the crontab scheduling task.
"""

import os
import subprocess
import re
import pytest


class TestFinalState:
    """Validate the final state after the student performs the task."""

    def test_etl_directory_still_exists(self):
        """Verify /home/user/etl directory still exists."""
        etl_dir = "/home/user/etl"
        assert os.path.isdir(etl_dir), f"Directory {etl_dir} does not exist"

    def test_daily_ingest_script_still_exists(self):
        """Verify /home/user/etl/daily_ingest.sh still exists."""
        script_path = "/home/user/etl/daily_ingest.sh"
        assert os.path.isfile(script_path), f"Script {script_path} does not exist"

    def test_daily_ingest_script_still_executable(self):
        """Verify /home/user/etl/daily_ingest.sh is still executable."""
        script_path = "/home/user/etl/daily_ingest.sh"
        assert os.access(script_path, os.X_OK), f"Script {script_path} is not executable"

    def test_logs_directory_still_exists(self):
        """Verify /home/user/etl/logs directory still exists."""
        logs_dir = "/home/user/etl/logs"
        assert os.path.isdir(logs_dir), f"Directory {logs_dir} does not exist"

    def test_crontab_has_entries(self):
        """Verify user crontab has at least one entry."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}. User crontab should have entries."

        content = result.stdout.strip()
        # Filter out comment lines and empty lines
        non_comment_lines = [
            line for line in content.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        assert len(non_comment_lines) >= 1, \
            "User crontab should have at least one job entry"

    def test_crontab_has_exactly_one_job(self):
        """Verify user crontab has exactly one job entry."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        content = result.stdout.strip()
        # Filter out comment lines and empty lines
        non_comment_lines = [
            line for line in content.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
        assert len(non_comment_lines) == 1, \
            f"User crontab should have exactly one job entry, found {len(non_comment_lines)}: {non_comment_lines}"

    def test_crontab_correct_time_schedule(self):
        """Verify cron entry has correct time fields: 15 3 * * * (3:15 AM daily)."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        content = result.stdout

        # Check for the correct time pattern: 15 3 * * *
        # The pattern should be at the start of a line (possibly with leading whitespace)
        pattern = r'^\s*15\s+3\s+\*\s+\*\s+\*'
        match = re.search(pattern, content, re.MULTILINE)

        assert match is not None, \
            f"Cron entry must have time fields '15 3 * * *' for 3:15 AM daily. Current crontab:\n{content}"

    def test_crontab_references_daily_ingest_script(self):
        """Verify cron entry references /home/user/etl/daily_ingest.sh."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        content = result.stdout

        # Check that daily_ingest.sh is referenced (with full path or just the script name)
        assert "daily_ingest.sh" in content, \
            f"Cron entry must reference daily_ingest.sh. Current crontab:\n{content}"

        # Preferably with full path
        assert "/home/user/etl/daily_ingest.sh" in content, \
            f"Cron entry should reference full path /home/user/etl/daily_ingest.sh. Current crontab:\n{content}"

    def test_crontab_has_output_redirection_to_cron_log(self):
        """Verify cron entry redirects output to /home/user/etl/logs/cron.log."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        content = result.stdout

        # Check that cron.log is referenced for output redirection
        assert "cron.log" in content, \
            f"Cron entry must redirect output to cron.log. Current crontab:\n{content}"

        # Check for the full path
        assert "/home/user/etl/logs/cron.log" in content, \
            f"Cron entry should redirect to /home/user/etl/logs/cron.log. Current crontab:\n{content}"

    def test_crontab_redirects_stderr(self):
        """Verify cron entry redirects stderr (2>&1 or similar)."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        content = result.stdout

        # Check for stderr redirection - common patterns:
        # 2>&1, &>, 2>>, etc.
        stderr_patterns = [
            r'2>&1',           # redirect stderr to stdout
            r'2>>\s*/home/user/etl/logs/cron\.log',  # redirect stderr separately (append)
            r'2>\s*/home/user/etl/logs/cron\.log',   # redirect stderr separately (overwrite)
            r'&>>',            # bash append both
            r'&>',             # bash redirect both
        ]

        has_stderr_redirect = any(re.search(p, content) for p in stderr_patterns)

        assert has_stderr_redirect, \
            f"Cron entry must redirect both stdout AND stderr to cron.log (e.g., using 2>&1 or &>). Current crontab:\n{content}"

    def test_anti_shortcut_grep_time_and_script(self):
        """Anti-shortcut: grep for correct time pattern with daily_ingest.sh."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        # Use grep-like pattern matching
        pattern = r'^15\s+3\s+\*\s+\*\s+\*.*daily_ingest\.sh'
        match = re.search(pattern, result.stdout, re.MULTILINE)

        assert match is not None, \
            f"Anti-shortcut check failed: crontab must have entry matching '15 3 * * * ... daily_ingest.sh'. Current crontab:\n{result.stdout}"

    def test_anti_shortcut_grep_cron_log(self):
        """Anti-shortcut: grep for cron.log in crontab."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        # Check for cron.log in the output
        pattern = r'cron\.log'
        match = re.search(pattern, result.stdout)

        assert match is not None, \
            f"Anti-shortcut check failed: crontab must reference cron.log for output redirection. Current crontab:\n{result.stdout}"

    def test_complete_cron_entry_format(self):
        """Verify the complete cron entry has all required components."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f"crontab -l failed: {result.stderr}"

        content = result.stdout

        # Find the actual cron job line (non-comment, non-empty)
        job_lines = [
            line for line in content.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

        assert len(job_lines) == 1, \
            f"Expected exactly one cron job line, found {len(job_lines)}"

        job_line = job_lines[0]

        # Verify all components are present in the job line:
        # 1. Time: 15 3 * * *
        # 2. Script: /home/user/etl/daily_ingest.sh
        # 3. Output redirect to cron.log
        # 4. Stderr redirect

        assert re.match(r'^\s*15\s+3\s+\*\s+\*\s+\*', job_line), \
            f"Cron job must start with '15 3 * * *'. Found: {job_line}"

        assert "/home/user/etl/daily_ingest.sh" in job_line, \
            f"Cron job must include /home/user/etl/daily_ingest.sh. Found: {job_line}"

        assert "/home/user/etl/logs/cron.log" in job_line, \
            f"Cron job must redirect to /home/user/etl/logs/cron.log. Found: {job_line}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
