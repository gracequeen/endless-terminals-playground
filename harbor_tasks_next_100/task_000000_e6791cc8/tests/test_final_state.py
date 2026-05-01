# test_final_state.py
"""
Tests to validate the final state of the system after the student
has completed the iptables rules.v4 modification task.
"""

import os
import re
import pytest


class TestIptablesRulesFileExists:
    """Test that the iptables rules file still exists and is accessible."""

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


class TestChainPoliciesPreserved:
    """Test that chain policies remain unchanged."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.v4 file content."""
        with open("/etc/iptables/rules.v4", "r") as f:
            return f.read()

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
            "INPUT chain must have DROP policy (:INPUT DROP) - policy was changed or removed"

    def test_forward_chain_policy_drop(self, rules_content):
        """Verify FORWARD chain has DROP policy."""
        assert ":FORWARD DROP" in rules_content, \
            "FORWARD chain must have DROP policy (:FORWARD DROP) - policy was changed or removed"

    def test_output_chain_policy_accept(self, rules_content):
        """Verify OUTPUT chain has ACCEPT policy."""
        assert ":OUTPUT ACCEPT" in rules_content, \
            "OUTPUT chain must have ACCEPT policy (:OUTPUT ACCEPT) - policy was changed or removed"


class TestExistingRulesPreserved:
    """Test that existing rules are preserved."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.v4 file content."""
        with open("/etc/iptables/rules.v4", "r") as f:
            return f.read()

    def test_loopback_rule_exists(self, rules_content):
        """Verify loopback interface rule still exists."""
        assert "-A INPUT -i lo -j ACCEPT" in rules_content, \
            "Loopback rule (-A INPUT -i lo -j ACCEPT) was removed or modified - must be preserved"

    def test_established_related_rule_exists(self, rules_content):
        """Verify ESTABLISHED,RELATED rule still exists."""
        assert "-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT" in rules_content, \
            "ESTABLISHED,RELATED rule was removed or modified - must be preserved"

    def test_ssh_port_22_rule_exists(self, rules_content):
        """Verify SSH port 22 rule still exists using grep-style pattern."""
        # Pattern: -A INPUT ... --dport 22 ... ACCEPT
        pattern = r'^-A INPUT.*--dport 22.*ACCEPT'
        match = re.search(pattern, rules_content, re.MULTILINE)
        assert match is not None, \
            "SSH rule for port 22 was removed or modified - must be preserved"

    def test_https_port_443_rule_exists(self, rules_content):
        """Verify HTTPS port 443 rule still exists using grep-style pattern."""
        # Pattern: -A INPUT ... --dport 443 ... ACCEPT
        pattern = r'^-A INPUT.*--dport 443.*ACCEPT'
        match = re.search(pattern, rules_content, re.MULTILINE)
        assert match is not None, \
            "HTTPS rule for port 443 was removed or modified - must be preserved"


class TestPort8080RuleAdded:
    """Test that the new port 8080 rule was added correctly."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.v4 file content."""
        with open("/etc/iptables/rules.v4", "r") as f:
            return f.read()

    @pytest.fixture
    def rules_lines(self, rules_content):
        """Get rules as list of lines."""
        return rules_content.strip().split('\n')

    def test_port_8080_rule_exists(self, rules_content):
        """Verify port 8080 ACCEPT rule exists using grep-style pattern."""
        # Pattern: -A INPUT ... --dport 8080 ... ACCEPT
        pattern = r'^-A INPUT.*--dport 8080.*ACCEPT'
        match = re.search(pattern, rules_content, re.MULTILINE)
        assert match is not None, \
            "Port 8080 rule not found. Expected a line matching: -A INPUT -p tcp --dport 8080 -j ACCEPT"

    def test_port_8080_rule_is_tcp(self, rules_content):
        """Verify port 8080 rule is for TCP protocol."""
        # Find the 8080 rule and ensure it specifies tcp
        pattern = r'^-A INPUT.*-p tcp.*--dport 8080.*ACCEPT'
        match = re.search(pattern, rules_content, re.MULTILINE)
        assert match is not None, \
            "Port 8080 rule must specify TCP protocol (-p tcp)"

    def test_port_8080_rule_before_commit(self, rules_lines):
        """Verify port 8080 rule appears before COMMIT."""
        port_8080_line_idx = None
        commit_line_idx = None

        for idx, line in enumerate(rules_lines):
            if re.match(r'^-A INPUT.*--dport 8080.*ACCEPT', line):
                port_8080_line_idx = idx
            if line.strip() == "COMMIT":
                commit_line_idx = idx

        assert port_8080_line_idx is not None, \
            "Port 8080 rule not found in file"
        assert commit_line_idx is not None, \
            "COMMIT line not found in file"
        assert port_8080_line_idx < commit_line_idx, \
            "Port 8080 rule must appear before COMMIT"


class TestRuleOrdering:
    """Test that rules are in a sensible order."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.v4 file content."""
        with open("/etc/iptables/rules.v4", "r") as f:
            return f.read()

    @pytest.fixture
    def rules_lines(self, rules_content):
        """Get rules as list of lines."""
        return rules_content.strip().split('\n')

    def test_no_drop_or_reject_before_8080(self, rules_lines):
        """Verify no DROP or REJECT rules appear before the 8080 ACCEPT rule."""
        port_8080_line_idx = None

        for idx, line in enumerate(rules_lines):
            if re.match(r'^-A INPUT.*--dport 8080.*ACCEPT', line):
                port_8080_line_idx = idx
                break

        if port_8080_line_idx is None:
            pytest.fail("Port 8080 rule not found in file")

        # Check that no explicit DROP or REJECT rules come before the 8080 rule
        for idx in range(port_8080_line_idx):
            line = rules_lines[idx]
            if re.match(r'^-A INPUT.*-j (DROP|REJECT)', line):
                pytest.fail(
                    f"Found DROP/REJECT rule before port 8080 rule at line {idx + 1}: {line}. "
                    "The 8080 rule would be ineffective."
                )


class TestFileIntegrity:
    """Test overall file integrity."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.v4 file content."""
        with open("/etc/iptables/rules.v4", "r") as f:
            return f.read()

    def test_file_is_valid_iptables_format(self, rules_content):
        """Verify file has valid iptables-save format structure."""
        lines = rules_content.strip().split('\n')

        # Must start with table declaration
        assert lines[0].strip() == "*filter", \
            "File must start with '*filter' table declaration"

        # Must end with COMMIT
        assert lines[-1].strip() == "COMMIT", \
            "File must end with 'COMMIT'"

        # Check that chain policies are defined
        has_input_policy = False
        has_forward_policy = False
        has_output_policy = False

        for line in lines:
            if line.startswith(":INPUT"):
                has_input_policy = True
            if line.startswith(":FORWARD"):
                has_forward_policy = True
            if line.startswith(":OUTPUT"):
                has_output_policy = True

        assert has_input_policy, "Missing INPUT chain policy"
        assert has_forward_policy, "Missing FORWARD chain policy"
        assert has_output_policy, "Missing OUTPUT chain policy"

    def test_no_duplicate_8080_rules(self, rules_content):
        """Verify there's only one port 8080 rule."""
        pattern = r'^-A INPUT.*--dport 8080.*ACCEPT'
        matches = re.findall(pattern, rules_content, re.MULTILINE)
        assert len(matches) == 1, \
            f"Expected exactly one port 8080 rule, found {len(matches)}"
