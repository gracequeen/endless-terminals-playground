# test_initial_state.py
"""
Tests to validate the initial state of the firewall configuration
before the student performs any fixes.
"""

import os
import pytest


class TestFirewallDirectoryStructure:
    """Test that the firewall directory structure exists."""

    def test_firewall_directory_exists(self):
        """The /home/user/firewall/ directory must exist."""
        path = "/home/user/firewall"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_firewall_directory_writable(self):
        """The /home/user/firewall/ directory must be writable."""
        path = "/home/user/firewall"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_rules_d_directory_exists(self):
        """The /home/user/firewall/rules.d/ directory must exist."""
        path = "/home/user/firewall/rules.d"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestMainRulesFile:
    """Test the main rules.sh file exists and has expected content."""

    def test_rules_sh_exists(self):
        """The /home/user/firewall/rules.sh file must exist."""
        path = "/home/user/firewall/rules.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_rules_sh_writable(self):
        """The /home/user/firewall/rules.sh file must be writable."""
        path = "/home/user/firewall/rules.sh"
        assert os.access(path, os.W_OK), f"File {path} is not writable"

    def test_rules_sh_is_bash_script(self):
        """The rules.sh should be a bash script."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            first_line = f.readline()
        assert '#!/bin/bash' in first_line or first_line.startswith('#!'), \
            f"File {path} does not appear to be a bash script"

    def test_rules_sh_has_default_forward_drop_policy(self):
        """The rules.sh should have default FORWARD DROP policy."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'iptables -P FORWARD DROP' in content, \
            "rules.sh is missing 'iptables -P FORWARD DROP' policy"

    def test_rules_sh_sources_rules_d(self):
        """The rules.sh should source files from rules.d directory."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'rules.d' in content and 'source' in content, \
            "rules.sh does not appear to source files from rules.d"

    def test_rules_sh_has_other_subnet_rules(self):
        """The rules.sh should have ACCEPT rules for other subnets (10, 20, 30, 40, 60)."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        expected_subnets = ['10.0.10.0/24', '10.0.20.0/24', '10.0.30.0/24', 
                           '10.0.40.0/24', '10.0.60.0/24']
        for subnet in expected_subnets:
            assert subnet in content, \
                f"rules.sh is missing expected rule for subnet {subnet}"

    def test_rules_sh_missing_50_subnet_accept(self):
        """The rules.sh should be MISSING the 10.0.50.0/24 ACCEPT rule (this is the issue)."""
        path = "/home/user/firewall/rules.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Check that there's no ACCEPT rule for 10.0.50.0/24 to the wiki
        import re
        pattern = r'ACCEPT.*10\.0\.50.*192\.168\.1\.80.*8080'
        match = re.search(pattern, content)
        assert match is None, \
            "rules.sh already contains an ACCEPT rule for 10.0.50.0/24 - initial state should be missing this"


class TestRateLimitConfig:
    """Test the ratelimit.conf file exists and has the problematic DROP rule."""

    def test_ratelimit_conf_exists(self):
        """The /home/user/firewall/rules.d/ratelimit.conf file must exist."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_ratelimit_conf_writable(self):
        """The /home/user/firewall/rules.d/ratelimit.conf file must be writable."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        assert os.access(path, os.W_OK), f"File {path} is not writable"

    def test_ratelimit_conf_has_drop_rule_for_50_subnet(self):
        """The ratelimit.conf should have the problematic DROP rule for 10.0.50.0/24."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        with open(path, 'r') as f:
            content = f.read()

        import re
        # Look for an uncommented DROP rule for 10.0.50.0/24
        lines = content.split('\n')
        found_drop = False
        for line in lines:
            # Skip commented lines
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if '10.0.50' in line and 'DROP' in line:
                found_drop = True
                break

        assert found_drop, \
            "ratelimit.conf is missing the DROP rule for 10.0.50.0/24 - this should exist in initial state"

    def test_ratelimit_conf_has_rate_limit_for_70_subnet(self):
        """The ratelimit.conf should have rate limiting for 10.0.70.0/24."""
        path = "/home/user/firewall/rules.d/ratelimit.conf"
        with open(path, 'r') as f:
            content = f.read()

        assert '10.0.70.0/24' in content, \
            "ratelimit.conf is missing rate limit rule for 10.0.70.0/24"


class TestLoggingConfig:
    """Test the logging.conf file exists."""

    def test_logging_conf_exists(self):
        """The /home/user/firewall/rules.d/logging.conf file must exist."""
        path = "/home/user/firewall/rules.d/logging.conf"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_logging_conf_has_log_rule(self):
        """The logging.conf should have logging rules."""
        path = "/home/user/firewall/rules.d/logging.conf"
        with open(path, 'r') as f:
            content = f.read()

        assert 'LOG' in content, \
            "logging.conf is missing LOG rules"


class TestChangelogFile:
    """Test the changelog.txt file exists and has expected entries."""

    def test_changelog_exists(self):
        """The /home/user/firewall/changelog.txt file must exist."""
        path = "/home/user/firewall/changelog.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_changelog_mentions_march_ratelimit(self):
        """The changelog should mention the March ratelimit addition."""
        path = "/home/user/firewall/changelog.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert 'ratelimit' in content.lower() or '2024-03' in content, \
            "changelog.txt is missing reference to March ratelimit changes"
