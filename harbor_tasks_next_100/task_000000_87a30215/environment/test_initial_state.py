# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the devstack debugging task.
"""

import os
import subprocess
import pytest


DEVSTACK_DIR = "/home/user/devstack"


class TestDevstackDirectoryStructure:
    """Verify the devstack directory and its contents exist."""

    def test_devstack_directory_exists(self):
        """The /home/user/devstack directory must exist."""
        assert os.path.isdir(DEVSTACK_DIR), (
            f"Directory {DEVSTACK_DIR} does not exist. "
            "The devstack directory is required for this task."
        )

    def test_start_sh_exists_and_executable(self):
        """start.sh must exist and be executable."""
        start_sh = os.path.join(DEVSTACK_DIR, "start.sh")
        assert os.path.isfile(start_sh), (
            f"File {start_sh} does not exist. "
            "The main startup script is required."
        )
        assert os.access(start_sh, os.X_OK), (
            f"File {start_sh} is not executable. "
            "The startup script must be executable."
        )

    def test_logs_directory_exists(self):
        """logs/ directory must exist."""
        logs_dir = os.path.join(DEVSTACK_DIR, "logs")
        assert os.path.isdir(logs_dir), (
            f"Directory {logs_dir} does not exist. "
            "The logs directory is required for service output."
        )

    def test_config_directory_exists(self):
        """config/ directory must exist."""
        config_dir = os.path.join(DEVSTACK_DIR, "config")
        assert os.path.isdir(config_dir), (
            f"Directory {config_dir} does not exist. "
            "The config directory is required."
        )

    def test_services_directory_exists(self):
        """services/ directory must exist."""
        services_dir = os.path.join(DEVSTACK_DIR, "services")
        assert os.path.isdir(services_dir), (
            f"Directory {services_dir} does not exist. "
            "The services directory is required."
        )

    def test_app_directory_exists(self):
        """app/ directory must exist."""
        app_dir = os.path.join(DEVSTACK_DIR, "app")
        assert os.path.isdir(app_dir), (
            f"Directory {app_dir} does not exist. "
            "The app directory is required."
        )


class TestConfigFiles:
    """Verify configuration files exist."""

    def test_redis_conf_exists(self):
        """config/redis.conf must exist."""
        redis_conf = os.path.join(DEVSTACK_DIR, "config", "redis.conf")
        assert os.path.isfile(redis_conf), (
            f"File {redis_conf} does not exist. "
            "Redis configuration file is required."
        )

    def test_postgres_env_exists(self):
        """config/postgres.env must exist."""
        postgres_env = os.path.join(DEVSTACK_DIR, "config", "postgres.env")
        assert os.path.isfile(postgres_env), (
            f"File {postgres_env} does not exist. "
            "Postgres environment file is required."
        )

    def test_api_env_exists(self):
        """config/api.env must exist."""
        api_env = os.path.join(DEVSTACK_DIR, "config", "api.env")
        assert os.path.isfile(api_env), (
            f"File {api_env} does not exist. "
            "API environment file is required."
        )


class TestServiceScripts:
    """Verify service startup scripts exist."""

    def test_start_redis_sh_exists(self):
        """services/start_redis.sh must exist."""
        script = os.path.join(DEVSTACK_DIR, "services", "start_redis.sh")
        assert os.path.isfile(script), (
            f"File {script} does not exist. "
            "Redis startup script is required."
        )

    def test_start_postgres_sh_exists(self):
        """services/start_postgres.sh must exist."""
        script = os.path.join(DEVSTACK_DIR, "services", "start_postgres.sh")
        assert os.path.isfile(script), (
            f"File {script} does not exist. "
            "Postgres startup script is required."
        )

    def test_start_api_sh_exists(self):
        """services/start_api.sh must exist."""
        script = os.path.join(DEVSTACK_DIR, "services", "start_api.sh")
        assert os.path.isfile(script), (
            f"File {script} does not exist. "
            "API startup script is required."
        )


class TestApplicationFiles:
    """Verify application files exist."""

    def test_api_py_exists(self):
        """app/api.py must exist."""
        api_py = os.path.join(DEVSTACK_DIR, "app", "api.py")
        assert os.path.isfile(api_py), (
            f"File {api_py} does not exist. "
            "The Flask API application file is required."
        )


class TestRequiredToolsInstalled:
    """Verify required tools are installed on the system."""

    def test_redis_server_installed(self):
        """redis-server must be installed."""
        result = subprocess.run(
            ["which", "redis-server"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "redis-server is not installed or not in PATH. "
            "Redis server is required for this task."
        )

    def test_pg_ctl_installed(self):
        """pg_ctl (PostgreSQL) must be installed."""
        result = subprocess.run(
            ["which", "pg_ctl"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "pg_ctl is not installed or not in PATH. "
            "PostgreSQL tools are required for this task."
        )

    def test_initdb_installed(self):
        """initdb (PostgreSQL) must be installed."""
        result = subprocess.run(
            ["which", "initdb"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "initdb is not installed or not in PATH. "
            "PostgreSQL initialization tool is required for this task."
        )

    def test_python3_installed(self):
        """python3 must be installed."""
        result = subprocess.run(
            ["which", "python3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "python3 is not installed or not in PATH. "
            "Python 3 is required for this task."
        )

    def test_flask_installed(self):
        """Flask Python package must be installed."""
        result = subprocess.run(
            ["python3", "-c", "import flask"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Flask is not installed for python3. "
            "Flask package is required for the API."
        )

    def test_psycopg2_installed(self):
        """psycopg2 Python package must be installed."""
        result = subprocess.run(
            ["python3", "-c", "import psycopg2"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "psycopg2 is not installed for python3. "
            "psycopg2 package is required for PostgreSQL connectivity."
        )


class TestNoServicesRunning:
    """Verify that no services are currently running (initial state)."""

    def test_no_redis_running(self):
        """No redis-server process should be running initially."""
        result = subprocess.run(
            ["pgrep", "-f", "redis-server"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "redis-server is already running. "
            "Initial state should have no services running."
        )

    def test_no_postgres_running(self):
        """No postgres process should be running initially."""
        result = subprocess.run(
            ["pgrep", "-f", "postgres"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "postgres is already running. "
            "Initial state should have no services running."
        )

    def test_port_6379_not_listening(self):
        """Port 6379 (redis) should not be in use."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":6379" not in result.stdout, (
            "Port 6379 is already in use. "
            "Initial state should have redis port available."
        )

    def test_port_8080_not_listening(self):
        """Port 8080 (api) should not be in use."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" not in result.stdout, (
            "Port 8080 is already in use. "
            "Initial state should have API port available."
        )


class TestDirectoryWritable:
    """Verify the devstack directory is writable."""

    def test_devstack_writable(self):
        """The devstack directory must be writable."""
        assert os.access(DEVSTACK_DIR, os.W_OK), (
            f"Directory {DEVSTACK_DIR} is not writable. "
            "The devstack directory must be writable for this task."
        )

    def test_logs_directory_writable(self):
        """The logs directory must be writable."""
        logs_dir = os.path.join(DEVSTACK_DIR, "logs")
        assert os.access(logs_dir, os.W_OK), (
            f"Directory {logs_dir} is not writable. "
            "The logs directory must be writable for service output."
        )
