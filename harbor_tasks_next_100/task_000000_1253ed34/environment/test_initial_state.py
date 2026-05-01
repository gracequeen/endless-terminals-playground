# test_initial_state.py
"""
Tests to validate the initial state of the operating system / filesystem
before the student performs the firewall audit task.
"""

import os
import pytest


class TestFirewallDirectoryExists:
    """Test that the firewall directory exists and is writable."""

    def test_firewall_directory_exists(self):
        """The /home/user/firewall directory must exist."""
        path = "/home/user/firewall"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_firewall_directory_is_writable(self):
        """The /home/user/firewall directory must be writable."""
        path = "/home/user/firewall"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestPolicyConfFile:
    """Test that policy.conf exists with correct content."""

    def test_policy_conf_exists(self):
        """The policy.conf file must exist."""
        path = "/home/user/firewall/policy.conf"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_policy_conf_contains_allowed_ports_declaration(self):
        """policy.conf must contain the ALLOWED_PORTS declaration."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "ALLOWED_PORTS=22,80,443" in content, \
            f"policy.conf must contain 'ALLOWED_PORTS=22,80,443'"

    def test_policy_conf_contains_approved_ports_comment(self):
        """policy.conf must contain the approved inbound ports comment."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "# Approved inbound ports" in content, \
            f"policy.conf must contain '# Approved inbound ports' comment"

    def test_policy_conf_contains_review_date(self):
        """policy.conf must contain the last reviewed date."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "# Last reviewed: 2024-01-15" in content, \
            f"policy.conf must contain '# Last reviewed: 2024-01-15'"

    def test_policy_conf_does_not_contain_3306(self):
        """policy.conf must NOT contain port 3306."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "3306" not in content, \
            f"policy.conf must NOT contain '3306' - policy should only allow 22, 80, 443"

    def test_policy_conf_does_not_contain_6379(self):
        """policy.conf must NOT contain port 6379."""
        path = "/home/user/firewall/policy.conf"
        with open(path, "r") as f:
            content = f.read()
        assert "6379" not in content, \
            f"policy.conf must NOT contain '6379' - policy should only allow 22, 80, 443"


class TestCurrentRulesFile:
    """Test that current_rules.txt exists with the expected discrepancy."""

    def test_current_rules_exists(self):
        """The current_rules.txt file must exist."""
        path = "/home/user/firewall/current_rules.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_current_rules_is_iptables_format(self):
        """current_rules.txt must be in iptables-save format."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "*filter" in content, \
            "current_rules.txt must contain '*filter' (iptables-save format)"
        assert "COMMIT" in content, \
            "current_rules.txt must contain 'COMMIT' (iptables-save format)"

    def test_current_rules_has_input_drop_policy(self):
        """current_rules.txt must have INPUT chain with DROP policy."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert ":INPUT DROP" in content, \
            "current_rules.txt must have ':INPUT DROP' chain policy"

    def test_current_rules_has_port_22(self):
        """current_rules.txt must have rule for port 22."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 22" in content, \
            "current_rules.txt must contain rule for port 22"

    def test_current_rules_has_port_80(self):
        """current_rules.txt must have rule for port 80."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 80" in content, \
            "current_rules.txt must contain rule for port 80"

    def test_current_rules_has_port_443(self):
        """current_rules.txt must have rule for port 443."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 443" in content, \
            "current_rules.txt must contain rule for port 443"

    def test_current_rules_has_non_compliant_port_3306(self):
        """current_rules.txt must have the non-compliant port 3306 (MySQL) initially."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 3306" in content, \
            "current_rules.txt must contain non-compliant rule for port 3306 (MySQL) initially"

    def test_current_rules_has_non_compliant_port_6379(self):
        """current_rules.txt must have the non-compliant port 6379 (Redis) initially."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "--dport 6379" in content, \
            "current_rules.txt must contain non-compliant rule for port 6379 (Redis) initially"

    def test_current_rules_has_established_related_rule(self):
        """current_rules.txt must have ESTABLISHED,RELATED rule."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "ESTABLISHED,RELATED" in content, \
            "current_rules.txt must contain ESTABLISHED,RELATED rule"

    def test_current_rules_has_loopback_rule(self):
        """current_rules.txt must have loopback interface rule."""
        path = "/home/user/firewall/current_rules.txt"
        with open(path, "r") as f:
            content = f.read()
        assert "-i lo" in content, \
            "current_rules.txt must contain loopback interface rule (-i lo)"


class TestApplyRulesScript:
    """Test that apply_rules.sh exists and is executable."""

    def test_apply_rules_script_exists(self):
        """The apply_rules.sh script must exist."""
        path = "/home/user/firewall/apply_rules.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_apply_rules_script_is_executable(self):
        """The apply_rules.sh script must be executable."""
        path = "/home/user/firewall/apply_rules.sh"
        assert os.access(path, os.X_OK), f"File {path} is not executable"


class TestAuditReportDoesNotExist:
    """Test that audit_report.txt does NOT exist initially."""

    def test_audit_report_does_not_exist(self):
        """The audit_report.txt file must NOT exist initially."""
        path = "/home/user/firewall/audit_report.txt"
        assert not os.path.exists(path), \
            f"File {path} must NOT exist initially - it should be created by the student"
