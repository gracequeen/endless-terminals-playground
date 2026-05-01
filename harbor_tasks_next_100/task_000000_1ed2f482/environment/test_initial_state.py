# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the credential rotation debugging task.
"""

import json
import os
import subprocess
import time
import pytest


HOME = "/home/user"
BATCH_DIR = os.path.join(HOME, "batch")
CONFIG_DIR = os.path.join(BATCH_DIR, "config")
LOGS_DIR = os.path.join(BATCH_DIR, "logs")
CACHE_DIR = os.path.join(BATCH_DIR, ".cache")

RUNNER_PY = os.path.join(BATCH_DIR, "runner.py")
CREDENTIALS_JSON = os.path.join(CONFIG_DIR, "credentials.json")
AUTH_TOKEN_CACHE = os.path.join(CACHE_DIR, "auth_token")
RUNNER_LOG = os.path.join(LOGS_DIR, "runner.log")


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_batch_directory_exists(self):
        assert os.path.isdir(BATCH_DIR), f"Directory {BATCH_DIR} does not exist"

    def test_config_directory_exists(self):
        assert os.path.isdir(CONFIG_DIR), f"Directory {CONFIG_DIR} does not exist"

    def test_logs_directory_exists(self):
        assert os.path.isdir(LOGS_DIR), f"Directory {LOGS_DIR} does not exist"

    def test_cache_directory_exists(self):
        assert os.path.isdir(CACHE_DIR), f"Directory {CACHE_DIR} does not exist"


class TestRequiredFiles:
    """Test that required files exist."""

    def test_runner_py_exists(self):
        assert os.path.isfile(RUNNER_PY), f"File {RUNNER_PY} does not exist"

    def test_credentials_json_exists(self):
        assert os.path.isfile(CREDENTIALS_JSON), f"File {CREDENTIALS_JSON} does not exist"

    def test_auth_token_cache_exists(self):
        assert os.path.isfile(AUTH_TOKEN_CACHE), f"Cached auth token file {AUTH_TOKEN_CACHE} does not exist"

    def test_runner_log_exists(self):
        assert os.path.isfile(RUNNER_LOG), f"Log file {RUNNER_LOG} does not exist"


class TestCredentialsJson:
    """Test the credentials.json file has the new key."""

    def test_credentials_json_is_valid_json(self):
        with open(CREDENTIALS_JSON, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"credentials.json is not valid JSON: {e}")

    def test_credentials_json_has_new_key_id(self):
        with open(CREDENTIALS_JSON, 'r') as f:
            data = json.load(f)
        assert "key_id" in data, "credentials.json missing 'key_id' field"
        assert data["key_id"] == "sa-batch-7f2a", \
            f"credentials.json has key_id '{data['key_id']}', expected 'sa-batch-7f2a'"

    def test_credentials_json_has_secret(self):
        with open(CREDENTIALS_JSON, 'r') as f:
            data = json.load(f)
        assert "secret" in data, "credentials.json missing 'secret' field"


class TestCachedAuthToken:
    """Test the cached auth token file contains the OLD key."""

    def test_auth_token_cache_is_valid_json(self):
        with open(AUTH_TOKEN_CACHE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"auth_token cache is not valid JSON: {e}")

    def test_auth_token_cache_has_old_key_id(self):
        with open(AUTH_TOKEN_CACHE, 'r') as f:
            data = json.load(f)
        assert "key_id" in data, "auth_token cache missing 'key_id' field"
        assert data["key_id"] == "sa-batch-4e1c", \
            f"auth_token cache has key_id '{data['key_id']}', expected old key 'sa-batch-4e1c'"

    def test_auth_token_cache_has_token(self):
        with open(AUTH_TOKEN_CACHE, 'r') as f:
            data = json.load(f)
        assert "token" in data, "auth_token cache missing 'token' field"
        assert "4e1c" in data["token"], \
            f"auth_token cache token doesn't appear to be the old token: {data['token']}"

    def test_auth_token_cache_is_recent(self):
        """The cache file should have a recent mtime (within 24 hours) so runner.py considers it valid."""
        mtime = os.path.getmtime(AUTH_TOKEN_CACHE)
        current_time = time.time()
        age_hours = (current_time - mtime) / 3600
        assert age_hours < 24, \
            f"auth_token cache mtime is {age_hours:.1f} hours old, should be < 24 hours for the bug to manifest"


class TestRunnerLog:
    """Test the runner.log shows the expected error pattern."""

    def test_runner_log_shows_credentials_loaded(self):
        with open(RUNNER_LOG, 'r') as f:
            content = f.read()
        assert "Loaded credentials from config" in content, \
            "runner.log should show 'Loaded credentials from config' message"

    def test_runner_log_shows_cached_token_used(self):
        with open(RUNNER_LOG, 'r') as f:
            content = f.read()
        assert "cached auth token" in content.lower() or "Found cached auth token" in content, \
            "runner.log should indicate cached auth token was used"

    def test_runner_log_shows_403_error(self):
        with open(RUNNER_LOG, 'r') as f:
            content = f.read()
        assert "403" in content, \
            "runner.log should show 403 Forbidden error"


class TestRunnerPy:
    """Test the runner.py script properties."""

    def test_runner_py_is_python_script(self):
        with open(RUNNER_PY, 'r') as f:
            first_line = f.readline()
            content = first_line + f.read()
        # Check it looks like Python (has imports or shebang)
        is_python = (
            "import " in content or
            "from " in content or
            "#!/" in first_line and "python" in first_line
        )
        assert is_python, f"{RUNNER_PY} doesn't appear to be a Python script"

    def test_runner_py_references_credentials_json(self):
        with open(RUNNER_PY, 'r') as f:
            content = f.read()
        assert "credentials.json" in content or "credentials" in content.lower(), \
            "runner.py should reference credentials.json"

    def test_runner_py_references_cache(self):
        with open(RUNNER_PY, 'r') as f:
            content = f.read()
        assert "cache" in content.lower() or "auth_token" in content, \
            "runner.py should have cache-related logic"


class TestMockAPIServer:
    """Test that the mock API server is running on localhost:9100."""

    def test_port_9100_is_listening(self):
        """Check that something is listening on port 9100."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":9100" in result.stdout, \
            "No service listening on port 9100. The mock API server should be running."

    def test_api_server_responds(self):
        """Test that the API server responds to requests."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "http://localhost:9100/", "--max-time", "5"],
            capture_output=True,
            text=True
        )
        # Any response (even 404) means server is up
        assert result.returncode == 0, \
            f"curl to localhost:9100 failed: {result.stderr}"

    def test_api_auth_endpoint_with_new_credentials(self):
        """Test that the new credentials work with the API."""
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", 
             "-H", "Content-Type: application/json",
             "-d", '{"key_id": "sa-batch-7f2a", "secret": "newsecret7f2a9x"}',
             "http://localhost:9100/api/auth",
             "--max-time", "5"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"curl to auth endpoint failed: {result.stderr}"
        # Should return a token
        try:
            data = json.loads(result.stdout)
            assert "token" in data, f"Auth response should contain token: {result.stdout}"
        except json.JSONDecodeError:
            pytest.fail(f"Auth endpoint did not return valid JSON: {result.stdout}")

    def test_api_rejects_old_token(self):
        """Test that the old token gets 403."""
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}",
             "-H", "Authorization: bearer-old-4e1c-abc123",
             "http://localhost:9100/api/process",
             "--max-time", "5"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        http_code = lines[-1] if lines else ""
        assert http_code == "403", \
            f"API should return 403 for old token, got {http_code}"


class TestPythonEnvironment:
    """Test Python environment is properly set up."""

    def test_python3_available(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "python3 is not available"

    def test_requests_library_installed(self):
        result = subprocess.run(
            ["python3", "-c", "import requests"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"requests library is not installed: {result.stderr}"


class TestTools:
    """Test that required tools are available."""

    def test_curl_available(self):
        result = subprocess.run(["which", "curl"], capture_output=True)
        assert result.returncode == 0, "curl is not available"

    def test_jq_available(self):
        result = subprocess.run(["which", "jq"], capture_output=True)
        assert result.returncode == 0, "jq is not available"
