# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the credential rotation report task.
"""

import os
import subprocess
import pytest


class TestDirectoryStructure:
    """Test that required directories exist and are accessible."""

    def test_credential_rotation_directory_exists(self):
        """The /home/user/credential-rotation directory must exist."""
        dir_path = "/home/user/credential-rotation"
        assert os.path.exists(dir_path), (
            f"Directory {dir_path} does not exist. "
            "This directory should contain the log files for credential rotation."
        )

    def test_credential_rotation_directory_is_directory(self):
        """The credential-rotation path must be a directory, not a file."""
        dir_path = "/home/user/credential-rotation"
        assert os.path.isdir(dir_path), (
            f"{dir_path} exists but is not a directory. "
            "It should be a directory containing log files."
        )

    def test_credential_rotation_directory_is_writable(self):
        """The credential-rotation directory must be writable."""
        dir_path = "/home/user/credential-rotation"
        assert os.access(dir_path, os.W_OK), (
            f"Directory {dir_path} is not writable. "
            "The student needs write access to create the report file."
        )


class TestLogFilesExist:
    """Test that all required log files exist."""

    def test_aws_rotation_log_exists(self):
        """The aws-rotation.log file must exist."""
        file_path = "/home/user/credential-rotation/aws-rotation.log"
        assert os.path.exists(file_path), (
            f"File {file_path} does not exist. "
            "This file should contain AWS IAM key rotation entries."
        )

    def test_aws_rotation_log_is_file(self):
        """The aws-rotation.log must be a regular file."""
        file_path = "/home/user/credential-rotation/aws-rotation.log"
        assert os.path.isfile(file_path), (
            f"{file_path} exists but is not a regular file."
        )

    def test_db_rotation_log_exists(self):
        """The db-rotation.log file must exist."""
        file_path = "/home/user/credential-rotation/db-rotation.log"
        assert os.path.exists(file_path), (
            f"File {file_path} does not exist. "
            "This file should contain database password rotation entries."
        )

    def test_db_rotation_log_is_file(self):
        """The db-rotation.log must be a regular file."""
        file_path = "/home/user/credential-rotation/db-rotation.log"
        assert os.path.isfile(file_path), (
            f"{file_path} exists but is not a regular file."
        )

    def test_api_keys_log_exists(self):
        """The api-keys.log file must exist."""
        file_path = "/home/user/credential-rotation/api-keys.log"
        assert os.path.exists(file_path), (
            f"File {file_path} does not exist. "
            "This file should contain third-party API key rotation entries."
        )

    def test_api_keys_log_is_file(self):
        """The api-keys.log must be a regular file."""
        file_path = "/home/user/credential-rotation/api-keys.log"
        assert os.path.isfile(file_path), (
            f"{file_path} exists but is not a regular file."
        )


class TestLogFileContents:
    """Test that log files have the expected content."""

    def test_aws_rotation_log_has_correct_entries(self):
        """The aws-rotation.log should have exactly 5 entries."""
        file_path = "/home/user/credential-rotation/aws-rotation.log"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 5, (
            f"aws-rotation.log should have 5 entries, but found {len(lines)}. "
            "Expected entries for: payment-service, user-auth-api, analytics-pipeline, "
            "notification-worker, backup-service"
        )

    def test_aws_rotation_log_contains_expected_services(self):
        """The aws-rotation.log should contain specific service names."""
        file_path = "/home/user/credential-rotation/aws-rotation.log"
        with open(file_path, 'r') as f:
            content = f.read()
        expected_services = [
            "payment-service",
            "user-auth-api",
            "analytics-pipeline",
            "notification-worker",
            "backup-service"
        ]
        for service in expected_services:
            assert service in content, (
                f"aws-rotation.log is missing entry for '{service}'"
            )

    def test_aws_rotation_log_has_one_failed_entry(self):
        """The aws-rotation.log should have exactly 1 FAILED entry."""
        file_path = "/home/user/credential-rotation/aws-rotation.log"
        with open(file_path, 'r') as f:
            content = f.read()
        failed_count = content.count("| FAILED |")
        assert failed_count == 1, (
            f"aws-rotation.log should have 1 FAILED entry, but found {failed_count}"
        )

    def test_db_rotation_log_has_correct_entries(self):
        """The db-rotation.log should have exactly 4 entries."""
        file_path = "/home/user/credential-rotation/db-rotation.log"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 4, (
            f"db-rotation.log should have 4 entries, but found {len(lines)}. "
            "Expected entries for: postgres-primary, mysql-reporting, redis-cache, mongodb-sessions"
        )

    def test_db_rotation_log_contains_expected_services(self):
        """The db-rotation.log should contain specific service names."""
        file_path = "/home/user/credential-rotation/db-rotation.log"
        with open(file_path, 'r') as f:
            content = f.read()
        expected_services = [
            "postgres-primary",
            "mysql-reporting",
            "redis-cache",
            "mongodb-sessions"
        ]
        for service in expected_services:
            assert service in content, (
                f"db-rotation.log is missing entry for '{service}'"
            )

    def test_db_rotation_log_has_one_failed_entry(self):
        """The db-rotation.log should have exactly 1 FAILED entry."""
        file_path = "/home/user/credential-rotation/db-rotation.log"
        with open(file_path, 'r') as f:
            content = f.read()
        failed_count = content.count("| FAILED |")
        assert failed_count == 1, (
            f"db-rotation.log should have 1 FAILED entry, but found {failed_count}"
        )

    def test_api_keys_log_has_correct_entries(self):
        """The api-keys.log should have exactly 5 entries."""
        file_path = "/home/user/credential-rotation/api-keys.log"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 5, (
            f"api-keys.log should have 5 entries, but found {len(lines)}. "
            "Expected entries for: stripe-payments, sendgrid-email, twilio-sms, "
            "datadog-monitoring, github-actions"
        )

    def test_api_keys_log_contains_expected_services(self):
        """The api-keys.log should contain specific service names."""
        file_path = "/home/user/credential-rotation/api-keys.log"
        with open(file_path, 'r') as f:
            content = f.read()
        expected_services = [
            "stripe-payments",
            "sendgrid-email",
            "twilio-sms",
            "datadog-monitoring",
            "github-actions"
        ]
        for service in expected_services:
            assert service in content, (
                f"api-keys.log is missing entry for '{service}'"
            )

    def test_api_keys_log_has_one_failed_entry(self):
        """The api-keys.log should have exactly 1 FAILED entry."""
        file_path = "/home/user/credential-rotation/api-keys.log"
        with open(file_path, 'r') as f:
            content = f.read()
        failed_count = content.count("| FAILED |")
        assert failed_count == 1, (
            f"api-keys.log should have 1 FAILED entry, but found {failed_count}"
        )


class TestLogFileFormat:
    """Test that log files follow the expected format."""

    def test_aws_log_entries_have_correct_format(self):
        """Each entry in aws-rotation.log should match expected format."""
        file_path = "/home/user/credential-rotation/aws-rotation.log"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            # Format: [TIMESTAMP] SERVICE_NAME | OLD_KEY_ID | NEW_KEY_ID | STATUS | ROTATED_BY
            assert line.startswith("["), (
                f"Line does not start with timestamp bracket: {line}"
            )
            assert "] " in line, (
                f"Line missing timestamp closing bracket: {line}"
            )
            pipe_count = line.count(" | ")
            assert pipe_count == 4, (
                f"Line should have 4 pipe separators, found {pipe_count}: {line}"
            )

    def test_db_log_entries_have_correct_format(self):
        """Each entry in db-rotation.log should match expected format."""
        file_path = "/home/user/credential-rotation/db-rotation.log"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            assert line.startswith("["), (
                f"Line does not start with timestamp bracket: {line}"
            )
            assert "] " in line, (
                f"Line missing timestamp closing bracket: {line}"
            )
            pipe_count = line.count(" | ")
            assert pipe_count == 4, (
                f"Line should have 4 pipe separators, found {pipe_count}: {line}"
            )

    def test_api_keys_log_entries_have_correct_format(self):
        """Each entry in api-keys.log should match expected format."""
        file_path = "/home/user/credential-rotation/api-keys.log"
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            assert line.startswith("["), (
                f"Line does not start with timestamp bracket: {line}"
            )
            assert "] " in line, (
                f"Line missing timestamp closing bracket: {line}"
            )
            pipe_count = line.count(" | ")
            assert pipe_count == 4, (
                f"Line should have 4 pipe separators, found {pipe_count}: {line}"
            )


class TestNodeJsAndNpm:
    """Test that Node.js and npm are installed for markdownlint-cli."""

    def test_node_is_installed(self):
        """Node.js must be installed."""
        result = subprocess.run(
            ["which", "node"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Node.js is not installed. "
            "Node.js is required to install and run markdownlint-cli."
        )

    def test_npm_is_installed(self):
        """npm must be installed."""
        result = subprocess.run(
            ["which", "npm"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "npm is not installed. "
            "npm is required to install markdownlint-cli."
        )

    def test_node_version_is_accessible(self):
        """Node.js version command should work."""
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Cannot get Node.js version. Node.js may not be properly installed."
        )

    def test_npm_version_is_accessible(self):
        """npm version command should work."""
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Cannot get npm version. npm may not be properly installed."
        )


class TestMarkdownlintNotPreinstalled:
    """Test that markdownlint-cli is NOT pre-installed."""

    def test_markdownlint_not_in_path(self):
        """markdownlint should NOT be available in PATH initially."""
        result = subprocess.run(
            ["which", "markdownlint"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "markdownlint-cli is already installed globally. "
            "According to the task, it should NOT be pre-installed - "
            "the student needs to install it themselves."
        )

    def test_markdownlint_cli_not_globally_installed(self):
        """markdownlint-cli should NOT be in npm global packages."""
        result = subprocess.run(
            ["npm", "list", "-g", "markdownlint-cli", "--depth=0"],
            capture_output=True,
            text=True
        )
        # npm list returns non-zero if package is not found
        # or the output won't contain markdownlint-cli as installed
        if result.returncode == 0 and "markdownlint-cli" in result.stdout:
            # Check if it's actually installed (not just in the search)
            if "(empty)" not in result.stdout:
                pytest.fail(
                    "markdownlint-cli appears to be globally installed. "
                    "It should NOT be pre-installed according to the task requirements."
                )


class TestHomeDirectory:
    """Test that the home directory is correctly set up."""

    def test_home_user_directory_exists(self):
        """The /home/user directory must exist."""
        dir_path = "/home/user"
        assert os.path.exists(dir_path), (
            f"Directory {dir_path} does not exist. "
            "The home directory for the user should exist."
        )

    def test_home_user_is_directory(self):
        """The /home/user path must be a directory."""
        dir_path = "/home/user"
        assert os.path.isdir(dir_path), (
            f"{dir_path} exists but is not a directory."
        )
