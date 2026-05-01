# test_final_state.py
"""
Tests to validate the final state of the system after the student has
performed the chmod operation to secure the .env file to permissions 600.
"""

import os
import stat
import pwd
import grp
import subprocess
import pytest


class TestFinalState:
    """Test suite to verify the final state after remediation."""

    def test_env_file_exists(self):
        """Verify /home/user/webapp/.env file still exists."""
        env_file = "/home/user/webapp/.env"
        assert os.path.isfile(env_file), (
            f"File {env_file} does not exist. "
            "The .env file must still exist after changing permissions."
        )

    def test_env_file_permissions_are_600(self):
        """Verify .env file has owner-only permissions (600)."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)
        # Extract permission bits (last 9 bits)
        permissions = stat.S_IMODE(file_stat.st_mode)
        octal_perms = oct(permissions)[-3:]

        assert octal_perms == "600", (
            f"File {env_file} has permissions {octal_perms}, expected 600 (rw-------). "
            "The file should be locked down to owner-only read/write access."
        )

    def test_env_file_permissions_via_stat_command(self):
        """Anti-shortcut guard: verify permissions using stat command."""
        env_file = "/home/user/webapp/.env"
        result = subprocess.run(
            ["stat", "-c", "%a", env_file],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"stat command failed with return code {result.returncode}: {result.stderr}"
        )

        perms = result.stdout.strip()
        assert perms == "600", (
            f"stat -c '%a' {env_file} returned '{perms}', expected exactly '600'. "
            "The file permissions must be set to 600 (owner read/write only)."
        )

    def test_env_file_owned_by_user(self):
        """Verify .env file ownership remains user:user."""
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
            "File ownership must remain unchanged."
        )
        assert group_name == "user", (
            f"File {env_file} has group '{group_name}', expected 'user'. "
            "File group ownership must remain unchanged."
        )

    def test_env_file_content_unchanged(self):
        """Verify .env file content is unchanged (contains expected secrets)."""
        env_file = "/home/user/webapp/.env"

        with open(env_file, 'r') as f:
            content = f.read()

        assert "DB_PASSWORD=hunter2" in content, (
            f"File {env_file} does not contain 'DB_PASSWORD=hunter2'. "
            "File content must remain unchanged after permission modification."
        )
        assert "API_KEY=sk-test-12345" in content, (
            f"File {env_file} does not contain 'API_KEY=sk-test-12345'. "
            "File content must remain unchanged after permission modification."
        )

    def test_env_file_no_group_read(self):
        """Verify .env file has no group read permission."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)
        permissions = stat.S_IMODE(file_stat.st_mode)

        assert not (permissions & stat.S_IRGRP), (
            f"File {env_file} still has group read permission. "
            "Group read access must be removed (permissions should be 600)."
        )

    def test_env_file_no_other_read(self):
        """Verify .env file has no other/world read permission."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)
        permissions = stat.S_IMODE(file_stat.st_mode)

        assert not (permissions & stat.S_IROTH), (
            f"File {env_file} still has world/other read permission. "
            "World read access must be removed (permissions should be 600)."
        )

    def test_env_file_owner_can_read_write(self):
        """Verify .env file owner has read and write permissions."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)
        permissions = stat.S_IMODE(file_stat.st_mode)

        assert permissions & stat.S_IRUSR, (
            f"File {env_file} does not have owner read permission. "
            "Owner should retain read access."
        )
        assert permissions & stat.S_IWUSR, (
            f"File {env_file} does not have owner write permission. "
            "Owner should retain write access."
        )

    def test_env_file_no_execute_permissions(self):
        """Verify .env file has no execute permissions for anyone."""
        env_file = "/home/user/webapp/.env"
        file_stat = os.stat(env_file)
        permissions = stat.S_IMODE(file_stat.st_mode)

        assert not (permissions & stat.S_IXUSR), (
            f"File {env_file} has owner execute permission, which is unexpected."
        )
        assert not (permissions & stat.S_IXGRP), (
            f"File {env_file} has group execute permission, which is unexpected."
        )
        assert not (permissions & stat.S_IXOTH), (
            f"File {env_file} has other execute permission, which is unexpected."
        )

    def test_webapp_directory_unchanged(self):
        """Verify /home/user/webapp/ directory still exists and is accessible."""
        webapp_dir = "/home/user/webapp"
        assert os.path.isdir(webapp_dir), (
            f"Directory {webapp_dir} does not exist. "
            "The webapp directory must remain intact."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
