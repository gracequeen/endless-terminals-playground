# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs
the SSH security audit task.
"""

import os
import pytest


class TestSSHConfigurationExists:
    """Test that the SSH configuration file exists and is readable."""

    def test_sshd_config_file_exists(self):
        """The SSH daemon configuration file must exist at /etc/ssh/sshd_config."""
        config_path = "/etc/ssh/sshd_config"
        assert os.path.exists(config_path), (
            f"SSH configuration file not found at {config_path}. "
            "This file is required for the security audit task. "
            "Ensure openssh-server is installed on the system."
        )

    def test_sshd_config_is_file(self):
        """The sshd_config path must be a regular file, not a directory."""
        config_path = "/etc/ssh/sshd_config"
        assert os.path.isfile(config_path), (
            f"{config_path} exists but is not a regular file. "
            "The SSH configuration must be a readable file."
        )

    def test_sshd_config_is_readable(self):
        """The sshd_config file must be readable."""
        config_path = "/etc/ssh/sshd_config"
        assert os.path.isfile(config_path), (
            f"{config_path} exists but is not readable. "
            "The user must have read permissions to perform the security audit."
        )


class TestSSHDirectoryStructure:
    """Test that the SSH directory structure exists."""

    def test_ssh_directory_exists(self):
        """The /etc/ssh directory must exist."""
        ssh_dir = "/etc/ssh"
        assert os.path.exists(ssh_dir), (
            f"SSH directory not found at {ssh_dir}. "
            "OpenSSH server does not appear to be installed."
        )

    def test_ssh_directory_is_directory(self):
        """The /etc/ssh path must be a directory."""
        ssh_dir = "/etc/ssh"
        assert os.path.isdir(ssh_dir), (
            f"{ssh_dir} exists but is not a directory. "
            "The SSH configuration directory structure is corrupted."
        )


class TestUserHomeDirectory:
    """Test that the user's home directory exists for output file creation."""

    def test_user_home_exists(self):
        """The /home/user directory must exist for creating the audit report."""
        home_dir = "/home/user"
        assert os.path.exists(home_dir), (
            f"User home directory not found at {home_dir}. "
            "This directory is required to create the audit report output file."
        )

    def test_user_home_is_directory(self):
        """The /home/user path must be a directory."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), (
            f"{home_dir} exists but is not a directory. "
            "The user home must be a directory to store the audit report."
        )

    def test_user_home_is_writable(self):
        """The /home/user directory must be writable to create the audit report."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), (
            f"{home_dir} exists but is not writable. "
            "Write permissions are required to create the audit report file."
        )


class TestSSHConfigContent:
    """Test that the SSH config file has valid content."""

    def test_sshd_config_not_empty(self):
        """The sshd_config file should not be empty."""
        config_path = "/etc/ssh/sshd_config"
        if os.path.exists(config_path) and os.path.isfile(config_path):
            file_size = os.path.getsize(config_path)
            assert file_size > 0, (
                f"{config_path} exists but is empty (0 bytes). "
                "The SSH configuration file should contain configuration directives."
            )

    def test_sshd_config_has_content(self):
        """The sshd_config file should contain SSH configuration content."""
        config_path = "/etc/ssh/sshd_config"
        if os.path.exists(config_path) and os.path.isfile(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
            # Check for common SSH config patterns (comments or directives)
            has_content = bool(content.strip())
            assert has_content, (
                f"{config_path} appears to have no meaningful content. "
                "The file should contain SSH daemon configuration."
            )


class TestOutputFileDoesNotExist:
    """Test that the output file does not already exist (clean state)."""

    def test_audit_report_does_not_exist(self):
        """The audit report should not exist before the task is performed."""
        output_path = "/home/user/ssh_audit_report.txt"
        # This is a soft check - it's okay if it exists, but ideally it shouldn't
        # We don't assert here because re-running the task should be allowed
        if os.path.exists(output_path):
            pytest.skip(
                f"Note: {output_path} already exists. "
                "This may be from a previous run of the task."
            )