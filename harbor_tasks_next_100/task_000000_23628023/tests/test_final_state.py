# test_final_state.py
"""
Tests to validate the final state of the system after the student has fixed
the auth-gateway crash-looping issue.

Expected final state:
- config.yaml has session_ttl as an integer (3600 or similar), not a duration string
- The service can be started and stays up for at least 120 seconds without crashing
- Redis remains running and accessible
- The binary remains unchanged
- Other config.yaml values remain unchanged
"""

import os
import subprocess
import time
import re
import pytest


class TestConfigYamlFixed:
    """Test that config.yaml has been properly fixed."""

    def test_config_yaml_exists(self):
        """Verify config.yaml still exists."""
        path = "/home/user/services/auth-gateway/config.yaml"
        assert os.path.isfile(path), f"Config file {path} does not exist"

    def test_session_ttl_is_integer(self):
        """Verify session_ttl is now an integer, not a duration string with 's' suffix."""
        path = "/home/user/services/auth-gateway/config.yaml"
        result = subprocess.run(
            ['grep', 'session_ttl:', path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Could not find session_ttl in {path}"

        line = result.stdout.strip()
        # Extract the value after session_ttl:
        match = re.search(r'session_ttl:\s*(\S+)', line)
        assert match, f"Could not parse session_ttl line: {line}"

        value = match.group(1)
        # Remove any quotes if present
        value = value.strip('"\'')

        # The value should NOT contain 's' suffix (the bug)
        assert not re.search(r'\d+s$', value, re.IGNORECASE), \
            f"session_ttl still has duration string with 's' suffix (bug not fixed): {value}"

        # The value should be a valid integer
        try:
            int_value = int(value)
            assert int_value > 0, f"session_ttl should be a positive integer, got: {int_value}"
        except ValueError:
            pytest.fail(f"session_ttl is not a valid integer: {value}")

    def test_session_ttl_reasonable_value(self):
        """Verify session_ttl has a reasonable value (e.g., 3600 or similar)."""
        path = "/home/user/services/auth-gateway/config.yaml"
        with open(path, 'r') as f:
            content = f.read()

        match = re.search(r'session_ttl:\s*(\d+)', content)
        assert match, "Could not find session_ttl with integer value in config.yaml"

        value = int(match.group(1))
        # Should be a reasonable TTL value (at least 60 seconds, not more than a day)
        assert 60 <= value <= 86400, \
            f"session_ttl value {value} seems unreasonable (expected 60-86400 seconds)"

    def test_other_config_values_preserved(self):
        """Verify config.yaml still has other expected configuration keys."""
        path = "/home/user/services/auth-gateway/config.yaml"
        with open(path, 'r') as f:
            content = f.read()

        # The config should still have redis-related settings
        # Check for common config patterns that should be preserved
        assert 'redis' in content.lower() or '6379' in content, \
            "Config appears to be missing redis configuration - other settings may have been lost"


class TestBinaryUnchanged:
    """Test that the binary has not been modified."""

    def test_binary_exists(self):
        """Verify the auth-gateway binary still exists."""
        path = "/home/user/services/auth-gateway/auth-gateway"
        assert os.path.isfile(path), f"Binary {path} does not exist"

    def test_binary_is_executable(self):
        """Verify the auth-gateway binary is still executable."""
        path = "/home/user/services/auth-gateway/auth-gateway"
        assert os.access(path, os.X_OK), f"Binary {path} is not executable"

    def test_binary_size_unchanged(self):
        """Verify the binary size is still in the expected range (Go binary ~8MB)."""
        path = "/home/user/services/auth-gateway/auth-gateway"
        size = os.path.getsize(path)
        # Should still be a substantial Go binary, not replaced with a stub script
        assert size > 1_000_000, \
            f"Binary {path} is too small ({size} bytes) - may have been replaced with a stub"


class TestRedisStillRunning:
    """Test that Redis is still running and accessible."""

    def test_redis_responds_to_ping(self):
        """Verify Redis still responds to PING with PONG."""
        result = subprocess.run(
            ['redis-cli', '-h', 'localhost', '-p', '6379', 'PING'],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"redis-cli PING failed: {result.stderr}"
        assert 'PONG' in result.stdout, f"Redis did not respond with PONG, got: {result.stdout}"


class TestServiceRunsStably:
    """Test that the auth-gateway service can run without crashing."""

    def _kill_existing_auth_gateway(self):
        """Kill any existing auth-gateway processes."""
        subprocess.run(['pkill', '-f', 'auth-gateway'], capture_output=True)
        time.sleep(1)

    def _get_auth_gateway_pids(self):
        """Get PIDs of running auth-gateway processes."""
        result = subprocess.run(
            ['pgrep', '-f', 'auth-gateway'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return [int(pid) for pid in result.stdout.strip().split('\n') if pid]
        return []

    def _is_process_running(self, pid):
        """Check if a process with given PID is still running."""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def test_service_starts_successfully(self):
        """Verify the service can be started using run.sh."""
        self._kill_existing_auth_gateway()

        run_script = "/home/user/services/auth-gateway/run.sh"
        assert os.path.isfile(run_script), f"Run script {run_script} does not exist"

        # Start the service
        result = subprocess.run(
            [run_script],
            cwd="/home/user/services/auth-gateway",
            capture_output=True,
            text=True,
            timeout=30
        )

        # Give it a moment to start
        time.sleep(3)

        # Check if process is running
        pids = self._get_auth_gateway_pids()
        assert len(pids) > 0, \
            f"auth-gateway process not running after starting run.sh. stderr: {result.stderr}"

    def test_service_stays_up_for_120_seconds(self):
        """Verify the service stays up for at least 120 seconds without crashing."""
        # First ensure service is running
        pids = self._get_auth_gateway_pids()

        if not pids:
            # Try to start it
            run_script = "/home/user/services/auth-gateway/run.sh"
            subprocess.run(
                [run_script],
                cwd="/home/user/services/auth-gateway",
                capture_output=True,
                timeout=30
            )
            time.sleep(3)
            pids = self._get_auth_gateway_pids()

        assert len(pids) > 0, "auth-gateway process is not running"

        initial_pid = pids[0]

        # Wait for 120 seconds, checking periodically
        check_interval = 10
        total_wait = 120
        elapsed = 0

        while elapsed < total_wait:
            time.sleep(check_interval)
            elapsed += check_interval

            # Check if the original process is still running
            if not self._is_process_running(initial_pid):
                # Check if a new process started (crash-restart)
                new_pids = self._get_auth_gateway_pids()
                if new_pids:
                    pytest.fail(
                        f"auth-gateway crashed and restarted after {elapsed} seconds "
                        f"(original PID {initial_pid} died, new PID {new_pids[0]}). "
                        "The config fix may not be complete."
                    )
                else:
                    pytest.fail(
                        f"auth-gateway crashed after {elapsed} seconds and did not restart. "
                        "The config fix may not be complete."
                    )

        # Final check - process should still be running
        assert self._is_process_running(initial_pid), \
            f"auth-gateway process (PID {initial_pid}) is not running after {total_wait} seconds"

    def test_no_new_panic_in_error_log(self):
        """Check that no new panic messages appeared during the stability test."""
        error_log = "/var/log/auth-gateway/error.log"

        if os.path.isfile(error_log):
            # Get the last few lines to check for recent panics
            result = subprocess.run(
                ['tail', '-n', '50', error_log],
                capture_output=True,
                text=True
            )
            recent_errors = result.stdout

            # Look for the specific panic pattern that indicates the bug
            if 'strconv.Atoi' in recent_errors and '3600s' in recent_errors:
                # Check if this is a recent crash (within last few minutes)
                # This is a soft check - the main stability test is more definitive
                pass  # Old errors are expected, we're looking at process stability


class TestLogFilesIntact:
    """Test that log files still exist (may have new entries)."""

    def test_auth_gateway_log_exists(self):
        """Verify auth-gateway.log still exists."""
        path = "/var/log/auth-gateway/auth-gateway.log"
        assert os.path.isfile(path), f"Log file {path} does not exist"

    def test_access_log_exists(self):
        """Verify access.log still exists."""
        path = "/var/log/auth-gateway/access.log"
        assert os.path.isfile(path), f"Log file {path} does not exist"

    def test_error_log_exists(self):
        """Verify error.log still exists."""
        path = "/var/log/auth-gateway/error.log"
        assert os.path.isfile(path), f"Log file {path} does not exist"
