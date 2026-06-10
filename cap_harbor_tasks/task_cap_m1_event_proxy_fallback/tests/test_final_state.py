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

    def test_fallback_path_present(self):
        """Verify fallback to webagentsUrl is implemented in event-proxy.js."""
        result = subprocess.run(
            ["grep", "-n", "webagentsUrl", "src/lib/event-proxy.js"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0, \
            "No fallback to webagentsUrl found in src/lib/event-proxy.js"

    # TODO: add specific FAIL_TO_PASS test assertions once base_commit is resolved
