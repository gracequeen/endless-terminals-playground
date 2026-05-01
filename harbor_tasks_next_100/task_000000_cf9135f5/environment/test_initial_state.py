# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the version bump and changelog update task.
"""

import json
import os
import pytest


class TestInitialState:
    """Tests to verify the initial state before the task is performed."""

    def test_pg_backup_tool_directory_exists(self):
        """Verify the pg-backup-tool directory exists."""
        dir_path = "/home/user/pg-backup-tool"
        assert os.path.isdir(dir_path), (
            f"Directory {dir_path} does not exist. "
            "The pg-backup-tool project directory must be present."
        )

    def test_package_json_exists(self):
        """Verify package.json file exists."""
        file_path = "/home/user/pg-backup-tool/package.json"
        assert os.path.isfile(file_path), (
            f"File {file_path} does not exist. "
            "The package.json file must be present in the pg-backup-tool directory."
        )

    def test_package_json_is_readable(self):
        """Verify package.json is readable."""
        file_path = "/home/user/pg-backup-tool/package.json"
        assert os.access(file_path, os.R_OK), (
            f"File {file_path} is not readable. "
            "The package.json file must be readable."
        )

    def test_package_json_is_writable(self):
        """Verify package.json is writable."""
        file_path = "/home/user/pg-backup-tool/package.json"
        assert os.access(file_path, os.W_OK), (
            f"File {file_path} is not writable. "
            "The package.json file must be writable by the agent user."
        )

    def test_package_json_is_valid_json(self):
        """Verify package.json contains valid JSON."""
        file_path = "/home/user/pg-backup-tool/package.json"
        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {file_path} does not contain valid JSON: {e}. "
                "The package.json must be valid JSON."
            )

    def test_package_json_has_version_2_3_1(self):
        """Verify package.json has version 2.3.1."""
        file_path = "/home/user/pg-backup-tool/package.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        assert 'version' in data, (
            f"File {file_path} does not have a 'version' field. "
            "The package.json must contain a version field."
        )
        assert data['version'] == "2.3.1", (
            f"File {file_path} has version '{data['version']}' but expected '2.3.1'. "
            "The initial version must be 2.3.1."
        )

    def test_package_json_has_other_fields(self):
        """Verify package.json has other expected fields (name, description, dependencies)."""
        file_path = "/home/user/pg-backup-tool/package.json"
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Check for at least some other fields that should be present
        assert 'name' in data, (
            f"File {file_path} does not have a 'name' field. "
            "The package.json should have a name field."
        )

    def test_changelog_exists(self):
        """Verify CHANGELOG.md file exists."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        assert os.path.isfile(file_path), (
            f"File {file_path} does not exist. "
            "The CHANGELOG.md file must be present in the pg-backup-tool directory."
        )

    def test_changelog_is_readable(self):
        """Verify CHANGELOG.md is readable."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        assert os.access(file_path, os.R_OK), (
            f"File {file_path} is not readable. "
            "The CHANGELOG.md file must be readable."
        )

    def test_changelog_is_writable(self):
        """Verify CHANGELOG.md is writable."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        assert os.access(file_path, os.W_OK), (
            f"File {file_path} is not writable. "
            "The CHANGELOG.md file must be writable by the agent user."
        )

    def test_changelog_has_2_3_1_section(self):
        """Verify CHANGELOG.md has the 2.3.1 section at the top."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            content = f.read()

        assert "## 2.3.1" in content, (
            f"File {file_path} does not contain '## 2.3.1' section. "
            "The CHANGELOG.md must have an existing 2.3.1 section."
        )

    def test_changelog_2_3_1_section_has_date(self):
        """Verify the 2.3.1 section has the expected date format."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            content = f.read()

        # Check for the specific format mentioned in truth: "## 2.3.1 - 2024-01-15"
        assert "## 2.3.1 - 2024-01-15" in content, (
            f"File {file_path} does not contain '## 2.3.1 - 2024-01-15'. "
            "The CHANGELOG.md must have the 2.3.1 section with date 2024-01-15."
        )

    def test_changelog_2_3_1_is_top_section(self):
        """Verify 2.3.1 is currently the top version section."""
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

        assert "2.3.1" in first_version_line, (
            f"The first version section in {file_path} is '{first_version_line.strip()}' "
            "but expected it to be the 2.3.1 section. "
            "The 2.3.1 section must be at the top of the changelog."
        )

    def test_changelog_has_content_after_header(self):
        """Verify CHANGELOG.md has some content (bullet points) after the 2.3.1 header."""
        file_path = "/home/user/pg-backup-tool/CHANGELOG.md"
        with open(file_path, 'r') as f:
            content = f.read()

        # Should have some content - at least a few lines
        lines = [l for l in content.split('\n') if l.strip()]
        assert len(lines) > 2, (
            f"File {file_path} appears to have very little content. "
            "The CHANGELOG.md should have existing entries with bullet points."
        )
