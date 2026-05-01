# test_final_state.py
"""
Tests to validate the final state of the operating system / filesystem
after the student has completed the firewall audit task.

The task requires:
1. Reconciling current_rules.txt to only allow ports 22, 80, 443 (removing 3306 and 6379)
2. Creating an audit_report.txt documenting the non-compliant ports and remediation
3. Leaving policy.conf unchanged (it's the source of truth)
"""

import os
import re
import pytest


class TestFirewallDirectoryIntact:
    """Test that the firewall directory still exists."""

    def test_firewall_directory_exists(self):
        """The /home/user/firewall directory must still exist."""
        path = "/home/user/firewall"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestPolicyConfUnchanged:
    """Test that policy.conf remains unchanged (source of truth)."""

    def test_policy_conf_exists(self):
        """The policy.conf file must still exist."""
        path = "/home/user/firewall/policy.conf"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_policy_conf_contains_allowed_ports_declaration(self):
        """policy.conf must still contain the original ALLOWED_PORTS declaration."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "ALLOWED_PORTS=22,80,443" in content, \
            "policy.conf must contain 'ALLOWED_PORTS=22,80,443' - policy should not be modified"

    def test_policy_conf_contains_approved_ports_comment(self):
        """policy.conf must still contain the approved inbound ports comment."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "# Approved inbound ports" in content, \
            "policy.conf must contain '# Approved inbound ports' comment"

    def test_policy_conf_contains_review_date(self):
        """policy.conf must still contain the last reviewed date."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "# Last reviewed: 2024-01-15" in content, \
            "policy.conf must contain '# Last reviewed: 2024-01-15'"

    def test_policy_conf_not_loosened_no_3306(self):
        """policy.conf must NOT contain port 3306 - policy should not be loosened."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "3306" not in content, \
            "policy.conf must NOT contain '3306' - agent should not loosen policy to match bad rules"

    def test_policy_conf_not_loosened_no_6379(self):
        """policy.conf must NOT contain port 6379 - policy should not be loosened."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "6379" not in content, \
            "policy.conf must NOT contain '6379' - agent should not loosen policy to match bad rules"


class TestCurrentRulesCompliant:
    """Test that current_rules.txt has been fixed to match policy."""

    def test_current_rules_exists(self):
        """The current_rules.txt file must still exist."""
        path = "/home/user/firewall/current_rules.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_current_rules_is_valid_iptables_format_filter(self):
        """current_rules.txt must still be valid iptables-save format with *filter."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "*filter" in content, \
            "current_rules.txt must contain '*filter' (iptables-save format must be preserved)"

    def test_current_rules_is_valid_iptables_format_commit(self):
        """current_rules.txt must still be valid iptables-save format with COMMIT."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "COMMIT" in content, \
            "current_rules.txt must contain 'COMMIT' (iptables-save format must be preserved)"

    def test_current_rules_input_drop_policy_preserved(self):
        """current_rules.txt must still have INPUT chain with DROP policy."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert ":INPUT DROP" in content, \
            "current_rules.txt must have ':INPUT DROP' chain policy preserved"

    def test_current_rules_forward_drop_policy_preserved(self):
        """current_rules.txt must still have FORWARD chain with DROP policy."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert ":FORWARD DROP" in content, \
            "current_rules.txt must have ':FORWARD DROP' chain policy preserved"

    def test_current_rules_output_accept_policy_preserved(self):
        """current_rules.txt must still have OUTPUT chain with ACCEPT policy."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert ":OUTPUT ACCEPT" in content, \
            "current_rules.txt must have ':OUTPUT ACCEPT' chain policy preserved"

    def test_current_rules_established_related_preserved(self):
        """current_rules.txt must still have ESTABLISHED,RELATED rule."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "ESTABLISHED,RELATED" in content, \
            "current_rules.txt must preserve ESTABLISHED,RELATED rule"

    def test_current_rules_loopback_preserved(self):
        """current_rules.txt must still have loopback interface rule."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "-i lo" in content, \
            "current_rules.txt must preserve loopback interface rule (-i lo)"

    def test_current_rules_has_port_22(self):
        """current_rules.txt must still have rule for port 22 (SSH)."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 22" in content, \
            "current_rules.txt must preserve rule for port 22 (SSH)"

    def test_current_rules_has_port_80(self):
        """current_rules.txt must still have rule for port 80 (HTTP)."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 80" in content, \
            "current_rules.txt must preserve rule for port 80 (HTTP)"

    def test_current_rules_has_port_443(self):
        """current_rules.txt must still have rule for port 443 (HTTPS)."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 443" in content, \
            "current_rules.txt must preserve rule for port 443 (HTTPS)"

    def test_current_rules_no_port_3306(self):
        """current_rules.txt must NOT contain port 3306 (MySQL) - non-compliant port removed."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "3306" not in content, \
            "current_rules.txt must NOT contain '3306' - non-compliant MySQL port must be removed"

    def test_current_rules_no_port_6379(self):
        """current_rules.txt must NOT contain port 6379 (Redis) - non-compliant port removed."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "6379" not in content, \
            "current_rules.txt must NOT contain '6379' - non-compliant Redis port must be removed"

    def test_current_rules_exactly_three_dport_rules(self):
        """current_rules.txt must have exactly 3 dport rules (22, 80, 443)."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        # Count lines with --dport for the allowed ports
        dport_pattern = re.compile(r'--dport\s+(22|80|443)\b')
        matches = dport_pattern.findall(content)
        assert len(matches) == 3, \
            f"current_rules.txt must have exactly 3 dport rules for ports 22, 80, 443. Found: {len(matches)}"


class TestAuditReportCreated:
    """Test that audit_report.txt was created with required content."""

    def test_audit_report_exists(self):
        """The audit_report.txt file must exist."""
        path = "/home/user/firewall/audit_report.txt"
        assert os.path.isfile(path), \
            f"File {path} does not exist - audit report must be created"

    def test_audit_report_not_empty(self):
        """The audit_report.txt file must not be empty."""
        path = "/home/user/firewall/audit_report.txt"
        with open(path, "r") as f:
            content = f.read()
        assert len(content.strip()) > 0, \
            "audit_report.txt must not be empty"

    def test_audit_report_mentions_port_3306(self):
        """The audit_report.txt must mention port 3306 as non-compliant."""
        path = "/home/user/firewall/audit_report.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "3306" in content, \
            "audit_report.txt must mention port 3306 (the non-compliant MySQL port)"

    def test_audit_report_mentions_port_6379(self):
        """The audit_report.txt must mention port 6379 as non-compliant."""
        path = "/home/user/firewall/audit_report.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "6379" in content, \
            "audit_report.txt must mention port 6379 (the non-compliant Redis port)"

    def test_audit_report_indicates_remediation(self):
        """The audit_report.txt should indicate some remediation action was taken."""
        path = "/home/user/firewall/audit_report.txt"
        with open(path, "r") as f:
            content = f.read().lower()
        # Check for common remediation-related terms
        remediation_indicators = [
            "remov", "delet", "fix", "correct", "updat", "chang", 
            "compli", "resolv", "address", "action", "modif"
        ]
        has_remediation_mention = any(indicator in content for indicator in remediation_indicators)
        assert has_remediation_mention, \
            "audit_report.txt should indicate what remediation action was taken (e.g., removed, fixed, updated, etc.)"


class TestApplyRulesScriptPreserved:
    """Test that apply_rules.sh still exists and is executable."""

    def test_apply_rules_script_exists(self):
        """The apply_rules.sh script must still exist."""
        path = "/home/user/firewall/apply_rules.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_apply_rules_script_is_executable(self):
        """The apply_rules.sh script must still be executable."""
        path = "/home/user/firewall/apply_rules.sh"
        assert os.access(path, os.X_OK), f"File {path} is not executable"
