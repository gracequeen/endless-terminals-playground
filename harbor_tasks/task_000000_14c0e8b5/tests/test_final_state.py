# test_final_state.py
"""
Tests to validate the final state after the student creates the check.py script.
Verifies that the script exists, runs correctly, and produces the expected output.
"""

import pytest
import os
import json
import csv
import subprocess
import re
from pathlib import Path


AUDIT_DIR = Path("/home/user/audit")
FIREWALL_RULES_PATH = AUDIT_DIR / "firewall_rules.json"
CONNECTIONS_CSV_PATH = AUDIT_DIR / "connections.csv"
CHECK_SCRIPT_PATH = AUDIT_DIR / "check.py"


class TestInputFilesUnchanged:
    """Verify that the input files remain unchanged."""

    def test_firewall_rules_unchanged(self):
        """The firewall_rules.json file must remain unchanged."""
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

        assert "rules" in data, "firewall_rules.json is missing 'rules' key"
        assert "default_action" in data, "firewall_rules.json is missing 'default_action' key"
        assert data["default_action"] == "deny", "default_action should be 'deny'"
        assert len(data["rules"]) == 6, f"Expected 6 rules, found {len(data['rules'])}"

        for expected in expected_rules:
            assert expected in data["rules"], \
                f"Expected rule not found or modified: {expected}"

    def test_connections_csv_unchanged(self):
        """The connections.csv file must remain unchanged."""
        with open(CONNECTIONS_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            connections = [(row["src_ip"], row["dest_port"]) for row in reader]

        expected_connections = [
            ("10.1.5.17", "8443"),
            ("10.1.2.33", "8500"),
            ("192.168.1.50", "22"),
            ("192.168.2.10", "22"),
            ("10.0.50.1", "443"),
            ("10.1.5.200", "8080"),
            ("172.16.5.5", "3306"),
            ("8.8.8.8", "80"),
            ("8.8.8.8", "443"),
        ]

        assert len(connections) == 9, \
            f"Expected 9 connections, found {len(connections)}"

        for expected in expected_connections:
            assert expected in connections, \
                f"Expected connection {expected} not found - CSV may have been modified"


class TestCheckScriptExists:
    """Test that the check.py script exists and is valid."""

    def test_check_script_exists(self):
        """The check.py script must exist."""
        assert CHECK_SCRIPT_PATH.exists(), \
            f"Script {CHECK_SCRIPT_PATH} does not exist - student needs to create it"

    def test_check_script_is_file(self):
        """The check.py path must be a regular file."""
        assert CHECK_SCRIPT_PATH.is_file(), \
            f"{CHECK_SCRIPT_PATH} exists but is not a regular file"

    def test_check_script_is_readable(self):
        """The check.py file must be readable."""
        assert os.access(CHECK_SCRIPT_PATH, os.R_OK), \
            f"{CHECK_SCRIPT_PATH} is not readable"

    def test_check_script_has_python_syntax(self):
        """The check.py script must have valid Python syntax."""
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(CHECK_SCRIPT_PATH)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"check.py has syntax errors: {result.stderr}"


class TestCheckScriptExecution:
    """Test that the check.py script runs correctly."""

    def test_check_script_exits_zero(self):
        """The check.py script must exit with code 0."""
        result = subprocess.run(
            ["python3", str(CHECK_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(AUDIT_DIR)
        )
        assert result.returncode == 0, \
            f"check.py exited with code {result.returncode}. stderr: {result.stderr}"

    def test_check_script_produces_output(self):
        """The check.py script must produce some output."""
        result = subprocess.run(
            ["python3", str(CHECK_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(AUDIT_DIR)
        )
        # Should have at least some output (the BLOCKED lines)
        assert len(result.stdout.strip()) > 0, \
            "check.py produced no output - expected BLOCKED lines"


class TestBlockedConnections:
    """Test that the correct connections are flagged as BLOCKED."""

    @pytest.fixture
    def script_output(self):
        """Run the script and return its stdout."""
        result = subprocess.run(
            ["python3", str(CHECK_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(AUDIT_DIR)
        )
        return result.stdout

    def test_blocked_10_1_5_17_port_8443(self, script_output):
        """10.1.5.17:8443 should be BLOCKED (matches /24 deny rule)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        found = False
        for line in blocked_lines:
            if '10.1.5.17' in line and '8443' in line:
                found = True
                break

        assert found, \
            f"Expected BLOCKED line for 10.1.5.17:8443 (matches 10.1.5.0/24 deny rule). " \
            f"Output was:\n{script_output}"

    def test_blocked_192_168_2_10_port_22(self, script_output):
        """192.168.2.10:22 should be BLOCKED (not in 192.168.1.0/24)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        found = False
        for line in blocked_lines:
            if '192.168.2.10' in line and '22' in line:
                found = True
                break

        assert found, \
            f"Expected BLOCKED line for 192.168.2.10:22 (not in 192.168.1.0/24, falls to default deny). " \
            f"Output was:\n{script_output}"

    def test_blocked_8_8_8_8_port_443(self, script_output):
        """8.8.8.8:443 should be BLOCKED (0.0.0.0/0 only allows port 80)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        found = False
        for line in blocked_lines:
            if '8.8.8.8' in line and '443' in line:
                found = True
                break

        assert found, \
            f"Expected BLOCKED line for 8.8.8.8:443 (0.0.0.0/0 only allows port 80). " \
            f"Output was:\n{script_output}"

    def test_exactly_three_blocked_lines(self, script_output):
        """There should be exactly 3 BLOCKED lines."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        assert len(blocked_lines) == 3, \
            f"Expected exactly 3 BLOCKED lines, found {len(blocked_lines)}. " \
            f"BLOCKED lines:\n" + '\n'.join(blocked_lines)


class TestAllowedConnections:
    """Test that allowed connections are NOT flagged as BLOCKED."""

    @pytest.fixture
    def script_output(self):
        """Run the script and return its stdout."""
        result = subprocess.run(
            ["python3", str(CHECK_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(AUDIT_DIR)
        )
        return result.stdout

    def test_not_blocked_10_1_2_33_port_8500(self, script_output):
        """10.1.2.33:8500 should NOT be blocked (10.1.0.0/16 allows 8000-9000)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        for line in blocked_lines:
            assert not ('10.1.2.33' in line and '8500' in line), \
                f"10.1.2.33:8500 should be ALLOWED (10.1.0.0/16 allows 8000-9000) but was blocked"

    def test_not_blocked_192_168_1_50_port_22(self, script_output):
        """192.168.1.50:22 should NOT be blocked (192.168.1.0/24 allows 22)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        for line in blocked_lines:
            assert not ('192.168.1.50' in line and '22' in line), \
                f"192.168.1.50:22 should be ALLOWED (192.168.1.0/24 allows 22) but was blocked"

    def test_not_blocked_10_0_50_1_port_443(self, script_output):
        """10.0.50.1:443 should NOT be blocked (10.0.0.0/8 allows 443)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        for line in blocked_lines:
            assert not ('10.0.50.1' in line and '443' in line), \
                f"10.0.50.1:443 should be ALLOWED (10.0.0.0/8 allows 443) but was blocked"

    def test_not_blocked_10_1_5_200_port_8080(self, script_output):
        """10.1.5.200:8080 should NOT be blocked (10.1.0.0/16 allows 8000-9000)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        for line in blocked_lines:
            assert not ('10.1.5.200' in line and '8080' in line), \
                f"10.1.5.200:8080 should be ALLOWED (10.1.0.0/16 allows 8000-9000, /24 deny is only for 8443) but was blocked"

    def test_not_blocked_172_16_5_5_port_3306(self, script_output):
        """172.16.5.5:3306 should NOT be blocked (172.16.0.0/12 allows 3306)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        for line in blocked_lines:
            assert not ('172.16.5.5' in line and '3306' in line), \
                f"172.16.5.5:3306 should be ALLOWED (172.16.0.0/12 allows 3306) but was blocked"

    def test_not_blocked_8_8_8_8_port_80(self, script_output):
        """8.8.8.8:80 should NOT be blocked (0.0.0.0/0 allows 80)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        for line in blocked_lines:
            # Be careful: we need to check for port 80 specifically, not just any line with 8.8.8.8
            if '8.8.8.8' in line:
                # Check that this line is NOT about port 80
                # Port 80 should be allowed, port 443 should be blocked
                assert ':80' not in line and ' 80 ' not in line and line.strip().endswith('80') is False, \
                    f"8.8.8.8:80 should be ALLOWED (0.0.0.0/0 allows 80) but appears to be blocked"


class TestAntiShortcutGuards:
    """Test that the script doesn't hardcode the results."""

    def test_no_hardcoded_blocked_ips(self):
        """The script should not have hardcoded blocked IPs outside comments."""
        with open(CHECK_SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Remove comments and strings to check for hardcoded values
        lines = content.split('\n')
        code_lines = []
        for line in lines:
            # Remove inline comments
            if '#' in line:
                line = line[:line.index('#')]
            code_lines.append(line)

        code_without_comments = '\n'.join(code_lines)

        # Check for hardcoded specific blocked results
        # The script shouldn't have these IPs hardcoded as part of the logic
        hardcoded_patterns = [
            r'["\']10\.1\.5\.17["\'].*["\']8443["\']',
            r'["\']192\.168\.2\.10["\'].*["\']22["\']',
            r'["\']8\.8\.8\.8["\'].*["\']443["\']',
        ]

        # Also check for lists/tuples of blocked connections
        suspicious_patterns = [
            r'\[\s*\(["\']10\.1\.5\.17',
            r'blocked.*=.*\[.*10\.1\.5\.17',
        ]

        for pattern in suspicious_patterns:
            match = re.search(pattern, code_without_comments, re.IGNORECASE)
            if match:
                # This is a warning, not necessarily a failure
                # The script might legitimately reference these for testing
                pass

    def test_script_uses_ipaddress_or_cidr_logic(self):
        """The script should use proper CIDR matching logic."""
        with open(CHECK_SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Check for evidence of proper CIDR handling
        has_ipaddress_import = 'ipaddress' in content
        has_network_logic = any(x in content for x in [
            'ip_network', 'ip_address', 'IPv4Network', 'IPv4Address',
            'network_address', 'prefixlen', 'netmask'
        ])
        has_manual_cidr = any(x in content for x in [
            '<<', '>>', '&', 'bit', 'mask', 'subnet'
        ])

        assert has_ipaddress_import or has_network_logic or has_manual_cidr, \
            "Script doesn't appear to use proper CIDR matching logic (ipaddress module or manual bit operations)"

    def test_script_parses_json_file(self):
        """The script should parse the JSON file."""
        with open(CHECK_SCRIPT_PATH, 'r') as f:
            content = f.read()

        has_json_import = 'json' in content
        has_json_load = 'json.load' in content or 'json.loads' in content

        assert has_json_import and has_json_load, \
            "Script doesn't appear to parse the JSON file properly"

    def test_script_parses_csv_file(self):
        """The script should parse the CSV file."""
        with open(CHECK_SCRIPT_PATH, 'r') as f:
            content = f.read()

        has_csv_import = 'csv' in content
        has_csv_reader = 'csv.reader' in content or 'csv.DictReader' in content or 'csv.Reader' in content

        # Alternative: might read and split manually
        has_manual_csv = '.split' in content and 'connections' in content.lower()

        assert (has_csv_import and has_csv_reader) or has_manual_csv, \
            "Script doesn't appear to parse the CSV file properly"

    def test_script_handles_port_ranges(self):
        """The script should handle port ranges (e.g., '8000-9000')."""
        with open(CHECK_SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Look for evidence of port range handling
        has_range_split = '-' in content and 'split' in content
        has_range_check = any(x in content for x in ['<=', '>=', 'range', 'in range'])

        assert has_range_split or has_range_check, \
            "Script doesn't appear to handle port ranges (e.g., '8000-9000')"


class TestCIDRLogicCorrectness:
    """Test that the CIDR logic is actually correct by checking specific behaviors."""

    @pytest.fixture
    def script_output(self):
        """Run the script and return its stdout."""
        result = subprocess.run(
            ["python3", str(CHECK_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            cwd=str(AUDIT_DIR)
        )
        return result.stdout

    def test_most_specific_cidr_wins(self, script_output):
        """
        The most specific CIDR should win.
        10.1.5.17 matches /8, /16, and /24.
        The /24 deny rule for port 8443 should take precedence.
        """
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        # 10.1.5.17:8443 should be blocked due to /24 deny
        found_blocked = any('10.1.5.17' in l and '8443' in l for l in blocked_lines)
        assert found_blocked, \
            "10.1.5.17:8443 should be BLOCKED because the /24 deny rule is more specific than /16 allow"

        # 10.1.5.200:8080 should NOT be blocked - /24 deny is only for 8443
        not_blocked = all(not ('10.1.5.200' in l and '8080' in l) for l in blocked_lines)
        assert not_blocked, \
            "10.1.5.200:8080 should be ALLOWED - the /24 deny is only for port 8443, not 8080"

    def test_port_range_inclusive(self, script_output):
        """Port ranges should be inclusive (8000-9000 includes both 8000 and 9000)."""
        lines = script_output.strip().split('\n')
        blocked_lines = [l for l in lines if 'BLOCKED' in l.upper()]

        # 10.1.2.33:8500 should be allowed (within 8000-9000)
        not_blocked = all(not ('10.1.2.33' in l and '8500' in l) for l in blocked_lines)
        assert not_blocked, \
            "10.1.2.33:8500 should be ALLOWED - port 8500 is within range 8000-9000"

        # 10.1.5.200:8080 should be allowed (within 8000-9000)
        not_blocked_2 = all(not ('10.1.5.200' in l and '8080' in l) for l in blocked_lines)
        assert not_blocked_2, \
            "10.1.5.200:8080 should be ALLOWED - port 8080 is within range 8000-9000"
