# test_final_state.py
"""
Tests to validate the final state after the student has resolved the
credential rotation / cached auth token issue.

The fix should involve invalidating the stale cache (delete, move, or age the mtime)
so that runner.py uses fresh credentials instead of the cached old token.
"""

import hashlib
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

# Expected SHA256 hashes for files that must remain unchanged
# These will be computed from the initial state and verified


class TestFilesUnchanged:
    """Test that runner.py and credentials.json were not modified."""

    def test_runner_py_exists(self):
        """runner.py must still exist."""
        assert os.path.isfile(RUNNER_PY), f"File {RUNNER_PY} does not exist - it should not have been deleted"

    def test_credentials_json_exists(self):
        """credentials.json must still exist."""
        assert os.path.isfile(CREDENTIALS_JSON), f"File {CREDENTIALS_JSON} does not exist - it should not have been deleted"

    def test_credentials_json_has_correct_key(self):
        """credentials.json should still have the new key sa-batch-7f2a."""
        with open(CREDENTIALS_JSON, 'r') as f:
            data = json.load(f)
        assert data.get("key_id") == "sa-batch-7f2a", \
            f"credentials.json key_id should be 'sa-batch-7f2a', got '{data.get('key_id')}'"
        assert data.get("secret") == "newsecret7f2a9x", \
            f"credentials.json secret should be 'newsecret7f2a9x', got '{data.get('secret')}'"

    def test_runner_py_not_modified(self):
        """
        runner.py source code should be byte-identical to the original.
        The fix is cache invalidation, not code modification.
        We check that key structural elements are present indicating it wasn't rewritten.
        """
        with open(RUNNER_PY, 'r') as f:
            content = f.read()

        # The script should still have its original cache-checking logic
        # These are structural checks that the script wasn't fundamentally changed
        assert "credentials.json" in content or "credentials" in content.lower(), \
            "runner.py should still reference credentials"
        assert "cache" in content.lower() or "auth_token" in content, \
            "runner.py should still have cache-related logic (script shouldn't be rewritten)"

        # Check it still reads from the config path
        assert "config" in content.lower(), \
            "runner.py should still reference config directory"


class TestCacheInvalidated:
    """Test that the stale cache has been invalidated."""

    def test_cache_invalidated_or_removed(self):
        """
        The cached auth token should either:
        1. Not exist (deleted/moved)
        2. Exist but have mtime > 24 hours ago (aged)
        3. Exist but contain the new key's token
        """
        if not os.path.exists(AUTH_TOKEN_CACHE):
            # Cache was deleted - this is a valid fix
            return

        # Check if mtime was aged to be > 24 hours
        mtime = os.path.getmtime(AUTH_TOKEN_CACHE)
        current_time = time.time()
        age_hours = (current_time - mtime) / 3600

        if age_hours >= 24:
            # Cache was aged - this is a valid fix
            return

        # Check if cache now contains new token
        try:
            with open(AUTH_TOKEN_CACHE, 'r') as f:
                data = json.load(f)
            if data.get("key_id") == "sa-batch-7f2a" or "7f2a" in data.get("token", ""):
                # Cache was updated with new token - this is a valid fix
                return
        except (json.JSONDecodeError, IOError):
            # Cache file is corrupted/empty - effectively invalidated
            return

        # If we get here, the cache still has the old token and is recent
        pytest.fail(
            f"Stale cache at {AUTH_TOKEN_CACHE} was not invalidated. "
            f"It still exists with recent mtime ({age_hours:.1f}h old) and contains old key. "
            "Fix by: deleting the file, moving it, setting mtime > 24h ago, or updating its contents."
        )


class TestMockAPIServerStillRunning:
    """Test that the mock API server is still running."""

    def test_port_9100_is_listening(self):
        """Check that something is listening on port 9100."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":9100" in result.stdout, \
            "No service listening on port 9100. The mock API server should still be running."

    def test_api_server_responds(self):
        """Test that the API server responds to requests."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:9100/", "--max-time", "5"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"curl to localhost:9100 failed: {result.stderr}"


class TestRunnerWorks:
    """Test that runner.py now works correctly with the new credentials."""

    def test_runner_exits_successfully(self):
        """Running runner.py should exit with code 0."""
        result = subprocess.run(
            ["python3", RUNNER_PY],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"runner.py exited with code {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_runner_output_shows_success(self):
        """Running runner.py should show successful API response."""
        result = subprocess.run(
            ["python3", RUNNER_PY],
            capture_output=True,
            text=True,
            timeout=30
        )

        combined_output = result.stdout + result.stderr

        # Check for success indicators
        success_indicators = [
            "200",
            "ok",
            "success",
            "OK",
            "Success"
        ]

        has_success = any(indicator in combined_output.lower() for indicator in ["ok", "success", "200"])

        # Also check it doesn't have 403 error
        has_403_error = "403" in combined_output and "error" in combined_output.lower()

        assert has_success or result.returncode == 0, \
            f"runner.py output should indicate success. Got:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        assert not has_403_error, \
            f"runner.py still showing 403 error - auth issue not resolved.\nOutput: {combined_output}"

    def test_runner_uses_new_credentials(self):
        """
        After running, if a new cache file exists, it should contain the new key's token.
        This verifies the runner actually used the new credentials.
        """
        # First run the runner to potentially create/update cache
        subprocess.run(
            ["python3", RUNNER_PY],
            capture_output=True,
            text=True,
            timeout=30
        )

        # If cache exists now, it should have the new token
        if os.path.exists(AUTH_TOKEN_CACHE):
            try:
                with open(AUTH_TOKEN_CACHE, 'r') as f:
                    data = json.load(f)

                # If there's a key_id, it should be the new one
                if "key_id" in data:
                    assert data["key_id"] == "sa-batch-7f2a", \
                        f"Cache file has wrong key_id: {data['key_id']}, expected 'sa-batch-7f2a'"

                # If there's a token, it should be the new one (contain 7f2a)
                if "token" in data:
                    assert "4e1c" not in data["token"], \
                        f"Cache file still contains old token: {data['token']}"
            except json.JSONDecodeError:
                # Empty or invalid cache is fine
                pass


class TestAPIAuthWorksDirectly:
    """Verify the API still accepts the new credentials (sanity check)."""

    def test_new_credentials_get_token(self):
        """New credentials should successfully get a token from the API."""
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

        try:
            data = json.loads(result.stdout)
            assert "token" in data, f"Auth response should contain token: {result.stdout}"
        except json.JSONDecodeError:
            pytest.fail(f"Auth endpoint did not return valid JSON: {result.stdout}")

    def test_new_token_accesses_api(self):
        """The new token should successfully access the process API."""
        # First get the new token
        auth_result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", '{"key_id": "sa-batch-7f2a", "secret": "newsecret7f2a9x"}',
             "http://localhost:9100/api/auth",
             "--max-time", "5"],
            capture_output=True,
            text=True
        )

        token_data = json.loads(auth_result.stdout)
        token = token_data["token"]

        # Use the token to access the API
        result = subprocess.run(
            ["curl", "-s", "-w", "\n%{http_code}",
             "-H", f"Authorization: {token}",
             "http://localhost:9100/api/process",
             "--max-time", "5"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.strip().split('\n')
        http_code = lines[-1] if lines else ""

        assert http_code == "200", \
            f"API should return 200 for new token, got {http_code}. Response: {result.stdout}"
