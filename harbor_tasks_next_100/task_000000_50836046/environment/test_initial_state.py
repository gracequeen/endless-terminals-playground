# test_initial_state.py
"""
Tests to validate the initial state of the firewall configuration task.
Verifies that the problem scenario exists as described before the student attempts to fix it.
"""

import os
import subprocess
import pytest

FIREWALL_DIR = "/home/user/firewall"
RULES_CONF = os.path.join(FIREWALL_DIR, "rules.conf")
APPLY_SH = os.path.join(FIREWALL_DIR, "apply.sh")
CONN_LOG = os.path.join(FIREWALL_DIR, "conn.log")


class TestFirewallDirectoryExists:
    """Test that the firewall directory and required files exist."""

    def test_firewall_directory_exists(self):
        """The /home/user/firewall directory must exist."""
        assert os.path.isdir(FIREWALL_DIR), (
            f"Directory {FIREWALL_DIR} does not exist. "
            "The firewall configuration directory is required for this task."
        )

    def test_rules_conf_exists(self):
        """The rules.conf file must exist."""
        assert os.path.isfile(RULES_CONF), (
            f"File {RULES_CONF} does not exist. "
            "The firewall rules configuration file is required."
        )

    def test_apply_sh_exists(self):
        """The apply.sh script must exist."""
        assert os.path.isfile(APPLY_SH), (
            f"File {APPLY_SH} does not exist. "
            "The apply script is required to apply firewall rules."
        )

    def test_apply_sh_is_executable(self):
        """The apply.sh script must be executable."""
        assert os.access(APPLY_SH, os.X_OK), (
            f"File {APPLY_SH} is not executable. "
            "The apply script must have execute permissions."
        )

    def test_conn_log_exists(self):
        """The conn.log file must exist."""
        assert os.path.isfile(CONN_LOG), (
            f"File {CONN_LOG} does not exist. "
            "The connection log file is required for debugging."
        )


class TestRulesConfContent:
    """Test that rules.conf contains the expected problematic configuration."""

    def test_rules_conf_readable(self):
        """rules.conf must be readable."""
        assert os.access(RULES_CONF, os.R_OK), (
            f"File {RULES_CONF} is not readable."
        )

    def test_rules_conf_writable(self):
        """rules.conf must be writable for the fix."""
        assert os.access(RULES_CONF, os.W_OK), (
            f"File {RULES_CONF} is not writable. "
            "The student needs to modify this file to fix the issue."
        )

    def test_default_input_drop_policy_exists(self):
        """rules.conf must have a default drop policy for input."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()
        assert "default_input: drop" in content.lower() or "default_input:drop" in content.lower(), (
            "rules.conf must contain a 'default_input: drop' policy. "
            "This is required for the firewall security model."
        )

    def test_deny_rule_for_bad_subnet_exists(self):
        """rules.conf must have a deny rule for 10.80.0.0/16."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()
        assert "deny in from 10.80.0.0/16" in content, (
            "rules.conf must contain 'deny in from 10.80.0.0/16'. "
            "This is the rule that blocks the broader subnet."
        )

    def test_monitoring_allow_rule_exists(self):
        """rules.conf must have an allow rule for monitoring subnet."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()
        assert "allow in tcp 9100 from 10.80.4.0/24" in content, (
            "rules.conf must contain 'allow in tcp 9100 from 10.80.4.0/24'. "
            "This is the monitoring access rule that should work but doesn't."
        )

    def test_ssh_allow_rule_exists(self):
        """rules.conf must have an allow rule for SSH."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()
        assert "allow in tcp 22" in content, (
            "rules.conf must contain an SSH allow rule (port 22). "
            "SSH access must remain functional."
        )

    def test_web_traffic_rules_exist(self):
        """rules.conf must have allow rules for web traffic."""
        with open(RULES_CONF, 'r') as f:
            content = f.read()
        assert "allow in tcp 80" in content, (
            "rules.conf must contain a rule allowing port 80. "
            "Web traffic must remain functional."
        )
        assert "allow in tcp 443" in content, (
            "rules.conf must contain a rule allowing port 443. "
            "HTTPS traffic must remain functional."
        )

    def test_deny_rule_appears_before_monitoring_allow(self):
        """The bug: deny rule for 10.80.0.0/16 must appear BEFORE the monitoring allow rule."""
        with open(RULES_CONF, 'r') as f:
            lines = f.readlines()

        deny_line_num = None
        allow_line_num = None

        for i, line in enumerate(lines):
            if "deny in from 10.80.0.0/16" in line:
                deny_line_num = i
            if "allow in tcp 9100 from 10.80.4.0/24" in line:
                allow_line_num = i

        assert deny_line_num is not None, (
            "Could not find 'deny in from 10.80.0.0/16' in rules.conf"
        )
        assert allow_line_num is not None, (
            "Could not find 'allow in tcp 9100 from 10.80.4.0/24' in rules.conf"
        )
        assert deny_line_num < allow_line_num, (
            f"Initial state error: The deny rule (line {deny_line_num + 1}) must appear "
            f"BEFORE the monitoring allow rule (line {allow_line_num + 1}) to demonstrate the bug. "
            "This is the rule ordering issue the student needs to fix."
        )


class TestConnLogContent:
    """Test that conn.log shows the expected failed connection."""

    def test_conn_log_shows_monitoring_ip(self):
        """conn.log must show a connection attempt from the monitoring subnet."""
        with open(CONN_LOG, 'r') as f:
            content = f.read()
        assert "10.80.4." in content, (
            "conn.log must show a connection attempt from the 10.80.4.x subnet. "
            "This demonstrates the monitoring traffic that is being blocked."
        )

    def test_conn_log_shows_port_9100(self):
        """conn.log must show a connection to port 9100."""
        with open(CONN_LOG, 'r') as f:
            content = f.read()
        assert "9100" in content, (
            "conn.log must reference port 9100. "
            "This is the Prometheus metrics port being scraped."
        )

    def test_conn_log_shows_drop_action(self):
        """conn.log must show that the connection was dropped."""
        with open(CONN_LOG, 'r') as f:
            content = f.read()
        assert "DROP" in content.upper(), (
            "conn.log must show a DROP action. "
            "This demonstrates that the monitoring traffic is being blocked."
        )

    def test_conn_log_shows_deny_rule_match(self):
        """conn.log must show that the deny rule was matched."""
        with open(CONN_LOG, 'r') as f:
            content = f.read()
        assert "10.80.0.0/16" in content, (
            "conn.log must show that the 10.80.0.0/16 deny rule was matched. "
            "This demonstrates the rule ordering bug."
        )


class TestApplyShScript:
    """Test that apply.sh is a valid bash script."""

    def test_apply_sh_is_bash_script(self):
        """apply.sh should be a bash script."""
        with open(APPLY_SH, 'r') as f:
            first_line = f.readline()
        assert "bash" in first_line or "sh" in first_line, (
            f"apply.sh should have a bash/sh shebang. Got: {first_line.strip()}"
        )

    def test_apply_sh_references_rules_conf(self):
        """apply.sh should reference rules.conf."""
        with open(APPLY_SH, 'r') as f:
            content = f.read()
        assert "rules.conf" in content, (
            "apply.sh should reference rules.conf to read the firewall rules."
        )


class TestDirectoryWritable:
    """Test that the firewall directory is writable for output files."""

    def test_firewall_directory_writable(self):
        """The firewall directory must be writable."""
        assert os.access(FIREWALL_DIR, os.W_OK), (
            f"Directory {FIREWALL_DIR} is not writable. "
            "The student needs to be able to modify files and the script needs to write applied.log."
        )
