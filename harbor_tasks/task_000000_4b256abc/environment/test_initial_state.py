# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the debugging task for the config templating system.
"""

import os
import subprocess
import pytest
from pathlib import Path


BASE_DIR = Path("/home/user/deploy")


class TestDirectoryStructure:
    """Verify the expected directory structure exists."""

    def test_deploy_directory_exists(self):
        assert BASE_DIR.exists(), f"Deploy directory {BASE_DIR} does not exist"
        assert BASE_DIR.is_dir(), f"{BASE_DIR} is not a directory"

    def test_base_directory_exists(self):
        base_dir = BASE_DIR / "base"
        assert base_dir.exists(), f"Base directory {base_dir} does not exist"
        assert base_dir.is_dir(), f"{base_dir} is not a directory"

    def test_environments_directory_exists(self):
        env_dir = BASE_DIR / "environments"
        assert env_dir.exists(), f"Environments directory {env_dir} does not exist"
        assert env_dir.is_dir(), f"{env_dir} is not a directory"

    def test_services_directory_exists(self):
        svc_dir = BASE_DIR / "services"
        assert svc_dir.exists(), f"Services directory {svc_dir} does not exist"
        assert svc_dir.is_dir(), f"{svc_dir} is not a directory"

    def test_overrides_directory_exists(self):
        overrides_dir = BASE_DIR / "overrides"
        assert overrides_dir.exists(), f"Overrides directory {overrides_dir} does not exist"
        assert overrides_dir.is_dir(), f"{overrides_dir} is not a directory"

    def test_overrides_staging_directory_exists(self):
        staging_dir = BASE_DIR / "overrides" / "staging"
        assert staging_dir.exists(), f"Staging overrides directory {staging_dir} does not exist"
        assert staging_dir.is_dir(), f"{staging_dir} is not a directory"

    def test_overrides_production_directory_exists(self):
        prod_dir = BASE_DIR / "overrides" / "production"
        assert prod_dir.exists(), f"Production overrides directory {prod_dir} does not exist"
        assert prod_dir.is_dir(), f"{prod_dir} is not a directory"

    def test_legacy_hidden_directory_exists(self):
        """The hidden .legacy directory must exist as it's part of the bug."""
        legacy_dir = BASE_DIR / "overrides" / ".legacy"
        assert legacy_dir.exists(), f"Legacy hidden directory {legacy_dir} does not exist (this is part of the bug)"
        assert legacy_dir.is_dir(), f"{legacy_dir} is not a directory"


class TestRequiredFiles:
    """Verify all required configuration files exist."""

    def test_render_py_exists(self):
        render_py = BASE_DIR / "render.py"
        assert render_py.exists(), f"render.py script {render_py} does not exist"
        assert render_py.is_file(), f"{render_py} is not a file"

    def test_render_py_is_executable_or_readable(self):
        render_py = BASE_DIR / "render.py"
        assert os.access(render_py, os.R_OK), f"{render_py} is not readable"

    def test_base_defaults_yaml_exists(self):
        defaults = BASE_DIR / "base" / "defaults.yaml"
        assert defaults.exists(), f"Base defaults file {defaults} does not exist"
        assert defaults.is_file(), f"{defaults} is not a file"

    def test_environments_staging_yaml_exists(self):
        staging = BASE_DIR / "environments" / "staging.yaml"
        assert staging.exists(), f"Staging environment file {staging} does not exist"
        assert staging.is_file(), f"{staging} is not a file"

    def test_environments_production_yaml_exists(self):
        production = BASE_DIR / "environments" / "production.yaml"
        assert production.exists(), f"Production environment file {production} does not exist"
        assert production.is_file(), f"{production} is not a file"

    def test_services_web_api_yaml_exists(self):
        web_api = BASE_DIR / "services" / "web-api.yaml"
        assert web_api.exists(), f"Web-api service file {web_api} does not exist"
        assert web_api.is_file(), f"{web_api} is not a file"

    def test_overrides_staging_web_api_yaml_exists(self):
        override = BASE_DIR / "overrides" / "staging" / "web-api.yaml"
        assert override.exists(), f"Staging web-api override file {override} does not exist"
        assert override.is_file(), f"{override} is not a file"

    def test_overrides_production_web_api_yaml_exists(self):
        override = BASE_DIR / "overrides" / "production" / "web-api.yaml"
        assert override.exists(), f"Production web-api override file {override} does not exist"
        assert override.is_file(), f"{override} is not a file"

    def test_legacy_web_api_yaml_exists(self):
        """The hidden legacy file must exist as it's the source of the bug."""
        legacy = BASE_DIR / "overrides" / ".legacy" / "web-api.yaml"
        assert legacy.exists(), f"Legacy web-api file {legacy} does not exist (this is the bug source)"
        assert legacy.is_file(), f"{legacy} is not a file"


class TestFileContents:
    """Verify file contents match expected initial state."""

    def test_base_defaults_contains_db_dev(self):
        defaults = BASE_DIR / "base" / "defaults.yaml"
        content = defaults.read_text()
        assert "db-dev.internal" in content, "Base defaults should contain db-dev.internal"

    def test_staging_env_contains_db_staging(self):
        staging = BASE_DIR / "environments" / "staging.yaml"
        content = staging.read_text()
        assert "db-staging.internal" in content, "Staging environment should contain db-staging.internal"

    def test_production_env_contains_db_prod(self):
        production = BASE_DIR / "environments" / "production.yaml"
        content = production.read_text()
        assert "db-prod.internal" in content, "Production environment should contain db-prod.internal"

    def test_legacy_file_contains_db_prod(self):
        """The legacy file must contain db-prod.internal as this is the bug."""
        legacy = BASE_DIR / "overrides" / ".legacy" / "web-api.yaml"
        content = legacy.read_text()
        assert "db-prod.internal" in content, "Legacy file should contain db-prod.internal (this is the bug)"

    def test_render_py_contains_legacy_loading_code(self):
        """Verify render.py has the legacy loading code that causes the bug."""
        render_py = BASE_DIR / "render.py"
        content = render_py.read_text()
        assert ".legacy" in content, "render.py should contain .legacy path reference"
        assert "legacy_path" in content, "render.py should contain legacy_path variable"

    def test_render_py_contains_deep_merge_function(self):
        render_py = BASE_DIR / "render.py"
        content = render_py.read_text()
        assert "def deep_merge" in content, "render.py should contain deep_merge function"

    def test_staging_override_has_debug_mode(self):
        override = BASE_DIR / "overrides" / "staging" / "web-api.yaml"
        content = override.read_text()
        assert "debug_mode" in content, "Staging override should have debug_mode feature"

    def test_production_override_has_pool_size_100(self):
        override = BASE_DIR / "overrides" / "production" / "web-api.yaml"
        content = override.read_text()
        assert "100" in content, "Production override should have pool_size 100"


class TestPythonEnvironment:
    """Verify Python environment is properly set up."""

    def test_python3_available(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python3 is not available"

    def test_pyyaml_installed(self):
        result = subprocess.run(
            ["python3", "-c", "import yaml; print(yaml.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "PyYAML is not installed"


class TestCurrentBuggyBehavior:
    """Verify the bug exists in the initial state."""

    def test_staging_web_api_returns_wrong_db_host(self):
        """The bug: staging web-api returns db-prod.internal instead of db-staging.internal."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py"), "staging", "web-api"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        assert result.returncode == 0, f"render.py failed: {result.stderr}"
        # This is the BUG - it should return db-staging.internal but returns db-prod.internal
        assert "db-prod.internal" in result.stdout, \
            "Initial buggy state: staging web-api should incorrectly return db-prod.internal"
        # The staging host should NOT be present (this is the bug)
        # We check that the bug exists
        lines = [l.strip() for l in result.stdout.split('\n') if 'host:' in l and 'db-' in l]
        db_host_line = [l for l in lines if 'db-' in l][0] if lines else ""
        assert "db-staging.internal" not in db_host_line, \
            "Bug should exist: staging web-api should NOT have correct db-staging.internal in initial state"

    def test_production_web_api_returns_correct_db_host(self):
        """Production should work correctly (returns db-prod.internal)."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py"), "production", "web-api"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        assert result.returncode == 0, f"render.py failed: {result.stderr}"
        assert "db-prod.internal" in result.stdout, \
            "Production web-api should return db-prod.internal"

    def test_render_script_runs_without_error(self):
        """Verify the render script can be executed."""
        result = subprocess.run(
            ["python3", str(BASE_DIR / "render.py"), "staging", "web-api"],
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR)
        )
        assert result.returncode == 0, f"render.py should run without errors: {result.stderr}"


class TestDirectoryWritable:
    """Verify the deploy directory is writable for fixes."""

    def test_deploy_directory_writable(self):
        assert os.access(BASE_DIR, os.W_OK), f"{BASE_DIR} is not writable"

    def test_overrides_directory_writable(self):
        overrides_dir = BASE_DIR / "overrides"
        assert os.access(overrides_dir, os.W_OK), f"{overrides_dir} is not writable"

    def test_render_py_writable(self):
        render_py = BASE_DIR / "render.py"
        assert os.access(render_py, os.W_OK), f"{render_py} is not writable"

    def test_legacy_directory_writable(self):
        legacy_dir = BASE_DIR / "overrides" / ".legacy"
        assert os.access(legacy_dir, os.W_OK), f"{legacy_dir} is not writable"
