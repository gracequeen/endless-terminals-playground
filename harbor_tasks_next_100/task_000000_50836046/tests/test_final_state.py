# test_final_state.py
"""
Tests to validate the final state after the firewall configuration task is completed.
Verifies that the rule ordering bug has been fixed and all invariants are maintained.
"""

import os
import subprocess
import pytest
import re

FIREWALL_DIR = "/home/user/firewall"
RULES_CONF = os.path.join(FIREWALL_DIR, "rules.conf")
APPLY_SH = os.path.join(FIREWALL_DIR, "apply.sh")
APPLIED_LOG = os.path.join(FIREWALL_DIR, "applied.log")


class TestApplyShExecution:
    """Test that apply.sh executes successfully."""

    def test_apply_sh_exists_and_executable(self):
        """apply.sh must still exist and be executable."""
        assert os.path.isfile(APPLY_SH), (
            f"File {APPLY_SH} does not exist. "
            "The apply script must not be deleted."
        )
        assert os.access(APPLY_SH, os.X_OK), (
            f"File {APPLY_SH} is not executable."
        )

    def test_apply_sh_exits_zero(self):
        """Running ./apply.sh must exit with code 0."""
        result = subprocess.run(
            ["./apply.sh"],
            cwd=FIREWALL_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"apply.sh exited with code {result.returncode}. "
            f"Expected exit code 0.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_applied_log_created(self):
        """applied.log must be created after running apply.sh."""
        # Run apply.sh first to ensure applied.log is generated
        subprocess.run(
            ["./apply.sh"],
            cwd=FIREWALL_DIR,
            capture_output=True,
            text=True
        )
        assert os.path.isfile(APPLIED_LOG), (
            f"File {APPLIED_LOG} does not exist after running apply.sh. "
            "The script should generate this file showing the applied rules."
        )


class TestRuleOrderingInAppliedLog:
    """Test that applied.log shows correct rule ordering."""

    @pytest.fixture(autouse=True)
    def run_apply_sh(self):
        """Run apply.sh before each test to ensure applied.log is current."""
        subprocess.run(
            ["./apply.sh"],
            cwd=FIREWALL_DIR,
            capture_output=True,
            text=True
        )

    def test_monitoring_allow_rule_in_applied_log(self):
        """applied.log must contain the monitoring allow rule."""
        with open(APPLIED_LOG, 'r') as f:
            content = f.read()

        # Check for the monitoring rule - should have 10.80.4.0/24, port 9100, and ACCEPT
        has_monitoring_rule = (
            "10.80.4.0/24" in content and 
            "9100" in content and 
            "ACCEPT" in content.upper()
        )
        assert has_monitoring_rule, (
            "applied.log must contain a rule allowing 10.80.4.0/24 on port 9100 with ACCEPT action. "
            "The monitoring subnet must be explicitly allowed."
        )

    def test_deny_rule_in_applied_log(self):
        """applied.log must contain the deny rule for 10.80.0.0/16."""
        with open(APPLIED_LOG, 'r') as f:
            content = f.read()

        has_deny_rule = (
            "10.80.0.0/16" in content and 
            "DROP" in content.upper()
        )
        assert has_deny_rule, (
            "applied.log must contain a rule dropping traffic from 10.80.0.0/16. "
            "The broader deny rule must still exist to block other bad traffic."
        )

    def test_monitoring_allow_before_deny_in_applied_log(self):
        """The monitoring allow rule must appear BEFORE the deny rule in applied.log."""
        with open(APPLIED_LOG, 'r') as f:
            lines = f.readlines()

        monitoring_allow_line = None
        deny_line = None

        for i, line in enumerate(lines):
            line_upper = line.upper()
            # Find the monitoring allow rule (10.80.4.0/24, 9100, ACCEPT)
            if "10.80.4.0/24" in line and "9100" in line and "ACCEPT" in line_upper:
                if monitoring_allow_line is None:
                    monitoring_allow_line = i
            # Find the deny rule (10.80.0.0/16, DROP)
            if "10.80.0.0/16" in line and "DROP" in line_upper:
                if deny_line is None:
                    deny_line = i

        assert monitoring_allow_line is not None, (
            "Could not find the monitoring allow rule (10.80.4.0/24, port 9100, ACCEPT) in applied.log. "
            "The monitoring subnet must be explicitly allowed."
        )
        assert deny_line is not None, (
            "Could not find the deny rule (10.80.0.0/16, DROP) in applied.log. "
            "The broader deny rule must still exist."
        )
        assert monitoring_allow_line < deny_line, (
            f"Rule ordering is still incorrect! "
            f"The monitoring allow rule (line {monitoring_allow_line + 1}) must appear BEFORE "
            f"the deny rule (line {deny_line + 1}) in applied.log. "
            f"Currently the deny rule would still match first and block monitoring traffic."
        )


class TestRulesConfContent:
    """Test that rules.conf maintains required rules and invariants."""

    def test_rules_conf_exists(self):
        """rules.conf must still exist."""
        assert os.path.isfile(RULES_CONF), (
            f"File {RULES_CONF} does not exist. "
            "The rules configuration file must not be deleted."
        )

    def test_monitoring_allow_rule_in_rules_conf(self):
        """rules.conf must still contain the monitoring allow rule."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()

        # Check for monitoring rule - allow tcp 9100 from 10.80.4.0/24
        has_rule = (
            "10.80.4.0/24" in content and 
            "9100" in content and 
            "allow" in content.lower()
        )
        assert has_rule, (
            "rules.conf must contain an allow rule for 10.80.4.0/24 on port 9100. "
            "The monitoring subnet rule must not be deleted."
        )

    def test_deny_rule_in_rules_conf(self):
        """rules.conf must still contain the deny rule for 10.80.0.0/16."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()

        assert "10.80.0.0/16" in content, (
            "rules.conf must still contain a reference to 10.80.0.0/16. "
            "The broader deny rule must not be deleted - it blocks other bad traffic."
        )
        assert "deny" in content.lower(), (
            "rules.conf must still contain a deny rule. "
            "The security policy requires blocking the bad subnet."
        )

    def test_default_drop_policy_exists(self):
        """rules.conf must maintain the default drop policy."""
        with open(RULES_CONF, 'r') as f:
            content = f.read().lower()

        assert "default_input" in content and "drop" in content, (
            "rules.conf must maintain the 'default_input: drop' policy. "
            "The default drop policy is required for security."
        )

    def test_ssh_access_allowed(self):
        """rules.conf must still allow SSH access on port 22."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()

        has_ssh = "22" in content and "allow" in content.lower()
        assert has_ssh, (
            "rules.conf must contain an allow rule for port 22 (SSH). "
            "SSH access must remain functional."
        )

    def test_web_traffic_port_80_allowed(self):
        """rules.conf must still allow web traffic on port 80."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()

        # Check for port 80 allow rule
        has_http = "80" in content and "allow" in content.lower()
        assert has_http, (
            "rules.conf must contain an allow rule for port 80 (HTTP). "
            "Web traffic must remain functional."
        )

    def test_web_traffic_port_443_allowed(self):
        """rules.conf must still allow web traffic on port 443."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()

        # Check for port 443 allow rule
        has_https = "443" in content and "allow" in content.lower()
        assert has_https, (
            "rules.conf must contain an allow rule for port 443 (HTTPS). "
            "HTTPS traffic must remain functional."
        )

    def test_monitoring_rule_before_deny_in_rules_conf(self):
        """In rules.conf, the monitoring allow rule must appear before the broad deny rule."""
        with open(RULES_CONF, 'r') as f:
            lines = f.readlines()

        monitoring_line = None
        deny_line = None

        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Find monitoring allow rule
            if "10.80.4.0/24" in line and "9100" in line and "allow" in line_lower:
                if monitoring_line is None:
                    monitoring_line = i
            # Find the broad deny rule
            if "10.80.0.0/16" in line and "deny" in line_lower:
                if deny_line is None:
                    deny_line = i

        assert monitoring_line is not None, (
            "Could not find the monitoring allow rule in rules.conf. "
            "Expected a rule like 'allow in tcp 9100 from 10.80.4.0/24'."
        )
        assert deny_line is not None, (
            "Could not find the deny rule for 10.80.0.0/16 in rules.conf. "
            "This rule must still exist to block other bad traffic."
        )
        assert monitoring_line < deny_line, (
            f"Rule ordering in rules.conf is incorrect! "
            f"The monitoring allow rule (line {monitoring_line + 1}) must appear BEFORE "
            f"the deny rule for 10.80.0.0/16 (line {deny_line + 1}). "
            f"This ensures the more specific allow rule is matched first."
        )


class TestApplyShNotModified:
    """Test that apply.sh was not modified (invariant)."""

    def test_apply_sh_still_references_rules_conf(self):
        """apply.sh must still reference rules.conf."""
        with open(APPLY_SH, 'r') as f:
            content = f.read()
        assert "rules.conf" in content, (
            "apply.sh must still reference rules.conf. "
            "The script should not have been modified."
        )

    def test_apply_sh_is_bash_script(self):
        """apply.sh must still be a bash script."""
        with open(APPLY_SH, 'r') as f:
            first_line = f.readline()
        assert "bash" in first_line or "sh" in first_line, (
            f"apply.sh must have a bash/sh shebang. Got: {first_line.strip()}. "
            "The script should not have been modified."
        )
