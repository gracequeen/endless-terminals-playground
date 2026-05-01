# test_final_state.py
"""
Tests to validate the final state after the student has fixed the config templating bug.

The fix should ensure:
1. `./render.py staging web-api` outputs database.host as `db-staging.internal`
2. `./render.py production web-api` still outputs database.host as `db-prod.internal`
3. Staging web-api still has features.debug_mode as true
4. Production web-api still has database.pool_size as 100
5. The fix addresses the root cause (legacy file or load order), not a workaround
"""

import os
import subprocess
import pytest
import yaml
from pathlib import Path


BASE_DIR = Path("/home/user/deploy")


def run_render(environment: str, service: str) -> dict:
    """Run render.py and return parsed YAML output."""
    result = subprocess.run(
        ["python3", str(BASE_DIR / "render.py"), environment, service],
        capture_output=True,
        text=True,
        cwd=str(BASE_DIR)
    )
    if result.returncode != 0:
        raise RuntimeError(f"render.py failed with exit code {result.returncode}: {result.stderr}")
    return yaml.safe_load(result.stdout) or {}


class TestStagingWebApiFixed:
    """Verify the main bug is fixed: staging web-api should have correct db host."""

    def test_staging_web_api_has_correct_database_host(self):
        """The primary fix: staging web-api must return db-staging.internal."""
        config = run_render("staging", "web-api")

        assert "database" in config, "Config should have 'database' section"
        assert "host" in config["database"], "Database section should have 'host' key"

        actual_host = config["database"]["host"]
        expected_host = "db-staging.internal"

        assert actual_host == expected_host, (
            f"Staging web-api database.host should be '{expected_host}', "
            f"but got '{actual_host}'. The bug is not fixed."
        )

    def test_staging_web_api_has_debug_mode_enabled(self):
        """Staging web-api should still have features.debug_mode as true."""
        config = run_render("staging", "web-api")

        assert "features" in config, "Config should have 'features' section"
        assert "debug_mode" in config["features"], "Features section should have 'debug_mode' key"

        assert config["features"]["debug_mode"] is True, (
            f"Staging web-api features.debug_mode should be True, "
            f"but got {config['features']['debug_mode']}"
        )

    def test_staging_web_api_render_succeeds(self):
        """Render script should complete without errors for staging web-api."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py"), "staging", "web-api"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        assert result.returncode == 0, f"render.py failed: {result.stderr}"


class TestProductionWebApiStillWorks:
    """Verify production web-api still works correctly after the fix."""

    def test_production_web_api_has_correct_database_host(self):
        """Production web-api must still return db-prod.internal."""
        config = run_render("production", "web-api")

        assert "database" in config, "Config should have 'database' section"
        assert "host" in config["database"], "Database section should have 'host' key"

        actual_host = config["database"]["host"]
        expected_host = "db-prod.internal"

        assert actual_host == expected_host, (
            f"Production web-api database.host should be '{expected_host}', "
            f"but got '{actual_host}'. The fix broke production."
        )

    def test_production_web_api_has_correct_pool_size(self):
        """Production web-api should have database.pool_size as 100."""
        config = run_render("production", "web-api")

        assert "database" in config, "Config should have 'database' section"
        assert "pool_size" in config["database"], "Database section should have 'pool_size' key"

        actual_pool_size = config["database"]["pool_size"]
        expected_pool_size = 100

        assert actual_pool_size == expected_pool_size, (
            f"Production web-api database.pool_size should be {expected_pool_size}, "
            f"but got {actual_pool_size}"
        )

    def test_production_web_api_render_succeeds(self):
        """Render script should complete without errors for production web-api."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py"), "production", "web-api"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        assert result.returncode == 0, f"render.py failed: {result.stderr}"


class TestAntiShortcutGuards:
    """Ensure the fix addresses root cause, not a workaround."""

    def test_staging_override_does_not_hardcode_db_host(self):
        """
        The staging override should NOT have db-staging.internal hardcoded.
        This would be a workaround that defeats the layering purpose.
        """
        override_path = BASE_DIR / "overrides" / "staging" / "web-api.yaml"

        if not override_path.exists():
            # File might have been removed as part of a valid fix
            return

        content = override_path.read_text()

        # Count occurrences of db-staging in this file
        # It should be 0 - the host should come from the environment layer
        db_staging_count = content.count("db-staging")

        assert db_staging_count == 0, (
            f"Found 'db-staging' {db_staging_count} time(s) in staging override file. "
            "This is a workaround, not a proper fix. The database host should come from "
            "the environment layer (environments/staging.yaml), not be duplicated in the override."
        )

    def test_legacy_file_root_cause_addressed(self):
        """
        The root cause must be addressed. Either:
        1. The legacy file is removed/renamed, OR
        2. The legacy file no longer contains database.host, OR
        3. The load order in render.py is changed so legacy doesn't affect final output inappropriately

        We verify by checking that the bug is fixed (covered by other tests) and that
        the staging override doesn't have the workaround (covered above).
        This test checks the legacy file state.
        """
        legacy_path = BASE_DIR / "overrides" / ".legacy" / "web-api.yaml"

        if not legacy_path.exists():
            # Legacy file was removed - valid fix
            return

        content = legacy_path.read_text()
        legacy_config = yaml.safe_load(content) or {}

        # If legacy file still exists, check if it still has database.host
        if "database" in legacy_config and "host" in legacy_config.get("database", {}):
            # Legacy file still has database.host - the fix must be in render.py load order
            # We verify by checking that staging still works (other tests cover this)
            # Just note this for informational purposes
            pass

    def test_environments_staging_yaml_unchanged(self):
        """The environments/staging.yaml file must remain unchanged."""
        staging_env_path = BASE_DIR / "environments" / "staging.yaml"

        assert staging_env_path.exists(), "environments/staging.yaml should still exist"

        content = staging_env_path.read_text()
        config = yaml.safe_load(content) or {}

        # Verify expected content
        assert "database" in config, "staging.yaml should have database section"
        assert config["database"].get("host") == "db-staging.internal", (
            "staging.yaml database.host should be db-staging.internal"
        )
        assert config["database"].get("pool_size") == 10, (
            "staging.yaml database.pool_size should be 10"
        )
        assert "cache" in config, "staging.yaml should have cache section"
        assert config["cache"].get("host") == "redis-staging.internal", (
            "staging.yaml cache.host should be redis-staging.internal"
        )


class TestDeepMergeFunctionIntact:
    """Verify the deep_merge function logic remains intact."""

    def test_render_py_still_has_deep_merge_function(self):
        """The deep_merge function should still exist in render.py."""
        render_py = BASE_DIR / "render.py"
        content = render_py.read_text()

        assert "def deep_merge" in content, (
            "render.py should still contain the deep_merge function definition"
        )

    def test_deep_merge_recursive_logic_intact(self):
        """The deep_merge function should still have recursive merge logic."""
        render_py = BASE_DIR / "render.py"
        content = render_py.read_text()

        # Check for key recursive merge patterns
        assert "deep_merge" in content, "deep_merge function should exist"
        # The function should still do recursive merging
        assert "isinstance" in content or "dict" in content, (
            "deep_merge should still check for dict types for recursive merging"
        )


class TestOtherConfigurationsNotBroken:
    """Verify the fix doesn't break other service/environment combinations."""

    def test_render_py_still_executable(self):
        """render.py should still be runnable."""
        render_py = BASE_DIR / "render.py"
        assert render_py.exists(), "render.py should exist"
        assert os.access(render_py, os.R_OK), "render.py should be readable"

    def test_staging_web_api_has_expected_structure(self):
        """Staging web-api config should have all expected sections."""
        config = run_render("staging", "web-api")

        # Check all expected top-level sections exist
        assert "database" in config, "Config should have 'database' section"
        assert "cache" in config, "Config should have 'cache' section"
        assert "features" in config, "Config should have 'features' section"
        assert "logging" in config, "Config should have 'logging' section"

    def test_production_web_api_has_expected_structure(self):
        """Production web-api config should have all expected sections."""
        config = run_render("production", "web-api")

        # Check all expected top-level sections exist
        assert "database" in config, "Config should have 'database' section"
        assert "cache" in config, "Config should have 'cache' section"
        assert "features" in config, "Config should have 'features' section"
        assert "logging" in config, "Config should have 'logging' section"

    def test_staging_inherits_base_logging_level(self):
        """Staging should inherit logging.level from base (INFO)."""
        config = run_render("staging", "web-api")

        assert "logging" in config, "Config should have 'logging' section"
        assert config["logging"].get("level") == "INFO", (
            "Staging should inherit logging.level INFO from base"
        )

    def test_production_has_warning_logging_level(self):
        """Production should have logging.level WARNING from production env."""
        config = run_render("production", "web-api")

        assert "logging" in config, "Config should have 'logging' section"
        assert config["logging"].get("level") == "WARNING", (
            "Production should have logging.level WARNING"
        )


class TestRenderScriptFunctionality:
    """Verify render.py still functions correctly."""

    def test_render_py_usage_message(self):
        """render.py should show usage when called without arguments."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py")],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        # Should exit with non-zero and show usage
        assert result.returncode != 0, "render.py should exit with error when no args"
        assert "usage" in result.stderr.lower() or "Usage" in result.stderr, (
            "render.py should show usage message"
        )

    def test_render_py_outputs_valid_yaml(self):
        """render.py output should be valid YAML."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py"), "staging", "web-api"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        assert result.returncode == 0, f"render.py failed: {result.stderr}"

        # Should be parseable as YAML
        try:
            parsed = yaml.safe_load(result.stdout)
            assert parsed is not None, "Output should not be empty"
            assert isinstance(parsed, dict), "Output should be a dictionary"
        except yaml.YAMLError as e:
            pytest.fail(f"render.py output is not valid YAML: {e}")
