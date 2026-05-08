# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the DATABASE_PASSWORD rotation task.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial state before password rotation."""

    ENV_FILE_PATH = "/home/user/webapp/.env"

    def test_webapp_directory_exists(self):
        """Verify /home/user/webapp directory exists."""
        webapp_dir = "/home/user/webapp"
        assert os.path.isdir(webapp_dir), (
            f"Directory {webapp_dir} does not exist. "
            "The webapp directory must be present for this task."
        )

    def test_env_file_exists(self):
        """Verify .env file exists at the expected location."""
        assert os.path.isfile(self.ENV_FILE_PATH), (
            f"File {self.ENV_FILE_PATH} does not exist. "
            "The .env file must be present for this task."
        )

    def test_env_file_is_readable(self):
        """Verify .env file is readable."""
        assert os.access(self.ENV_FILE_PATH, os.R_OK), (
            f"File {self.ENV_FILE_PATH} is not readable. "
            "The agent must be able to read the .env file."
        )

    def test_env_file_is_writable(self):
        """Verify .env file is writable by the current user."""
        assert os.access(self.ENV_FILE_PATH, os.W_OK), (
            f"File {self.ENV_FILE_PATH} is not writable. "
            "The agent must be able to write to the .env file to update the password."
        )

    def test_env_file_contains_app_name(self):
        """Verify .env contains APP_NAME=webapp."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "APP_NAME=webapp" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'APP_NAME=webapp'. "
            "The initial .env file must have this environment variable."
        )

    def test_env_file_contains_database_host(self):
        """Verify .env contains DATABASE_HOST=db.internal.local."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_HOST=db.internal.local" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_HOST=db.internal.local'. "
            "The initial .env file must have this environment variable."
        )

    def test_env_file_contains_database_port(self):
        """Verify .env contains DATABASE_PORT=5432."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_PORT=5432" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_PORT=5432'. "
            "The initial .env file must have this environment variable."
        )

    def test_env_file_contains_database_user(self):
        """Verify .env contains DATABASE_USER=webapp_prod."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_USER=webapp_prod" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_USER=webapp_prod'. "
            "The initial .env file must have this environment variable."
        )

    def test_env_file_contains_old_database_password(self):
        """Verify .env contains the OLD password that needs to be rotated."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        old_password = "xK9#mP2$vL"
        assert f"DATABASE_PASSWORD={old_password}" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_PASSWORD={old_password}'. "
            "The initial .env file must have the old password that needs to be rotated."
        )

    def test_env_file_contains_redis_url(self):
        """Verify .env contains REDIS_URL=redis://cache.internal.local:6379."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "REDIS_URL=redis://cache.internal.local:6379" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'REDIS_URL=redis://cache.internal.local:6379'. "
            "The initial .env file must have this environment variable."
        )

    def test_env_file_contains_log_level(self):
        """Verify .env contains LOG_LEVEL=info."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "LOG_LEVEL=info" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'LOG_LEVEL=info'. "
            "The initial .env file must have this environment variable."
        )

    def test_env_file_does_not_contain_new_password(self):
        """Verify .env does NOT already contain the new password (task not yet done)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        new_password = "Nh7*qR4!bZ"
        assert new_password not in content, (
            f"File {self.ENV_FILE_PATH} already contains the new password '{new_password}'. "
            "The initial state should have the old password, not the new one."
        )

    def test_env_file_has_expected_line_count(self):
        """Verify .env has exactly 7 lines as expected in initial state."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()
        # Count non-empty lines or all lines depending on format
        line_count = len(lines)
        assert line_count == 7, (
            f"File {self.ENV_FILE_PATH} has {line_count} lines, expected 7. "
            "The initial .env file should have exactly 7 lines."
        )

    def test_database_password_line_exists(self):
        """Verify there is exactly one DATABASE_PASSWORD line."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()
        password_lines = [line for line in lines if line.startswith("DATABASE_PASSWORD=")]
        assert len(password_lines) == 1, (
            f"Expected exactly 1 line starting with 'DATABASE_PASSWORD=' in {self.ENV_FILE_PATH}, "
            f"found {len(password_lines)}. The .env file should have exactly one DATABASE_PASSWORD entry."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
