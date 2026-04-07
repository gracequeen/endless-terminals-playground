# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the API credential rotation task.
"""

import os
import pytest


class TestBackupFileExists:
    """Test that the backup file exists and has correct properties."""

    def test_old_keys_backup_exists(self):
        """The old_keys.backup file must exist after task completion."""
        file_path = "/home/user/app_config/old_keys.backup"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' does not exist. "
            "The backup file should be created containing the original API key lines."
        )

    def test_old_keys_backup_is_readable(self):
        """The old_keys.backup file must be readable."""
        file_path = "/home/user/app_config/old_keys.backup"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' is not readable. "
            "Please ensure the file has read permissions."
        )


class TestBackupFileContent:
    """Test that the backup file contains the correct original API keys."""

    def test_backup_contains_exactly_three_lines(self):
        """The backup file should contain exactly 3 lines (no extra blank lines)."""
        file_path = "/home/user/app_config/old_keys.backup"
        with open(file_path, 'r') as f:
            content = f.read()
        # Remove trailing newline if present, then count lines
        lines = content.rstrip('\n').split('\n') if content.strip() else []
        assert len(lines) == 3, (
            f"File '{file_path}' should contain exactly 3 lines, "
            f"but found {len(lines)} lines. "
            "Expected: PAYMENT_API_KEY, ANALYTICS_API_KEY, NOTIFICATION_API_KEY entries."
        )

    def test_backup_contains_payment_api_key(self):
        """The backup file should contain the original PAYMENT_API_KEY line."""
        file_path = "/home/user/app_config/old_keys.backup"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "PAYMENT_API_KEY=sk_live_abc123xyz789" in content, (
            f"File '{file_path}' is missing 'PAYMENT_API_KEY=sk_live_abc123xyz789'. "
            "The backup should contain the original API key values."
        )

    def test_backup_contains_analytics_api_key(self):
        """The backup file should contain the original ANALYTICS_API_KEY line."""
        file_path = "/home/user/app_config/old_keys.backup"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "ANALYTICS_API_KEY=ak_prod_def456uvw" in content, (
            f"File '{file_path}' is missing 'ANALYTICS_API_KEY=ak_prod_def456uvw'. "
            "The backup should contain the original API key values."
        )

    def test_backup_contains_notification_api_key(self):
        """The backup file should contain the original NOTIFICATION_API_KEY line."""
        file_path = "/home/user/app_config/old_keys.backup"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "NOTIFICATION_API_KEY=nk_main_ghi789rst" in content, (
            f"File '{file_path}' is missing 'NOTIFICATION_API_KEY=nk_main_ghi789rst'. "
            "The backup should contain the original API key values."
        )


class TestServicesConfExists:
    """Test that the services.conf file still exists."""

    def test_services_conf_exists(self):
        """The services.conf file must still exist after task completion."""
        file_path = "/home/user/app_config/services.conf"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' does not exist. "
            "The original config file should be modified in place, not deleted."
        )

    def test_services_conf_is_readable(self):
        """The services.conf file must be readable."""
        file_path = "/home/user/app_config/services.conf"
        assert os.path.isfile(file_path), (
            f"File '{file_path}' is not readable. "
            "Please ensure the file has read permissions."
        )


class TestServicesConfRotatedKeys:
    """Test that API keys in services.conf have been rotated."""

    def test_payment_api_key_rotated(self):
        """PAYMENT_API_KEY should have the rotated placeholder value."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "PAYMENT_API_KEY=ROTATED_PENDING_UPDATE" in content, (
            f"File '{file_path}' is missing 'PAYMENT_API_KEY=ROTATED_PENDING_UPDATE'. "
            "The API key value should be replaced with 'ROTATED_PENDING_UPDATE'."
        )

    def test_analytics_api_key_rotated(self):
        """ANALYTICS_API_KEY should have the rotated placeholder value."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "ANALYTICS_API_KEY=ROTATED_PENDING_UPDATE" in content, (
            f"File '{file_path}' is missing 'ANALYTICS_API_KEY=ROTATED_PENDING_UPDATE'. "
            "The API key value should be replaced with 'ROTATED_PENDING_UPDATE'."
        )

    def test_notification_api_key_rotated(self):
        """NOTIFICATION_API_KEY should have the rotated placeholder value."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "NOTIFICATION_API_KEY=ROTATED_PENDING_UPDATE" in content, (
            f"File '{file_path}' is missing 'NOTIFICATION_API_KEY=ROTATED_PENDING_UPDATE'. "
            "The API key value should be replaced with 'ROTATED_PENDING_UPDATE'."
        )


class TestServicesConfOldKeysRemoved:
    """Test that original API key values are no longer in services.conf."""

    def test_old_payment_key_removed(self):
        """The original PAYMENT_API_KEY value should NOT be in services.conf."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "sk_live_abc123xyz789" not in content, (
            f"File '{file_path}' still contains 'sk_live_abc123xyz789'. "
            "The original API key value should be replaced with 'ROTATED_PENDING_UPDATE'."
        )

    def test_old_analytics_key_removed(self):
        """The original ANALYTICS_API_KEY value should NOT be in services.conf."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "ak_prod_def456uvw" not in content, (
            f"File '{file_path}' still contains 'ak_prod_def456uvw'. "
            "The original API key value should be replaced with 'ROTATED_PENDING_UPDATE'."
        )

    def test_old_notification_key_removed(self):
        """The original NOTIFICATION_API_KEY value should NOT be in services.conf."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "nk_main_ghi789rst" not in content, (
            f"File '{file_path}' still contains 'nk_main_ghi789rst'. "
            "The original API key value should be replaced with 'ROTATED_PENDING_UPDATE'."
        )


class TestServicesConfUnchangedEntries:
    """Test that non-API-KEY entries in services.conf remain unchanged."""

    def test_comment_header_unchanged(self):
        """The configuration comment header should remain unchanged."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "# Application Configuration" in content, (
            f"File '{file_path}' is missing '# Application Configuration' header. "
            "Non-API-KEY lines should remain unchanged."
        )

    def test_database_host_unchanged(self):
        """DATABASE_HOST should remain unchanged."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "DATABASE_HOST=localhost" in content, (
            f"File '{file_path}' is missing 'DATABASE_HOST=localhost'. "
            "Non-API-KEY lines should remain unchanged."
        )

    def test_database_port_unchanged(self):
        """DATABASE_PORT should remain unchanged."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "DATABASE_PORT=5432" in content, (
            f"File '{file_path}' is missing 'DATABASE_PORT=5432'. "
            "Non-API-KEY lines should remain unchanged."
        )

    def test_logging_level_unchanged(self):
        """LOGGING_LEVEL should remain unchanged."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "LOGGING_LEVEL=INFO" in content, (
            f"File '{file_path}' is missing 'LOGGING_LEVEL=INFO'. "
            "Non-API-KEY lines should remain unchanged."
        )

    def test_cache_ttl_unchanged(self):
        """CACHE_TTL should remain unchanged."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "CACHE_TTL=3600" in content, (
            f"File '{file_path}' is missing 'CACHE_TTL=3600'. "
            "Non-API-KEY lines should remain unchanged."
        )

    def test_service_endpoint_unchanged(self):
        """SERVICE_ENDPOINT should remain unchanged."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            content = f.read()
        assert "SERVICE_ENDPOINT=https://api.example.com" in content, (
            f"File '{file_path}' is missing 'SERVICE_ENDPOINT=https://api.example.com'. "
            "Non-API-KEY lines should remain unchanged."
        )


class TestServicesConfStructure:
    """Test that the overall structure of services.conf is preserved."""

    def test_services_conf_has_correct_line_count(self):
        """The services.conf file should still have 9 non-empty lines."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            lines = f.readlines()
        # Count non-empty lines (including comment)
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) == 9, (
            f"File '{file_path}' should have 9 non-empty lines, "
            f"but found {len(non_empty_lines)}. "
            "The file structure should be preserved with only API key values changed."
        )

    def test_services_conf_has_three_rotated_api_keys(self):
        """The services.conf file should have exactly 3 lines with ROTATED_PENDING_UPDATE."""
        file_path = "/home/user/app_config/services.conf"
        with open(file_path, 'r') as f:
            lines = f.readlines()
        rotated_lines = [line for line in lines if "ROTATED_PENDING_UPDATE" in line]
        assert len(rotated_lines) == 3, (
            f"File '{file_path}' should have exactly 3 lines with 'ROTATED_PENDING_UPDATE', "
            f"but found {len(rotated_lines)}. "
            "Only API_KEY entries should be rotated."
        )