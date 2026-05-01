# test_final_state.py
"""
Tests to validate the final state after the student has completed the task.
Verifies that the Flask health check app is running and responding correctly on port 8080.
"""

import json
import os
import subprocess
import socket
import time
import pytest


# Expected content of app.py (must remain unchanged)
EXPECTED_APP_CONTENT = '''from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
'''


class TestFinalState:
    """Test suite to validate the final state after task completion."""

    def test_app_py_unchanged(self):
        """Verify /home/user/healthcheck/app.py remains byte-identical to its initial state."""
        path = "/home/user/healthcheck/app.py"
        assert os.path.isfile(path), f"File {path} no longer exists - it should not be modified or deleted"

        with open(path, 'r') as f:
            content = f.read()

        # Normalize whitespace for comparison
        expected_normalized = EXPECTED_APP_CONTENT.strip()
        actual_normalized = content.strip()

        assert actual_normalized == expected_normalized, (
            f"File {path} has been modified but should remain unchanged.\n"
            f"Expected:\n{expected_normalized}\n\n"
            f"Actual:\n{actual_normalized}"
        )

    def test_port_8080_listening(self):
        """Verify that something is listening on port 8080."""
        # Try to connect to port 8080
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex(('localhost', 8080))
            assert result == 0, (
                f"No process is listening on port 8080. "
                f"The Flask health check server should be running and accepting connections."
            )
        finally:
            sock.close()

    def test_process_running_on_8080(self):
        """Verify a process is actively listening on port 8080 using ss."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )

        found_listener = False
        lines = result.stdout.split('\n')
        for line in lines:
            if ':8080' in line and 'LISTEN' in line:
                found_listener = True
                break

        assert found_listener, (
            "No process found listening on port 8080.\n"
            f"ss output:\n{result.stdout}\n"
            "The Flask health check server should be running in the background."
        )

    def test_health_endpoint_responds(self):
        """Verify that curl can reach the /health endpoint."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, (
            f"curl failed to connect to http://localhost:8080/health. "
            f"Error: {result.stderr}"
        )

        http_code = result.stdout.strip()
        assert http_code == "200", (
            f"Expected HTTP 200 response from /health endpoint, but got {http_code}. "
            "The Flask server should return a successful response."
        )

    def test_health_endpoint_returns_valid_json(self):
        """Verify that /health returns valid JSON."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, (
            f"curl failed to connect to http://localhost:8080/health. "
            f"Error: {result.stderr}"
        )

        response_body = result.stdout.strip()

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"Response from /health is not valid JSON.\n"
                f"Response body: {response_body}\n"
                f"JSON parse error: {e}"
            )

    def test_health_endpoint_returns_status_ok(self):
        """Verify that /health returns JSON with status='ok'."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, (
            f"curl failed to connect to http://localhost:8080/health. "
            f"Error: {result.stderr}"
        )

        response_body = result.stdout.strip()

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"Response from /health is not valid JSON.\n"
                f"Response body: {response_body}\n"
                f"JSON parse error: {e}"
            )

        assert "status" in parsed, (
            f"Response JSON does not contain 'status' key.\n"
            f"Response: {parsed}\n"
            f"Expected: {{\"status\": \"ok\"}}"
        )

        assert parsed["status"] == "ok", (
            f"Response JSON 'status' value is not 'ok'.\n"
            f"Got: {parsed['status']}\n"
            f"Expected: 'ok'"
        )

    def test_health_endpoint_only_has_status_key(self):
        """Verify that /health returns JSON with exactly the expected structure."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, (
            f"curl failed to connect to http://localhost:8080/health. "
            f"Error: {result.stderr}"
        )

        response_body = result.stdout.strip()
        parsed = json.loads(response_body)

        # The expected response is {"status": "ok"} - just one key
        assert parsed == {"status": "ok"}, (
            f"Response JSON does not match expected structure.\n"
            f"Got: {parsed}\n"
            f"Expected: {{\"status\": \"ok\"}}"
        )

    def test_server_is_http_server(self):
        """Verify the server responds with proper HTTP headers."""
        result = subprocess.run(
            ["curl", "-s", "-I", "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, (
            f"curl failed to get headers from http://localhost:8080/health. "
            f"Error: {result.stderr}"
        )

        headers = result.stdout

        # Check for HTTP response line
        assert "HTTP/" in headers, (
            f"Response does not appear to be a valid HTTP response.\n"
            f"Headers: {headers}\n"
            "Expected HTTP protocol response headers."
        )

        # Check for 200 OK status
        assert "200" in headers.split('\n')[0], (
            f"HTTP response status is not 200 OK.\n"
            f"Headers: {headers}"
        )

    def test_server_continues_running(self):
        """Verify the server continues to respond after multiple requests (not a one-shot)."""
        # Make multiple requests to ensure server stays up
        for i in range(3):
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8080/health"],
                capture_output=True,
                text=True,
                timeout=10
            )

            assert result.returncode == 0, (
                f"Request {i+1} failed. Server may have stopped.\n"
                f"Error: {result.stderr}"
            )

            parsed = json.loads(result.stdout.strip())
            assert parsed == {"status": "ok"}, (
                f"Request {i+1} returned unexpected response: {parsed}"
            )

            # Small delay between requests
            time.sleep(0.1)
