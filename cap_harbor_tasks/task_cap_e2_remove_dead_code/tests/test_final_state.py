import os
import json
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

    def test_dead_files_removed(self):
        base = "/home/user/app-generation-gateway"
        for path in ["src/lib/errors.js", "src/lib/errors.test.js"]:
            assert not os.path.exists(os.path.join(base, path)), \
                f"{path} should have been removed"

    def test_migrations_dir_removed(self):
        assert not os.path.isdir("/home/user/app-generation-gateway/src/migrations"), \
            "src/migrations/ should have been removed"

    def test_package_json_cleaned(self):
        with open("/home/user/app-generation-gateway/package.json") as f:
            pkg = json.load(f)
        dev_deps = pkg.get("devDependencies", {})
        assert "chai" not in dev_deps, "chai should be removed from devDependencies"
        assert "@eslint/js" not in dev_deps, "@eslint/js should be removed from devDependencies"

    # TODO: add specific FAIL_TO_PASS test assertions once base_commit is resolved
