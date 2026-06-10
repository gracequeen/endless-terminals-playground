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

    def test_execute_http_request_used(self):
        """Verify the production BTP path is implemented in event-proxy.js."""
        result = subprocess.run(
            ["grep", "-n", "executeHttpRequest", "src/lib/event-proxy.js"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0, \
            "executeHttpRequest not found in src/lib/event-proxy.js — production BTP path not implemented"

    def test_destination_binding_detection(self):
        """Verify VCAP_SERVICES destination detection is present."""
        result = subprocess.run(
            ["grep", "-n", "destination", "src/lib/event-proxy.js"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0 and "destination" in result.stdout, \
            "No destination binding detection found in src/lib/event-proxy.js"

    # TODO: add specific FAIL_TO_PASS test assertions once base_commit is resolved
