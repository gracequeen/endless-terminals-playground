import os
import subprocess
import pytest


class TestInitialState:
    def test_repo_exists(self):
        assert os.path.isdir("/home/user/app-generation-gateway")

    def test_package_json_exists(self):
        assert os.path.isfile("/home/user/app-generation-gateway/package.json")

    def test_node_modules_installed(self):
        assert os.path.isdir("/home/user/app-generation-gateway/node_modules")

    def test_server_js_exists(self):
        assert os.path.isfile("/home/user/app-generation-gateway/srv/server.js")

    def test_npm_test_unit_fails(self):
        result = subprocess.run(
            ["npm", "run", "test:unit"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode != 0, \
            "Expected some tests to fail in the initial state"
