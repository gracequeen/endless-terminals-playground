# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the iptables analysis task.
"""

import os
import pytest


class TestPentestDirectoryExists:
    """Verify the pentest working directory exists and is writable."""

    def test_pentest_directory_exists(self):
        """The /home/user/pentest directory must exist."""
        pentest_dir = "/home/user/pentest"
        assert os.path.exists(pentest_dir), (
            f"Directory {pentest_dir} does not exist. "
            "The pentest working directory must be present."
        )

    def test_pentest_directory_is_directory(self):
        """The /home/user/pentest path must be a directory."""
        pentest_dir = "/home/user/pentest"
        assert os.path.isdir(pentest_dir), (
            f"{pentest_dir} exists but is not a directory. "
            "It must be a directory for the task."
        )

    def test_pentest_directory_is_writable(self):
        """The /home/user/pentest directory must be writable."""
        pentest_dir = "/home/user/pentest"
        assert os.access(pentest_dir, os.W_OK), (
            f"Directory {pentest_dir} is not writable. "
            "The student needs write access to create finding.txt."
        )


class TestIptablesRulesetFile:
    """Verify the iptables ruleset export file exists with correct content."""

    def test_iptables_file_exists(self):
        """The target_iptables.txt file must exist."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        assert os.path.exists(iptables_file), (
            f"File {iptables_file} does not exist. "
            "The exported iptables ruleset must be present for analysis."
        )

    def test_iptables_file_is_readable(self):
        """The target_iptables.txt file must be readable."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        assert os.access(iptables_file, os.R_OK), (
            f"File {iptables_file} is not readable. "
            "The student needs read access to analyze the ruleset."
        )

    def test_iptables_file_contains_filter_table(self):
        """The iptables file must contain the *filter table marker."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        assert "*filter" in content, (
            "The iptables ruleset file does not contain '*filter' table marker. "
            "The file should be in iptables-save format."
        )

    def test_iptables_file_contains_ssh_rule(self):
        """The iptables file must contain the SSH accept rule on port 22."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        assert "--dport 22" in content and "ACCEPT" in content, (
            "The iptables ruleset does not contain an SSH (port 22) ACCEPT rule. "
            "This rule is needed to explain why SSH works."
        )

    def test_iptables_file_contains_http_string_match_rule(self):
        """The iptables file must contain the HTTP string match rule."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        # Check for the problematic string match rule on port 80
        has_port_80_string_match = (
            "--dport 80" in content and 
            "-m string" in content and 
            '"Mozilla"' in content
        )
        assert has_port_80_string_match, (
            "The iptables ruleset does not contain the expected HTTP (port 80) "
            "string match rule with 'Mozilla'. This is the problematic rule "
            "the student needs to analyze."
        )

    def test_iptables_file_contains_https_string_match_rule(self):
        """The iptables file must contain the HTTPS string match rule."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        # Check for the problematic string match rule on port 443
        has_port_443_string_match = (
            "--dport 443" in content and 
            "-m string" in content and 
            '"Mozilla"' in content
        )
        assert has_port_443_string_match, (
            "The iptables ruleset does not contain the expected HTTPS (port 443) "
            "string match rule with 'Mozilla'. This is the problematic rule "
            "the student needs to analyze."
        )

    def test_iptables_file_contains_http_drop_rule(self):
        """The iptables file must contain the HTTP DROP fallback rule."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        # Check for DROP rule on port 80
        has_port_80_drop = "--dport 80" in content and "DROP" in content
        assert has_port_80_drop, (
            "The iptables ruleset does not contain an HTTP (port 80) DROP rule. "
            "This catch-all DROP is what causes the connection to hang."
        )

    def test_iptables_file_contains_https_drop_rule(self):
        """The iptables file must contain the HTTPS DROP fallback rule."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        # Check for DROP rule on port 443
        has_port_443_drop = "--dport 443" in content and "DROP" in content
        assert has_port_443_drop, (
            "The iptables ruleset does not contain an HTTPS (port 443) DROP rule. "
            "This catch-all DROP is what causes the connection to hang."
        )

    def test_iptables_file_contains_commit(self):
        """The iptables file must contain COMMIT (proper iptables-save format)."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        assert "COMMIT" in content, (
            "The iptables ruleset file does not contain 'COMMIT'. "
            "The file should be in proper iptables-save format."
        )

    def test_iptables_file_has_default_drop_policy(self):
        """The iptables file should have DROP as default INPUT policy."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()
        assert ":INPUT DROP" in content, (
            "The iptables ruleset does not have ':INPUT DROP' default policy. "
            "This is important context for understanding the blocking behavior."
        )


class TestFindingFileDoesNotExist:
    """Verify the finding.txt output file does not exist initially."""

    def test_finding_file_does_not_exist(self):
        """The finding.txt file must NOT exist initially."""
        finding_file = "/home/user/pentest/finding.txt"
        assert not os.path.exists(finding_file), (
            f"File {finding_file} already exists. "
            "The finding.txt file should not exist before the student creates it."
        )


class TestIptablesRuleOrder:
    """Verify the rule order in the iptables file is correct for the scenario."""

    def test_ssh_accept_before_string_match(self):
        """SSH ACCEPT rule should appear before HTTP string match rules."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            lines = f.readlines()

        ssh_accept_line = None
        http_string_match_line = None

        for i, line in enumerate(lines):
            if "--dport 22" in line and "ACCEPT" in line:
                ssh_accept_line = i
            if "--dport 80" in line and "-m string" in line and ssh_accept_line is None:
                http_string_match_line = i
                break
            if "--dport 80" in line and "-m string" in line:
                http_string_match_line = i

        assert ssh_accept_line is not None, (
            "Could not find SSH ACCEPT rule in iptables file."
        )
        assert http_string_match_line is not None, (
            "Could not find HTTP string match rule in iptables file."
        )
        assert ssh_accept_line < http_string_match_line, (
            "SSH ACCEPT rule should appear before HTTP string match rules. "
            "This ordering is crucial to explain why SSH works but HTTP doesn't."
        )

    def test_string_match_before_drop(self):
        """HTTP string match ACCEPT should appear before HTTP DROP."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            lines = f.readlines()

        http_string_match_line = None
        http_drop_line = None

        for i, line in enumerate(lines):
            if "--dport 80" in line and "-m string" in line and "ACCEPT" in line:
                http_string_match_line = i
            if "--dport 80" in line and "DROP" in line and "-m string" not in line:
                http_drop_line = i

        assert http_string_match_line is not None, (
            "Could not find HTTP string match ACCEPT rule in iptables file."
        )
        assert http_drop_line is not None, (
            "Could not find HTTP DROP rule in iptables file."
        )
        assert http_string_match_line < http_drop_line, (
            "HTTP string match ACCEPT rule should appear before HTTP DROP rule. "
            "This ordering means packets that don't match the string fall through to DROP."
        )
