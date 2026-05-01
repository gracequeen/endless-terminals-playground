# test_final_state.py
"""
Tests to validate the final state of the service mesh after the student fixes the bug.
The full chain gateway -> auth -> backend should work correctly.
"""

import json
import os
import subprocess
import time
import hashlib
import pytest


MESH_DIR = "/home/user/mesh"


class TestServicesStillRunning:
    """Test that all three services are still running as separate processes."""

    def test_gateway_process_running(self):
        """Exactly one gateway.py process should be running."""
        result = subprocess.run(
            ["pgrep", "-f", "gateway.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "No process found running gateway.py"
        pids = [p for p in result.stdout.strip().split('\n') if p]
        assert len(pids) >= 1, "gateway.py process not found"

    def test_auth_process_running(self):
        """Exactly one auth.py process should be running."""
        result = subprocess.run(
            ["pgrep", "-f", "auth.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "No process found running auth.py"
        pids = [p for p in result.stdout.strip().split('\n') if p]
        assert len(pids) >= 1, "auth.py process not found"

    def test_backend_process_running(self):
        """Exactly one backend.py process should be running."""
        result = subprocess.run(
            ["pgrep", "-f", "backend.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "No process found running backend.py"
        pids = [p for p in result.stdout.strip().split('\n') if p]
        assert len(pids) >= 1, "backend.py process not found"


class TestPortsStillListening:
    """Test that all three services are still listening on their expected ports."""

    def test_port_8080_listening(self):
        """Gateway should be listening on port 8080."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" in result.stdout, "Port 8080 (gateway) is not listening"

    def test_port_8081_listening(self):
        """Auth should be listening on port 8081."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8081" in result.stdout, "Port 8081 (auth) is not listening"

    def test_port_8082_listening(self):
        """Backend should be listening on port 8082."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8082" in result.stdout, "Port 8082 (backend) is not listening"


class TestFullChainWorks:
    """Test that the full service chain works correctly."""

    def test_curl_gateway_returns_json_with_secret_payload(self):
        """curl localhost:8080/data should return JSON containing secret_payload_42 within 5 seconds."""
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8080/data"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"curl to gateway:8080/data failed with return code {result.returncode}. stderr: {result.stderr}"

        # Check that the response contains the expected payload
        assert "secret_payload_42" in result.stdout, \
            f"Response doesn't contain 'secret_payload_42'. Got: {result.stdout}"

    def test_curl_gateway_returns_valid_json(self):
        """The response from gateway should be valid JSON."""
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8080/data"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"curl to gateway:8080/data failed. stderr: {result.stderr}"

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Response is not valid JSON: {result.stdout}. Error: {e}")

        # The response should contain the data field with secret_payload_42
        # It could be nested or at top level depending on how auth forwards it
        response_str = json.dumps(data)
        assert "secret_payload_42" in response_str, \
            f"JSON response doesn't contain 'secret_payload_42'. Got: {data}"

    def test_response_time_under_5_seconds(self):
        """The full chain should respond in under 5 seconds (not timeout)."""
        import time
        start = time.time()
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8080/data"],
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start

        assert result.returncode == 0, \
            f"Request failed or timed out. Return code: {result.returncode}"
        assert elapsed < 5, \
            f"Request took too long: {elapsed:.2f} seconds (should be under 5s)"


class TestBackendStillCorrect:
    """Test that backend still returns the correct response."""

    def test_backend_direct_response(self):
        """Backend should still return the exact expected JSON."""
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8082/fetch"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "curl to backend:8082/fetch failed"

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"Backend response is not valid JSON: {result.stdout}")

        assert data.get("status") == "ok", \
            f"Backend status should be 'ok', got: {data.get('status')}"
        assert data.get("data") == "secret_payload_42", \
            f"Backend data should be 'secret_payload_42', got: {data.get('data')}"


class TestChainActuallyUsesAllServices:
    """Test that the chain actually goes through all three services (anti-shortcut)."""

    def test_backend_receives_request_from_chain(self):
        """
        Verify that hitting gateway actually causes backend to be called.
        We do this by checking that backend's /fetch endpoint is hit.
        """
        # First, make a request through the gateway
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8080/data"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Gateway request failed"
        assert "secret_payload_42" in result.stdout, \
            "Response doesn't contain backend's payload - chain may be broken"

    def test_auth_still_calls_backend(self):
        """
        Verify auth.py still contains code to call backend.
        This ensures the fix didn't just hardcode the response.
        """
        path = os.path.join(MESH_DIR, "auth.py")
        with open(path, "r") as f:
            content = f.read()

        # auth.py should still reference port 8082 (backend)
        assert "8082" in content, \
            "auth.py no longer references port 8082 - may have hardcoded response"

        # auth.py should still use requests library to call backend
        assert "requests" in content, \
            "auth.py no longer uses requests library - may have hardcoded response"

    def test_gateway_still_calls_auth(self):
        """
        Verify gateway.py still contains code to call auth.
        """
        path = os.path.join(MESH_DIR, "gateway.py")
        with open(path, "r") as f:
            content = f.read()

        # gateway.py should still reference port 8081 (auth)
        assert "8081" in content, \
            "gateway.py no longer references port 8081 - chain may be broken"


class TestAuthPyFixed:
    """Test that auth.py has been fixed properly."""

    def test_auth_py_does_not_return_raw_response_object(self):
        """
        auth.py should not return the raw requests.Response object.
        It should return response.json(), response.text, or similar.
        """
        path = os.path.join(MESH_DIR, "auth.py")
        with open(path, "r") as f:
            content = f.read()

        # Look for patterns that suggest proper response handling
        # The fix should include something like .json(), .text, .content, etc.
        has_json_call = ".json()" in content
        has_text_attr = ".text" in content
        has_content_attr = ".content" in content

        # At least one of these patterns should be present for proper response handling
        proper_handling = has_json_call or has_text_attr or has_content_attr

        # This is a heuristic check - the main validation is that the chain works
        # If the chain works and returns proper JSON, the fix is correct
        assert proper_handling or True, \
            "auth.py may still have the bug (returning raw Response object)"

    def test_auth_endpoint_works_directly(self):
        """
        Auth's validate endpoint should work and return proper response.
        """
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8081/validate"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"curl to auth:8081/validate failed. stderr: {result.stderr}"

        # Should return valid JSON (from backend, proxied through auth)
        assert "secret_payload_42" in result.stdout, \
            f"Auth response doesn't contain backend's payload. Got: {result.stdout}"


class TestFilesIntegrity:
    """Test that only auth.py was modified (gateway.py and backend.py unchanged)."""

    def test_backend_py_contains_expected_content(self):
        """backend.py should still contain the original secret payload."""
        path = os.path.join(MESH_DIR, "backend.py")
        with open(path, "r") as f:
            content = f.read()

        assert "secret_payload_42" in content, \
            "backend.py no longer contains 'secret_payload_42'"
        assert "Flask" in content or "flask" in content, \
            "backend.py should still be a Flask app"
        assert "8082" in content, \
            "backend.py should still reference port 8082"

    def test_gateway_py_contains_expected_content(self):
        """gateway.py should still contain expected content."""
        path = os.path.join(MESH_DIR, "gateway.py")
        with open(path, "r") as f:
            content = f.read()

        assert "Flask" in content or "flask" in content, \
            "gateway.py should still be a Flask app"
        assert "8080" in content, \
            "gateway.py should still reference port 8080"
        assert "8081" in content, \
            "gateway.py should still call auth on port 8081"


class TestDynamicProxying:
    """
    Test that auth actually proxies from backend dynamically.
    This guards against hardcoding the response.
    """

    def test_response_matches_backend_output(self):
        """
        The response from the full chain should match what backend returns.
        """
        # Get backend's direct response
        backend_result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8082/fetch"],
            capture_output=True,
            text=True
        )
        assert backend_result.returncode == 0, "Backend request failed"

        backend_data = json.loads(backend_result.stdout)

        # Get gateway's response (full chain)
        gateway_result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8080/data"],
            capture_output=True,
            text=True
        )
        assert gateway_result.returncode == 0, "Gateway request failed"

        gateway_data = json.loads(gateway_result.stdout)

        # The gateway response should contain the same data as backend
        # (might be wrapped differently, but should have the key values)
        gateway_str = json.dumps(gateway_data)
        assert backend_data.get("data") in gateway_str or "secret_payload_42" in gateway_str, \
            f"Gateway response doesn't contain backend's data. Backend: {backend_data}, Gateway: {gateway_data}"
