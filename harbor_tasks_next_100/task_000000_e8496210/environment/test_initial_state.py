# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
generates an SSH keypair for the data server.
"""

import os
import stat
import subprocess
import pwd
import pytest


class TestSSHDirectoryExists:
    """Verify the .ssh directory exists with correct properties."""

    def test_ssh_directory_exists(self):
        """The /home/user/.ssh directory must exist."""
        ssh_dir = "/home/user/.ssh"
        assert os.path.exists(ssh_dir), f"Directory {ssh_dir} does not exist"

    def test_ssh_is_directory(self):
        """The /home/user/.ssh path must be a directory, not a file."""
        ssh_dir = "/home/user/.ssh"
        assert os.path.isdir(ssh_dir), f"{ssh_dir} exists but is not a directory"

    def test_ssh_directory_permissions(self):
        """The /home/user/.ssh directory must have permissions 700."""
        ssh_dir = "/home/user/.ssh"
        st = os.stat(ssh_dir)
        mode = stat.S_IMODE(st.st_mode)
        assert mode == 0o700, f"{ssh_dir} has permissions {oct(mode)}, expected 0o700 (700)"

    def test_ssh_directory_owned_by_user(self):
        """The /home/user/.ssh directory must be owned by 'user'."""
        ssh_dir = "/home/user/.ssh"
        st = os.stat(ssh_dir)
        owner = pwd.getpwuid(st.st_uid).pw_name
        assert owner == "user", f"{ssh_dir} is owned by '{owner}', expected 'user'"

    def test_ssh_directory_is_empty(self):
        """The /home/user/.ssh directory must be empty."""
        ssh_dir = "/home/user/.ssh"
        contents = os.listdir(ssh_dir)
        assert len(contents) == 0, f"{ssh_dir} is not empty, contains: {contents}"


class TestOpenSSHClientInstalled:
    """Verify that openssh-client is installed and ssh-keygen is available."""

    def test_ssh_keygen_available(self):
        """The ssh-keygen command must be available in PATH."""
        result = subprocess.run(
            ["which", "ssh-keygen"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "ssh-keygen is not available. openssh-client may not be installed."

    def test_ssh_keygen_executable(self):
        """The ssh-keygen command must be executable."""
        result = subprocess.run(
            ["ssh-keygen", "--help"],
            capture_output=True,
            text=True
        )
        # ssh-keygen --help may return non-zero but should still produce output
        # We just check it runs without a "command not found" type error
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower() or result.returncode == 0, \
            "ssh-keygen does not appear to be working correctly"


class TestHomeDirectoryWritable:
    """Verify that /home/user is writable."""

    def test_home_user_exists(self):
        """The /home/user directory must exist."""
        home_dir = "/home/user"
        assert os.path.exists(home_dir), f"Directory {home_dir} does not exist"

    def test_home_user_is_directory(self):
        """The /home/user path must be a directory."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), f"{home_dir} exists but is not a directory"

    def test_home_user_writable(self):
        """The /home/user directory must be writable."""
        home_dir = "/home/user"
        assert os.access(home_dir, os.W_OK), f"{home_dir} is not writable"


class TestOutputFilesDoNotExist:
    """Verify that the expected output files do not exist yet."""

    def test_private_key_does_not_exist(self):
        """The private key file should not exist before the task."""
        private_key = "/home/user/.ssh/dataserver_key"
        assert not os.path.exists(private_key), \
            f"Private key {private_key} already exists - initial state should not have this file"

    def test_public_key_does_not_exist(self):
        """The public key file should not exist before the task."""
        public_key = "/home/user/.ssh/dataserver_key.pub"
        assert not os.path.exists(public_key), \
            f"Public key {public_key} already exists - initial state should not have this file"
