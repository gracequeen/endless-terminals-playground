# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the devstack debugging task.

Expected final state:
- redis-server process is running
- postgres process is running
- Flask API responds on port 8080 with healthy status
- app/api.py source code is unchanged
- Services are actually connected (health endpoint validates backends)
"""

import os
import subprocess
import socket
import time
import hashlib
import pytest


DEVSTACK_DIR = "/home/user/devstack"
API_PORT = 8080
API_HOST = "127.0.0.1"


class TestRedisRunning:
    """Verify Redis server is running."""

    def test_redis_process_running(self):
        """At least one redis-server process must be running."""
        result = subprocess.run(
            ["pgrep", "-f", "redis-server"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "redis-server process is not running. "
            "Redis must be started and running for the devstack to work. "
            f"pgrep output: {result.stderr}"
        )
        pids = result.stdout.strip().split('\n')
        assert len(pids) >= 1 and pids[0], (
            "No redis-server PIDs found. Redis must be running."
        )

    def test_redis_port_listening(self):
        """Redis should be listening on port 6379."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check for port 6379 listening
        assert ":6379" in result.stdout, (
            "Redis is not listening on port 6379. "
            "Redis must be bound to 127.0.0.1:6379 as per config. "
            f"Listening ports: {result.stdout}"
        )


class TestPostgresRunning:
    """Verify PostgreSQL server is running."""

    def test_postgres_process_running(self):
        """At least one postgres process must be running."""
        result = subprocess.run(
            ["pgrep", "-f", "postgres"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "postgres process is not running. "
            "PostgreSQL must be started and running for the devstack to work. "
            f"pgrep stderr: {result.stderr}"
        )
        pids = result.stdout.strip().split('\n')
        assert len(pids) >= 1 and pids[0], (
            "No postgres PIDs found. PostgreSQL must be running."
        )

    def test_postgres_port_listening(self):
        """PostgreSQL should be listening on its configured port."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Postgres could be on 5432 or 5433 depending on how bug was fixed
        # The key is that it's listening and the API can connect
        has_postgres_port = ":5432" in result.stdout or ":5433" in result.stdout
        assert has_postgres_port, (
            "PostgreSQL is not listening on expected port (5432 or 5433). "
            f"Listening ports: {result.stdout}"
        )


class TestFlaskAPIRunning:
    """Verify Flask API is running and responding."""

    def test_api_port_listening(self):
        """API should be listening on port 8080."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" in result.stdout, (
            "Flask API is not listening on port 8080. "
            "The API must be running on its configured port. "
            f"Listening ports: {result.stdout}"
        )

    def test_api_process_running(self):
        """A Python process running the API should exist."""
        # Check for python process running api.py or flask
        result = subprocess.run(
            ["pgrep", "-f", "api.py"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            # Try alternative pattern
            result = subprocess.run(
                ["pgrep", "-f", "flask"],
                capture_output=True,
                text=True
            )
        assert result.returncode == 0, (
            "No Python process running the Flask API found. "
            "The API must be running."
        )


class TestAPIHealthEndpoint:
    """Verify the API health endpoint responds correctly."""

    def test_health_endpoint_returns_200(self):
        """curl to /health should return HTTP 200."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             f"http://{API_HOST}:{API_PORT}/health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        http_code = result.stdout.strip()
        assert http_code == "200", (
            f"Health endpoint returned HTTP {http_code}, expected 200. "
            "This likely means either Redis or PostgreSQL is not properly "
            "connected. The /health endpoint checks both backends. "
            f"stderr: {result.stderr}"
        )

    def test_health_endpoint_contains_ok(self):
        """Health endpoint response body should contain 'ok'."""
        result = subprocess.run(
            ["curl", "-s", f"http://{API_HOST}:{API_PORT}/health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"curl to health endpoint failed: {result.stderr}"
        )
        response_body = result.stdout.lower()
        assert "ok" in response_body, (
            f"Health endpoint response does not contain 'ok'. "
            f"Response body: {result.stdout}. "
            "The health check must pass, indicating both Redis and "
            "PostgreSQL are reachable."
        )

    def test_health_endpoint_not_error(self):
        """Health endpoint should not return error status."""
        result = subprocess.run(
            ["curl", "-s", f"http://{API_HOST}:{API_PORT}/health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        response_body = result.stdout.lower()
        # Should not contain error indicators
        assert "error" not in response_body or "ok" in response_body, (
            f"Health endpoint indicates an error: {result.stdout}. "
            "Both Redis and PostgreSQL must be properly connected."
        )


class TestAPISourceUnchanged:
    """Verify that app/api.py was not modified (anti-shortcut guard)."""

    def test_api_py_exists(self):
        """app/api.py must still exist."""
        api_py = os.path.join(DEVSTACK_DIR, "app", "api.py")
        assert os.path.isfile(api_py), (
            f"File {api_py} does not exist. "
            "The API source file must not be deleted."
        )

    def test_api_py_contains_health_check_logic(self):
        """api.py must still contain the real health check logic."""
        api_py = os.path.join(DEVSTACK_DIR, "app", "api.py")
        with open(api_py, 'r') as f:
            content = f.read()

        # Check for Redis ping in health check
        assert "redis" in content.lower() and "ping" in content.lower(), (
            "api.py appears to have been modified - Redis ping check not found. "
            "The health endpoint must actually check Redis connectivity."
        )

        # Check for psycopg2/postgres connection in health check
        assert "psycopg2" in content.lower() or "database_url" in content.lower(), (
            "api.py appears to have been modified - PostgreSQL check not found. "
            "The health endpoint must actually check PostgreSQL connectivity."
        )

    def test_api_py_has_health_route(self):
        """api.py must have a /health route defined."""
        api_py = os.path.join(DEVSTACK_DIR, "app", "api.py")
        with open(api_py, 'r') as f:
            content = f.read()

        assert "/health" in content or "health" in content, (
            "api.py does not appear to have a health route. "
            "The health endpoint must exist and check backends."
        )


class TestServicesConnectivity:
    """Additional connectivity tests to ensure services are truly connected."""

    def test_can_connect_to_redis_port(self):
        """Should be able to establish TCP connection to Redis port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex(('127.0.0.1', 6379))
            assert result == 0, (
                f"Cannot connect to Redis on 127.0.0.1:6379 (error code: {result}). "
                "Redis must be running and accepting connections."
            )
        finally:
            sock.close()

    def test_can_connect_to_api_port(self):
        """Should be able to establish TCP connection to API port."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex((API_HOST, API_PORT))
            assert result == 0, (
                f"Cannot connect to API on {API_HOST}:{API_PORT} (error code: {result}). "
                "The Flask API must be running and accepting connections."
            )
        finally:
            sock.close()


class TestConfigurationFixed:
    """Verify that configuration issues have been addressed."""

    def test_redis_conf_has_valid_daemonize(self):
        """redis.conf should have correct 'daemonize' spelling."""
        redis_conf = os.path.join(DEVSTACK_DIR, "config", "redis.conf")
        if os.path.isfile(redis_conf):
            with open(redis_conf, 'r') as f:
                content = f.read()
            # Should not have the typo anymore, or redis wouldn't start
            # This is informational - the real test is that redis is running
            if "daemonise" in content.lower():
                pytest.fail(
                    "redis.conf still contains typo 'daemonise' instead of 'daemonize'. "
                    "However, if Redis is running, this may have been fixed elsewhere."
                )

    def test_port_configuration_consistent(self):
        """Database port in api.env should match actual postgres port."""
        # This is validated by the health check passing - if ports don't match,
        # the API can't connect to postgres and health returns 500
        # We just verify the health check passes (done in other tests)
        pass


class TestDevstackStructureIntact:
    """Verify the devstack directory structure is still intact."""

    def test_devstack_directory_exists(self):
        """The devstack directory must still exist."""
        assert os.path.isdir(DEVSTACK_DIR), (
            f"Directory {DEVSTACK_DIR} does not exist."
        )

    def test_start_sh_exists(self):
        """start.sh must still exist."""
        start_sh = os.path.join(DEVSTACK_DIR, "start.sh")
        assert os.path.isfile(start_sh), (
            f"File {start_sh} does not exist."
        )

    def test_logs_directory_exists(self):
        """logs/ directory must still exist."""
        logs_dir = os.path.join(DEVSTACK_DIR, "logs")
        assert os.path.isdir(logs_dir), (
            f"Directory {logs_dir} does not exist."
        )
