# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the iptables analysis task and created the finding.txt file.
"""

import os
import re
import pytest


class TestFindingFileExists:
    """Verify the finding.txt file exists and is properly created."""

    def test_finding_file_exists(self):
        """The finding.txt file must exist after task completion."""
        finding_file = "/home/user/pentest/finding.txt"
        assert os.path.exists(finding_file), (
            f"File {finding_file} does not exist. "
            "The student must create finding.txt with their analysis."
        )

    def test_finding_file_is_regular_file(self):
        """The finding.txt must be a regular file."""
        finding_file = "/home/user/pentest/finding.txt"
        assert os.path.isfile(finding_file), (
            f"{finding_file} exists but is not a regular file. "
            "It must be a regular text file."
        )

    def test_finding_file_is_not_empty(self):
        """The finding.txt file must not be empty."""
        finding_file = "/home/user/pentest/finding.txt"
        assert os.path.getsize(finding_file) > 0, (
            f"File {finding_file} is empty. "
            "The finding must contain the analysis."
        )

    def test_finding_file_is_readable(self):
        """The finding.txt file must be readable."""
        finding_file = "/home/user/pentest/finding.txt"
        assert os.access(finding_file, os.R_OK), (
            f"File {finding_file} is not readable."
        )


class TestFindingIdentifiesStringMatchRule:
    """Verify the finding identifies the problematic string match rules."""

    def test_finding_mentions_string_match(self):
        """The finding must mention string matching as the issue."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        # Check for mentions of string match/matching
        string_match_patterns = [
            'string match',
            'string-match',
            '-m string',
            'string module',
            'string filter',
            'string inspection',
            'matching.*string',
            'match.*mozilla',
            'mozilla.*match',
            '"mozilla"',
            "'mozilla'",
            'mozilla string',
        ]

        found = any(
            pattern in content or re.search(pattern, content)
            for pattern in string_match_patterns
        )

        assert found, (
            "The finding does not mention string matching. "
            "The analysis must identify the '-m string --string \"Mozilla\"' rules "
            "as the problematic configuration."
        )

    def test_finding_mentions_http_ports(self):
        """The finding must reference HTTP/HTTPS ports (80 and/or 443)."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        # Check for mentions of HTTP ports
        has_port_80 = '80' in content or 'http' in content
        has_port_443 = '443' in content or 'https' in content

        assert has_port_80 or has_port_443, (
            "The finding does not mention HTTP (port 80) or HTTPS (port 443). "
            "The analysis must identify which ports are affected."
        )


class TestFindingExplainsTimingLayerIssue:
    """
    Verify the finding explains WHY string matching fails - the timing/layer issue.
    This is the critical insight: string match on SYN packets fails because
    HTTP headers aren't present until after TCP handshake.
    """

    def test_finding_explains_syn_or_handshake_timing(self):
        """
        The finding must explain the timing/layer issue - that string matching
        fails on SYN packets because HTTP headers come after TCP handshake.
        """
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read()

        # Pattern from the anti-shortcut guard - must match at least one concept
        # that explains the timing/layering insight
        pattern = re.compile(
            r'(SYN|handshake|three.?way|connection establish|'
            r'TCP.*(before|prior)|layer.?[47]|L[47]|'
            r'payload.*(after|not.*present)|header.*(after|not.*present)|'
            r'initial.*packet|first.*packet|'
            r'tcp.*connect|connection.*setup|'
            r'no.*payload|empty.*payload|'
            r'before.*http|prior.*http|'
            r'packet.*no.*data|data.*after|'
            r'application.*layer|transport.*layer|'
            r'http.*header.*not|http.*request.*after|'
            r'user.?agent.*after|user.?agent.*not.*present)',
            re.IGNORECASE
        )

        match = pattern.search(content)

        assert match is not None, (
            "The finding does not explain the timing/layer issue. "
            "The analysis must explain WHY string matching fails - "
            "that the SYN packet (initial TCP connection) contains no HTTP headers, "
            "because HTTP headers only appear after the TCP handshake completes. "
            "Expected concepts: SYN, handshake, three-way, connection establishment, "
            "layer 4/7, payload timing, headers not present in initial packet, etc."
        )


class TestFindingExplainsSSHWorks:
    """Verify the finding explains why SSH works (unconditional ACCEPT)."""

    def test_finding_mentions_ssh(self):
        """The finding must mention SSH."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        assert 'ssh' in content or '22' in content, (
            "The finding does not mention SSH or port 22. "
            "The analysis must explain why SSH works."
        )

    def test_finding_explains_ssh_unconditional(self):
        """The finding must explain SSH works due to unconditional accept."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        # Check for explanation that SSH has no string match requirement
        ssh_explanation_patterns = [
            'unconditional',
            'no string',
            'without string',
            'no.*match',
            'not.*string',
            'simple accept',
            'direct.*accept',
            'just.*accept',
            'only.*accept',
            'accept.*without',
            'no.*filter',
            'no.*restriction',
            'allow.*all',
            'accept.*any',
            'before.*string',
            'doesn\'t.*require',
            'does not.*require',
            'no.*mozilla',
            'without.*mozilla',
        ]

        found = any(pattern in content for pattern in ssh_explanation_patterns) or \
                any(re.search(pattern, content) for pattern in ssh_explanation_patterns)

        # Also accept if they mention SSH and ACCEPT in proximity
        ssh_accept_pattern = re.search(r'(ssh|port.?22).{0,100}accept', content) or \
                            re.search(r'accept.{0,100}(ssh|port.?22)', content)

        assert found or ssh_accept_pattern, (
            "The finding does not adequately explain why SSH works. "
            "The analysis should note that SSH (port 22) has an unconditional "
            "ACCEPT rule without any string matching requirement."
        )


class TestFindingIncludesRecommendation:
    """Verify the finding includes a recommendation for fixing the issue."""

    def test_finding_has_recommendation(self):
        """The finding should include a recommendation or suggestion."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        recommendation_patterns = [
            'recommend',
            'suggestion',
            'should',
            'could',
            'fix',
            'solution',
            'resolve',
            'change',
            'modify',
            'remove',
            'instead',
            'alternative',
            'waf',
            'web application firewall',
            'layer 7',
            'l7',
            'proxy',
            'established',
            'conntrack',
        ]

        found = any(pattern in content for pattern in recommendation_patterns)

        assert found, (
            "The finding does not appear to include a recommendation. "
            "The analysis should suggest how to fix the issue "
            "(e.g., remove string match, use WAF, inspect only ESTABLISHED connections)."
        )


class TestIptablesFileUnchanged:
    """Verify the original iptables file was not modified."""

    def test_iptables_file_still_exists(self):
        """The target_iptables.txt file must still exist."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        assert os.path.exists(iptables_file), (
            f"File {iptables_file} no longer exists. "
            "The original iptables ruleset should not be deleted."
        )

    def test_iptables_file_contains_original_content(self):
        """The target_iptables.txt must contain the original ruleset."""
        iptables_file = "/home/user/pentest/target_iptables.txt"
        with open(iptables_file, 'r') as f:
            content = f.read()

        # Check for key elements that should be in the original file
        required_elements = [
            '*filter',
            ':INPUT DROP',
            '--dport 22',
            '--dport 80',
            '--dport 443',
            '-m string',
            '"Mozilla"',
            'COMMIT',
        ]

        for element in required_elements:
            assert element in content, (
                f"The iptables file is missing '{element}'. "
                "The original target_iptables.txt should not be modified."
            )


class TestFindingQuality:
    """Additional quality checks for the finding content."""

    def test_finding_has_minimum_length(self):
        """The finding should have substantive content (not just a few words)."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read()

        # Remove extra whitespace and count words
        words = content.split()
        word_count = len(words)

        assert word_count >= 30, (
            f"The finding only contains {word_count} words. "
            "A proper analysis should contain at least 30 words explaining "
            "the issue, why SSH works, and a recommendation."
        )

    def test_finding_mentions_drop(self):
        """The finding should mention that traffic is being dropped."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        drop_patterns = ['drop', 'block', 'reject', 'deny', 'filter', 'hang']
        found = any(pattern in content for pattern in drop_patterns)

        assert found, (
            "The finding does not mention that traffic is being dropped/blocked. "
            "The analysis should explain that HTTP traffic hits the DROP rule."
        )

    def test_finding_not_generic(self):
        """The finding should be specific, not generic firewall advice."""
        finding_file = "/home/user/pentest/finding.txt"
        with open(finding_file, 'r') as f:
            content = f.read().lower()

        # Must mention specific technical details from the ruleset
        specific_patterns = [
            'mozilla',
            'string',
            'port 80',
            'port 443',
            '80',
            '443',
            'http',
            'https',
            'iptables',
            'rule',
        ]

        matches = sum(1 for pattern in specific_patterns if pattern in content)

        assert matches >= 3, (
            "The finding appears too generic. "
            "The analysis must specifically reference the string match rules, "
            "the ports involved, and the iptables configuration details."
        )
