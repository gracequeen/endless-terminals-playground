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

    def test_trust_proxy_configured(self):
        """Verify the fix is present: app.set('trust proxy', 1) in server.js."""
        result = subprocess.run(
            ["grep", "-r", "trust proxy", "srv/"],
            cwd="/home/user/app-generation-gateway",
            capture_output=True, text=True
        )
        assert result.returncode == 0, \
            "Could not find 'trust proxy' setting in srv/ — fix not applied"

    # TODO: add specific FAIL_TO_PASS test assertions once base_commit is resolved
