# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the healthcheck script's 401 errors.
"""

import os
import subprocess
import pytest


class TestInitialDirectoryStructure:
    """Test that required directories exist."""

    def test_collector_directory_exists(self):
        """The /home/user/collector directory must exist."""
        path = "/home/user/collector"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_opt_mock_api_directory_exists(self):
        """The /opt/mock-api directory must exist for the mock server."""
        path = "/opt/mock-api"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestInitialEnvFile:
    """Test the .env file exists with correct content."""

    def test_env_file_exists(self):
        """The .env file must exist."""
        path = "/home/user/collector/.env"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_env_file_contains_api_host(self):
        """The .env file must contain API_HOST=http://localhost:8080."""
        path = "/home/user/collector/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "API_HOST=http://localhost:8080" in content, \
            f".env file does not contain API_HOST=http://localhost:8080"

    def test_env_file_contains_new_api_key(self):
        """The .env file must contain the new API key starting with sk_stg_9f."""
        path = "/home/user/collector/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "API_KEY=sk_stg_9f7a2e3c8b" in content, \
            f".env file does not contain the new API key (API_KEY=sk_stg_9f7a2e3c8b)"

    def test_env_file_contains_log_level(self):
        """The .env file must contain LOG_LEVEL=debug."""
        path = "/home/user/collector/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "LOG_LEVEL=debug" in content, \
            f".env file does not contain LOG_LEVEL=debug"


class TestInitialHealthcheckScript:
    """Test the healthcheck.sh script exists with correct content."""

    def test_healthcheck_script_exists(self):
        """The healthcheck.sh script must exist."""
        path = "/home/user/collector/healthcheck.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_healthcheck_script_is_executable(self):
        """The healthcheck.sh script must be executable."""
        path = "/home/user/collector/healthcheck.sh"
        assert os.access(path, os.X_OK), f"File {path} is not executable"

    def test_healthcheck_script_sources_config(self):
        """The healthcheck.sh script must source config.sh."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        assert "source /home/user/collector/config.sh" in content, \
            "healthcheck.sh does not source config.sh"

    def test_healthcheck_script_uses_api_key_variable(self):
        """The healthcheck.sh script must use $API_KEY variable."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        assert "$API_KEY" in content, \
            "healthcheck.sh does not use $API_KEY variable"

    def test_healthcheck_script_hits_v1_status(self):
        """The healthcheck.sh script must hit /v1/status endpoint."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        assert "/v1/status" in content, \
            "healthcheck.sh does not reference /v1/status endpoint"


class TestInitialConfigScript:
    """Test the config.sh script exists with correct content."""

    def test_config_script_exists(self):
        """The config.sh script must exist."""
        path = "/home/user/collector/config.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_config_script_sources_env_file(self):
        """The config.sh script must source the .env file."""
        path = "/home/user/collector/config.sh"
        with open(path, "r") as f:
            content = f.read()
        assert "/home/user/collector/.env" in content, \
            "config.sh does not reference .env file"

    def test_config_script_sources_credentials_cache(self):
        """The config.sh script must source .credentials_cache (the problematic override)."""
        path = "/home/user/collector/config.sh"
        with open(path, "r") as f:
            content = f.read()
        assert ".credentials_cache" in content, \
            "config.sh does not reference .credentials_cache file"


class TestInitialCredentialsCache:
    """Test the .credentials_cache file exists with the OLD (invalid) key."""

    def test_credentials_cache_exists(self):
        """The .credentials_cache file must exist (contains old key)."""
        path = "/home/user/collector/.credentials_cache"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_credentials_cache_contains_old_key(self):
        """The .credentials_cache must contain the OLD invalid API key."""
        path = "/home/user/collector/.credentials_cache"
        with open(path, "r") as f:
            content = f.read()
        assert "API_KEY=sk_stg_7d4b1a9e2f" in content, \
            ".credentials_cache does not contain the old API key (sk_stg_7d4b1a9e2f)"


class TestInitialMockApiServer:
    """Test that the mock API server is running and accessible."""

    def test_mock_server_script_exists(self):
        """The mock server script must exist."""
        path = "/opt/mock-api/server.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_mock_server_is_running(self):
        """A process should be running the mock API server."""
        result = subprocess.run(
            ["pgrep", "-f", "server.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Mock API server process is not running (pgrep -f server.py found nothing)"

    def test_port_8080_is_listening(self):
        """Port 8080 should be listening for the mock API server."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" in result.stdout, \
            "Port 8080 is not listening - mock API server may not be running"

    def test_mock_server_responds_to_valid_key(self):
        """The mock server should return 200 for the valid new API key."""
        result = subprocess.run(
            [
                "curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
                "-H", "Authorization: Bearer sk_stg_9f7a2e3c8b",
                "http://localhost:8080/v1/status"
            ],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "200", \
            f"Mock server did not return 200 for valid key, got: {result.stdout.strip()}"

    def test_mock_server_rejects_old_key(self):
        """The mock server should return 401 for the old invalid API key."""
        result = subprocess.run(
            [
                "curl", "-s", "-w", "%{http_code}", "-o", "/dev/null",
                "-H", "Authorization: Bearer sk_stg_7d4b1a9e2f",
                "http://localhost:8080/v1/status"
            ],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "401", \
            f"Mock server did not return 401 for old key, got: {result.stdout.strip()}"


class TestInitialHealthcheckFails:
    """Test that the healthcheck currently fails (the problem to be fixed)."""

    def test_healthcheck_currently_fails(self):
        """The healthcheck.sh script should currently fail with 401."""
        result = subprocess.run(
            ["bash", "/home/user/collector/healthcheck.sh"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "healthcheck.sh should be failing initially (this is the bug to fix)"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_bash_available(self):
        """Bash must be available."""
        result = subprocess.run(["which", "bash"], capture_output=True)
        assert result.returncode == 0, "bash is not available"

    def test_curl_available(self):
        """Curl must be available."""
        result = subprocess.run(["which", "curl"], capture_output=True)
        assert result.returncode == 0, "curl is not available"

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(["which", "python3"], capture_output=True)
        assert result.returncode == 0, "python3 is not available"


class TestFilePermissions:
    """Test that collector files are writable."""

    def test_collector_directory_writable(self):
        """The /home/user/collector directory must be writable."""
        path = "/home/user/collector"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_env_file_writable(self):
        """The .env file must be writable."""
        path = "/home/user/collector/.env"
        assert os.access(path, os.W_OK), f"File {path} is not writable"

    def test_config_script_writable(self):
        """The config.sh file must be writable."""
        path = "/home/user/collector/config.sh"
        assert os.access(path, os.W_OK), f"File {path} is not writable"

    def test_credentials_cache_writable(self):
        """The .credentials_cache file must be writable."""
        path = "/home/user/collector/.credentials_cache"
        assert os.access(path, os.W_OK), f"File {path} is not writable"

    def test_healthcheck_script_writable(self):
        """The healthcheck.sh file must be writable."""
        path = "/home/user/collector/healthcheck.sh"
        assert os.access(path, os.W_OK), f"File {path} is not writable"
