# test_final_state.py
"""
Tests to validate the final state of the firewall configuration after the student fixes it.
This verifies that traffic from 10.200.0.0/16 can reach 10.100.0.42:5000 through the FORWARD chain.
"""

import os
import subprocess
import pytest


FIREWALL_DIR = "/home/user/firewall"
RULES_SCRIPT = "/home/user/firewall/rules.sh"
TEST_SCRIPT = "/home/user/firewall/test.sh"


class TestFirewallScriptsExist:
    """Test that the firewall scripts still exist and are accessible."""

    def test_rules_script_exists(self):
        """The rules.sh script must still exist."""
        assert os.path.isfile(RULES_SCRIPT), (
            f"File {RULES_SCRIPT} does not exist. "
            "The iptables rules script must not be deleted."
        )

    def test_rules_script_is_executable(self):
        """The rules.sh script must still be executable."""
        assert os.access(RULES_SCRIPT, os.X_OK), (
            f"File {RULES_SCRIPT} is not executable. "
            "The script must remain executable."
        )

    def test_test_script_exists(self):
        """The test.sh script must still exist."""
        assert os.path.isfile(TEST_SCRIPT), (
            f"File {TEST_SCRIPT} does not exist. "
            "The test script must not be deleted."
        )

    def test_test_script_is_executable(self):
        """The test.sh script must still be executable."""
        assert os.access(TEST_SCRIPT, os.X_OK), (
            f"File {TEST_SCRIPT} is not executable."
        )


class TestRulesScriptPreservesInvariants:
    """Test that the rules.sh script preserves required invariants."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.sh content."""
        with open(RULES_SCRIPT, 'r') as f:
            return f.read()

    def test_script_still_flushes_rules(self, rules_content):
        """The script must still flush existing rules at start."""
        assert "iptables -F" in rules_content, (
            "rules.sh must still contain 'iptables -F' to flush existing rules. "
            "The fix must be in the script itself, not a separate script that runs after."
        )

    def test_script_preserves_default_forward_drop_policy(self, rules_content):
        """The script must preserve default FORWARD policy as DROP."""
        assert "iptables -P FORWARD DROP" in rules_content, (
            "rules.sh must preserve 'iptables -P FORWARD DROP'. "
            "Don't just set the policy to ACCEPT - that's not a proper fix."
        )

    def test_script_preserves_ssh_rule(self, rules_content):
        """The script must preserve SSH access rule."""
        # Check for SSH rule - port 22 in INPUT chain
        has_ssh_rule = False
        lines = rules_content.split('\n')
        for line in lines:
            if "INPUT" in line and "22" in line and ("ACCEPT" in line or "-j ACCEPT" in line):
                has_ssh_rule = True
                break

        assert has_ssh_rule, (
            "rules.sh must preserve the SSH access rule (port 22) in INPUT chain. "
            "This rule is required for gateway management."
        )

    def test_script_preserves_nat_masquerade(self, rules_content):
        """The script must preserve NAT/MASQUERADE rule."""
        assert "MASQUERADE" in rules_content, (
            "rules.sh must preserve the MASQUERADE rule for NAT. "
            "This is required for outbound traffic from the inference subnet."
        )
        assert "10.200.0.0/16" in rules_content, (
            "rules.sh must still reference the inference subnet 10.200.0.0/16."
        )


class TestForwardChainFix:
    """Test that the FORWARD chain is properly configured to allow the traffic."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.sh content."""
        with open(RULES_SCRIPT, 'r') as f:
            return f.read()

    def test_forward_chain_has_accept_for_inference_to_registry(self, rules_content):
        """The FORWARD chain must have an ACCEPT rule for inference->registry traffic."""
        lines = rules_content.split('\n')

        # Look for a FORWARD ACCEPT rule that would allow 10.200.0.0/16 -> 10.100.0.0/16
        # This could be:
        # 1. A specific rule for the subnet pair
        # 2. A rule allowing eth1 -> eth2 traffic
        # 3. A rule allowing the specific port 5000 traffic

        has_forward_accept = False
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('#'):
                continue
            if "FORWARD" in line and "ACCEPT" in line:
                # Check if this rule would match our traffic
                # Could be subnet-based or interface-based
                if ("10.200.0.0/16" in line and "10.100.0.0/16" in line) or \
                   ("eth1" in line and "eth2" in line) or \
                   ("10.200.0.0/16" in line and "5000" in line):
                    has_forward_accept = True
                    break

        assert has_forward_accept, (
            "rules.sh must have a FORWARD chain ACCEPT rule that allows traffic from "
            "10.200.0.0/16 to 10.100.0.0/16 (or eth1 to eth2). "
            "The original INPUT rule was in the wrong chain - traffic between subnets "
            "traverses the FORWARD chain, not INPUT."
        )

    def test_accept_rule_before_drop_rule(self, rules_content):
        """Any ACCEPT rule for this traffic must appear BEFORE any DROP rule that matches."""
        lines = rules_content.split('\n')

        # Find line numbers of relevant rules
        accept_line_num = None
        drop_line_num = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith('#'):
                continue

            # Check for ACCEPT rules that would match our traffic
            if "FORWARD" in line and "ACCEPT" in line:
                if accept_line_num is None:
                    # Check if this ACCEPT would match 10.200.0.0/16 -> 10.100.0.0/16 traffic
                    if ("10.200.0.0/16" in line and "10.100.0.0/16" in line) or \
                       ("10.200.0.0/16" in line and "5000" in line) or \
                       ("eth1" in line and "eth2" in line) or \
                       ("10.200.0.0/16" in line and "-d 10.100.0" in line):
                        accept_line_num = i

            # Check for DROP rules that would match our traffic
            if "FORWARD" in line and "DROP" in line:
                if "10.200.0.0/16" in line and "10.100.0.0/16" in line:
                    if drop_line_num is None:
                        drop_line_num = i

        # If there's no DROP rule anymore, that's also acceptable
        if drop_line_num is None:
            return

        # If there's a DROP rule, there must be an ACCEPT rule before it
        assert accept_line_num is not None, (
            "There is a DROP rule for 10.200.0.0/16 -> 10.100.0.0/16 traffic but no "
            "ACCEPT rule that would match the inference->registry traffic before it."
        )

        assert accept_line_num < drop_line_num, (
            f"The ACCEPT rule (line {accept_line_num}) must appear BEFORE the DROP rule "
            f"(line {drop_line_num}) in the FORWARD chain. Rule ordering matters in iptables - "
            "the first matching rule wins."
        )


class TestInputChainNotUsedForForwardedTraffic:
    """Test that the fix uses FORWARD chain, not INPUT chain."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.sh content."""
        with open(RULES_SCRIPT, 'r') as f:
            return f.read()

    def test_forward_chain_used_not_just_input(self, rules_content):
        """The fix must use FORWARD chain, not rely solely on INPUT chain."""
        lines = rules_content.split('\n')

        # Check if there's still only an INPUT rule for the traffic
        has_input_rule_for_traffic = False
        has_forward_rule_for_traffic = False

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('#'):
                continue

            # Check for INPUT rule for 10.200.0.0/16 on port 5000
            if "INPUT" in line and "10.200.0.0/16" in line and "5000" in line and "ACCEPT" in line:
                has_input_rule_for_traffic = True

            # Check for FORWARD rule that would allow the traffic
            if "FORWARD" in line and "ACCEPT" in line:
                if ("10.200.0.0/16" in line) or ("eth1" in line and "eth2" in line):
                    has_forward_rule_for_traffic = True

        assert has_forward_rule_for_traffic, (
            "The fix must add a rule to the FORWARD chain, not the INPUT chain. "
            "Traffic between subnets (10.200.0.0/16 -> 10.100.0.0/16) traverses the "
            "FORWARD chain because the gateway is routing, not receiving the traffic."
        )


class TestFirewallScriptsExecuteSuccessfully:
    """Test that the firewall scripts execute successfully."""

    def test_rules_script_executes_without_error(self):
        """The rules.sh script must execute without errors."""
        result = subprocess.run(
            ["bash", RULES_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Allow for permission errors on iptables if not root, but script should parse
        # Check that it's at least syntactically valid
        if result.returncode != 0:
            # If it fails due to iptables permissions, that's okay for syntax check
            if "Permission denied" in result.stderr or "Operation not permitted" in result.stderr:
                pass  # Expected if not running as root
            else:
                pytest.fail(
                    f"rules.sh failed to execute: {result.stderr}\n"
                    "The script must be syntactically valid and executable."
                )

    def test_test_script_passes(self):
        """The test.sh script must pass (exit 0) after rules are applied."""
        # First apply the rules
        subprocess.run(
            ["bash", RULES_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Then run the test
        result = subprocess.run(
            ["bash", TEST_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"test.sh failed with exit code {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}\n"
            "The test script must pass, indicating that traffic from 10.200.0.0/16 "
            "to 10.100.0.42:5000 would be accepted through the FORWARD chain."
        )


class TestIptablesState:
    """Test the actual iptables state after applying rules."""

    @pytest.fixture(scope="class")
    def apply_rules(self):
        """Apply the firewall rules."""
        subprocess.run(
            ["bash", RULES_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30
        )

    def test_iptables_forward_allows_traffic(self, apply_rules):
        """Check that iptables FORWARD chain would allow the traffic."""
        # Get iptables-save output
        result = subprocess.run(
            ["iptables-save"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            # If iptables-save fails (permissions), skip this test
            pytest.skip("Cannot run iptables-save (likely permission issue)")

        rules_output = result.stdout

        # Parse the rules to check ordering
        lines = rules_output.split('\n')

        accept_line_num = None
        drop_line_num = None

        for i, line in enumerate(lines):
            # Look for FORWARD rules
            if "-A FORWARD" in line:
                if "ACCEPT" in line:
                    # Check if this would match our traffic
                    if ("10.200.0.0/16" in line) or ("-i eth1" in line and "-o eth2" in line):
                        if accept_line_num is None:
                            accept_line_num = i

                if "DROP" in line:
                    if "10.200.0.0/16" in line and "10.100.0.0/16" in line:
                        if drop_line_num is None:
                            drop_line_num = i

        # Either no DROP rule, or ACCEPT comes before DROP
        if drop_line_num is not None:
            assert accept_line_num is not None and accept_line_num < drop_line_num, (
                "In the active iptables rules, the ACCEPT rule for inference->registry "
                "traffic must appear before any DROP rule that would block it."
            )


class TestAntiShortcutGuards:
    """Tests to ensure the fix is proper and not a shortcut."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.sh content."""
        with open(RULES_SCRIPT, 'r') as f:
            return f.read()

    def test_default_policy_not_changed_to_accept(self, rules_content):
        """The default FORWARD policy must remain DROP, not changed to ACCEPT."""
        # Check that there's no "iptables -P FORWARD ACCEPT"
        assert "iptables -P FORWARD ACCEPT" not in rules_content, (
            "The default FORWARD policy must remain DROP. "
            "Changing it to ACCEPT is not a proper fix - it would allow all forwarded traffic."
        )

    def test_fix_is_in_rules_script(self):
        """The fix must be in rules.sh itself, not a separate script."""
        # This is implicitly tested by the test_test_script_passes test,
        # but let's also verify the rules.sh has the necessary content
        with open(RULES_SCRIPT, 'r') as f:
            content = f.read()

        # Must have FORWARD ACCEPT rule in the script
        has_forward_accept = False
        lines = content.split('\n')
        for line in lines:
            if "FORWARD" in line and "ACCEPT" in line and not line.strip().startswith('#'):
                has_forward_accept = True
                break

        assert has_forward_accept, (
            "The fix must be in rules.sh itself. "
            "The script must contain a FORWARD chain ACCEPT rule."
        )

    def test_script_still_has_structure(self, rules_content):
        """The script should maintain its basic structure (flush, policies, rules)."""
        # Check for basic structure elements
        assert "iptables -F" in rules_content, "Script must still flush rules"
        assert "iptables -P" in rules_content, "Script must still set policies"
        assert "iptables -A" in rules_content, "Script must still add rules"
