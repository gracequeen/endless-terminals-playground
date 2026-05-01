# test_final_state.py
"""
Tests to validate the final state of the system after the student has
completed the Redis restart task.
"""

import os
import subprocess
import socket
import time
import pytest


class TestRedisProcessRunning:
    """Tests to verify Redis server process is running."""

    def test_redis_server_process_exists(self):
        """Verify redis-server process is running."""
        result = subprocess.run(
            ["pgrep", "-x", "redis-server"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Redis server process is NOT running. "
            "The task requires starting redis-server so it is running."
        )

    def test_redis_server_process_count(self):
        """Verify at least one redis-server process is running."""
        result = subprocess.run(
            ["pgrep", "-x", "redis-server"],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split('\n')
        pids = [p for p in pids if p]  # Filter empty strings
        assert len(pids) >= 1, (
            f"Expected at least 1 redis-server process, found {len(pids)}. "
            "Redis must be running."
        )


class TestRedisResponding:
    """Tests to verify Redis is responding to commands."""

    def test_redis_cli_ping_returns_pong(self):
        """Verify redis-cli ping returns PONG."""
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"redis-cli ping failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}. "
            "Redis must be running and responding to commands."
        )
        assert "PONG" in result.stdout.upper(), (
            f"redis-cli ping did not return PONG. Got: '{result.stdout.strip()}'. "
            "Redis must respond with PONG to a PING command."
        )

    def test_redis_cli_ping_exit_code_zero(self):
        """Verify redis-cli ping exits with code 0."""
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"redis-cli ping exited with code {result.returncode}, expected 0. "
            f"stderr: {result.stderr}. "
            "Redis must be running and healthy."
        )


class TestRedisPortListening:
    """Tests to verify Redis is listening on port 6379."""

    def test_port_6379_listening_via_ss(self):
        """Verify port 6379 is listening using ss command."""
        result = subprocess.run(
            ["ss", "-tln"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"ss command failed: {result.stderr}"
        )
        # Check for port 6379 in listening state
        assert ":6379" in result.stdout, (
            "Port 6379 is NOT listening. "
            f"ss -tln output: {result.stdout}. "
            "Redis must be listening on port 6379."
        )

    def test_can_connect_to_port_6379(self):
        """Verify we can establish a TCP connection to port 6379."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex(('127.0.0.1', 6379))
            assert result == 0, (
                f"Cannot connect to 127.0.0.1:6379. Connection error code: {result}. "
                "Redis must be listening and accepting connections on port 6379."
            )
        finally:
            sock.close()


class TestConfigurationInvariant:
    """Tests to verify configuration file was not modified."""

    def test_redis_config_still_exists(self):
        """Verify redis.conf still exists at the expected location."""
        config_path = "/etc/redis/redis.conf"
        assert os.path.isfile(config_path), (
            f"Redis configuration file not found at {config_path}. "
            "The config file must not be deleted."
        )

    def test_redis_config_still_has_port_6379(self):
        """Verify redis.conf still contains port 6379 configuration."""
        config_path = "/etc/redis/redis.conf"
        with open(config_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        port_configured = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if stripped.startswith('port'):
                parts = stripped.split()
                if len(parts) >= 2 and parts[1] == '6379':
                    port_configured = True
                    break

        assert port_configured, (
            f"Redis configuration at {config_path} no longer contains 'port 6379'. "
            "The configuration must not be modified."
        )

    def test_redis_config_still_has_data_dir(self):
        """Verify redis.conf still contains the correct data directory."""
        config_path = "/etc/redis/redis.conf"
        with open(config_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        dir_configured = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if stripped.startswith('dir'):
                parts = stripped.split()
                if len(parts) >= 2 and parts[1] == '/var/lib/redis':
                    dir_configured = True
                    break

        assert dir_configured, (
            f"Redis configuration at {config_path} no longer contains 'dir /var/lib/redis'. "
            "The configuration must not be modified."
        )


class TestDataDirectoryInvariant:
    """Tests to verify data directory still exists."""

    def test_redis_data_dir_still_exists(self):
        """Verify /var/lib/redis directory still exists."""
        data_dir = "/var/lib/redis"
        assert os.path.isdir(data_dir), (
            f"Redis data directory not found at {data_dir}. "
            "The data directory must not be deleted."
        )


class TestRedisActuallyWorking:
    """Tests to verify Redis is actually functional, not a mock or stub."""

    def test_redis_can_set_and_get_value(self):
        """Verify Redis can actually store and retrieve data."""
        test_key = "pytest_verification_key"
        test_value = "pytest_verification_value_12345"

        # Set a value
        set_result = subprocess.run(
            ["redis-cli", "SET", test_key, test_value],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert set_result.returncode == 0, (
            f"redis-cli SET failed: {set_result.stderr}. "
            "Redis must be able to accept write commands."
        )
        assert "OK" in set_result.stdout.upper(), (
            f"redis-cli SET did not return OK. Got: '{set_result.stdout.strip()}'. "
            "Redis must acknowledge successful writes."
        )

        # Get the value back
        get_result = subprocess.run(
            ["redis-cli", "GET", test_key],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert get_result.returncode == 0, (
            f"redis-cli GET failed: {get_result.stderr}. "
            "Redis must be able to accept read commands."
        )
        assert test_value in get_result.stdout, (
            f"redis-cli GET did not return expected value. "
            f"Expected '{test_value}', got '{get_result.stdout.strip()}'. "
            "Redis must correctly store and retrieve data."
        )

        # Clean up
        subprocess.run(
            ["redis-cli", "DEL", test_key],
            capture_output=True,
            text=True,
            timeout=10
        )

    def test_redis_info_returns_valid_response(self):
        """Verify redis-cli INFO returns a valid response."""
        result = subprocess.run(
            ["redis-cli", "INFO", "server"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"redis-cli INFO failed: {result.stderr}. "
            "Redis must respond to INFO command."
        )
        # Check for expected fields in INFO output
        assert "redis_version" in result.stdout, (
            "redis-cli INFO did not contain redis_version. "
            f"Got: {result.stdout[:200]}... "
            "This suggests Redis is not actually running properly."
        )
