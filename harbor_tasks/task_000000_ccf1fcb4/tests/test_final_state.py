# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed the task.
This verifies the bug has been fixed and the Flask app serves correctly on port 5000.
"""

import os
import subprocess
import time
import socket
import pytest


BASE_DIR = "/home/user/labeler"


def kill_existing_gunicorn():
    """Kill any existing gunicorn processes to ensure clean state."""
    subprocess.run(["pkill", "-f", "gunicorn"], capture_output=True)
    time.sleep(1)


def start_service():
    """Start the service using start.sh and wait for it to be ready."""
    kill_existing_gunicorn()

    # Run start.sh from the labeler directory
    result = subprocess.run(
        ["./start.sh"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )

    # Give the daemon time to start
    time.sleep(3)
    return result


def is_port_listening(port, host="127.0.0.1", timeout=1):
    """Check if a port is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()


class TestSettingsIniFix:
    """Verify the bug in settings.ini has been fixed."""

    def test_settings_ini_has_correct_server_section(self):
        """settings.ini must have the correct [server] section header."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        result = subprocess.run(
            ["grep", "-q", r"^\[server\]", filepath],
            capture_output=True
        )
        assert result.returncode == 0, (
            "settings.ini does not have [server] section. "
            "The typo [sevrer] should be corrected to [server]."
        )

    def test_settings_ini_no_typo(self):
        """settings.ini must NOT have the typo [sevrer] anymore."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        with open(filepath, "r") as f:
            content = f.read()
        assert "[sevrer]" not in content, (
            "settings.ini still contains the typo [sevrer]. "
            "This should be corrected to [server]."
        )

    def test_settings_ini_has_port_5000(self):
        """settings.ini must still have port=5000 configured."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        with open(filepath, "r") as f:
            content = f.read()
        # Allow for different spacing styles
        has_port = "port=5000" in content or "port = 5000" in content
        assert has_port, "settings.ini does not have port=5000 configured"


class TestNoShortcuts:
    """Verify the fix was done correctly without shortcuts."""

    def test_gunicorn_conf_no_hardcoded_port(self):
        """gunicorn.conf.py must NOT have port 5000 hardcoded in bind."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        result = subprocess.run(
            ["grep", "-q", r"bind.*5000", filepath],
            capture_output=True
        )
        assert result.returncode != 0, (
            "gunicorn.conf.py has port 5000 hardcoded in bind. "
            "The fix should be in settings.ini, not by hardcoding the port."
        )

    def test_start_sh_no_hardcoded_port(self):
        """start.sh must NOT have port 5000 hardcoded."""
        filepath = os.path.join(BASE_DIR, "start.sh")
        with open(filepath, "r") as f:
            content = f.read()
        # Check for common patterns of hardcoding port in start.sh
        assert "-b 127.0.0.1:5000" not in content, (
            "start.sh has port 5000 hardcoded. "
            "The fix should be in settings.ini."
        )
        assert "--bind 127.0.0.1:5000" not in content, (
            "start.sh has port 5000 hardcoded. "
            "The fix should be in settings.ini."
        )
        assert "-b 0.0.0.0:5000" not in content, (
            "start.sh has port 5000 hardcoded. "
            "The fix should be in settings.ini."
        )
        assert "--bind 0.0.0.0:5000" not in content, (
            "start.sh has port 5000 hardcoded. "
            "The fix should be in settings.ini."
        )


class TestFilesUnchanged:
    """Verify that files that should remain unchanged are intact."""

    def test_app_init_has_create_app(self):
        """app/__init__.py must still have create_app factory function."""
        filepath = os.path.join(BASE_DIR, "app", "__init__.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "create_app" in content, (
            "app/__init__.py should not be modified - create_app is missing"
        )

    def test_app_routes_has_expected_response(self):
        """app/routes.py must still have the expected response."""
        filepath = os.path.join(BASE_DIR, "app", "routes.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "Labeler v2.1 running" in content, (
            "app/routes.py should not be modified - expected response is missing"
        )

    def test_start_sh_uses_gunicorn(self):
        """start.sh must still use gunicorn."""
        filepath = os.path.join(BASE_DIR, "start.sh")
        with open(filepath, "r") as f:
            content = f.read()
        assert "gunicorn" in content, (
            "start.sh should still use gunicorn, not be switched to flask dev server"
        )

    def test_gunicorn_conf_reads_settings(self):
        """gunicorn.conf.py must still read from settings.ini."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "settings.ini" in content, (
            "gunicorn.conf.py should still read from settings.ini"
        )


class TestServiceStarts:
    """Verify the service starts correctly on port 5000."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Start the service before tests and clean up after."""
        start_service()
        yield
        kill_existing_gunicorn()

    def test_gunicorn_process_running(self):
        """Gunicorn processes must be running after start.sh."""
        result = subprocess.run(
            ["pgrep", "-f", "gunicorn"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0 and result.stdout.strip(), (
            "No gunicorn processes are running. "
            "The service should start as a daemon."
        )

    def test_port_5000_listening(self):
        """Port 5000 must be listening after start.sh."""
        assert is_port_listening(5000), (
            "Port 5000 is not listening. "
            "After fixing settings.ini, the service should bind to port 5000."
        )

    def test_curl_localhost_5000_returns_expected(self):
        """curl localhost:5000 must return 'Labeler v2.1 running'."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5000/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"curl to localhost:5000 failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )
        assert "Labeler v2.1 running" in result.stdout, (
            f"Expected 'Labeler v2.1 running' in response, but got: {result.stdout}"
        )

    def test_port_8000_not_listening(self):
        """Port 8000 should NOT be listening (that was the fallback port)."""
        # This verifies the fix is correct - if the typo still existed,
        # the service would be on port 8000 due to the fallback
        if is_port_listening(8000):
            # Check if it's our gunicorn on 8000
            result = subprocess.run(
                ["curl", "-s", "http://localhost:8000/"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if "Labeler" in result.stdout:
                pytest.fail(
                    "The labeler service is running on port 8000 instead of 5000. "
                    "This suggests the settings.ini typo [sevrer] was not fixed to [server]."
                )


class TestServiceFunctionality:
    """Additional tests to verify service is fully functional."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Start the service before tests and clean up after."""
        start_service()
        yield
        kill_existing_gunicorn()

    def test_multiple_requests(self):
        """Service should handle multiple requests."""
        for i in range(3):
            result = subprocess.run(
                ["curl", "-s", "http://localhost:5000/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert "Labeler v2.1 running" in result.stdout, (
                f"Request {i+1} failed. Expected 'Labeler v2.1 running', got: {result.stdout}"
            )

    def test_http_status_200(self):
        """Service should return HTTP 200 status."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:5000/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.stdout.strip() == "200", (
            f"Expected HTTP 200, got: {result.stdout.strip()}"
        )
