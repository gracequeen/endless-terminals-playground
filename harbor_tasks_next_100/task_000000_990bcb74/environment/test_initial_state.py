# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the API key rotation task.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    ENV_FILE_PATH = "/home/user/webapp/.env"
    WEBAPP_DIR = "/home/user/webapp"

    def test_webapp_directory_exists(self):
        """Verify the webapp directory exists."""
        assert os.path.isdir(self.WEBAPP_DIR), (
            f"Directory {self.WEBAPP_DIR} does not exist. "
            "The webapp directory must exist before performing the task."
        )

    def test_env_file_exists(self):
        """Verify the .env file exists."""
        assert os.path.isfile(self.ENV_FILE_PATH), (
            f"File {self.ENV_FILE_PATH} does not exist. "
            "The .env file must exist before performing the task."
        )

    def test_env_file_is_writable(self):
        """Verify the .env file is writable."""
        assert os.access(self.ENV_FILE_PATH, os.W_OK), (
            f"File {self.ENV_FILE_PATH} is not writable. "
            "The .env file must be writable to update the API key."
        )

    def test_env_file_is_readable(self):
        """Verify the .env file is readable."""
        assert os.access(self.ENV_FILE_PATH, os.R_OK), (
            f"File {self.ENV_FILE_PATH} is not readable. "
            "The .env file must be readable to verify its contents."
        )

    def test_env_file_contains_database_url(self):
        """Verify the .env file contains the DATABASE_URL variable."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_URL=postgres://localhost:5432/webapp" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected DATABASE_URL. "
            "Expected: DATABASE_URL=postgres://localhost:5432/webapp"
        )

    def test_env_file_contains_stripe_secret_key(self):
        """Verify the .env file contains the STRIPE_SECRET_KEY variable with the old compromised key."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "STRIPE_SECRET_KEY=sk_live_OLD_COMPROMISED_KEY" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected old STRIPE_SECRET_KEY. "
            "Expected: STRIPE_SECRET_KEY=sk_live_OLD_COMPROMISED_KEY"
        )

    def test_env_file_contains_redis_host(self):
        """Verify the .env file contains the REDIS_HOST variable."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "REDIS_HOST=127.0.0.1" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected REDIS_HOST. "
            "Expected: REDIS_HOST=127.0.0.1"
        )

    def test_env_file_contains_debug(self):
        """Verify the .env file contains the DEBUG variable."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DEBUG=false" in content, (
            f"File {self.ENV_FILE_PATH} does not contain the expected DEBUG. "
            "Expected: DEBUG=false"
        )

    def test_env_file_has_exactly_four_variables(self):
        """Verify the .env file has exactly 4 KEY=value lines."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()

        # Count lines that match KEY=value pattern (uppercase letters and underscores)
        import re
        key_value_pattern = re.compile(r'^[A-Z_]+=')
        key_value_lines = [line for line in lines if key_value_pattern.match(line)]

        assert len(key_value_lines) == 4, (
            f"File {self.ENV_FILE_PATH} should have exactly 4 KEY=value lines. "
            f"Found {len(key_value_lines)} lines."
        )

    def test_env_file_uses_lf_line_endings(self):
        """Verify the .env file uses LF line endings (not CRLF)."""
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

        # Check for common quote patterns around values
        import re
        quoted_pattern = re.compile(r'^[A-Z_]+=["\'].*["\']$', re.MULTILINE)
        matches = quoted_pattern.findall(content)

        assert len(matches) == 0, (
            f"File {self.ENV_FILE_PATH} contains quoted values. "
            "Expected standard KEY=value format without quotes."
        )

    def test_env_file_has_four_non_empty_lines(self):
        """Verify the .env file has exactly 4 non-empty lines."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()

        non_empty_lines = [line for line in lines if line.strip()]

        assert len(non_empty_lines) == 4, (
            f"File {self.ENV_FILE_PATH} should have exactly 4 non-empty lines. "
            f"Found {len(non_empty_lines)} non-empty lines."
        )
