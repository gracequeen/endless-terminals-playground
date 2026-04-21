# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the credential rotation report task.
"""

import os
import re
import subprocess
import pytest


class TestReportFileExists:
    """Test that the report file was created."""

    def test_rotation_report_exists(self):
        """The ROTATION_REPORT.md file must exist."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        assert os.path.exists(file_path), (
            f"File {file_path} does not exist. "
            "The student must create this markdown report file."
        )

    def test_rotation_report_is_file(self):
        """The ROTATION_REPORT.md must be a regular file."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        assert os.path.isfile(file_path), (
            f"{file_path} exists but is not a regular file."
        )

    def test_rotation_report_is_not_empty(self):
        """The ROTATION_REPORT.md must not be empty."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        assert os.path.getsize(file_path) > 0, (
            f"{file_path} exists but is empty."
        )


class TestLintResultsFile:
    """Test that the lint results file was created."""

    def test_lint_results_exists(self):
        """The lint-results.txt file must exist."""
        file_path = "/home/user/credential-rotation/lint-results.txt"
        assert os.path.exists(file_path), (
            f"File {file_path} does not exist. "
            "The student must create this file with markdownlint output."
        )

    def test_lint_results_is_file(self):
        """The lint-results.txt must be a regular file."""
        file_path = "/home/user/credential-rotation/lint-results.txt"
        assert os.path.isfile(file_path), (
            f"{file_path} exists but is not a regular file."
        )

    def test_lint_results_shows_no_errors(self):
        """The lint-results.txt should contain no error messages."""
        file_path = "/home/user/credential-rotation/lint-results.txt"
        with open(file_path, 'r') as f:
            content = f.read().strip()
        # Empty or contains success message - no actual lint errors
        # Lint errors typically contain file path with line numbers like "file.md:1:2"
        error_pattern = r'ROTATION_REPORT\.md:\d+'
        assert not re.search(error_pattern, content), (
            f"lint-results.txt contains lint errors: {content}"
        )


class TestMarkdownlintInstalled:
    """Test that markdownlint-cli is installed."""

    def test_markdownlint_is_available(self):
        """markdownlint should be available (globally or via npx)."""
        # Try direct command first
        result = subprocess.run(
            ["which", "markdownlint"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return  # Found globally

        # Try npx
        result = subprocess.run(
            ["npx", "markdownlint", "--version"],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, (
            "markdownlint-cli is not installed. "
            "The student must install it using npm."
        )


class TestMarkdownlintPasses:
    """Test that the report passes markdownlint."""

    def test_report_passes_markdownlint(self):
        """Running markdownlint on the report should return exit code 0."""
        report_path = "/home/user/credential-rotation/ROTATION_REPORT.md"

        # Try direct markdownlint first
        result = subprocess.run(
            ["which", "markdownlint"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Use direct command
            lint_result = subprocess.run(
                ["markdownlint", report_path],
                capture_output=True,
                text=True
            )
        else:
            # Use npx
            lint_result = subprocess.run(
                ["npx", "markdownlint", report_path],
                capture_output=True,
                text=True,
                timeout=60
            )

        assert lint_result.returncode == 0, (
            f"markdownlint failed with exit code {lint_result.returncode}. "
            f"Errors: {lint_result.stdout}{lint_result.stderr}"
        )


class TestReportStructure:
    """Test that the report has the correct structure."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_has_main_title(self, report_content):
        """Report must have the main title."""
        assert "# Credential Rotation Report" in report_content, (
            "Report is missing the main title '# Credential Rotation Report'"
        )

    def test_has_generated_timestamp(self, report_content):
        """Report must have a Generated timestamp in correct format."""
        # Look for **Generated:** followed by YYYY-MM-DD HH:MM:SS
        pattern = r'\*\*Generated:\*\*\s*\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
        assert re.search(pattern, report_content), (
            "Report is missing or has incorrectly formatted 'Generated' timestamp. "
            "Expected format: **Generated:** YYYY-MM-DD HH:MM:SS"
        )

    def test_has_total_credentials_count(self, report_content):
        """Report must show Total Credentials Rotated: 14."""
        pattern = r'\*\*Total Credentials Rotated:\*\*\s*14'
        assert re.search(pattern, report_content), (
            "Report should show 'Total Credentials Rotated: 14' "
            "(5 AWS + 4 DB + 5 API = 14 total)"
        )

    def test_has_summary_section(self, report_content):
        """Report must have Summary by Category section."""
        assert "## Summary by Category" in report_content, (
            "Report is missing '## Summary by Category' section"
        )

    def test_has_detailed_log_section(self, report_content):
        """Report must have Detailed Rotation Log section."""
        assert "## Detailed Rotation Log" in report_content, (
            "Report is missing '## Detailed Rotation Log' section"
        )

    def test_has_aws_credentials_subsection(self, report_content):
        """Report must have AWS IAM Credentials subsection."""
        assert "### AWS IAM Credentials" in report_content, (
            "Report is missing '### AWS IAM Credentials' subsection"
        )

    def test_has_database_credentials_subsection(self, report_content):
        """Report must have Database Credentials subsection."""
        assert "### Database Credentials" in report_content, (
            "Report is missing '### Database Credentials' subsection"
        )

    def test_has_api_keys_subsection(self, report_content):
        """Report must have API Keys subsection."""
        assert "### API Keys" in report_content, (
            "Report is missing '### API Keys' subsection"
        )

    def test_has_failed_rotations_section(self, report_content):
        """Report must have Failed Rotations section."""
        assert "## Failed Rotations" in report_content, (
            "Report is missing '## Failed Rotations' section"
        )

    def test_has_signoff_section(self, report_content):
        """Report must have Sign-off section."""
        assert "## Sign-off" in report_content, (
            "Report is missing '## Sign-off' section"
        )


class TestSummaryTable:
    """Test that the summary table has correct counts."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_aws_summary_row(self, report_content):
        """AWS IAM row should show: 5 total, 4 success, 1 failed."""
        # Look for a table row with AWS IAM and the correct counts
        # Format: | AWS IAM | 5 | 4 | 1 |
        pattern = r'\|\s*AWS\s*IAM\s*\|\s*5\s*\|\s*4\s*\|\s*1\s*\|'
        assert re.search(pattern, report_content), (
            "Summary table AWS IAM row should show: 5 total, 4 success, 1 failed"
        )

    def test_database_summary_row(self, report_content):
        """Database row should show: 4 total, 3 success, 1 failed."""
        pattern = r'\|\s*Database\s*\|\s*4\s*\|\s*3\s*\|\s*1\s*\|'
        assert re.search(pattern, report_content), (
            "Summary table Database row should show: 4 total, 3 success, 1 failed"
        )

    def test_api_keys_summary_row(self, report_content):
        """API Keys row should show: 5 total, 4 success, 1 failed."""
        pattern = r'\|\s*API\s*Keys\s*\|\s*5\s*\|\s*4\s*\|\s*1\s*\|'
        assert re.search(pattern, report_content), (
            "Summary table API Keys row should show: 5 total, 4 success, 1 failed"
        )


class TestAWSSection:
    """Test the AWS IAM Credentials section."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_aws_section_has_five_entries(self, report_content):
        """AWS section should have 5 service entries."""
        expected_services = [
            "analytics-pipeline",
            "backup-service",
            "notification-worker",
            "payment-service",
            "user-auth-api"
        ]
        for service in expected_services:
            assert service in report_content, (
                f"AWS section is missing entry for '{service}'"
            )

    def test_aws_entries_sorted_alphabetically(self, report_content):
        """AWS entries should be sorted alphabetically by service name."""
        # Find the AWS section
        aws_start = report_content.find("### AWS IAM Credentials")
        # Find the next section (Database)
        db_start = report_content.find("### Database Credentials")

        if aws_start == -1 or db_start == -1:
            pytest.fail("Could not find AWS or Database sections")

        aws_section = report_content[aws_start:db_start]

        # Expected order (alphabetical)
        expected_order = [
            "analytics-pipeline",
            "backup-service",
            "notification-worker",
            "payment-service",
            "user-auth-api"
        ]

        positions = []
        for service in expected_order:
            pos = aws_section.find(service)
            assert pos != -1, f"Service '{service}' not found in AWS section"
            positions.append(pos)

        assert positions == sorted(positions), (
            f"AWS entries are not sorted alphabetically. "
            f"Expected order: {expected_order}"
        )


class TestDatabaseSection:
    """Test the Database Credentials section."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_database_section_has_four_entries(self, report_content):
        """Database section should have 4 service entries."""
        expected_services = [
            "mongodb-sessions",
            "mysql-reporting",
            "postgres-primary",
            "redis-cache"
        ]
        for service in expected_services:
            assert service in report_content, (
                f"Database section is missing entry for '{service}'"
            )

    def test_database_entries_sorted_alphabetically(self, report_content):
        """Database entries should be sorted alphabetically by service name."""
        # Find the Database section
        db_start = report_content.find("### Database Credentials")
        # Find the next section (API Keys)
        api_start = report_content.find("### API Keys")

        if db_start == -1 or api_start == -1:
            pytest.fail("Could not find Database or API Keys sections")

        db_section = report_content[db_start:api_start]

        # Expected order (alphabetical)
        expected_order = [
            "mongodb-sessions",
            "mysql-reporting",
            "postgres-primary",
            "redis-cache"
        ]

        positions = []
        for service in expected_order:
            pos = db_section.find(service)
            assert pos != -1, f"Service '{service}' not found in Database section"
            positions.append(pos)

        assert positions == sorted(positions), (
            f"Database entries are not sorted alphabetically. "
            f"Expected order: {expected_order}"
        )


class TestAPIKeysSection:
    """Test the API Keys section."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_api_keys_section_has_five_entries(self, report_content):
        """API Keys section should have 5 service entries."""
        expected_services = [
            "datadog-monitoring",
            "github-actions",
            "sendgrid-email",
            "stripe-payments",
            "twilio-sms"
        ]
        for service in expected_services:
            assert service in report_content, (
                f"API Keys section is missing entry for '{service}'"
            )

    def test_api_keys_entries_sorted_alphabetically(self, report_content):
        """API Keys entries should be sorted alphabetically by service name."""
        # Find the API Keys section
        api_start = report_content.find("### API Keys")
        # Find the next section (Failed Rotations)
        failed_start = report_content.find("## Failed Rotations")

        if api_start == -1 or failed_start == -1:
            pytest.fail("Could not find API Keys or Failed Rotations sections")

        api_section = report_content[api_start:failed_start]

        # Expected order (alphabetical)
        expected_order = [
            "datadog-monitoring",
            "github-actions",
            "sendgrid-email",
            "stripe-payments",
            "twilio-sms"
        ]

        positions = []
        for service in expected_order:
            pos = api_section.find(service)
            assert pos != -1, f"Service '{service}' not found in API Keys section"
            positions.append(pos)

        assert positions == sorted(positions), (
            f"API Keys entries are not sorted alphabetically. "
            f"Expected order: {expected_order}"
        )


class TestFailedRotationsSection:
    """Test the Failed Rotations section."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_failed_section_lists_analytics_pipeline(self, report_content):
        """Failed section should list analytics-pipeline (AWS IAM)."""
        failed_start = report_content.find("## Failed Rotations")
        signoff_start = report_content.find("## Sign-off")

        if failed_start == -1 or signoff_start == -1:
            pytest.fail("Could not find Failed Rotations or Sign-off sections")

        failed_section = report_content[failed_start:signoff_start]

        assert "analytics-pipeline" in failed_section, (
            "Failed Rotations section should list 'analytics-pipeline'"
        )
        # Check it's associated with AWS
        assert "AWS" in failed_section or "aws" in failed_section.lower(), (
            "Failed Rotations should indicate AWS IAM category for analytics-pipeline"
        )

    def test_failed_section_lists_redis_cache(self, report_content):
        """Failed section should list redis-cache (Database)."""
        failed_start = report_content.find("## Failed Rotations")
        signoff_start = report_content.find("## Sign-off")

        if failed_start == -1 or signoff_start == -1:
            pytest.fail("Could not find Failed Rotations or Sign-off sections")

        failed_section = report_content[failed_start:signoff_start]

        assert "redis-cache" in failed_section, (
            "Failed Rotations section should list 'redis-cache'"
        )

    def test_failed_section_lists_datadog_monitoring(self, report_content):
        """Failed section should list datadog-monitoring (API Keys)."""
        failed_start = report_content.find("## Failed Rotations")
        signoff_start = report_content.find("## Sign-off")

        if failed_start == -1 or signoff_start == -1:
            pytest.fail("Could not find Failed Rotations or Sign-off sections")

        failed_section = report_content[failed_start:signoff_start]

        assert "datadog-monitoring" in failed_section, (
            "Failed Rotations section should list 'datadog-monitoring'"
        )

    def test_failed_section_has_exactly_three_failures(self, report_content):
        """Failed section should list exactly 3 failed services."""
        failed_start = report_content.find("## Failed Rotations")
        signoff_start = report_content.find("## Sign-off")

        if failed_start == -1 or signoff_start == -1:
            pytest.fail("Could not find Failed Rotations or Sign-off sections")

        failed_section = report_content[failed_start:signoff_start]

        failed_services = ["analytics-pipeline", "redis-cache", "datadog-monitoring"]
        found_count = sum(1 for svc in failed_services if svc in failed_section)

        assert found_count == 3, (
            f"Failed Rotations section should list exactly 3 failures: "
            f"analytics-pipeline, redis-cache, datadog-monitoring. Found {found_count}."
        )


class TestSignoffSection:
    """Test the Sign-off section."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_signoff_has_verification_checkbox(self, report_content):
        """Sign-off should have checkbox for successful rotations verified."""
        signoff_start = report_content.find("## Sign-off")
        if signoff_start == -1:
            pytest.fail("Could not find Sign-off section")

        signoff_section = report_content[signoff_start:]

        assert "All successful rotations verified" in signoff_section, (
            "Sign-off section should include 'All successful rotations verified' checkbox"
        )

    def test_signoff_has_escalation_checkbox(self, report_content):
        """Sign-off should have checkbox for failed rotations escalated."""
        signoff_start = report_content.find("## Sign-off")
        if signoff_start == -1:
            pytest.fail("Could not find Sign-off section")

        signoff_section = report_content[signoff_start:]

        assert "Failed rotations escalated" in signoff_section, (
            "Sign-off section should include 'Failed rotations escalated' checkbox"
        )

    def test_signoff_has_deletion_checkbox(self, report_content):
        """Sign-off should have checkbox for old credentials deletion."""
        signoff_start = report_content.find("## Sign-off")
        if signoff_start == -1:
            pytest.fail("Could not find Sign-off section")

        signoff_section = report_content[signoff_start:]

        assert "Old credentials scheduled for deletion" in signoff_section, (
            "Sign-off section should include 'Old credentials scheduled for deletion' checkbox"
        )


class TestTableFormatting:
    """Test that tables are properly formatted."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_summary_table_has_header_separator(self, report_content):
        """Summary table should have proper header separator."""
        # Look for table separator pattern like |---|---|---|---|
        pattern = r'\|[-:\s]+\|[-:\s]+\|[-:\s]+\|[-:\s]+\|'
        assert re.search(pattern, report_content), (
            "Summary table is missing proper header separator row"
        )

    def test_detailed_tables_have_five_columns(self, report_content):
        """Detailed tables should have 5 columns (Service, Old Key, New Key, Status, Rotated By)."""
        # Check for table rows with 5 pipe-separated columns
        # Header: | Service | Old Key ID | New Key ID | Status | Rotated By |
        pattern = r'\|\s*Service\s*\|\s*Old Key'
        assert re.search(pattern, report_content), (
            "Detailed tables should have Service and Old Key ID columns"
        )


class TestKeyData:
    """Test that specific key data is present in the report."""

    @pytest.fixture
    def report_content(self):
        """Load the report content."""
        file_path = "/home/user/credential-rotation/ROTATION_REPORT.md"
        with open(file_path, 'r') as f:
            return f.read()

    def test_contains_aws_key_ids(self, report_content):
        """Report should contain AWS key IDs."""
        assert "AKIA3EXAMPLE1OLD" in report_content, (
            "Report should contain old AWS key ID 'AKIA3EXAMPLE1OLD'"
        )
        assert "AKIA3EXAMPLE1NEW" in report_content, (
            "Report should contain new AWS key ID 'AKIA3EXAMPLE1NEW'"
        )

    def test_contains_db_hashes(self, report_content):
        """Report should contain database hashes."""
        assert "db_old_hash_001" in report_content, (
            "Report should contain old DB hash 'db_old_hash_001'"
        )
        assert "db_new_hash_001" in report_content, (
            "Report should contain new DB hash 'db_new_hash_001'"
        )

    def test_contains_api_keys(self, report_content):
        """Report should contain API keys."""
        assert "sk_old_stripe123" in report_content, (
            "Report should contain old Stripe key 'sk_old_stripe123'"
        )
        assert "sk_new_stripe456" in report_content, (
            "Report should contain new Stripe key 'sk_new_stripe456'"
        )

    def test_contains_rotated_by_users(self, report_content):
        """Report should contain the usernames who performed rotations."""
        assert "jsmith" in report_content, (
            "Report should contain rotated by user 'jsmith'"
        )
        assert "mwilliams" in report_content, (
            "Report should contain rotated by user 'mwilliams'"
        )
