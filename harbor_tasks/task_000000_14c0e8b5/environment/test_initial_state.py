# test_initial_state.py
"""
Tests to validate the initial state before the student creates the check.py script.
Verifies that the required input files exist with the correct content.
"""

import pytest
import os
import json
import csv
from pathlib import Path


AUDIT_DIR = Path("/home/user/audit")
FIREWALL_RULES_PATH = AUDIT_DIR / "firewall_rules.json"
CONNECTIONS_CSV_PATH = AUDIT_DIR / "connections.csv"


class TestAuditDirectoryExists:
    """Test that the audit directory exists and is accessible."""

    def test_audit_directory_exists(self):
        """The /home/user/audit directory must exist."""
        assert AUDIT_DIR.exists(), f"Directory {AUDIT_DIR} does not exist"

    def test_audit_directory_is_directory(self):
        """The /home/user/audit path must be a directory."""
        assert AUDIT_DIR.is_dir(), f"{AUDIT_DIR} exists but is not a directory"

    def test_audit_directory_is_writable(self):
        """The /home/user/audit directory must be writable."""
        assert os.access(AUDIT_DIR, os.W_OK), f"{AUDIT_DIR} is not writable"


class TestFirewallRulesFile:
    """Test that the firewall_rules.json file exists with correct content."""

    def test_firewall_rules_file_exists(self):
        """The firewall_rules.json file must exist."""
        assert FIREWALL_RULES_PATH.exists(), \
            f"File {FIREWALL_RULES_PATH} does not exist"

    def test_firewall_rules_is_file(self):
        """The firewall_rules.json path must be a regular file."""
        assert FIREWALL_RULES_PATH.is_file(), \
            f"{FIREWALL_RULES_PATH} exists but is not a regular file"

    def test_firewall_rules_is_readable(self):
        """The firewall_rules.json file must be readable."""
        assert os.access(FIREWALL_RULES_PATH, os.R_OK), \
            f"{FIREWALL_RULES_PATH} is not readable"

    def test_firewall_rules_is_valid_json(self):
        """The firewall_rules.json file must contain valid JSON."""
        try:
            with open(FIREWALL_RULES_PATH, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"{FIREWALL_RULES_PATH} contains invalid JSON: {e}")

    def test_firewall_rules_has_rules_key(self):
        """The JSON must have a 'rules' key."""
        with open(FIREWALL_RULES_PATH, 'r') as f:
            data = json.load(f)
        assert "rules" in data, \
            f"{FIREWALL_RULES_PATH} is missing 'rules' key"

    def test_firewall_rules_has_default_action(self):
        """The JSON must have a 'default_action' key."""
        with open(FIREWALL_RULES_PATH, 'r') as f:
            data = json.load(f)
        assert "default_action" in data, \
            f"{FIREWALL_RULES_PATH} is missing 'default_action' key"

    def test_firewall_rules_default_action_is_deny(self):
        """The default_action must be 'deny'."""
        with open(FIREWALL_RULES_PATH, 'r') as f:
            data = json.load(f)
        assert data["default_action"] == "deny", \
            f"Expected default_action to be 'deny', got '{data['default_action']}'"

    def test_firewall_rules_has_six_rules(self):
        """There must be exactly 6 rules."""
        with open(FIREWALL_RULES_PATH, 'r') as f:
            data = json.load(f)
        assert len(data["rules"]) == 6, \
            f"Expected 6 rules, found {len(data['rules'])}"

    def test_firewall_rules_structure(self):
        """Each rule must have id, action, source_cidr, and dest_port."""
        with open(FIREWALL_RULES_PATH, 'r') as f:
            data = json.load(f)

        required_keys = {"id", "action", "source_cidr", "dest_port"}
        for i, rule in enumerate(data["rules"]):
            missing = required_keys - set(rule.keys())
            assert not missing, \
                f"Rule {i+1} is missing keys: {missing}"

    def test_firewall_rules_expected_content(self):
        """Verify the specific rules match expected content."""
        with open(FIREWALL_RULES_PATH, 'r') as f:
            data = json.load(f)

        expected_rules = [
            {"id": 1, "action": "allow", "source_cidr": "10.0.0.0/8", "dest_port": "443"},
            {"id": 2, "action": "allow", "source_cidr": "10.1.0.0/16", "dest_port": "8000-9000"},
            {"id": 3, "action": "deny", "source_cidr": "10.1.5.0/24", "dest_port": "8443"},
            {"id": 4, "action": "allow", "source_cidr": "192.168.1.0/24", "dest_port": "22"},
            {"id": 5, "action": "allow", "source_cidr": "0.0.0.0/0", "dest_port": "80"},
            {"id": 6, "action": "allow", "source_cidr": "172.16.0.0/12", "dest_port": "3306"},
        ]

        for expected in expected_rules:
            found = False
            for rule in data["rules"]:
                if rule == expected:
                    found = True
                    break
            assert found, f"Expected rule not found: {expected}"


class TestConnectionsCSVFile:
    """Test that the connections.csv file exists with correct content."""

    def test_connections_csv_exists(self):
        """The connections.csv file must exist."""
        assert CONNECTIONS_CSV_PATH.exists(), \
            f"File {CONNECTIONS_CSV_PATH} does not exist"

    def test_connections_csv_is_file(self):
        """The connections.csv path must be a regular file."""
        assert CONNECTIONS_CSV_PATH.is_file(), \
            f"{CONNECTIONS_CSV_PATH} exists but is not a regular file"

    def test_connections_csv_is_readable(self):
        """The connections.csv file must be readable."""
        assert os.access(CONNECTIONS_CSV_PATH, os.R_OK), \
            f"{CONNECTIONS_CSV_PATH} is not readable"

    def test_connections_csv_has_header(self):
        """The CSV must have the expected header."""
        with open(CONNECTIONS_CSV_PATH, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

        expected_header = ["timestamp", "src_ip", "src_port", "dest_ip", "dest_port", "proto"]
        assert header == expected_header, \
            f"Expected header {expected_header}, got {header}"

    def test_connections_csv_has_nine_data_rows(self):
        """The CSV must have exactly 9 data rows (excluding header)."""
        with open(CONNECTIONS_CSV_PATH, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

        assert len(rows) == 9, \
            f"Expected 9 data rows, found {len(rows)}"

    def test_connections_csv_expected_source_ips(self):
        """Verify the expected source IPs are present."""
        with open(CONNECTIONS_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            src_ips = [row["src_ip"] for row in reader]

        expected_ips = [
            "10.1.5.17",
            "10.1.2.33",
            "192.168.1.50",
            "192.168.2.10",
            "10.0.50.1",
            "10.1.5.200",
            "172.16.5.5",
            "8.8.8.8",
            "8.8.8.8",
        ]

        assert sorted(src_ips) == sorted(expected_ips), \
            f"Source IPs don't match expected. Got: {src_ips}"

    def test_connections_csv_expected_dest_ports(self):
        """Verify the expected destination ports are present."""
        with open(CONNECTIONS_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            dest_ports = [row["dest_port"] for row in reader]

        expected_ports = ["8443", "8500", "22", "22", "443", "8080", "3306", "80", "443"]

        assert sorted(dest_ports) == sorted(expected_ports), \
            f"Destination ports don't match expected. Got: {dest_ports}"

    def test_connections_csv_specific_connections(self):
        """Verify specific connection combinations exist."""
        with open(CONNECTIONS_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            connections = [(row["src_ip"], row["dest_port"]) for row in reader]

        # These are the connections that should be BLOCKED
        expected_blocked = [
            ("10.1.5.17", "8443"),   # matches /24 deny
            ("192.168.2.10", "22"),  # not in 192.168.1.0/24
            ("8.8.8.8", "443"),      # 0.0.0.0/0 only allows 80
        ]

        for conn in expected_blocked:
            assert conn in connections, \
                f"Expected connection {conn} not found in CSV"

        # These are the connections that should be ALLOWED
        expected_allowed = [
            ("10.1.2.33", "8500"),   # 10.1.0.0/16 allows 8000-9000
            ("192.168.1.50", "22"),  # 192.168.1.0/24 allows 22
            ("10.0.50.1", "443"),    # 10.0.0.0/8 allows 443
            ("10.1.5.200", "8080"),  # 10.1.0.0/16 allows 8000-9000
            ("172.16.5.5", "3306"),  # 172.16.0.0/12 allows 3306
            ("8.8.8.8", "80"),       # 0.0.0.0/0 allows 80
        ]

        for conn in expected_allowed:
            assert conn in connections, \
                f"Expected connection {conn} not found in CSV"


class TestCheckScriptDoesNotExist:
    """Test that the check.py script does NOT exist yet (student needs to create it)."""

    def test_check_script_does_not_exist(self):
        """The check.py script should NOT exist yet - student needs to create it."""
        check_script_path = AUDIT_DIR / "check.py"
        assert not check_script_path.exists(), \
            f"{check_script_path} already exists - it should be created by the student"


class TestPythonAvailable:
    """Test that Python 3 is available for running the script."""

    def test_python3_available(self):
        """Python 3 must be available."""
        import subprocess
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "python3 is not available or not working"

    def test_python3_has_ipaddress_module(self):
        """Python 3 must have the ipaddress module (stdlib)."""
        import subprocess
        result = subprocess.run(
            ["python3", "-c", "import ipaddress; print('ok')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Python ipaddress module is not available"
        assert "ok" in result.stdout, \
            "Python ipaddress module import failed"
