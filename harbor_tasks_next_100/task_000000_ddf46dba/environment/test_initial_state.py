# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs
the Redis restart task.
"""

import os
import subprocess
import pytest


class TestRedisInstallation:
    """Tests to verify Redis is properly installed."""

    def test_redis_server_binary_exists(self):
        """Verify redis-server binary exists at expected location."""
        redis_server_path = "/usr/bin/redis-server"
        assert os.path.isfile(redis_server_path), (
            f"Redis server binary not found at {redis_server_path}. "
            "Redis must be installed for this task."
        )

    def test_redis_server_is_executable(self):
        """Verify redis-server binary is executable."""
        redis_server_path = "/usr/bin/redis-server"
        assert os.access(redis_server_path, os.X_OK), (
            f"Redis server binary at {redis_server_path} is not executable. "
            "The agent user must have execute permissions."
        )


class TestRedisConfiguration:
    """Tests to verify Redis configuration is properly set up."""

    def test_redis_config_file_exists(self):
        """Verify redis.conf exists at the expected location."""
        config_path = "/etc/redis/redis.conf"
        assert os.path.isfile(config_path), (
            f"Redis configuration file not found at {config_path}. "
            "The config file must exist for this task."
        )

    def test_redis_config_is_readable(self):
        """Verify redis.conf is readable by the agent user."""
        config_path = "/etc/redis/redis.conf"
        assert os.access(config_path, os.R_OK), (
            f"Redis configuration file at {config_path} is not readable. "
            "The agent user must have read permissions."
        )

    def test_redis_config_contains_port_6379(self):
        """Verify redis.conf contains port 6379 configuration."""
        config_path = "/etc/redis/redis.conf"
        with open(config_path, 'r') as f:
            content = f.read()

        # Check for port configuration (could be 'port 6379' with various whitespace)
        lines = content.split('\n')
        port_configured = False
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue
            if stripped.startswith('port'):
                parts = stripped.split()
                if len(parts) >= 2 and parts[1] == '6379':
                    port_configured = True
                    break

        assert port_configured, (
            f"Redis configuration at {config_path} does not contain 'port 6379'. "
            "The configuration must specify port 6379."
        )

    def test_redis_config_contains_data_dir(self):
        """Verify redis.conf contains the correct data directory configuration."""
        config_path = "/etc/redis/redis.conf"
        with open(config_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        dir_configured = False
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue
            if stripped.startswith('dir'):
                parts = stripped.split()
                if len(parts) >= 2 and parts[1] == '/var/lib/redis':
                    dir_configured = True
                    break

        assert dir_configured, (
            f"Redis configuration at {config_path} does not contain 'dir /var/lib/redis'. "
            "The configuration must specify the data directory as /var/lib/redis."
        )


class TestRedisDataDirectory:
    """Tests to verify Redis data directory is properly set up."""

    def test_redis_data_dir_exists(self):
        """Verify /var/lib/redis directory exists."""
        data_dir = "/var/lib/redis"
        assert os.path.isdir(data_dir), (
            f"Redis data directory not found at {data_dir}. "
            "The data directory must exist for this task."
        )

    def test_redis_data_dir_is_writable(self):
        """Verify /var/lib/redis is writable by the agent user."""
        data_dir = "/var/lib/redis"
        assert os.access(data_dir, os.W_OK), (
            f"Redis data directory at {data_dir} is not writable. "
            "The agent user must have write permissions to the data directory."
        )


class TestRedisNotRunning:
    """Tests to verify Redis is NOT currently running (initial broken state)."""

    def test_no_redis_process_running(self):
        """Verify no redis-server process is currently running."""
        result = subprocess.run(
            ["pgrep", "-x", "redis-server"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "Redis server process is already running. "
            "For this task, Redis should NOT be running initially."
        )

    def test_port_6379_not_listening(self):
        """Verify nothing is listening on port 6379."""
        result = subprocess.run(
            ["ss", "-tln"],
            capture_output=True,
            text=True
        )
        assert ":6379" not in result.stdout, (
            "Port 6379 is already in use. "
            "For this task, nothing should be listening on port 6379 initially."
        )


class TestSystemRequirements:
    """Tests to verify system requirements for the task."""

    def test_redis_cli_available(self):
        """Verify redis-cli is available for verification."""
        redis_cli_path = "/usr/bin/redis-cli"
        # redis-cli might be in different locations, check common ones
        possible_paths = ["/usr/bin/redis-cli", "/usr/local/bin/redis-cli"]
        cli_exists = any(os.path.isfile(p) for p in possible_paths)

        if not cli_exists:
            # Try to find it via which
            result = subprocess.run(
                ["which", "redis-cli"],
                capture_output=True,
                text=True
            )
            cli_exists = result.returncode == 0

        assert cli_exists, (
            "redis-cli not found. "
            "redis-cli must be available for verifying Redis is responding."
        )

    def test_ss_command_available(self):
        """Verify ss command is available for port checking."""
        result = subprocess.run(
            ["which", "ss"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "ss command not found. "
            "ss must be available for verifying port listening state."
        )
