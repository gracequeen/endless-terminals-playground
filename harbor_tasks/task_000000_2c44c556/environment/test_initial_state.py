# test_initial_state.py
"""
Tests to validate the initial state of the firewall configuration before the student fixes it.
This verifies the buggy state exists as described in the task.
"""

import os
import stat
import subprocess
import pytest


FIREWALL_DIR = "/home/user/firewall"
RULES_SCRIPT = "/home/user/firewall/rules.sh"
TEST_SCRIPT = "/home/user/firewall/test.sh"


class TestFirewallDirectoryExists:
    """Test that the firewall directory exists and is accessible."""

    def test_firewall_directory_exists(self):
        """The /home/user/firewall directory must exist."""
        assert os.path.isdir(FIREWALL_DIR), (
            f"Directory {FIREWALL_DIR} does not exist. "
            "The firewall configuration directory is required for this task."
        )

    def test_firewall_directory_is_writable(self):
        """The /home/user/firewall directory must be writable."""
        assert os.access(FIREWALL_DIR, os.W_OK), (
            f"Directory {FIREWALL_DIR} is not writable. "
            "The student needs write access to modify the firewall rules."
        )


class TestRulesScriptExists:
    """Test that the rules.sh script exists with proper configuration."""

    def test_rules_script_exists(self):
        """The rules.sh script must exist."""
        assert os.path.isfile(RULES_SCRIPT), (
            f"File {RULES_SCRIPT} does not exist. "
            "The iptables rules script is required for this task."
        )

    def test_rules_script_is_executable(self):
        """The rules.sh script must be executable."""
        assert os.access(RULES_SCRIPT, os.X_OK), (
            f"File {RULES_SCRIPT} is not executable. "
            "The script must be executable to apply firewall rules."
        )

    def test_rules_script_is_readable(self):
        """The rules.sh script must be readable."""
        assert os.access(RULES_SCRIPT, os.R_OK), (
            f"File {RULES_SCRIPT} is not readable. "
            "The student needs to read the script to diagnose the issue."
        )


class TestRulesScriptContent:
    """Test that the rules.sh script contains the expected buggy configuration."""

    @pytest.fixture
    def rules_content(self):
        """Read the rules.sh content."""
        with open(RULES_SCRIPT, 'r') as f:
            return f.read()

    def test_script_has_shebang(self, rules_content):
        """The script should have a bash shebang."""
        assert rules_content.startswith("#!/bin/bash") or "#!/bin/bash" in rules_content.split('\n')[0], (
            "rules.sh should start with #!/bin/bash shebang"
        )

    def test_script_flushes_rules(self, rules_content):
        """The script should flush existing rules."""
        assert "iptables -F" in rules_content, (
            "rules.sh should contain 'iptables -F' to flush existing rules"
        )

    def test_script_has_default_forward_drop_policy(self, rules_content):
        """The script should set default FORWARD policy to DROP."""
        assert "iptables -P FORWARD DROP" in rules_content, (
            "rules.sh should contain 'iptables -P FORWARD DROP' for default policy"
        )

    def test_script_has_ssh_rule(self, rules_content):
        """The script should have SSH access rule."""
        assert "--dport 22" in rules_content and "INPUT" in rules_content, (
            "rules.sh should contain SSH access rule on port 22 in INPUT chain"
        )

    def test_script_has_nat_masquerade(self, rules_content):
        """The script should have NAT/MASQUERADE rule."""
        assert "MASQUERADE" in rules_content and "10.200.0.0/16" in rules_content, (
            "rules.sh should contain MASQUERADE rule for 10.200.0.0/16 subnet"
        )

    def test_script_has_wrong_input_rule(self, rules_content):
        """The script should have the buggy INPUT rule for port 5000 (wrong chain)."""
        # Check for the INPUT rule that should be in FORWARD
        assert "INPUT" in rules_content and "10.200.0.0/16" in rules_content and "5000" in rules_content, (
            "rules.sh should contain the buggy INPUT rule for 10.200.0.0/16 on port 5000. "
            "This is the rule in the wrong chain that the student needs to fix."
        )

    def test_script_has_forward_drop_for_inference_to_registry(self, rules_content):
        """The script should have the DROP rule in FORWARD chain blocking inference->registry traffic."""
        # Check for DROP rule in FORWARD chain for the subnet pair
        lines = rules_content.split('\n')
        has_forward_drop = False
        for line in lines:
            if "FORWARD" in line and "10.200.0.0/16" in line and "10.100.0.0/16" in line and "DROP" in line:
                has_forward_drop = True
                break

        assert has_forward_drop, (
            "rules.sh should contain a DROP rule in FORWARD chain for traffic from "
            "10.200.0.0/16 to 10.100.0.0/16. This is the blocking rule that causes the timeout."
        )

    def test_script_has_general_forward_accept_after_drop(self, rules_content):
        """The script should have a general FORWARD ACCEPT that comes after the DROP (rule ordering bug)."""
        lines = rules_content.split('\n')
        drop_line_num = None
        accept_line_num = None

        for i, line in enumerate(lines):
            if "FORWARD" in line and "10.200.0.0/16" in line and "10.100.0.0/16" in line and "DROP" in line:
                if drop_line_num is None:
                    drop_line_num = i
            if "FORWARD" in line and "eth1" in line and "eth2" in line and "ACCEPT" in line:
                if accept_line_num is None:
                    accept_line_num = i

        assert drop_line_num is not None, (
            "Could not find the DROP rule for inference->registry traffic in FORWARD chain"
        )
        assert accept_line_num is not None, (
            "Could not find the general FORWARD ACCEPT rule for eth1->eth2 traffic"
        )
        assert drop_line_num < accept_line_num, (
            "The DROP rule should appear BEFORE the ACCEPT rule in the script (rule ordering bug). "
            f"DROP is at line {drop_line_num}, ACCEPT is at line {accept_line_num}"
        )


class TestTestScriptExists:
    """Test that the test.sh script exists and is properly configured."""

    def test_test_script_exists(self):
        """The test.sh script must exist."""
        assert os.path.isfile(TEST_SCRIPT), (
            f"File {TEST_SCRIPT} does not exist. "
            "The test script is required to verify the fix."
        )

    def test_test_script_is_executable(self):
        """The test.sh script must be executable."""
        assert os.access(TEST_SCRIPT, os.X_OK), (
            f"File {TEST_SCRIPT} is not executable. "
            "The test script must be executable to verify the fix."
        )

    def test_test_script_is_readable(self):
        """The test.sh script must be readable."""
        assert os.access(TEST_SCRIPT, os.R_OK), (
            f"File {TEST_SCRIPT} is not readable."
        )


class TestTestScriptContent:
    """Test that the test.sh script has the expected validation logic."""

    @pytest.fixture
    def test_content(self):
        """Read the test.sh content."""
        with open(TEST_SCRIPT, 'r') as f:
            return f.read()

    def test_test_script_checks_forward_chain(self, test_content):
        """The test script should check the FORWARD chain."""
        assert "FORWARD" in test_content, (
            "test.sh should check the FORWARD chain for traffic validation"
        )

    def test_test_script_checks_relevant_subnets(self, test_content):
        """The test script should check for the relevant subnets."""
        assert "10.200.0.0/16" in test_content or "10.200.0" in test_content, (
            "test.sh should reference the inference subnet 10.200.0.0/16"
        )
        assert "10.100.0" in test_content, (
            "test.sh should reference the registry subnet 10.100.0.0/16"
        )


class TestIptablesAvailable:
    """Test that iptables command is available."""

    def test_iptables_command_exists(self):
        """The iptables command must be available."""
        result = subprocess.run(
            ["which", "iptables"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "iptables command is not available. "
            "iptables is required to apply and test firewall rules."
        )


class TestInitialBuggyState:
    """Test that the initial state is buggy as expected."""

    def test_input_rule_exists_for_5000(self):
        """Verify the buggy INPUT rule exists for port 5000."""
        with open(RULES_SCRIPT, 'r') as f:
            content = f.read()

        # Look for INPUT rule with 10.200.0.0/16 and port 5000
        lines = content.split('\n')
        input_rule_found = False
        for line in lines:
            if "INPUT" in line and "10.200.0.0/16" in line and "5000" in line and "ACCEPT" in line:
                input_rule_found = True
                break

        assert input_rule_found, (
            "The buggy INPUT rule for 10.200.0.0/16 on port 5000 should exist. "
            "This is the rule that the user added to the wrong chain."
        )

    def test_no_correct_forward_rule_for_specific_traffic(self):
        """Verify there's no correct FORWARD ACCEPT rule for the specific traffic before DROP."""
        with open(RULES_SCRIPT, 'r') as f:
            content = f.read()

        lines = content.split('\n')

        # Find positions of relevant rules
        specific_accept_before_drop = False
        drop_line_num = None

        for i, line in enumerate(lines):
            # Check for specific ACCEPT rule for 10.200.0.0/16 -> 10.100.0.0/16 with port 5000
            if ("FORWARD" in line and "10.200.0.0/16" in line and 
                "10.100.0.0/16" in line and "5000" in line and "ACCEPT" in line):
                if drop_line_num is None:
                    specific_accept_before_drop = True

            # Track where the DROP rule is
            if "FORWARD" in line and "10.200.0.0/16" in line and "10.100.0.0/16" in line and "DROP" in line:
                if drop_line_num is None:
                    drop_line_num = i

        assert not specific_accept_before_drop, (
            "There should NOT be a correct FORWARD ACCEPT rule for the specific traffic "
            "before the DROP rule. The initial state should be buggy."
        )
