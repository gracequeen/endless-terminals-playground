# test_final_state.py
"""
Tests to validate the final state after the student has fixed the Go service
startup issue. The server should be running and responding on port 8080.
"""

import os
import subprocess
import time
import socket
import pytest


HOME = "/home/user"
PROJECT_DIR = os.path.join(HOME, "profilesvc")


class TestProjectIntegrity:
    """Verify the project structure is still intact and not bypassed."""

    def test_main_go_still_has_cache_init(self):
        """main.go must still call cache.Init() - cannot delete init calls."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "cache.Init" in content, (
            "main.go is missing cache.Init() call. "
            "The fix cannot simply remove the cache initialization call."
        )

    def test_main_go_still_has_db_init(self):
        """main.go must still call db.Init() - cannot delete init calls."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "db.Init" in content, (
            "main.go is missing db.Init() call. "
            "The fix cannot simply remove the database initialization call."
        )

    def test_both_init_calls_present(self):
        """Both cache.Init and db.Init must be present in main.go."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        result = subprocess.run(
            ["grep", "-c", r"cache\.Init\|db\.Init", main_go],
            capture_output=True,
            text=True
        )
        # grep -c returns the count of matching lines
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 2, (
            f"Expected at least 2 init calls (cache.Init and db.Init) in main.go, "
            f"but found {count}. Cannot bypass the initialization logic."
        )

    def test_cache_package_exists(self):
        """The cache package must still exist."""
        cache_go = os.path.join(PROJECT_DIR, "internal", "cache", "cache.go")
        assert os.path.isfile(cache_go), (
            f"cache.go not found at {cache_go}. "
            "Cannot delete the entire cache package as a fix."
        )

    def test_db_package_exists(self):
        """The db package must still exist."""
        db_go = os.path.join(PROJECT_DIR, "internal", "db", "db.go")
        assert os.path.isfile(db_go), (
            f"db.go not found at {db_go}. "
            "Cannot delete the entire db package as a fix."
        )

    def test_health_endpoint_still_defined(self):
        """The /health endpoint must still be defined in main.go."""
        main_go = os.path.join(PROJECT_DIR, "main.go")
        with open(main_go, 'r') as f:
            content = f.read()
        assert "/health" in content, (
            "main.go is missing /health endpoint definition. "
            "The health endpoint must remain functional."
        )


class TestServerRunning:
    """Verify the server is running and responding on port 8080."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Start the server before tests and clean up after."""
        # Kill any existing processes on port 8080
        subprocess.run(
            ["pkill", "-f", "profilesvc"],
            capture_output=True
        )
        subprocess.run(
            ["fuser", "-k", "8080/tcp"],
            capture_output=True,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1)

        # Start the server in background
        self.server_process = subprocess.Popen(
            ["go", "run", "main.go"],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        # Wait for server to start (up to 10 seconds)
        start_time = time.time()
        server_ready = False
        while time.time() - start_time < 10:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 8080))
                sock.close()
                if result == 0:
                    server_ready = True
                    break
            except:
                pass
            time.sleep(0.5)

        yield server_ready

        # Cleanup: kill the server process
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

        # Also kill any remaining processes on port 8080
        subprocess.run(
            ["fuser", "-k", "8080/tcp"],
            capture_output=True,
            stderr=subprocess.DEVNULL
        )

    def test_server_starts_within_timeout(self, setup_and_teardown):
        """Server must start and bind to port 8080 within 10 seconds."""
        server_ready = setup_and_teardown
        if not server_ready:
            # Get stderr for debugging
            stderr_output = ""
            if self.server_process.poll() is not None:
                _, stderr = self.server_process.communicate(timeout=1)
                stderr_output = stderr.decode('utf-8', errors='replace')
            pytest.fail(
                f"Server failed to start and bind to port 8080 within 10 seconds. "
                f"The startup issue has not been fixed.\n"
                f"Server stderr: {stderr_output}"
            )

    def test_port_8080_is_listening(self, setup_and_teardown):
        """Port 8080 must be listening after server starts."""
        server_ready = setup_and_teardown
        if not server_ready:
            pytest.skip("Server did not start")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex(('localhost', 8080))
            assert result == 0, (
                f"Port 8080 is not listening (connect returned {result}). "
                "The server must be bound to port 8080."
            )
        finally:
            sock.close()

    def test_health_endpoint_returns_200(self, setup_and_teardown):
        """GET /health must return HTTP 200."""
        server_ready = setup_and_teardown
        if not server_ready:
            pytest.skip("Server did not start")

        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=5
        )
        http_code = result.stdout.strip()
        assert http_code == "200", (
            f"GET /health returned HTTP {http_code}, expected 200. "
            "The health endpoint must return a successful response."
        )

    def test_health_endpoint_returns_ok(self, setup_and_teardown):
        """GET /health response body must contain 'ok'."""
        server_ready = setup_and_teardown
        if not server_ready:
            pytest.skip("Server did not start")

        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/health"],
            capture_output=True,
            text=True,
            timeout=5
        )
        response_body = result.stdout.lower()
        assert "ok" in response_body, (
            f"GET /health response body does not contain 'ok'. "
            f"Got: {result.stdout}\n"
            "The health endpoint must indicate the service is healthy."
        )


class TestServerStartsQuickly:
    """Verify the server starts quickly (within 5 seconds) as specified."""

    def test_server_responds_within_5_seconds(self):
        """Server must be responding within 5 seconds of starting."""
        # Kill any existing processes
        subprocess.run(["pkill", "-f", "profilesvc"], capture_output=True)
        subprocess.run(
            ["fuser", "-k", "8080/tcp"],
            capture_output=True,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1)

        # Start the server
        server_process = subprocess.Popen(
            ["go", "run", "main.go"],
            cwd=PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )

        try:
            # Wait up to 5 seconds for the server to respond
            start_time = time.time()
            server_ready = False

            while time.time() - start_time < 5:
                try:
                    result = subprocess.run(
                        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "http://localhost:8080/health"],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                    if result.stdout.strip() == "200":
                        server_ready = True
                        break
                except:
                    pass
                time.sleep(0.3)

            elapsed = time.time() - start_time

            if not server_ready:
                # Check if process died
                stderr_output = ""
                if server_process.poll() is not None:
                    _, stderr = server_process.communicate(timeout=1)
                    stderr_output = stderr.decode('utf-8', errors='replace')
                pytest.fail(
                    f"Server did not respond within 5 seconds (waited {elapsed:.1f}s). "
                    f"The startup latency issue has not been fixed.\n"
                    f"Server stderr: {stderr_output}"
                )

        finally:
            # Cleanup
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            subprocess.run(
                ["fuser", "-k", "8080/tcp"],
                capture_output=True,
                stderr=subprocess.DEVNULL
            )


class TestConfigurationNotBroken:
    """Verify the configuration file still exists and has valid structure."""

    def test_config_yaml_exists(self):
        """config.yaml must still exist."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        assert os.path.isfile(config_yaml), (
            f"config.yaml not found at {config_yaml}. "
            "The configuration file must remain present."
        )

    def test_config_yaml_is_valid_yaml(self):
        """config.yaml must be valid YAML (parseable)."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        # Use Python to check if it's valid YAML-like structure
        # Since we can only use stdlib, do basic check
        with open(config_yaml, 'r') as f:
            content = f.read()
        # Basic check: should have key: value patterns
        assert ':' in content, (
            "config.yaml does not appear to be valid YAML (no key: value pairs found)."
        )

    def test_port_config_is_8080(self):
        """The configured port must still be 8080."""
        config_yaml = os.path.join(PROJECT_DIR, "config.yaml")
        with open(config_yaml, 'r') as f:
            content = f.read()
        # Check that port is configured as 8080
        import re
        port_match = re.search(r'port:\s*(\d+)', content)
        if port_match:
            port = int(port_match.group(1))
            assert port == 8080, (
                f"Port is configured as {port}, but must be 8080. "
                "Cannot change the port as a workaround."
            )
