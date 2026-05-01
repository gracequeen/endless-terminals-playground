# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the API key rotation task.
"""

import os
import re
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    ENV_FILE_PATH = "/home/user/webapp/.env"
    WEBAPP_DIR = "/home/user/webapp"
    NEW_STRIPE_KEY = "sk_live_9f8x2mK4pL7nQ3wR"

    def test_env_file_exists(self):
        """Verify the .env file still exists."""
        assert os.path.isfile(self.ENV_FILE_PATH), (
            f"File {self.ENV_FILE_PATH} does not exist. "
            "The .env file must still exist after the task."
        )

    def test_stripe_secret_key_updated(self):
        """Verify STRIPE_SECRET_KEY has been updated to the new key."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()

        expected_line = f"STRIPE_SECRET_KEY={self.NEW_STRIPE_KEY}"
        assert expected_line in content, (
            f"File {self.ENV_FILE_PATH} does not contain the updated STRIPE_SECRET_KEY. "
            f"Expected: {expected_line}"
        )

    def test_stripe_secret_key_grep_exact_match(self):
        """Verify grep returns exactly the expected STRIPE_SECRET_KEY line."""
        result = subprocess.run(
            ["grep", f"^STRIPE_SECRET_KEY=", self.ENV_FILE_PATH],
            capture_output=True,
            text=True
        )

        expected_output = f"STRIPE_SECRET_KEY={self.NEW_STRIPE_KEY}"
        actual_output = result.stdout.strip()

        assert actual_output == expected_output, (
            f"grep '^STRIPE_SECRET_KEY=' did not return expected output. "
            f"Expected: '{expected_output}', Got: '{actual_output}'"
        )

    def test_old_compromised_key_removed(self):
        """Verify the old compromised key is no longer in the file."""
        result = subprocess.run(
            ["grep", "OLD_COMPROMISED", self.ENV_FILE_PATH],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0, (
            f"File {self.ENV_FILE_PATH} still contains 'OLD_COMPROMISED'. "
            "The old compromised key should have been removed."
        )
        assert "OLD_COMPROMISED" not in result.stdout, (
            f"File {self.ENV_FILE_PATH} still contains 'OLD_COMPROMISED' in output."
        )

    def test_database_url_unchanged(self):
        """Verify DATABASE_URL line is unchanged."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()

        assert "DATABASE_URL=postgres://localhost:5432/webapp" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected DATABASE_URL. "
            "Expected: DATABASE_URL=postgres://localhost:5432/webapp (should be unchanged)"
        )

    def test_redis_host_unchanged(self):
        """Verify REDIS_HOST line is unchanged."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()

        assert "REDIS_HOST=127.0.0.1" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected REDIS_HOST. "
            "Expected: REDIS_HOST=127.0.0.1 (should be unchanged)"
        )

    def test_debug_unchanged(self):
        """Verify DEBUG line is unchanged."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()

        assert "DEBUG=false" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected DEBUG. "
            "Expected: DEBUG=false (should be unchanged)"
        )

    def test_exactly_four_variables_preserved(self):
        """Verify all 4 original variables are preserved (anti-shortcut guard)."""
        result = subprocess.run(
            ["grep", "-c", "^[A-Z_]*=", self.ENV_FILE_PATH],
            capture_output=True,
            text=True
        )

        count = int(result.stdout.strip())
        assert count == 4, (
            f"File {self.ENV_FILE_PATH} should have exactly 4 KEY=value lines. "
            f"Found {count} lines. All original variables must be preserved."
        )

    def test_exactly_four_non_empty_lines(self):
        """Verify the file still has exactly 4 non-empty lines."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()

        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) == 4, (
            f"File {self.ENV_FILE_PATH} should have exactly 4 non-empty lines. "
            f"Found {len(non_empty_lines)} non-empty lines."
        )

    def test_no_backup_files_created(self):
        """Verify no backup files were created in the webapp directory."""
        backup_patterns = ['.env.bak', '.env.old', '.env.backup', '.env~']

        for pattern in backup_patterns:
            backup_path = os.path.join(self.WEBAPP_DIR, pattern)
            assert not os.path.exists(backup_path), (
                f"Backup file {backup_path} was created. "
                "No backup files should be created in the webapp directory."
            )

        # Also check for any files starting with .env. (common sed backup pattern)
        if os.path.isdir(self.WEBAPP_DIR):
            files = os.listdir(self.WEBAPP_DIR)
            env_backups = [f for f in files if f.startswith('.env.') or f.startswith('.env~')]
            assert len(env_backups) == 0, (
                f"Backup files found in {self.WEBAPP_DIR}: {env_backups}. "
                "No backup files should be created."
            )

    def test_env_file_uses_lf_line_endings(self):
        """Verify the .env file still uses LF line endings."""
        with open(self.ENV_FILE_PATH, 'rb') as f:
            content = f.read()

        assert b'\r\n' not in content, (
            f"File {self.ENV_FILE_PATH} contains CRLF line endings. "
            "Expected LF line endings only."
        )

    def test_env_file_no_quotes_around_values(self):
        """Verify the .env file values are not quoted."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()

        quoted_pattern = re.compile(r'^[A-Z_]+=["\'].*["\']$', re.MULTILINE)
        matches = quoted_pattern.findall(content)

        assert len(matches) == 0, (
            f"File {self.ENV_FILE_PATH} contains quoted values. "
            "Expected standard KEY=value format without quotes."
        )

    def test_stripe_key_is_only_occurrence(self):
        """Verify STRIPE_SECRET_KEY appears exactly once in the file."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()

        occurrences = content.count("STRIPE_SECRET_KEY=")
        assert occurrences == 1, (
            f"STRIPE_SECRET_KEY appears {occurrences} times in the file. "
            "It should appear exactly once."
        )
