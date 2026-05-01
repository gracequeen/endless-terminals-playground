# test_final_state.py
"""
Tests to validate the final state of the firewall configuration
after the student has completed the fix for 10.0.50.0/24 subnet access to the wiki.

The fix requires BOTH:
1. Removing/commenting the DROP rule for 10.0.50.0/24 in ratelimit.conf
2. Adding an ACCEPT rule for 10.0.50.0/24 to 192.168.1.80:8080 in rules.sh
"""

import os
import re
import pytest


class TestDropRuleRemoved:
    """Test that the problematic DROP rule for 10.0.50.0/24 has been removed or commented."""

    def test_ratelimit_conf_exists(self):
        """The ratelimit.conf file should still exist."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        assert os.path.isfile(path), f"File {path} does not exist - it should still exist, just with the DROP rule removed"

    def test_no_active_drop_rule_for_50_subnet(self):
        """The DROP rule for 10.0.50.0/24 must be removed or commented out."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        with open(path, 'r') as f:
            content = f.read()

        # Check each line for an uncommented DROP rule targeting 10.0.50
        lines = content.split('\n')
        active_drop_rules = []
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            # Check if this is a DROP rule for 10.0.50
            if '10.0.50' in line and 'DROP' in line.upper():
                active_drop_rules.append(f"Line {line_num}: {line}")

        assert len(active_drop_rules) == 0, \
            f"Found active DROP rule(s) for 10.0.50.0/24 that should be removed or commented:\n" + \
            "\n".join(active_drop_rules)

    def test_grep_style_check_no_drop(self):
        """Verify using grep-style pattern that no active DROP for 10.0.50 exists."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        with open(path, 'r') as f:
            lines = f.readlines()

        # Pattern similar to: grep -E '10\.0\.50.*DROP'
        pattern = re.compile(r'10\.0\.50.*DROP', re.IGNORECASE)

        for line in lines:
            stripped = line.strip()
            # Skip commented lines
            if stripped.startswith('#'):
                continue
            if pattern.search(line):
                pytest.fail(
                    f"Found uncommented DROP rule for 10.0.50.0/24 in ratelimit.conf: {line.strip()}\n"
                    "This rule must be removed or commented out to allow 10.0.50.0/24 traffic."
                )


class TestAcceptRuleAdded:
    """Test that an ACCEPT rule for 10.0.50.0/24 to the wiki has been added."""

    def test_rules_sh_exists(self):
        """The rules.sh file should still exist."""
        path = "/home/user/firewall/rules.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_accept_rule_for_50_subnet_exists(self):
        """An ACCEPT rule for 10.0.50.0/24 to 192.168.1.80:8080 must exist in rules.sh."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Look for an ACCEPT rule that allows 10.0.50.0/24 to reach 192.168.1.80 on port 8080
        # Pattern should match variations like:
        # iptables -A FORWARD -s 10.0.50.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT

        # Check for key components in the same line (uncommented)
        lines = content.split('\n')
        found_accept = False

        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue

            # Check if line contains all required elements for the ACCEPT rule
            has_accept = 'ACCEPT' in line
            has_50_subnet = '10.0.50' in line
            has_wiki_ip = '192.168.1.80' in line
            has_port_8080 = '8080' in line

            if has_accept and has_50_subnet and has_wiki_ip and has_port_8080:
                found_accept = True
                break

        assert found_accept, \
            "Missing ACCEPT rule for 10.0.50.0/24 to 192.168.1.80:8080 in rules.sh.\n" \
            "A rule similar to the other subnet rules must be added, e.g.:\n" \
            "iptables -A FORWARD -s 10.0.50.0/24 -d 192.168.1.80 -p tcp --dport 8080 -j ACCEPT"

    def test_grep_style_check_accept(self):
        """Verify using grep-style pattern that ACCEPT rule exists."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Pattern similar to: grep -E 'ACCEPT.*10\.0\.50.*192\.168\.1\.80.*8080'
        pattern = re.compile(r'ACCEPT.*10\.0\.50.*192\.168\.1\.80.*8080', re.IGNORECASE)

        match = pattern.search(content)
        assert match is not None, \
            "No ACCEPT rule matching pattern 'ACCEPT.*10.0.50.*192.168.1.80.*8080' found in rules.sh.\n" \
            "The 10.0.50.0/24 subnet needs an explicit ACCEPT rule to reach the wiki."


class TestOtherSubnetsPreserved:
    """Test that rules for other subnets are preserved and unchanged."""

    def test_other_subnet_accept_rules_preserved(self):
        """ACCEPT rules for 10.0.10/20/30/40/60 subnets must still exist."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        expected_subnets = ['10.0.10.0/24', '10.0.20.0/24', '10.0.30.0/24', 
                           '10.0.40.0/24', '10.0.60.0/24']

        missing_subnets = []
        for subnet in expected_subnets:
            if subnet not in content:
                missing_subnets.append(subnet)

        assert len(missing_subnets) == 0, \
            f"The following subnet rules are missing from rules.sh (should be preserved): {missing_subnets}"


class TestRateLimitPreserved:
    """Test that the rate limiting rule for 10.0.70.0/24 is preserved."""

    def test_rate_limit_70_subnet_preserved(self):
        """The rate limit rule for 10.0.70.0/24 must still exist."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        with open(path, 'r') as f:
            content = f.read()

        assert '10.0.70.0/24' in content, \
            "Rate limit rule for 10.0.70.0/24 is missing from ratelimit.conf - this should be preserved"

        # Also check it's an active rule (not commented)
        lines = content.split('\n')
        found_active = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if '10.0.70.0/24' in line:
                found_active = True
                break

        assert found_active, \
            "Rate limit rule for 10.0.70.0/24 appears to be commented out - it should remain active"


class TestLoggingConfigUnchanged:
    """Test that logging.conf is unchanged."""

    def test_logging_conf_exists(self):
        """The logging.conf file should still exist."""
        path = "/home/user/firewall/rules.d/logging.conf"
        assert os.path.isfile(path), f"File {path} does not exist - it should not be deleted"

    def test_logging_conf_has_log_rules(self):
        """The logging.conf should still have LOG rules."""
        path = "/home/user/firewall/rules.d/logging.conf"
        with open(path, 'r') as f:
            content = f.read()

        assert 'LOG' in content, \
            "logging.conf is missing LOG rules - the file should remain unchanged"


class TestFirewallStructurePreserved:
    """Test that the overall firewall structure is preserved."""

    def test_rules_sh_still_sources_rules_d(self):
        """The rules.sh should still source files from rules.d."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Check for the sourcing mechanism
        has_source_loop = 'for' in content and 'rules.d' in content and 'source' in content
        assert has_source_loop, \
            "rules.sh no longer sources files from rules.d - the for loop mechanism must be preserved"

    def test_default_forward_drop_policy_preserved(self):
        """The default FORWARD DROP policy must be preserved."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        assert 'iptables -P FORWARD DROP' in content, \
            "Default FORWARD DROP policy is missing from rules.sh - this must be preserved"

    def test_no_blanket_accept_rules_added(self):
        """No blanket ACCEPT rules should be added that bypass security."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Check that there's no rule like "iptables -A FORWARD -j ACCEPT" without conditions
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # Look for dangerous blanket accept rules
            if 'FORWARD' in line and 'ACCEPT' in line:
                # It should have source (-s) and destination (-d) restrictions
                if '-s' not in line and '-d' not in line:
                    pytest.fail(
                        f"Found potentially dangerous blanket ACCEPT rule without source/dest restrictions: {line}\n"
                        "Rules should be specific to subnets and destinations."
                    )

    def test_no_forward_drop_rules_in_rules_sh(self):
        """rules.sh should not have explicit FORWARD DROP rules (only the policy)."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Count -A FORWARD ... DROP rules (not the -P policy)
        lines = content.split('\n')
        drop_rules = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if '-A' in line and 'FORWARD' in line and 'DROP' in line:
                drop_rules.append(line)

        assert len(drop_rules) == 0, \
            f"Found explicit FORWARD DROP rules in rules.sh (should only have DROP policy):\n" + \
            "\n".join(drop_rules)


class TestBothFixesApplied:
    """Meta-test to ensure both required fixes were applied."""

    def test_complete_fix_verification(self):
        """
        Verify that BOTH fixes were applied:
        1. DROP rule removed from ratelimit.conf
        2. ACCEPT rule added to rules.sh

        Both are required because:
        - Without removing DROP: traffic is blocked before reaching ACCEPT rules
        - Without adding ACCEPT: default FORWARD DROP policy blocks traffic
        """
        # Check DROP rule removed
        ratelimit_path = "/home/user/firewall/rules.d/ratelimit.conf"
        with open(ratelimit_path, 'r') as f:
            ratelimit_content = f.read()

        drop_removed = True
        for line in ratelimit_content.split('\n'):
            if line.strip().startswith('#'):
                continue
            if '10.0.50' in line and 'DROP' in line.upper():
                drop_removed = False
                break

        # Check ACCEPT rule added
        rules_path = "/home/user/firewall/rules.sh"
        with open(rules_path, 'r') as f:
            rules_content = f.read()

        accept_pattern = re.compile(r'ACCEPT.*10\.0\.50.*192\.168\.1\.80.*8080', re.IGNORECASE)
        accept_added = accept_pattern.search(rules_content) is not None

        # Both must be true
        if not drop_removed and not accept_added:
            pytest.fail(
                "INCOMPLETE FIX: Neither fix was applied!\n"
                "1. The DROP rule for 10.0.50.0/24 in ratelimit.conf must be removed/commented\n"
                "2. An ACCEPT rule for 10.0.50.0/24 to 192.168.1.80:8080 must be added to rules.sh"
            )
        elif not drop_removed:
            pytest.fail(
                "INCOMPLETE FIX: DROP rule still active!\n"
                "The DROP rule for 10.0.50.0/24 in ratelimit.conf is still blocking traffic.\n"
                "This rule is sourced BEFORE the ACCEPT rules, so it takes precedence."
            )
        elif not accept_added:
            pytest.fail(
                "INCOMPLETE FIX: ACCEPT rule not added!\n"
                "Even with the DROP rule removed, there's no ACCEPT rule for 10.0.50.0/24.\n"
                "Due to the default 'iptables -P FORWARD DROP' policy, traffic would still be blocked."
            )
