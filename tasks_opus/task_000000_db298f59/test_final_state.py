# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed
the SSH security audit task.
"""

import os
import re
from datetime import datetime
import pytest


class TestAuditReportExists:
    """Test that the audit report file exists and has correct properties."""

    def test_audit_report_file_exists(self):
        """The SSH audit report must exist at /home/user/ssh_audit_report.txt."""
        report_path = "/home/user/ssh_audit_report.txt"
        assert os.path.exists(report_path), (
            f"SSH audit report not found at {report_path}. "
            "The task requires creating this file with the security audit results."
        )

    def test_audit_report_is_file(self):
        """The audit report path must be a regular file."""
        report_path = "/home/user/ssh_audit_report.txt"
        assert os.path.isfile(report_path), (
            f"{report_path} exists but is not a regular file. "
            "The audit report must be a text file."
        )

    def test_audit_report_is_readable(self):
        """The audit report must be readable."""
        report_path = "/home/user/ssh_audit_report.txt"
        assert os.path.isfile(report_path), (
            f"{report_path} exists but is not readable. "
            "The audit report file must have read permissions."
        )

    def test_audit_report_not_empty(self):
        """The audit report must not be empty."""
        report_path = "/home/user/ssh_audit_report.txt"
        if os.path.exists(report_path):
            file_size = os.path.getsize(report_path)
            assert file_size > 0, (
                f"{report_path} exists but is empty (0 bytes). "
                "The audit report should contain the security audit results."
            )


class TestAuditReportHeader:
    """Test that the audit report contains the required header."""

    @pytest.fixture
    def report_content(self):
        """Read the audit report content."""
        report_path = "/home/user/ssh_audit_report.txt"
        if os.path.exists(report_path) and os.path.isfile(report_path):
            with open(report_path, 'r') as f:
                return f.read()
        return ""

    def test_contains_title(self, report_content):
        """The report must contain the title 'SSH SECURITY AUDIT REPORT'."""
        assert "SSH SECURITY AUDIT REPORT" in report_content, (
            "The audit report is missing the required title 'SSH SECURITY AUDIT REPORT'. "
            "The report must start with this exact header."
        )

    def test_contains_separator_line(self, report_content):
        """The report must contain the separator line '========================='."""
        assert "=========================" in report_content, (
            "The audit report is missing the separator line '========================='. "
            "This line should appear after the title."
        )

    def test_contains_scan_date_label(self, report_content):
        """The report must contain a 'Scan Date:' line."""
        assert "Scan Date:" in report_content, (
            "The audit report is missing the 'Scan Date:' line. "
            "The report must include the date when the scan was performed."
        )

    def test_scan_date_format(self, report_content):
        """The scan date must be in YYYY-MM-DD format."""
        # Look for a date pattern after "Scan Date:"
        date_pattern = r"Scan Date:\s*(\d{4}-\d{2}-\d{2})"
        match = re.search(date_pattern, report_content)
        assert match is not None, (
            "The 'Scan Date:' line does not contain a date in YYYY-MM-DD format. "
            "Expected format: 'Scan Date: 2024-01-15' (example)."
        )
        # Validate that the date is actually valid
        date_str = match.group(1)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pytest.fail(
                f"The date '{date_str}' is not a valid date. "
                "The Scan Date must be a real date in YYYY-MM-DD format."
            )

    def test_contains_configuration_file_path(self, report_content):
        """The report must reference the configuration file path."""
        assert "Configuration File: /etc/ssh/sshd_config" in report_content, (
            "The audit report is missing 'Configuration File: /etc/ssh/sshd_config'. "
            "The report must specify which configuration file was scanned."
        )


class TestAuditReportFindings:
    """Test that the audit report contains the required findings section."""

    @pytest.fixture
    def report_content(self):
        """Read the audit report content."""
        report_path = "/home/user/ssh_audit_report.txt"
        if os.path.exists(report_path) and os.path.isfile(report_path):
            with open(report_path, 'r') as f:
                return f.read()
        return ""

    def test_contains_findings_section(self, report_content):
        """The report must contain a 'FINDINGS:' section."""
        assert "FINDINGS:" in report_content, (
            "The audit report is missing the 'FINDINGS:' section header. "
            "This section should list the security settings that were checked."
        )

    def test_contains_findings_separator(self, report_content):
        """The report must contain the findings separator '---------'."""
        assert "---------" in report_content, (
            "The audit report is missing the separator line '---------' under FINDINGS. "
            "This line should appear after the FINDINGS header."
        )

    def test_contains_permit_root_login_finding(self, report_content):
        """The report must contain a finding for PermitRootLogin."""
        assert "PermitRootLogin:" in report_content, (
            "The audit report is missing the 'PermitRootLogin:' finding. "
            "This setting must be checked and reported."
        )

    def test_contains_password_authentication_finding(self, report_content):
        """The report must contain a finding for PasswordAuthentication."""
        assert "PasswordAuthentication:" in report_content, (
            "The audit report is missing the 'PasswordAuthentication:' finding. "
            "This setting must be checked and reported."
        )

    def test_contains_x11_forwarding_finding(self, report_content):
        """The report must contain a finding for X11Forwarding."""
        assert "X11Forwarding:" in report_content, (
            "The audit report is missing the 'X11Forwarding:' finding. "
            "This setting must be checked and reported."
        )

    def test_permit_root_login_has_security_assessment(self, report_content):
        """The PermitRootLogin finding must include SECURE or INSECURE assessment."""
        # Find the line containing PermitRootLogin
        lines = report_content.split('\n')
        permit_root_line = None
        for line in lines:
            if "PermitRootLogin:" in line:
                permit_root_line = line
                break

        assert permit_root_line is not None, (
            "Could not find PermitRootLogin line in the report."
        )
        assert "SECURE" in permit_root_line or "INSECURE" in permit_root_line, (
            f"The PermitRootLogin finding must include 'SECURE' or 'INSECURE'. "
            f"Found line: '{permit_root_line}'"
        )

    def test_password_authentication_has_security_assessment(self, report_content):
        """The PasswordAuthentication finding must include SECURE or INSECURE assessment."""
        lines = report_content.split('\n')
        password_auth_line = None
        for line in lines:
            if "PasswordAuthentication:" in line:
                password_auth_line = line
                break

        assert password_auth_line is not None, (
            "Could not find PasswordAuthentication line in the report."
        )
        assert "SECURE" in password_auth_line or "INSECURE" in password_auth_line, (
            f"The PasswordAuthentication finding must include 'SECURE' or 'INSECURE'. "
            f"Found line: '{password_auth_line}'"
        )

    def test_x11_forwarding_has_security_assessment(self, report_content):
        """The X11Forwarding finding must include SECURE or INSECURE assessment."""
        lines = report_content.split('\n')
        x11_line = None
        for line in lines:
            if "X11Forwarding:" in line:
                x11_line = line
                break

        assert x11_line is not None, (
            "Could not find X11Forwarding line in the report."
        )
        assert "SECURE" in x11_line or "INSECURE" in x11_line, (
            f"The X11Forwarding finding must include 'SECURE' or 'INSECURE'. "
            f"Found line: '{x11_line}'"
        )


class TestAuditReportSummary:
    """Test that the audit report contains the required summary section."""

    @pytest.fixture
    def report_content(self):
        """Read the audit report content."""
        report_path = "/home/user/ssh_audit_report.txt"
        if os.path.exists(report_path) and os.path.isfile(report_path):
            with open(report_path, 'r') as f:
                return f.read()
        return ""

    def test_contains_summary_section(self, report_content):
        """The report must contain a 'SUMMARY:' section."""
        assert "SUMMARY:" in report_content, (
            "The audit report is missing the 'SUMMARY:' section header. "
            "This section should provide a count of secure and insecure settings."
        )

    def test_contains_total_settings_checked(self, report_content):
        """The report must contain 'Total Settings Checked: 3'."""
        assert "Total Settings Checked: 3" in report_content, (
            "The audit report is missing 'Total Settings Checked: 3'. "
            "The summary must indicate that exactly 3 settings were checked."
        )

    def test_contains_secure_settings_count(self, report_content):
        """The report must contain a 'Secure Settings:' line with a number."""
        pattern = r"Secure Settings:\s*(\d+)"
        match = re.search(pattern, report_content)
        assert match is not None, (
            "The audit report is missing 'Secure Settings:' followed by a number. "
            "The summary must include a count of secure settings."
        )

    def test_contains_insecure_settings_count(self, report_content):
        """The report must contain an 'Insecure Settings:' line with a number."""
        pattern = r"Insecure Settings:\s*(\d+)"
        match = re.search(pattern, report_content)
        assert match is not None, (
            "The audit report is missing 'Insecure Settings:' followed by a number. "
            "The summary must include a count of insecure settings."
        )

    def test_secure_insecure_sum_equals_three(self, report_content):
        """The sum of Secure Settings and Insecure Settings must equal 3."""
        secure_pattern = r"Secure Settings:\s*(\d+)"
        insecure_pattern = r"Insecure Settings:\s*(\d+)"

        secure_match = re.search(secure_pattern, report_content)
        insecure_match = re.search(insecure_pattern, report_content)

        if secure_match is None or insecure_match is None:
            pytest.skip("Cannot verify sum - Secure or Insecure Settings count not found.")

        secure_count = int(secure_match.group(1))
        insecure_count = int(insecure_match.group(1))
        total = secure_count + insecure_count

        assert total == 3, (
            f"The sum of Secure Settings ({secure_count}) and Insecure Settings "
            f"({insecure_count}) is {total}, but it should equal 3. "
            "Three settings were checked, so the counts must add up to 3."
        )


class TestAuditReportFormat:
    """Test the overall format and structure of the audit report."""

    @pytest.fixture
    def report_content(self):
        """Read the audit report content."""
        report_path = "/home/user/ssh_audit_report.txt"
        if os.path.exists(report_path) and os.path.isfile(report_path):
            with open(report_path, 'r') as f:
                return f.read()
        return ""

    def test_findings_contain_values(self, report_content):
        """Each finding should contain a value (not just the setting name)."""
        settings = ["PermitRootLogin:", "PasswordAuthentication:", "X11Forwarding:"]

        for setting in settings:
            lines = report_content.split('\n')
            for line in lines:
                if setting in line:
                    # The line should have content after the setting name
                    # Format expected: "SettingName: [VALUE] - [SECURE/INSECURE]"
                    parts = line.split(setting)
                    if len(parts) > 1:
                        value_part = parts[1].strip()
                        assert len(value_part) > 0, (
                            f"The {setting} finding appears to have no value. "
                            f"Expected format: '{setting} [value] - [SECURE/INSECURE]'"
                        )
                    break

    def test_report_sections_in_order(self, report_content):
        """The report sections should appear in the correct order."""
        # Find positions of key sections
        title_pos = report_content.find("SSH SECURITY AUDIT REPORT")
        findings_pos = report_content.find("FINDINGS:")
        summary_pos = report_content.find("SUMMARY:")

        if title_pos == -1 or findings_pos == -1 or summary_pos == -1:
            pytest.skip("Cannot verify order - one or more sections not found.")

        assert title_pos < findings_pos < summary_pos, (
            "The report sections are not in the correct order. "
            "Expected order: Title/Header, then FINDINGS, then SUMMARY."
        )