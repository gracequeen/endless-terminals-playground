# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the DATABASE_PASSWORD rotation task.
"""

import os
import pytest


class TestFinalState:
    """Validate the final state after password rotation."""

    ENV_FILE_PATH = "/home/user/webapp/.env"
    NEW_PASSWORD = "Nh7*qR4!bZ"
    OLD_PASSWORD = "xK9#mP2$vL"

    def test_env_file_exists(self):
        """Verify .env file still exists at the expected location."""
        assert os.path.isfile(self.ENV_FILE_PATH), (
            f"File {self.ENV_FILE_PATH} does not exist. "
            "The .env file must still be present after the password rotation."
        )

    def test_env_file_contains_new_database_password(self):
        """Verify .env contains the NEW password after rotation."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        expected_line = f"DATABASE_PASSWORD={self.NEW_PASSWORD}"
        assert expected_line in content, (
            f"File {self.ENV_FILE_PATH} does not contain '{expected_line}'. "
            f"The DATABASE_PASSWORD should have been updated to the new value '{self.NEW_PASSWORD}'."
        )

    def test_env_file_does_not_contain_old_password(self):
        """Verify .env does NOT contain the old password anywhere."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert self.OLD_PASSWORD not in content, (
            f"File {self.ENV_FILE_PATH} still contains the old password '{self.OLD_PASSWORD}'. "
            "The old password should have been completely replaced with the new one."
        )

    def test_env_file_contains_app_name_unchanged(self):
        """Verify .env still contains APP_NAME=webapp (unchanged)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "APP_NAME=webapp" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'APP_NAME=webapp'. "
            "This environment variable should remain unchanged after password rotation."
        )

    def test_env_file_contains_database_host_unchanged(self):
        """Verify .env still contains DATABASE_HOST=db.internal.local (unchanged)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_HOST=db.internal.local" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_HOST=db.internal.local'. "
            "This environment variable should remain unchanged after password rotation."
        )

    def test_env_file_contains_database_port_unchanged(self):
        """Verify .env still contains DATABASE_PORT=5432 (unchanged)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_PORT=5432" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_PORT=5432'. "
            "This environment variable should remain unchanged after password rotation."
        )

    def test_env_file_contains_database_user_unchanged(self):
        """Verify .env still contains DATABASE_USER=webapp_prod (unchanged)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "DATABASE_USER=webapp_prod" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'DATABASE_USER=webapp_prod'. "
            "This environment variable should remain unchanged after password rotation."
        )

    def test_env_file_contains_redis_url_unchanged(self):
        """Verify .env still contains REDIS_URL=redis://cache.internal.local:6379 (unchanged)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "REDIS_URL=redis://cache.internal.local:6379" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'REDIS_URL=redis://cache.internal.local:6379'. "
            "This environment variable should remain unchanged after password rotation."
        )

    def test_env_file_contains_log_level_unchanged(self):
        """Verify .env still contains LOG_LEVEL=info (unchanged)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        assert "LOG_LEVEL=info" in content, (
            f"File {self.ENV_FILE_PATH} does not contain 'LOG_LEVEL=info'. "
            "This environment variable should remain unchanged after password rotation."
        )

    def test_env_file_has_expected_line_count(self):
        """Verify .env still has exactly 7 lines (same as initial state)."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()
        line_count = len(lines)
        assert line_count == 7, (
            f"File {self.ENV_FILE_PATH} has {line_count} lines, expected 7. "
            "The line count should remain the same after password rotation (no lines added or removed)."
        )

    def test_database_password_line_exists_exactly_once(self):
        """Verify there is exactly one DATABASE_PASSWORD line."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()
        password_lines = [line for line in lines if line.strip().startswith("DATABASE_PASSWORD=")]
        assert len(password_lines) == 1, (
            f"Expected exactly 1 line starting with 'DATABASE_PASSWORD=' in {self.ENV_FILE_PATH}, "
            f"found {len(password_lines)}. There should be exactly one DATABASE_PASSWORD entry."
        )

    def test_database_password_line_has_exact_value(self):
        """Verify the DATABASE_PASSWORD line has exactly the new password value."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            lines = f.readlines()
        password_lines = [line.strip() for line in lines if line.strip().startswith("DATABASE_PASSWORD=")]
        assert len(password_lines) == 1, (
            f"Expected exactly 1 DATABASE_PASSWORD line, found {len(password_lines)}."
        )
        expected_line = f"DATABASE_PASSWORD={self.NEW_PASSWORD}"
        assert password_lines[0] == expected_line, (
            f"DATABASE_PASSWORD line is '{password_lines[0]}', expected '{expected_line}'. "
            "The password value must be exactly the new password."
        )

    def test_new_password_appears_exactly_once(self):
        """Verify the new password appears exactly once in the file."""
        with open(self.ENV_FILE_PATH, 'r') as f:
            content = f.read()
        count = content.count(self.NEW_PASSWORD)
        assert count == 1, (
            f"The new password '{self.NEW_PASSWORD}' appears {count} times in {self.ENV_FILE_PATH}, "
            "expected exactly 1 occurrence."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
