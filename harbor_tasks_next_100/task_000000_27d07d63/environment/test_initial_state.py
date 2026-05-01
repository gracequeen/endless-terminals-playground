# test_initial_state.py
"""
Tests to validate the initial state before the student performs the action.
Verifies that the Flask health check app exists but is not yet running.
"""

import os
import subprocess
import sys
import pytest


# Expected content of app.py
EXPECTED_APP_CONTENT = '''from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
'''


class TestInitialState:
    """Test suite to validate the initial state of the system."""

    def test_healthcheck_directory_exists(self):
        """Verify /home/user/healthcheck directory exists."""
        path = "/home/user/healthcheck"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_healthcheck_directory_writable(self):
        """Verify /home/user/healthcheck directory is writable."""
        path = "/home/user/healthcheck"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_app_py_exists(self):
        """Verify /home/user/healthcheck/app.py exists."""
        path = "/home/user/healthcheck/app.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_app_py_content(self):
        """Verify /home/user/healthcheck/app.py contains the expected Flask app code."""
        path = "/home/user/healthcheck/app.py"
        with open(path, 'r') as f:
            content = f.read()

        # Normalize whitespace for comparison
        expected_normalized = EXPECTED_APP_CONTENT.strip()
        actual_normalized = content.strip()

        assert actual_normalized == expected_normalized, (
            f"File {path} does not contain the expected content.\n"
            f"Expected:\n{expected_normalized}\n\n"
            f"Actual:\n{actual_normalized}"
        )

    def test_flask_installed(self):
        """Verify Flask is installed in the Python environment."""
        result = subprocess.run(
            [sys.executable, "-c", "import flask; print(flask.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Flask is not installed. Error: {result.stderr}"
        )

    def test_python_version(self):
        """Verify Python version is 3.10 or higher."""
        version_info = sys.version_info
        assert version_info.major == 3 and version_info.minor >= 10, (
            f"Python version must be 3.10+, but found {version_info.major}.{version_info.minor}"
        )

    def test_port_8080_not_in_use(self):
        """Verify port 8080 is not currently in use."""
        # Use ss to check if anything is listening on port 8080
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )

        # Check if port 8080 appears in the output
        lines = result.stdout.split('\n')
        for line in lines:
            if ':8080' in line and 'LISTEN' in line:
                pytest.fail(
                    f"Port 8080 is already in use. Found: {line}\n"
                    "The port should be free before starting the health check server."
                )

    def test_no_flask_process_on_8080(self):
        """Verify no Flask/Python process is already serving on port 8080."""
        # Check using lsof if available, otherwise use ss
        result = subprocess.run(
            ["ss", "-tlnp", "sport", "=", ":8080"],
            capture_output=True,
            text=True
        )

        # If there's any output with LISTEN state, something is on 8080
        if 'LISTEN' in result.stdout:
            pytest.fail(
                f"A process is already listening on port 8080:\n{result.stdout}\n"
                "Expected port 8080 to be free."
            )

    def test_curl_available(self):
        """Verify curl is available on the system."""
        result = subprocess.run(
            ["which", "curl"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "curl is not available on this system. "
            "It is required for testing the health endpoint."
        )

    def test_curl_works(self):
        """Verify curl can be executed."""
        result = subprocess.run(
            ["curl", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"curl --version failed: {result.stderr}"
        )
