# test_initial_state.py
"""
Tests to validate the initial state of the system before the student
performs the iptables rules.v4 modification task.
"""

import os
import pytest


class TestIptablesRulesFileExists:
    """Test that the iptables rules file exists and is accessible."""

    def test_iptables_directory_exists(self):
        """Verify /etc/iptables directory exists."""
        assert os.path.isdir("/etc/iptables"), \
            "Directory /etc/iptables does not exist"

    def test_rules_v4_file_exists(self):
        """Verify /etc/iptables/rules.v4 file exists."""
        assert os.path.isfile("/etc/iptables/rules.v4"), \
            "File /etc/iptables/rules.v4 does not exist"

    def test_rules_v4_is_readable(self):
        """Verify /etc/iptables/rules.v4 is readable."""
        assert os.access("/etc/iptables/rules.v4", os.R_OK), \
            "File /etc/iptables/rules.v4 is not readable"

    def test_rules_v4_is_writable(self):
        """Verify /etc/iptables/rules.v4 is writable by the agent user."""
        assert os.access("/etc/iptables/rules.v4", os.W_OK), \
            "File /etc/iptables/rules.v4 is not writable"


class TestIptablesRulesContent:
    """Test that the iptables rules file has the expected initial content."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.v4 file content."""
        with open("/etc/iptables/rules.v4", "r") as f:
            return f.read()

    @pytest.fixture
    def rules_lines(self, rules_content):
        """Get rules as list of lines."""
        return rules_content.strip().split('\n')

    def test_file_starts_with_filter_table(self, rules_content):
        """Verify file starts with *filter."""
        assert rules_content.strip().startswith("*filter"), \
            "File /etc/iptables/rules.v4 must start with '*filter'"

    def test_file_ends_with_commit(self, rules_content):
        """Verify file ends with COMMIT."""
        assert rules_content.strip().endswith("COMMIT"), \
            "File /etc/iptables/rules.v4 must end with 'COMMIT'"

    def test_input_chain_policy_drop(self, rules_content):
        """Verify INPUT chain has DROP policy."""
        assert ":INPUT DROP" in rules_content, \
            "INPUT chain must have DROP policy (:INPUT DROP)"

    def test_forward_chain_policy_drop(self, rules_content):
        """Verify FORWARD chain has DROP policy."""
        assert ":FORWARD DROP" in rules_content, \
            "FORWARD chain must have DROP policy (:FORWARD DROP)"

    def test_output_chain_policy_accept(self, rules_content):
        """Verify OUTPUT chain has ACCEPT policy."""
        assert ":OUTPUT ACCEPT" in rules_content, \
            "OUTPUT chain must have ACCEPT policy (:OUTPUT ACCEPT)"

    def test_loopback_rule_exists(self, rules_content):
        """Verify loopback interface rule exists."""
        assert "-A INPUT -i lo -j ACCEPT" in rules_content, \
            "Loopback rule (-A INPUT -i lo -j ACCEPT) must exist"

    def test_established_related_rule_exists(self, rules_content):
        """Verify ESTABLISHED,RELATED rule exists."""
        assert "-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT" in rules_content, \
            "ESTABLISHED,RELATED rule must exist"

    def test_ssh_port_22_rule_exists(self, rules_content):
        """Verify SSH port 22 rule exists."""
        assert "-A INPUT -p tcp --dport 22 -j ACCEPT" in rules_content, \
            "SSH rule (-A INPUT -p tcp --dport 22 -j ACCEPT) must exist"

    def test_https_port_443_rule_exists(self, rules_content):
        """Verify HTTPS port 443 rule exists."""
        assert "-A INPUT -p tcp --dport 443 -j ACCEPT" in rules_content, \
            "HTTPS rule (-A INPUT -p tcp --dport 443 -j ACCEPT) must exist"

    def test_port_8080_rule_does_not_exist(self, rules_content):
        """Verify port 8080 rule does NOT exist yet (student needs to add it)."""
        assert "--dport 8080" not in rules_content, \
            "Port 8080 rule should NOT exist in initial state - student needs to add it"


class TestIptablesPersistentInstalled:
    """Test that iptables-persistent package is installed."""

    def test_iptables_persistent_installed(self):
        """Verify iptables-persistent is installed by checking for its files."""
        # Check for the existence of iptables-persistent related paths
        # The package creates the /etc/iptables directory and provides iptables-restore
        persistent_indicators = [
            "/etc/iptables",
            "/usr/sbin/iptables-restore"
        ]

        found = False
        for path in persistent_indicators:
            if os.path.exists(path):
                found = True
                break

        assert found, \
            "iptables-persistent does not appear to be installed (missing /etc/iptables or iptables-restore)"
