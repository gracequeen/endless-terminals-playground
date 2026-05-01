# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
sets up the Express server at /home/user/api.
"""

import os
import json
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the student performs the task."""

    def test_api_directory_exists(self):
        """Check that /home/user/api directory exists."""
        api_dir = "/home/user/api"
        assert os.path.isdir(api_dir), f"Directory {api_dir} does not exist"

    def test_api_directory_is_writable(self):
        """Check that /home/user/api directory is writable."""
        api_dir = "/home/user/api"
        assert os.access(api_dir, os.W_OK), f"Directory {api_dir} is not writable"

    def test_package_json_exists(self):
        """Check that /home/user/api/package.json exists."""
        package_json_path = "/home/user/api/package.json"
        assert os.path.isfile(package_json_path), f"File {package_json_path} does not exist"

    def test_package_json_content(self):
        """Check that package.json has the expected content."""
        package_json_path = "/home/user/api/package.json"
        with open(package_json_path, 'r') as f:
            content = json.load(f)

        assert content.get("name") == "api", \
            f"package.json 'name' should be 'api', got '{content.get('name')}'"
        assert content.get("version") == "1.0.0", \
            f"package.json 'version' should be '1.0.0', got '{content.get('version')}'"
        assert content.get("main") == "server.js", \
            f"package.json 'main' should be 'server.js', got '{content.get('main')}'"

    def test_node_modules_does_not_exist(self):
        """Check that node_modules directory does NOT exist (express not installed yet)."""
        node_modules_path = "/home/user/api/node_modules"
        assert not os.path.exists(node_modules_path), \
            f"Directory {node_modules_path} should NOT exist yet (express should not be installed)"

    def test_server_js_does_not_exist(self):
        """Check that server.js does NOT exist yet."""
        server_js_path = "/home/user/api/server.js"
        assert not os.path.exists(server_js_path), \
            f"File {server_js_path} should NOT exist yet (student needs to create it)"

    def test_nodejs_is_available(self):
        """Check that Node.js is available and is version 20.x."""
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Node.js is not available (node --version failed)"
        version = result.stdout.strip()
        assert version.startswith("v20."), \
            f"Node.js should be version 20.x, got {version}"

    def test_npm_is_available(self):
        """Check that npm is available."""
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "npm is not available (npm --version failed)"
        # Just check that we got a version string
        version = result.stdout.strip()
        assert version, "npm version string is empty"

    def test_port_3000_is_not_in_use(self):
        """Check that port 3000 is not currently in use."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if port 3000 appears in the listening ports
        if ":3000 " in result.stdout or ":3000\t" in result.stdout:
            pytest.fail("Port 3000 is already in use - it should be free for the student's server")
