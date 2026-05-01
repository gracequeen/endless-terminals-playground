# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the version bump and changelog update task.
"""

import json
import os
import re
import subprocess
import pytest


class TestFinalState:
    """Tests to verify the final state after the task is performed."""

    # ==================== package.json tests ====================

    def test_package_json_exists(self):
        """Verify package.json file still exists."""
        file_path = "/home/user/pg-backup-tool/package.json"
        assert os.path.isfile(file_path), (
            f"File {file_path} does not exist. "
            "The package.json file must still be present after the update."
        )

    def test_package_json_is_valid_json(self):
        """Verify package.json is still valid JSON after modification."""
        file_path = "/home/user/pg-backup-tool/package.json"
        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {file_path} is not valid JSON: {e}. "
                "The package.json must remain valid JSON after the version update."
            )

    def test_package_json_has_version_2_4_0(self):
        """Verify package.json has been updated to version 2.4.0."""
        file_path = "/home/user/pg-backup-tool/package.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        assert 'version' in data, (
            f"File {file_path} does not have a 'version' field. "
            "The package.json must contain a version field."
        )
        assert data['version'] == "2.4.0", (
            f"File {file_path} has version '{data['version']}' but expected '2.4.0'. "
            "The version must be bumped from 2.3.1 to 2.4.0."
        )

    def test_package_json_version_via_python_command(self):
        """Verify version using the exact command from the truth specification."""
        result = subprocess.run(
            [
                "python3", "-c",
                "import json; d=json.load(open('/home/user/pg-backup-tool/package.json')); assert d['version']=='2.4.0'"
            ],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Version check command failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}. "
            "The package.json version must be exactly '2.4.0'."
        )

    def test_package_json_name_field_preserved(self):
        """Verify the 'name' field in package.json is preserved."""
        file_path = "/home/user/pg-backup-tool/package.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        assert 'name' in data, (
            f"File {file_path} is missing the 'name' field. "
            "All other fields in package.json must be preserved."
        )

    def test_package_json_other_fields_preserved(self):
        """Verify that package.json has multiple fields (not just version)."""
        file_path = "/home/user/pg-backup-tool/package.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Should have more than just the version field
        assert len(data) > 1, (
            f"File {file_path} only has {len(data)} field(s). "
            "All other fields in package.json must be preserved (name, description, dependencies, etc.)."
        )

    # ==================== CHANGELOG.md tests ====================

    def test_changelog_exists(self):
        """Verify CHANGELOG.md file still exists."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        assert os.path.isfile(file_path), (
            f"File {file_path} does not exist. "
            "The CHANGELOG.md file must still be present after the update."
        )

    def test_changelog_has_2_4_0_section_at_top(self):
        """Verify CHANGELOG.md has a new 2.4.0 section at the top with proper date format."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"

        # Use the exact command from truth specification
        result = subprocess.run(
            ["sh", "-c", f"head -5 {file_path} | grep -E '## 2\\.4\\.0 - [0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Could not find '## 2.4.0 - YYYY-MM-DD' in the first 5 lines of {file_path}. "
            "A new section for version 2.4.0 with today's date (YYYY-MM-DD format) must be at the top."
        )

    def test_changelog_2_4_0_is_first_version_section(self):
        """Verify 2.4.0 is the first version section in the changelog."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Find the first line that starts with "## " (version header)
        first_version_line = None
        for line in lines:
            if line.startswith("## "):
                first_version_line = line
                break

        assert first_version_line is not None, (
            f"File {file_path} does not contain any version sections (lines starting with '## '). "
            "The CHANGELOG.md must have version sections."
        )

        assert "2.4.0" in first_version_line, (
            f"The first version section in {file_path} is '{first_version_line.strip()}' "
            "but expected it to be the 2.4.0 section. "
            "The new 2.4.0 section must be at the top of the changelog."
        )

    def test_changelog_mentions_incremental_backups(self):
        """Verify the new section mentions incremental backups."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"

        # Use the exact command from truth specification
        result = subprocess.run(
            ["sh", "-c", f"head -10 {file_path} | grep -i 'incremental'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Could not find 'incremental' (case-insensitive) in the first 10 lines of {file_path}. "
            "The new changelog entry must mention incremental backups."
        )

    def test_changelog_preserves_2_3_1_section(self):
        """Verify the existing 2.3.1 section is still present."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"

        # Use grep to check for the 2.3.1 section
        result = subprocess.run(
            ["grep", "## 2.3.1", file_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Could not find '## 2.3.1' in {file_path}. "
            "The existing 2.3.1 section must be preserved in the changelog."
        )

    def test_changelog_2_3_1_comes_after_2_4_0(self):
        """Verify 2.3.1 section comes after 2.4.0 section."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            content = f.read()

        # Find positions of both version headers
        pos_2_4_0 = content.find("## 2.4.0")
        pos_2_3_1 = content.find("## 2.3.1")

        assert pos_2_4_0 != -1, (
            f"Could not find '## 2.4.0' in {file_path}. "
            "The new 2.4.0 section must be present."
        )
        assert pos_2_3_1 != -1, (
            f"Could not find '## 2.3.1' in {file_path}. "
            "The existing 2.3.1 section must be preserved."
        )
        assert pos_2_4_0 < pos_2_3_1, (
            f"In {file_path}, the 2.4.0 section (position {pos_2_4_0}) "
            f"should come before the 2.3.1 section (position {pos_2_3_1}). "
            "The new version section must be at the top."
        )

    def test_changelog_has_valid_date_format(self):
        """Verify the 2.4.0 section has a valid date in YYYY-MM-DD format."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            content = f.read()

        # Look for the 2.4.0 header with date pattern
        pattern = r'## 2\.4\.0 - (\d{4})-(\d{2})-(\d{2})'
        match = re.search(pattern, content)

        assert match is not None, (
            f"Could not find '## 2.4.0 - YYYY-MM-DD' pattern in {file_path}. "
            "The new section must have a date in YYYY-MM-DD format."
        )

        # Validate the date components are reasonable
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        assert 2020 <= year <= 2030, (
            f"Year {year} in the changelog date seems unreasonable."
        )
        assert 1 <= month <= 12, (
            f"Month {month} in the changelog date is invalid."
        )
        assert 1 <= day <= 31, (
            f"Day {day} in the changelog date is invalid."
        )

    def test_changelog_2_4_0_has_content(self):
        """Verify the 2.4.0 section has at least one line of content about incremental backups."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Find the 2.4.0 section and check it has content before 2.3.1
        in_2_4_0_section = False
        content_lines = []

        for line in lines:
            if "## 2.4.0" in line:
                in_2_4_0_section = True
                continue
            if in_2_4_0_section:
                if line.startswith("## "):
                    # Hit the next section
                    break
                if line.strip():
                    content_lines.append(line.strip())

        assert len(content_lines) > 0, (
            f"The 2.4.0 section in {file_path} has no content. "
            "There must be at least one line about incremental backups."
        )

        # Check that at least one content line mentions incremental
        incremental_mentioned = any('incremental' in line.lower() for line in content_lines)
        assert incremental_mentioned, (
            f"The 2.4.0 section content does not mention 'incremental'. "
            f"Content found: {content_lines}. "
            "The changelog entry must mention incremental backups."
        )
