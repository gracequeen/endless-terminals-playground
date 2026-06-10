import os
import subprocess
import pytest


class TestInitialState:
    def test_repo_exists(self):
        assert os.path.isdir("/home/user/app-generation-gateway"), \
            "Repo not found at /home/user/app-generation-gateway"

    def test_package_json_exists(self):
        assert os.path.isfile("/home/user/app-generation-gateway/package.json")

    def test_node_modules_installed(self):
        assert os.path.isdir("/home/user/app-generation-gateway/node_modules"), \
            "node_modules missing — npm install may not have run"

    def test_npm_test_unit_fails(self):
        """Tests exist but should fail before the fix is applied."""
        # TODO: tighten to specific FAIL_TO_PASS test IDs once base_commit is resolved
        result = subprocess.run(
            ["npm", "run", "test:unit"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode != 0, \
            "Expected some tests to fail in the initial state (test_patch applied, non_test_patch not applied)"
