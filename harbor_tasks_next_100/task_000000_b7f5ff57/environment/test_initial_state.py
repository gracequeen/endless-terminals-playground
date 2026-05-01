# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the debugging task for the load testing latency report issue.
"""

import os
import subprocess
import signal
import pytest


LOADTEST_DIR = "/home/user/loadtest"


class TestLoadtestDirectoryStructure:
    """Verify the loadtest directory and required files exist."""

    def test_loadtest_directory_exists(self):
        """The /home/user/loadtest directory must exist."""
        assert os.path.isdir(LOADTEST_DIR), (
            f"Directory {LOADTEST_DIR} does not exist. "
            "The loadtest harness directory is required for this task."
        )

    def test_run_bench_script_exists(self):
        """run_bench.sh must exist in the loadtest directory."""
        script_path = os.path.join(LOADTEST_DIR, "run_bench.sh")
        assert os.path.isfile(script_path), (
            f"File {script_path} does not exist. "
            "The benchmark orchestration script is required."
        )

    def test_run_bench_script_is_executable(self):
        """run_bench.sh must be executable."""
        script_path = os.path.join(LOADTEST_DIR, "run_bench.sh")
        assert os.access(script_path, os.X_OK), (
            f"File {script_path} is not executable. "
            "The script must have execute permissions."
        )

    def test_client_py_exists(self):
        """client.py must exist in the loadtest directory."""
        client_path = os.path.join(LOADTEST_DIR, "client.py")
        assert os.path.isfile(client_path), (
            f"File {client_path} does not exist. "
            "The HTTP client script is required."
        )

    def test_aggregate_py_exists(self):
        """aggregate.py must exist in the loadtest directory."""
        aggregate_path = os.path.join(LOADTEST_DIR, "aggregate.py")
        assert os.path.isfile(aggregate_path), (
            f"File {aggregate_path} does not exist. "
            "The aggregation script is required."
        )

    def test_report_py_exists(self):
        """report.py must exist in the loadtest directory."""
        report_path = os.path.join(LOADTEST_DIR, "report.py")
        assert os.path.isfile(report_path), (
            f"File {report_path} does not exist. "
            "The reporting script is required."
        )

    def test_server_pid_file_exists(self):
        """The .server.pid file must exist indicating the mock server was started."""
        pid_file = os.path.join(LOADTEST_DIR, ".server.pid")
        assert os.path.isfile(pid_file), (
            f"File {pid_file} does not exist. "
            "The mock server PID file is required to verify the server is running."
        )


class TestMockServerRunning:
    """Verify the mock server is running and listening on the expected port."""

    def test_mock_server_process_exists(self):
        """The mock server process should be running (PID from .server.pid)."""
        pid_file = os.path.join(LOADTEST_DIR, ".server.pid")

        # First check if PID file exists
        if not os.path.isfile(pid_file):
            pytest.skip("PID file does not exist, cannot verify process")

        with open(pid_file, "r") as f:
            pid_content = f.read().strip()

        try:
            pid = int(pid_content)
        except ValueError:
            pytest.fail(
                f"PID file {pid_file} contains invalid content: '{pid_content}'. "
                "Expected a numeric process ID."
            )

        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
        except ProcessLookupError:
            pytest.fail(
                f"Mock server process with PID {pid} is not running. "
                "The mock server must be running on 127.0.0.1:9222."
            )
        except PermissionError:
            # Process exists but we don't have permission (unlikely for same user)
            pass

    def test_port_9222_is_listening(self):
        """Port 9222 should be listening on 127.0.0.1."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )

        # Check for 127.0.0.1:9222 or *:9222 in the output
        output = result.stdout
        listening = "127.0.0.1:9222" in output or "0.0.0.0:9222" in output or ":9222" in output

        assert listening, (
            "No process is listening on port 9222. "
            "The mock server must be running on 127.0.0.1:9222.\n"
            f"Current listening ports:\n{output}"
        )

    def test_mock_server_responds_to_http(self):
        """The mock server should respond to HTTP GET requests."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "--connect-timeout", "2", "http://127.0.0.1:9222/"],
            capture_output=True,
            text=True
        )

        http_code = result.stdout.strip()
        assert http_code == "200", (
            f"Mock server at 127.0.0.1:9222 returned HTTP {http_code}, expected 200. "
            "The mock server must be running and responding to requests."
        )


class TestPythonEnvironment:
    """Verify Python and required libraries are available."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python 3 is not available. "
            f"Error: {result.stderr}"
        )

    def test_requests_library_available(self):
        """The requests library must be importable."""
        result = subprocess.run(
            ["python3", "-c", "import requests"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python 'requests' library is not available. "
            f"Error: {result.stderr}"
        )


class TestScriptContents:
    """Verify the scripts have the expected structure for the buggy initial state."""

    def test_client_py_makes_http_requests(self):
        """client.py should contain code that makes HTTP requests."""
        client_path = os.path.join(LOADTEST_DIR, "client.py")
        with open(client_path, "r") as f:
            content = f.read()

        # Should use requests library or urllib to make HTTP calls
        has_requests = "requests" in content or "urllib" in content or "http.client" in content
        assert has_requests, (
            "client.py does not appear to make HTTP requests. "
            "Expected to find 'requests', 'urllib', or 'http.client' imports."
        )

    def test_aggregate_py_computes_percentiles(self):
        """aggregate.py should contain percentile computation logic."""
        aggregate_path = os.path.join(LOADTEST_DIR, "aggregate.py")
        with open(aggregate_path, "r") as f:
            content = f.read()

        # Should have some percentile-related logic
        has_percentile_logic = (
            "percentile" in content.lower() or 
            "p50" in content or 
            "p99" in content or
            "sorted" in content
        )
        assert has_percentile_logic, (
            "aggregate.py does not appear to compute percentiles. "
            "Expected percentile computation logic."
        )

    def test_report_py_prints_output(self):
        """report.py should contain print statements for the report."""
        report_path = os.path.join(LOADTEST_DIR, "report.py")
        with open(report_path, "r") as f:
            content = f.read()

        has_print = "print" in content
        assert has_print, (
            "report.py does not appear to print output. "
            "Expected print statements for the latency report."
        )

    def test_run_bench_calls_scripts(self):
        """run_bench.sh should orchestrate the benchmark by calling the Python scripts."""
        script_path = os.path.join(LOADTEST_DIR, "run_bench.sh")
        with open(script_path, "r") as f:
            content = f.read()

        # Should reference the Python scripts
        calls_client = "client" in content
        calls_aggregate = "aggregate" in content
        calls_report = "report" in content

        assert calls_client and calls_aggregate and calls_report, (
            "run_bench.sh does not appear to call all required scripts. "
            f"Found: client={calls_client}, aggregate={calls_aggregate}, report={calls_report}. "
            "Expected all three scripts to be called."
        )


class TestDirectoryWritable:
    """Verify the loadtest directory is writable."""

    def test_loadtest_directory_is_writable(self):
        """The /home/user/loadtest directory must be writable."""
        assert os.access(LOADTEST_DIR, os.W_OK), (
            f"Directory {LOADTEST_DIR} is not writable. "
            "The agent needs write access to fix the bugs."
        )

    def test_python_files_are_writable(self):
        """The Python files must be writable for the agent to fix bugs."""
        for filename in ["client.py", "aggregate.py", "report.py"]:
            filepath = os.path.join(LOADTEST_DIR, filename)
            if os.path.isfile(filepath):
                assert os.access(filepath, os.W_OK), (
                    f"File {filepath} is not writable. "
                    "The agent needs write access to fix bugs."
                )
