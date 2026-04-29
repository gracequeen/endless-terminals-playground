# test_final_state.py
"""
Tests to validate the final state after the student has fixed the healthcheck
script's 401 errors caused by the stale credentials cache override.
"""

import os
import subprocess
import re
import pytest


class TestHealthcheckPasses:
    """Test that the healthcheck now passes - the primary success criteria."""

    def test_healthcheck_exits_zero(self):
        """Running healthcheck.sh must exit with code 0."""
        result = subprocess.run(
            ["bash", "/home/user/collector/healthcheck.sh"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"healthcheck.sh failed with exit code {result.returncode}. " \
            f"stdout: {result.stdout}, stderr: {result.stderr}"

    def test_healthcheck_prints_passed_message(self):
        """Running healthcheck.sh must print 'Health check passed'."""
        result = subprocess.run(
            ["bash", "/home/user/collector/healthcheck.sh"],
            capture_output=True,
            text=True
        )
        assert "Health check passed" in result.stdout, \
            f"healthcheck.sh did not print 'Health check passed'. " \
            f"stdout: {result.stdout}, stderr: {result.stderr}"


class TestInvariantEnvFilePreserved:
    """Test that .env file still contains the new valid API key."""

    def test_env_file_exists(self):
        """The .env file must still exist."""
        path = "/home/user/collector/.env"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_env_file_contains_new_api_key(self):
        """The .env file must still contain the new valid API key."""
        path = "/home/user/collector/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "API_KEY=sk_stg_9f7a2e3c8b" in content, \
            f".env file must still contain API_KEY=sk_stg_9f7a2e3c8b. " \
            f"Current content: {content}"

    def test_env_file_contains_api_host(self):
        """The .env file must still contain API_HOST."""
        path = "/home/user/collector/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "API_HOST=http://localhost:8080" in content, \
            f".env file must still contain API_HOST=http://localhost:8080"


class TestInvariantMockServerRunning:
    """Test that the mock API server is still running."""

    def test_mock_server_is_running(self):
        """The mock API server process must still be running."""
        result = subprocess.run(
            ["pgrep", "-f", "server.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Mock API server process is not running"

    def test_port_8080_is_listening(self):
        """Port 8080 must still be listening."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" in result.stdout, \
            "Port 8080 is not listening - mock API server may have stopped"

    def test_mock_server_still_validates_correctly(self):
        """The mock server should still return 200 for valid key."""
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
            f"Mock server not responding correctly to valid key, got: {result.stdout.strip()}"


class TestInvariantMockServerUnmodified:
    """Test that the mock server script was not modified."""

    def test_mock_server_script_exists(self):
        """The mock server script must still exist."""
        path = "/opt/mock-api/server.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_mock_server_validates_correct_key(self):
        """Mock server must still validate sk_stg_9f7a2e3c8b as the valid key."""
        path = "/opt/mock-api/server.py"
        with open(path, "r") as f:
            content = f.read()
        # The server should contain the valid key for validation
        assert "sk_stg_9f7a2e3c8b" in content, \
            "Mock server script appears to have been modified - valid key not found"


class TestAntiShortcutHealthcheckSourcesConfig:
    """Test that healthcheck.sh still sources config.sh (not bypassed)."""

    def test_healthcheck_still_sources_config(self):
        """healthcheck.sh must still source config.sh."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        # Check for source command with config.sh
        pattern = r'source\s+.*config\.sh'
        assert re.search(pattern, content), \
            "healthcheck.sh must still source config.sh - the fix cannot bypass config loading"

    def test_healthcheck_no_hardcoded_api_key_assignment(self):
        """healthcheck.sh must not have API_KEY hardcoded with the actual key value."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        # Check that API_KEY is not assigned with the actual key value
        assert "API_KEY=sk_stg_9f" not in content, \
            "healthcheck.sh must not hardcode API_KEY=sk_stg_9f... - use config loading instead"

    def test_healthcheck_no_hardcoded_bearer_token(self):
        """healthcheck.sh must not have the bearer token hardcoded."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        # Check that Bearer token is not hardcoded with actual key
        assert "Bearer sk_stg_9f" not in content, \
            "healthcheck.sh must not hardcode 'Bearer sk_stg_9f...' - use $API_KEY variable"


class TestCredentialOverrideFixed:
    """Test that the credential override issue has been addressed."""

    def test_credentials_cache_issue_resolved(self):
        """
        The fix should address the .credentials_cache override.
        Either the file is removed, updated with new key, or config.sh changed.
        We verify by checking that sourcing config.sh results in correct API_KEY.
        """
        # Run a shell command that sources config.sh and echoes API_KEY
        result = subprocess.run(
            ["bash", "-c", "source /home/user/collector/config.sh && echo $API_KEY"],
            capture_output=True,
            text=True
        )
        api_key = result.stdout.strip()
        assert api_key == "sk_stg_9f7a2e3c8b", \
            f"After sourcing config.sh, API_KEY should be 'sk_stg_9f7a2e3c8b' but got '{api_key}'. " \
            f"The credential override issue has not been properly fixed."


class TestConfigScriptExists:
    """Test that config.sh still exists."""

    def test_config_script_exists(self):
        """The config.sh script must still exist."""
        path = "/home/user/collector/config.sh"
        assert os.path.isfile(path), f"File {path} does not exist"


class TestHealthcheckScriptExists:
    """Test that healthcheck.sh still exists and is executable."""

    def test_healthcheck_script_exists(self):
        """The healthcheck.sh script must still exist."""
        path = "/home/user/collector/healthcheck.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_healthcheck_script_is_executable(self):
        """The healthcheck.sh script must still be executable."""
        path = "/home/user/collector/healthcheck.sh"
        assert os.access(path, os.X_OK), f"File {path} is not executable"


class TestHealthcheckUsesApiKeyVariable:
    """Test that healthcheck.sh uses the $API_KEY variable (not hardcoded)."""

    def test_healthcheck_uses_api_key_variable(self):
        """healthcheck.sh must use $API_KEY variable for authorization."""
        path = "/home/user/collector/healthcheck.sh"
        with open(path, "r") as f:
            content = f.read()
        assert "$API_KEY" in content, \
            "healthcheck.sh must use $API_KEY variable"
