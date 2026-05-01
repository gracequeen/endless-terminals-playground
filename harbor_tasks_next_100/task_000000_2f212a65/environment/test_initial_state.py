# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs
the chmod operation to secure the .env file.
"""

import os
import stat
import pwd
import grp
import pytest


class TestInitialState:
    """Test suite to verify the initial state before remediation."""

    def test_webapp_directory_exists(self):
        """Verify /home/user/webapp/ directory exists."""
        webapp_dir = "/home/user/webapp"
        assert os.path.isdir(webapp_dir), (
            f"Directory {webapp_dir} does not exist. "
            "The webapp directory must exist before the task can be performed."
        )

    def test_env_file_exists(self):
        """Verify /home/user/webapp/.env file exists."""
        env_file = "/home/user/webapp/.env"
        assert os.path.isfile(env_file), (
            f"File {env_file} does not exist. "
            "The .env file must exist before the task can be performed."
        )

    def test_env_file_permissions_are_644(self):
        """Verify .env file has world-readable permissions (644)."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)
        # Extract permission bits (last 9 bits)
        permissions = stat.S_IMODE(file_stat.st_mode)
        octal_perms = oct(permissions)[-3:]

        assert octal_perms == "644", (
            f"File {env_file} has permissions {octal_perms}, expected 644 (rw-r--r--). "
            "The file should be world-readable in the initial state."
        )

    def test_env_file_owned_by_user(self):
        """Verify .env file is owned by user:user."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)

        # Get owner name
        try:
            owner_name = pwd.getpwuid(file_stat.st_uid).pw_name
        except KeyError:
            owner_name = str(file_stat.st_uid)

        # Get group name
        try:
            group_name = grp.getgrgid(file_stat.st_gid).gr_name
        except KeyError:
            group_name = str(file_stat.st_gid)

        assert owner_name == "user", (
            f"File {env_file} is owned by '{owner_name}', expected 'user'. "
            "The file must be owned by user."
        )
        assert group_name == "user", (
            f"File {env_file} has group '{group_name}', expected 'user'. "
            "The file must have group 'user'."
        )

    def test_webapp_directory_owned_by_user(self):
        """Verify /home/user/webapp/ is owned by user:user."""
        webapp_dir = "/home/user/webapp"
        dir_stat = os.stat(webapp_dir)

        # Get owner name
        try:
            owner_name = pwd.getpwuid(dir_stat.st_uid).pw_name
        except KeyError:
            owner_name = str(dir_stat.st_uid)

        # Get group name
        try:
            group_name = grp.getgrgid(dir_stat.st_gid).gr_name
        except KeyError:
            group_name = str(dir_stat.st_gid)

        assert owner_name == "user", (
            f"Directory {webapp_dir} is owned by '{owner_name}', expected 'user'."
        )
        assert group_name == "user", (
            f"Directory {webapp_dir} has group '{group_name}', expected 'user'."
        )

    def test_webapp_directory_writable(self):
        """Verify /home/user/webapp/ is writable by owner."""
        webapp_dir = "/home/user/webapp"
        dir_stat = os.stat(webapp_dir)
        permissions = stat.S_IMODE(dir_stat.st_mode)

        # Check if owner has write permission
        assert permissions & stat.S_IWUSR, (
            f"Directory {webapp_dir} is not writable by owner. "
            "The directory must be writable for the task."
        )

    def test_env_file_contains_placeholder_secrets(self):
        """Verify .env file contains the expected placeholder secrets."""
        env_file = "/home/user/webapp/.env"

        with open(env_file, 'r') as f:
            content = f.read()

        assert "DB_PASSWORD=hunter2" in content, (
            f"File {env_file} does not contain 'DB_PASSWORD=hunter2'. "
            "The file must contain the expected placeholder secrets."
        )
        assert "API_KEY=sk-test-12345" in content, (
            f"File {env_file} does not contain 'API_KEY=sk-test-12345'. "
            "The file must contain the expected placeholder secrets."
        )

    def test_env_file_is_readable(self):
        """Verify .env file is readable (can be opened and read)."""
        env_file = "/home/user/webapp/.env"

        try:
            with open(env_file, 'r') as f:
                content = f.read()
            assert len(content) > 0, (
                f"File {env_file} is empty. "
                "The file should contain placeholder secrets."
            )
        except PermissionError:
            pytest.fail(
                f"Cannot read {env_file} due to permission error. "
                "The file should be readable in the initial state."
            )
        except IOError as e:
            pytest.fail(
                f"Cannot read {env_file}: {e}. "
                "The file should be readable in the initial state."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
