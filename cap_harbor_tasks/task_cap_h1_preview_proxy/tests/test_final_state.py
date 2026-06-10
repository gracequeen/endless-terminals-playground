import subprocess
import pytest


class TestFinalState:
    def test_unit_tests_pass(self):
        result = subprocess.run(
            ["npm", "run", "test:unit"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0, \
            f"Unit tests failed:\n{result.stdout[-3000:]}\n{result.stderr[-1000:]}"

    def test_preview_proxy_file_exists(self):
        import os
        assert os.path.isfile("/home/user/app-generation-gateway/src/lib/preview-proxy.js"), \
            "src/lib/preview-proxy.js not found — proxy not implemented"

    def test_proxy_registered_in_server(self):
        result = subprocess.run(
            ["grep", "-n", "preview-proxy", "srv/server.js"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0, \
            "preview-proxy not imported/registered in srv/server.js"

    def test_preview_route_registered(self):
        result = subprocess.run(
            ["grep", "-n", "api/preview", "srv/server.js"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0, \
            "/api/preview route not registered in srv/server.js"

    def test_csp_header_present_in_proxy(self):
        result = subprocess.run(
            ["grep", "-n", "Content-Security-Policy", "src/lib/preview-proxy.js"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0, \
            "Content-Security-Policy not set in src/lib/preview-proxy.js"

    # TODO: add specific FAIL_TO_PASS test assertions once base_commit is resolved
