# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has set up the Express server at /home/user/api.
"""

import os
import json
import subprocess
import socket
import time
import re
import signal
import pytest


class TestFinalState:
    """Validate the final state after the student completes the task."""

    def test_server_js_exists(self):
        """Check that /home/user/api/server.js exists."""
        server_js_path = "/home/user/api/server.js"
        assert os.path.isfile(server_js_path), \
            f"File {server_js_path} does not exist - student needs to create server.js"

    def test_express_installed(self):
        """Check that express is installed (node_modules/express exists)."""
        express_path = "/home/user/api/node_modules/express"
        assert os.path.exists(express_path), \
            f"Directory {express_path} does not exist - express is not installed. Run 'npm install express' in /home/user/api"

    def test_package_json_still_exists(self):
        """Check that package.json still exists."""
        package_json_path = "/home/user/api/package.json"
        assert os.path.isfile(package_json_path), \
            f"File {package_json_path} should still exist"

    def test_server_js_uses_express_or_http(self):
        """Check that server.js uses express or http module (anti-shortcut guard)."""
        server_js_path = "/home/user/api/server.js"

        with open(server_js_path, 'r') as f:
            content = f.read()

        # Check for express or http module usage
        express_pattern = r'require\s*\(\s*["\']express["\']\s*\)|from\s+["\']express["\']'
        http_pattern = r'require\s*\(\s*["\']http["\']\s*\)|from\s+["\']http["\']'

        uses_express = re.search(express_pattern, content) is not None
        uses_http = re.search(http_pattern, content) is not None

        assert uses_express or uses_http, \
            "server.js must use 'express' or 'http' module - found neither require('express')/require('http') nor ES6 imports"

    def test_server_js_has_health_endpoint(self):
        """Check that server.js implements a /health endpoint in code."""
        server_js_path = "/home/user/api/server.js"

        with open(server_js_path, 'r') as f:
            content = f.read()

        # Check for /health route definition
        health_patterns = [
            r'["\']/health["\']',  # String literal '/health'
            r'\.get\s*\([^)]*health',  # .get() with health
            r'\.all\s*\([^)]*health',  # .all() with health
            r'url\s*[=!]==?\s*["\']/health["\']',  # url === '/health' or url == '/health'
            r'pathname\s*[=!]==?\s*["\']/health["\']',  # pathname check
        ]

        found_health = any(re.search(pattern, content, re.IGNORECASE) for pattern in health_patterns)
        assert found_health, \
            "server.js must implement a /health endpoint in code - could not find '/health' route definition"


class TestServerFunctionality:
    """Test that the server actually works correctly."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Start the server before tests and clean up after."""
        self.server_process = None

        # Kill any existing process on port 3000
        subprocess.run(
            ["pkill", "-f", "node.*server.js"],
            capture_output=True
        )
        time.sleep(0.5)

        # Start the server
        self.server_process = subprocess.Popen(
            ["node", "server.js"],
            cwd="/home/user/api",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )

        # Wait for server to start (try connecting to port 3000)
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 3000))
                sock.close()
                if result == 0:
                    break
            except:
                pass
            time.sleep(0.2)
        else:
            # Server didn't start, get error output
            if self.server_process:
                self.server_process.terminate()
                _, stderr = self.server_process.communicate(timeout=2)
                pytest.fail(f"Server failed to start on port 3000 within timeout. Stderr: {stderr.decode()}")

        yield

        # Cleanup: kill the server process
        if self.server_process:
            try:
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
            except:
                pass
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=2)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass

    def test_server_responds_on_port_3000(self):
        """Check that server is listening on port 3000."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 3000))
        sock.close()
        assert result == 0, "Server is not responding on port 3000"

    def test_health_endpoint_returns_correct_json(self):
        """Check that GET /health returns {"status":"ok"}."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:3000/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"curl command failed with return code {result.returncode}"

        response_body = result.stdout.strip()
        assert response_body, "Response body is empty"

        try:
            response_json = json.loads(response_body)
        except json.JSONDecodeError as e:
            pytest.fail(f"Response is not valid JSON: '{response_body}'. Error: {e}")

        assert response_json.get("status") == "ok", \
            f"Expected {{'status': 'ok'}}, got {response_json}"

    def test_health_endpoint_content_type_is_json(self):
        """Check that GET /health returns content-type application/json."""
        result = subprocess.run(
            ["curl", "-sI", "http://localhost:3000/health"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"curl command failed with return code {result.returncode}"

        headers = result.stdout.lower()
        assert "content-type" in headers, \
            f"No Content-Type header found in response headers: {result.stdout}"

        # Check that content-type contains application/json
        assert "application/json" in headers, \
            f"Content-Type should be application/json. Headers received: {result.stdout}"
