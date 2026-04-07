# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the API credential rotation task.
"""

import os
import pytest


class TestInitialDirectoryStructure:
    """Test that required directories exist."""

    def test_app_config_directory_exists(self):
        """The /home/user/app_config/ directory must exist."""
        dir_path = "/home/user/app_config"
        assert os.path.isdir(dir_path), (
            f"Directory '{dir_path}' does not exist. "
            "Please create the app_config directory before starting the task."
        )


class TestInitialConfigFile:
    """Test that the services.conf file exists with correct initial content."""

    def test_services_conf_exists(self):
        """The services.conf file must exist."""
        file_path = "/home/user/app_config/services.conf"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' does not exist. "
            "Please create the services.conf file before starting the task."
        )

    def test_services_conf_is_readable(self):
        """The services.conf file must be readable."""
        file_path = "/home/user/app_config/services.conf"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' is not readable. "
            "Please ensure the file has read permissions."
        )

    def test_services_conf_contains_comment_header(self):
        """The services.conf file should contain the configuration comment header."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "# Application Configuration" in content, (
            f"File '{file_path}' is missing the '# Application Configuration' header comment."
        )

    def test_services_conf_contains_database_host(self):
        """The services.conf file should contain DATABASE_HOST=localhost."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "DATABASE_HOST=localhost" in content, (
            f"File '{file_path}' is missing 'DATABASE_HOST=localhost' entry."
        )

    def test_services_conf_contains_database_port(self):
        """The services.conf file should contain DATABASE_PORT=5432."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "DATABASE_PORT=5432" in content, (
            f"File '{file_path}' is missing 'DATABASE_PORT=5432' entry."
        )

    def test_services_conf_contains_payment_api_key(self):
        """The services.conf file should contain the original PAYMENT_API_KEY."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "PAYMENT_API_KEY=sk_live_abc123xyz789" in content, (
            f"File '{file_path}' is missing 'PAYMENT_API_KEY=sk_live_abc123xyz789' entry. "
            "This is required for the rotation task."
        )

    def test_services_conf_contains_logging_level(self):
        """The services.conf file should contain LOGGING_LEVEL=INFO."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "LOGGING_LEVEL=INFO" in content, (
            f"File '{file_path}' is missing 'LOGGING_LEVEL=INFO' entry."
        )

    def test_services_conf_contains_analytics_api_key(self):
        """The services.conf file should contain the original ANALYTICS_API_KEY."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "ANALYTICS_API_KEY=ak_prod_def456uvw" in content, (
            f"File '{file_path}' is missing 'ANALYTICS_API_KEY=ak_prod_def456uvw' entry. "
            "This is required for the rotation task."
        )

    def test_services_conf_contains_cache_ttl(self):
        """The services.conf file should contain CACHE_TTL=3600."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "CACHE_TTL=3600" in content, (
            f"File '{file_path}' is missing 'CACHE_TTL=3600' entry."
        )

    def test_services_conf_contains_notification_api_key(self):
        """The services.conf file should contain the original NOTIFICATION_API_KEY."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "NOTIFICATION_API_KEY=nk_main_ghi789rst" in content, (
            f"File '{file_path}' is missing 'NOTIFICATION_API_KEY=nk_main_ghi789rst' entry. "
            "This is required for the rotation task."
        )

    def test_services_conf_contains_service_endpoint(self):
        """The services.conf file should contain SERVICE_ENDPOINT."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "SERVICE_ENDPOINT=https://api.example.com" in content, (
            f"File '{file_path}' is missing 'SERVICE_ENDPOINT=https://api.example.com' entry."
        )

    def test_services_conf_has_three_api_key_entries(self):
        """The services.conf file should have exactly 3 lines containing 'API_KEY'."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            lines = f.readlines()
        api_key_lines = [line for line in lines if "API_KEY" in line]
        assert len(api_key_lines) == 3, (
            f"File '{file_path}' should have exactly 3 lines containing 'API_KEY', "
            f"but found {len(api_key_lines)}. "
            "Expected: PAYMENT_API_KEY, ANALYTICS_API_KEY, NOTIFICATION_API_KEY"
        )


class TestBackupFileDoesNotExist:
    """Test that the backup file does not exist yet (initial state)."""

    def test_old_keys_backup_does_not_exist(self):
        """The old_keys.backup file should NOT exist before the task is performed."""
        file_path = "/home/user/app_config/old_keys.backup"
        assert not os.path.exists(file_path), (
            f"File '{file_path}' already exists. "
            "This file should be created by the student as part of the task, "
            "not exist beforehand. Please remove it to reset the initial state."
        )