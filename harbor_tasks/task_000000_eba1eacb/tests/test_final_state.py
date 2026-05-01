# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student has completed the task.
This verifies the netmon monitoring stack Makefile is properly created and aggregate.py is fixed.
"""

import os
import json
import subprocess
import pytest


BASE_DIR = "/home/user/netmon"


class TestMakefileExists:
    """Verify the Makefile exists and has required content."""

    def test_makefile_exists(self):
        makefile_path = os.path.join(BASE_DIR, "Makefile")
        assert os.path.isfile(makefile_path), f"Makefile does not exist at {makefile_path}"

    def test_makefile_references_hosts_conf(self):
        """Makefile must reference hosts.conf for the config dependency check."""
        makefile_path = os.path.join(BASE_DIR, "Makefile")
        result = subprocess.run(
            ["grep", "-E", "hosts\\.conf", makefile_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Makefile must reference hosts.conf for config dependency check. "
            "grep -E 'hosts\\.conf' did not find a match."
        )


class TestAggregatePySyntaxFixed:
    """Verify aggregate.py syntax error is fixed."""

    def test_aggregate_py_compiles(self):
        """aggregate.py must compile without syntax errors."""
        script_path = os.path.join(BASE_DIR, "aggregate.py")
        result = subprocess.run(
            ["python3", "-m", "py_compile", script_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"aggregate.py has a syntax error and does not compile. "
            f"Error: {result.stderr}"
        )


class TestMakeReportTarget:
    """Verify 'make report' target works correctly."""

    def test_make_report_exits_zero(self):
        """Running 'make report' should exit with code 0."""
        # Clean up any existing results first
        results_dir = os.path.join(BASE_DIR, "results")
        if os.path.exists(results_dir):
            for f in os.listdir(results_dir):
                os.remove(os.path.join(results_dir, f))

        result = subprocess.run(
            ["make", "report"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"'make report' failed with exit code {result.returncode}. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestResultsAfterMakeReport:
    """Verify results files are created correctly after running make report."""

    @pytest.fixture(autouse=True)
    def run_make_report(self):
        """Run make report before testing results."""
        # Clean up any existing results first
        results_dir = os.path.join(BASE_DIR, "results")
        if os.path.exists(results_dir):
            for f in os.listdir(results_dir):
                os.remove(os.path.join(results_dir, f))

        subprocess.run(
            ["make", "report"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )

    def test_ping_txt_exists(self):
        """results/ping.txt should exist after make report."""
        ping_path = os.path.join(BASE_DIR, "results", "ping.txt")
        assert os.path.isfile(ping_path), f"File {ping_path} does not exist after make report"

    def test_ping_txt_has_three_lines(self):
        """results/ping.txt should contain 3 lines (one per host)."""
        ping_path = os.path.join(BASE_DIR, "results", "ping.txt")
        with open(ping_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 3, (
            f"results/ping.txt should have 3 lines (one per host), but has {len(lines)} lines"
        )

    def test_ports_txt_exists(self):
        """results/ports.txt should exist after make report."""
        ports_path = os.path.join(BASE_DIR, "results", "ports.txt")
        assert os.path.isfile(ports_path), f"File {ports_path} does not exist after make report"

    def test_ports_txt_has_nine_lines(self):
        """results/ports.txt should contain 9 lines (3 hosts × 3 ports)."""
        ports_path = os.path.join(BASE_DIR, "results", "ports.txt")
        with open(ports_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 9, (
            f"results/ports.txt should have 9 lines (3 hosts × 3 ports), but has {len(lines)} lines"
        )

    def test_status_json_exists(self):
        """results/status.json should exist after make report."""
        json_path = os.path.join(BASE_DIR, "results", "status.json")
        assert os.path.isfile(json_path), f"File {json_path} does not exist after make report"

    def test_status_json_is_valid(self):
        """results/status.json should be valid JSON."""
        json_path = os.path.join(BASE_DIR, "results", "status.json")
        with open(json_path, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"results/status.json is not valid JSON: {e}")

    def test_status_json_has_hosts_key(self):
        """results/status.json should have a 'hosts' key."""
        json_path = os.path.join(BASE_DIR, "results", "status.json")
        with open(json_path, "r") as f:
            data = json.load(f)
        assert "hosts" in data, "results/status.json missing 'hosts' key"

    def test_status_json_has_all_three_hosts(self):
        """results/status.json should have entries for all 3 hosts."""
        json_path = os.path.join(BASE_DIR, "results", "status.json")
        with open(json_path, "r") as f:
            data = json.load(f)

        expected_hosts = ["192.168.1.1", "192.168.1.2", "10.0.0.1"]
        hosts = data.get("hosts", {})

        for host in expected_hosts:
            assert host in hosts, f"results/status.json missing host entry for {host}"


class TestConfigCheckFailsWithoutHostsConf:
    """Verify make report fails when hosts.conf is missing."""

    def test_make_report_fails_without_hosts_conf(self):
        """Running 'make report' should fail when hosts.conf is missing."""
        hosts_conf = os.path.join(BASE_DIR, "hosts.conf")
        hosts_conf_backup = os.path.join(BASE_DIR, "hosts.conf.bak")

        # Backup hosts.conf
        os.rename(hosts_conf, hosts_conf_backup)

        try:
            result = subprocess.run(
                ["make", "report"],
                cwd=BASE_DIR,
                capture_output=True,
                text=True
            )
            exit_code = result.returncode
        finally:
            # Restore hosts.conf
            os.rename(hosts_conf_backup, hosts_conf)

        assert exit_code != 0, (
            "make report should fail (exit nonzero) when hosts.conf is missing, "
            f"but it exited with code {exit_code}"
        )


class TestHostsConfUnchanged:
    """Verify hosts.conf content remains unchanged."""

    def test_hosts_conf_content_unchanged(self):
        """hosts.conf should have the original content."""
        hosts_conf = os.path.join(BASE_DIR, "hosts.conf")
        with open(hosts_conf, "r") as f:
            content = f.read().strip()

        expected_hosts = ["192.168.1.1", "192.168.1.2", "10.0.0.1"]
        actual_hosts = [line.strip() for line in content.split("\n") if line.strip()]

        assert actual_hosts == expected_hosts, (
            f"hosts.conf content changed. Expected: {expected_hosts}, Got: {actual_hosts}"
        )


class TestScriptsUnchanged:
    """Verify shell scripts logic remains unchanged."""

    def test_check_ping_script_still_valid(self):
        """check_ping.sh should still have its core functionality."""
        script_path = os.path.join(BASE_DIR, "scripts", "check_ping.sh")
        with open(script_path, "r") as f:
            content = f.read()

        assert "hosts.conf" in content, "check_ping.sh should still read from hosts.conf"
        assert "results/ping.txt" in content, "check_ping.sh should still write to results/ping.txt"
        assert "ping" in content, "check_ping.sh should still use ping command"

    def test_check_ports_script_still_valid(self):
        """check_ports.sh should still have its core functionality."""
        script_path = os.path.join(BASE_DIR, "scripts", "check_ports.sh")
        with open(script_path, "r") as f:
            content = f.read()

        assert "hosts.conf" in content, "check_ports.sh should still read from hosts.conf"
        assert "results/ports.txt" in content, "check_ports.sh should still write to results/ports.txt"


class TestMakefileInvokesScripts:
    """Verify Makefile actually invokes the scripts (anti-shortcut guard)."""

    def test_makefile_invokes_check_ping(self):
        """Makefile should invoke check_ping.sh."""
        makefile_path = os.path.join(BASE_DIR, "Makefile")
        with open(makefile_path, "r") as f:
            content = f.read()

        assert "check_ping" in content, (
            "Makefile should invoke check_ping.sh (not just create stub outputs)"
        )

    def test_makefile_invokes_check_ports(self):
        """Makefile should invoke check_ports.sh."""
        makefile_path = os.path.join(BASE_DIR, "Makefile")
        with open(makefile_path, "r") as f:
            content = f.read()

        assert "check_ports" in content, (
            "Makefile should invoke check_ports.sh (not just create stub outputs)"
        )

    def test_makefile_invokes_aggregate(self):
        """Makefile should invoke aggregate.py."""
        makefile_path = os.path.join(BASE_DIR, "Makefile")
        with open(makefile_path, "r") as f:
            content = f.read()

        assert "aggregate" in content, (
            "Makefile should invoke aggregate.py (not just create stub outputs)"
        )
