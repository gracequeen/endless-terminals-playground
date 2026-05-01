# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the Go service startup issue.
"""

import os
import subprocess
import pytest


HOME = "/home/user"
PROJECT_DIR = os.path.join(HOME, "profilesvc")


class TestProjectStructureExists:
    """Verify the project directory and required files exist."""

    def test_project_directory_exists(self):
        """The profilesvc directory must exist."""
        assert os.path.isdir(PROJECT_DIR), (
            f"Project directory {PROJECT_DIR} does not exist. "
            "The Go service project should be present."
        )

    def test_project_directory_is_writable(self):
        """The project directory must be writable."""
        assert os.access(PROJECT_DIR, os.W_OK), (
            f"Project directory {PROJECT_DIR} is not writable. "
            "User needs write access to fix the configuration."
        )

    def test_main_go_exists(self):
        """main.go must exist in the project."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        assert os.path.isfile(main_go), (
            f"main.go not found at {main_go}. "
            "The main Go source file is required."
        )

    def test_config_yaml_exists(self):
        """config.yaml must exist in the project."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        assert os.path.isfile(config_yaml), (
            f"config.yaml not found at {config_yaml}. "
            "The configuration file is required."
        )

    def test_go_mod_exists(self):
        """go.mod must exist for the Go module."""
        go_mod = os.path.join(PROJECT_DIR, "go.mod")
        assert os.path.isfile(go_mod), (
            f"go.mod not found at {go_mod}. "
            "The Go module file is required."
        )

    def test_internal_cache_directory_exists(self):
        """internal/cache directory must exist."""
        cache_dir = os.path.join(PROJECT_DIR, "internal", "cache")
        assert os.path.isdir(cache_dir), (
            f"internal/cache directory not found at {cache_dir}. "
            "The cache package directory is required."
        )

    def test_cache_go_exists(self):
        """internal/cache/cache.go must exist."""
        cache_go = os.path.join(PROJECT_DIR, "internal", "cache", "cache.go")
        assert os.path.isfile(cache_go), (
            f"cache.go not found at {cache_go}. "
            "The cache initialization module is required."
        )

    def test_internal_db_directory_exists(self):
        """internal/db directory must exist."""
        db_dir = os.path.join(PROJECT_DIR, "internal", "db")
        assert os.path.isdir(db_dir), (
            f"internal/db directory not found at {db_dir}. "
            "The db package directory is required."
        )

    def test_db_go_exists(self):
        """internal/db/db.go must exist."""
        db_go = os.path.join(PROJECT_DIR, "internal", "db", "db.go")
        assert os.path.isfile(db_go), (
            f"db.go not found at {db_go}. "
            "The database pool initialization module is required."
        )


class TestGoEnvironment:
    """Verify Go is installed and working."""

    def test_go_is_installed(self):
        """Go must be installed and accessible."""
        result = subprocess.run(
            ["which", "go"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Go is not installed or not in PATH. "
            "Go 1.21+ is required for this task."
        )

    def test_go_version_is_adequate(self):
        """Go version must be 1.21 or higher."""
        result = subprocess.run(
            ["go", "version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get Go version."

        # Parse version from output like "go version go1.21.0 linux/amd64"
        version_output = result.stdout.strip()
        assert "go" in version_output.lower(), (
            f"Unexpected go version output: {version_output}"
        )

        # Extract version number
        import re
        match = re.search(r'go(\d+)\.(\d+)', version_output)
        assert match, f"Could not parse Go version from: {version_output}"

        major = int(match.group(1))
        minor = int(match.group(2))

        assert (major > 1) or (major == 1 and minor >= 21), (
            f"Go version {major}.{minor} is too old. "
            "Go 1.21+ is required for this task."
        )


class TestConfigurationContent:
    """Verify the configuration file has expected settings."""

    def test_config_has_startup_timeout(self):
        """config.yaml should have startup_timeout setting."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        with open(config_yaml, 'r') as f:
            content = f.read()
        assert "startup_timeout" in content, (
            "config.yaml is missing 'startup_timeout' setting. "
            "This is part of the bug chain that needs to be investigated."
        )

    def test_config_has_cache_warmup(self):
        """config.yaml should have cache_warmup setting."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        with open(config_yaml, 'r') as f:
            content = f.read()
        assert "cache_warmup" in content, (
            "config.yaml is missing 'cache_warmup' setting. "
            "This is part of the bug chain that needs to be investigated."
        )

    def test_config_has_warmup_endpoint(self):
        """config.yaml should have warmup_endpoint setting."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        with open(config_yaml, 'r') as f:
            content = f.read()
        assert "warmup_endpoint" in content, (
            "config.yaml is missing 'warmup_endpoint' setting. "
            "This is part of the bug chain that needs to be investigated."
        )


class TestMainGoContent:
    """Verify main.go has the expected structure."""

    def test_main_go_has_cache_init(self):
        """main.go should call cache.Init()."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "cache.Init" in content or "cache.Init(" in content, (
            "main.go is missing cache.Init() call. "
            "The cache initialization call should be present."
        )

    def test_main_go_has_db_init(self):
        """main.go should call db.Init()."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "db.Init" in content or "db.Init(" in content, (
            "main.go is missing db.Init() call. "
            "The database initialization call should be present."
        )

    def test_main_go_has_health_handler(self):
        """main.go should have a health endpoint."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "/health" in content, (
            "main.go is missing /health endpoint. "
            "The health endpoint is required for the task."
        )

    def test_main_go_has_listen_and_serve(self):
        """main.go should have HTTP server setup."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "ListenAndServe" in content, (
            "main.go is missing ListenAndServe call. "
            "The HTTP server setup is required."
        )


class TestPort8080IsFree:
    """Verify port 8080 is not currently in use."""

    def test_port_8080_is_free(self):
        """Port 8080 should not be in use by another process."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if anything is listening on port 8080
        lines = result.stdout.split('\n')
        for line in lines:
            if ':8080' in line and 'LISTEN' in line:
                pytest.fail(
                    f"Port 8080 is already in use: {line}\n"
                    "The port must be free for the Go service to bind to it."
                )


class TestNoServiceRunning:
    """Verify the Go service is not already running."""

    def test_profilesvc_not_running(self):
        """The profilesvc should not already be running."""
        result = subprocess.run(
            ["pgrep", "-f", "profilesvc"],
            capture_output=True,
            text=True
        )
        # pgrep returns 0 if processes found, 1 if not found
        if result.returncode == 0:
            pids = result.stdout.strip()
            pytest.fail(
                f"profilesvc appears to already be running (PIDs: {pids}). "
                "The service should not be running in the initial state."
            )


class TestPort9999NotListening:
    """Verify port 9999 (warmup endpoint) is not listening - this is part of the bug."""

    def test_port_9999_not_listening(self):
        """Port 9999 should NOT be listening - this is the bug."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        lines = result.stdout.split('\n')
        for line in lines:
            if ':9999' in line and 'LISTEN' in line:
                pytest.fail(
                    f"Port 9999 is listening: {line}\n"
                    "In the initial buggy state, nothing should be listening on 9999 "
                    "(this is part of the bug - the warmup endpoint is unreachable)."
                )
