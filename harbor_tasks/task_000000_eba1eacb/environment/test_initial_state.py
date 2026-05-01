# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student performs the task.
This verifies the netmon monitoring stack setup is in the expected initial state.
"""

import os
import stat
import subprocess
import pytest


BASE_DIR = "/home/user/netmon"


class TestNetmonDirectoryExists:
    """Verify the netmon directory exists and is writable."""

    def test_netmon_directory_exists(self):
        assert os.path.isdir(BASE_DIR), f"Directory {BASE_DIR} does not exist"

    def test_netmon_directory_is_writable(self):
        assert os.access(BASE_DIR, os.W_OK), f"Directory {BASE_DIR} is not writable"


class TestHostsConfExists:
    """Verify hosts.conf exists with correct content."""

    def test_hosts_conf_exists(self):
        hosts_conf = os.path.join(BASE_DIR, "hosts.conf")
        assert os.path.isfile(hosts_conf), f"File {hosts_conf} does not exist"

    def test_hosts_conf_content(self):
        hosts_conf = os.path.join(BASE_DIR, "hosts.conf")
        with open(hosts_conf, "r") as f:
            content = f.read().strip()

        expected_hosts = ["192.168.1.1", "192.168.1.2", "10.0.0.1"]
        actual_hosts = [line.strip() for line in content.split("\n") if line.strip()]

        assert actual_hosts == expected_hosts, (
            f"hosts.conf content mismatch. Expected: {expected_hosts}, Got: {actual_hosts}"
        )


class TestCheckPingScript:
    """Verify check_ping.sh exists and is executable."""

    def test_check_ping_script_exists(self):
        script_path = os.path.join(BASE_DIR, "scripts", "check_ping.sh")
        assert os.path.isfile(script_path), f"Script {script_path} does not exist"

    def test_check_ping_script_is_executable(self):
        script_path = os.path.join(BASE_DIR, "scripts", "check_ping.sh")
        assert os.access(script_path, os.X_OK), f"Script {script_path} is not executable"

    def test_check_ping_script_content(self):
        script_path = os.path.join(BASE_DIR, "scripts", "check_ping.sh")
        with open(script_path, "r") as f:
            content = f.read()

        # Verify key parts of the script
        assert "#!/bin/bash" in content, "check_ping.sh missing shebang"
        assert "mkdir -p results" in content, "check_ping.sh missing 'mkdir -p results'"
        assert "hosts.conf" in content, "check_ping.sh should read from hosts.conf"
        assert "results/ping.txt" in content, "check_ping.sh should write to results/ping.txt"
        assert "ping" in content, "check_ping.sh should use ping command"


class TestCheckPortsScript:
    """Verify check_ports.sh exists and is executable."""

    def test_check_ports_script_exists(self):
        script_path = os.path.join(BASE_DIR, "scripts", "check_ports.sh")
        assert os.path.isfile(script_path), f"Script {script_path} does not exist"

    def test_check_ports_script_is_executable(self):
        script_path = os.path.join(BASE_DIR, "scripts", "check_ports.sh")
        assert os.access(script_path, os.X_OK), f"Script {script_path} is not executable"

    def test_check_ports_script_content(self):
        script_path = os.path.join(BASE_DIR, "scripts", "check_ports.sh")
        with open(script_path, "r") as f:
            content = f.read()

        # Verify key parts of the script
        assert "#!/bin/bash" in content, "check_ports.sh missing shebang"
        assert "mkdir -p results" in content, "check_ports.sh missing 'mkdir -p results'"
        assert "hosts.conf" in content, "check_ports.sh should read from hosts.conf"
        assert "results/ports.txt" in content, "check_ports.sh should write to results/ports.txt"
        assert "22 80 443" in content or ("22" in content and "80" in content and "443" in content), \
            "check_ports.sh should check ports 22, 80, 443"


class TestAggregatePyScript:
    """Verify aggregate.py exists and has the expected syntax error."""

    def test_aggregate_py_exists(self):
        script_path = os.path.join(BASE_DIR, "aggregate.py")
        assert os.path.isfile(script_path), f"Script {script_path} does not exist"

    def test_aggregate_py_has_syntax_error(self):
        """Verify aggregate.py has a syntax error (missing colon)."""
        script_path = os.path.join(BASE_DIR, "aggregate.py")
        result = subprocess.run(
            ["python3", "-m", "py_compile", script_path],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "aggregate.py should have a syntax error but py_compile succeeded. "
            "The initial state requires the syntax error to be present."
        )

    def test_aggregate_py_content_structure(self):
        """Verify aggregate.py has the expected structure (minus the syntax error)."""
        script_path = os.path.join(BASE_DIR, "aggregate.py")
        with open(script_path, "r") as f:
            content = f.read()

        assert "#!/usr/bin/env python3" in content, "aggregate.py missing shebang"
        assert "import json" in content, "aggregate.py should import json"
        assert "results/ping.txt" in content, "aggregate.py should read results/ping.txt"
        assert "results/ports.txt" in content, "aggregate.py should read results/ports.txt"
        assert "results/status.json" in content, "aggregate.py should write results/status.json"
        assert '"hosts"' in content or "'hosts'" in content, "aggregate.py should use 'hosts' key"


class TestResultsDirectoryNotExists:
    """Verify the results directory does NOT exist initially."""

    def test_results_directory_not_exists(self):
        results_dir = os.path.join(BASE_DIR, "results")
        assert not os.path.exists(results_dir), (
            f"Directory {results_dir} should NOT exist initially. "
            "The student task involves creating this directory via the Makefile/scripts."
        )


class TestMakefileNotExists:
    """Verify the Makefile does NOT exist initially."""

    def test_makefile_not_exists(self):
        makefile_path = os.path.join(BASE_DIR, "Makefile")
        assert not os.path.exists(makefile_path), (
            f"File {makefile_path} should NOT exist initially. "
            "The student task is to create this Makefile."
        )


class TestRequiredToolsAvailable:
    """Verify required tools are available on the system."""

    def test_python3_available(self):
        result = subprocess.run(["which", "python3"], capture_output=True)
        assert result.returncode == 0, "python3 is not available on the system"

    def test_bash_available(self):
        result = subprocess.run(["which", "bash"], capture_output=True)
        assert result.returncode == 0, "bash is not available on the system"

    def test_make_available(self):
        result = subprocess.run(["which", "make"], capture_output=True)
        assert result.returncode == 0, "make is not available on the system"

    def test_ping_available(self):
        result = subprocess.run(["which", "ping"], capture_output=True)
        assert result.returncode == 0, "ping is not available on the system"

    def test_timeout_available(self):
        result = subprocess.run(["which", "timeout"], capture_output=True)
        assert result.returncode == 0, "timeout is not available on the system"


class TestScriptsDirectoryExists:
    """Verify the scripts directory exists."""

    def test_scripts_directory_exists(self):
        scripts_dir = os.path.join(BASE_DIR, "scripts")
        assert os.path.isdir(scripts_dir), f"Directory {scripts_dir} does not exist"
