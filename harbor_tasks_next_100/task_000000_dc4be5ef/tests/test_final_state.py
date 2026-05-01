# test_final_state.py
"""
Tests to validate the final state of the operating system after the student
has completed the version bump and changelog update task.
"""

import json
import os
import subprocess
import re
import pytest


class TestFinalState:
    """Test suite to validate final state after the task is performed."""

    BASE_DIR = "/home/user/pg-backup-tool"
    PACKAGE_JSON_PATH = "/home/user/pg-backup-tool/package.json"
    CHANGELOG_PATH = "/home/user/pg-backup-tool/CHANGELOG.md"

    # ==================== package.json Tests ====================

    def test_package_json_exists(self):
        """Verify package.json file still exists."""
        assert os.path.isfile(self.PACKAGE_JSON_PATH), (
            f"File {self.PACKAGE_JSON_PATH} does not exist. "
            "The package.json file must still be present after modification."
        )

    def test_package_json_is_valid_json(self):
        """Verify package.json is still valid JSON after modification."""
        try:
            with open(self.PACKAGE_JSON_PATH, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {self.PACKAGE_JSON_PATH} is not valid JSON: {e}. "
                "The package.json must remain valid JSON after the version bump."
            )

    def test_jq_validates_package_json(self):
        """Verify jq can parse package.json (anti-shortcut guard)."""
        result = subprocess.run(
            ["jq", ".", self.PACKAGE_JSON_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq failed to parse {self.PACKAGE_JSON_PATH}: {result.stderr}. "
            "The package.json must be valid JSON that jq can parse."
        )

    def test_package_json_version_is_2_4_0(self):
        """Verify package.json contains version 2.4.0."""
        with open(self.PACKAGE_JSON_PATH, 'r') as f:
            data = json.load(f)

        assert "version" in data, (
            f"File {self.PACKAGE_JSON_PATH} does not contain a 'version' field. "
            "The package.json must have a version field."
        )
        assert data["version"] == "2.4.0", (
            f"File {self.PACKAGE_JSON_PATH} has version '{data['version']}' "
            "but expected '2.4.0'. The version must be bumped to 2.4.0."
        )

    def test_jq_reads_version_2_4_0(self):
        """Verify jq reads version as exactly 2.4.0 (anti-shortcut guard)."""
        result = subprocess.run(
            ["jq", "-r", ".version", self.PACKAGE_JSON_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq failed to read version from {self.PACKAGE_JSON_PATH}: {result.stderr}"
        )
        version = result.stdout.strip()
        assert version == "2.4.0", (
            f"jq reports version as '{version}' but expected exactly '2.4.0'. "
            "The version must be exactly 2.4.0."
        )

    def test_package_json_version_not_2_3_1(self):
        """Verify package.json no longer contains version 2.3.1."""
        with open(self.PACKAGE_JSON_PATH, 'r') as f:
            data = json.load(f)

        assert data.get("version") != "2.3.1", (
            f"File {self.PACKAGE_JSON_PATH} still has version '2.3.1'. "
            "The version should have been bumped to 2.4.0."
        )

    # ==================== CHANGELOG.md Tests ====================

    def test_changelog_exists(self):
        """Verify CHANGELOG.md file still exists."""
        assert os.path.isfile(self.CHANGELOG_PATH), (
            f"File {self.CHANGELOG_PATH} does not exist. "
            "The CHANGELOG.md file must still be present after modification."
        )

    def test_changelog_is_readable(self):
        """Verify CHANGELOG.md is readable (valid markdown file)."""
        try:
            with open(self.CHANGELOG_PATH, 'r') as f:
                content = f.read()
            assert len(content) > 0, "CHANGELOG.md is empty"
        except Exception as e:
            pytest.fail(
                f"File {self.CHANGELOG_PATH} could not be read: {e}. "
                "The CHANGELOG.md must remain readable."
            )

    def test_changelog_has_unreleased_section(self):
        """Verify CHANGELOG.md still contains the [Unreleased] section header."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "## [Unreleased]" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '## [Unreleased]' header. "
            "The CHANGELOG.md must still have an Unreleased section."
        )

    def test_changelog_has_incremental_backup_entry(self):
        """Verify CHANGELOG.md contains an incremental backup entry (case-insensitive)."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert re.search(r'incremental\s+backup', content, re.IGNORECASE), (
            f"File {self.CHANGELOG_PATH} does not contain 'incremental backup' "
            "(case-insensitive). An entry about incremental backup support must be added."
        )

    def test_changelog_incremental_backup_in_unreleased_section(self):
        """Verify the incremental backup entry is in the Unreleased section."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        unreleased_pos = content.find("## [Unreleased]")
        v231_pos = content.find("## [2.3.1]")

        assert unreleased_pos != -1, (
            "Could not find '## [Unreleased]' section in CHANGELOG.md"
        )
        assert v231_pos != -1, (
            "Could not find '## [2.3.1]' section in CHANGELOG.md"
        )

        # Find the incremental backup mention (case-insensitive)
        match = re.search(r'incremental\s+backup', content, re.IGNORECASE)
        assert match is not None, (
            "Could not find 'incremental backup' in CHANGELOG.md"
        )

        incremental_pos = match.start()

        assert unreleased_pos < incremental_pos < v231_pos, (
            f"The 'incremental backup' entry (position {incremental_pos}) "
            f"is not between [Unreleased] (position {unreleased_pos}) and "
            f"[2.3.1] (position {v231_pos}). "
            "The entry must be added in the Unreleased section, before the 2.3.1 section."
        )

    def test_changelog_preserves_2_3_1_section(self):
        """Verify the 2.3.1 section is still present and unmodified."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "## [2.3.1]" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '## [2.3.1]' header. "
            "The existing 2.3.1 section must be preserved."
        )
        assert "Connection timeout handling for replicas" in content, (
            f"File {self.CHANGELOG_PATH} does not contain the 2.3.1 fix entry. "
            "The existing changelog entries must be preserved."
        )

    def test_changelog_preserves_2_3_0_section(self):
        """Verify the 2.3.0 section is still present and unmodified."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "## [2.3.0]" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '## [2.3.0]' header. "
            "The existing 2.3.0 section must be preserved."
        )
        assert "Support for PostgreSQL 16" in content, (
            f"File {self.CHANGELOG_PATH} does not contain the 2.3.0 added entry. "
            "The existing changelog entries must be preserved."
        )

    def test_changelog_section_order_preserved(self):
        """Verify CHANGELOG.md sections remain in correct order."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        unreleased_pos = content.find("## [Unreleased]")
        v231_pos = content.find("## [2.3.1]")
        v230_pos = content.find("## [2.3.0]")

        assert unreleased_pos != -1, "Missing [Unreleased] section"
        assert v231_pos != -1, "Missing [2.3.1] section"
        assert v230_pos != -1, "Missing [2.3.0] section"

        assert unreleased_pos < v231_pos < v230_pos, (
            f"File {self.CHANGELOG_PATH} sections are not in correct order. "
            f"Expected order: [Unreleased] ({unreleased_pos}) -> "
            f"[2.3.1] ({v231_pos}) -> [2.3.0] ({v230_pos})"
        )

    def test_changelog_has_changelog_header(self):
        """Verify CHANGELOG.md still has the main Changelog header."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "# Changelog" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '# Changelog' header. "
            "The main changelog header must be preserved."
        )
