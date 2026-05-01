# test_initial_state.py
"""
Tests to validate the initial state of the operating system before the student
performs the version bump and changelog update task.
"""

import json
import os
import subprocess
import pytest


class TestInitialState:
    """Test suite to validate initial state before the task is performed."""

    BASE_DIR = "/home/user/pg-backup-tool"
    PACKAGE_JSON_PATH = "/home/user/pg-backup-tool/package.json"
    CHANGELOG_PATH = "/home/user/pg-backup-tool/CHANGELOG.md"

    def test_base_directory_exists(self):
        """Verify the pg-backup-tool directory exists."""
        assert os.path.isdir(self.BASE_DIR), (
            f"Directory {self.BASE_DIR} does not exist. "
            "The pg-backup-tool project directory must be present."
        )

    def test_package_json_exists(self):
        """Verify package.json file exists."""
        assert os.path.isfile(self.PACKAGE_JSON_PATH), (
            f"File {self.PACKAGE_JSON_PATH} does not exist. "
            "The package.json file must be present for the version bump task."
        )

    def test_package_json_is_readable(self):
        """Verify package.json is readable."""
        assert os.access(self.PACKAGE_JSON_PATH, os.R_OK), (
            f"File {self.PACKAGE_JSON_PATH} is not readable. "
            "The package.json file must be readable."
        )

    def test_package_json_is_writable(self):
        """Verify package.json is writable by the agent user."""
        assert os.access(self.PACKAGE_JSON_PATH, os.W_OK), (
            f"File {self.PACKAGE_JSON_PATH} is not writable. "
            "The package.json file must be writable to update the version."
        )

    def test_package_json_is_valid_json(self):
        """Verify package.json is valid JSON."""
        try:
            with open(self.PACKAGE_JSON_PATH, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {self.PACKAGE_JSON_PATH} is not valid JSON: {e}. "
                "The package.json must be valid JSON before modification."
            )

    def test_package_json_has_version_2_3_1(self):
        """Verify package.json contains version 2.3.1."""
        with open(self.PACKAGE_JSON_PATH, 'r') as f:
            data = json.load(f)

        assert "version" in data, (
            f"File {self.PACKAGE_JSON_PATH} does not contain a 'version' field. "
            "The package.json must have a version field to bump."
        )
        assert data["version"] == "2.3.1", (
            f"File {self.PACKAGE_JSON_PATH} has version '{data['version']}' "
            "but expected '2.3.1'. The initial version must be 2.3.1."
        )

    def test_package_json_version_string_in_file(self):
        """Verify the exact string '"version": "2.3.1"' appears in package.json."""
        with open(self.PACKAGE_JSON_PATH, 'r') as f:
            content = f.read()

        # Check that the version string exists somewhere in the file
        assert '"2.3.1"' in content, (
            f"File {self.PACKAGE_JSON_PATH} does not contain the string '\"2.3.1\"'. "
            "The version 2.3.1 must be present in the file."
        )

    def test_jq_validates_package_json(self):
        """Verify jq can parse package.json (anti-shortcut guard check)."""
        result = subprocess.run(
            ["jq", ".", self.PACKAGE_JSON_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq failed to parse {self.PACKAGE_JSON_PATH}: {result.stderr}. "
            "The package.json must be valid JSON that jq can parse."
        )

    def test_jq_reads_version_2_3_1(self):
        """Verify jq reads version as 2.3.1."""
        result = subprocess.run(
            ["jq", "-r", ".version", self.PACKAGE_JSON_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"jq failed to read version from {self.PACKAGE_JSON_PATH}: {result.stderr}"
        )
        version = result.stdout.strip()
        assert version == "2.3.1", (
            f"jq reports version as '{version}' but expected '2.3.1'. "
            "The initial version must be 2.3.1."
        )

    def test_changelog_exists(self):
        """Verify CHANGELOG.md file exists."""
        assert os.path.isfile(self.CHANGELOG_PATH), (
            f"File {self.CHANGELOG_PATH} does not exist. "
            "The CHANGELOG.md file must be present for adding the release entry."
        )

    def test_changelog_is_readable(self):
        """Verify CHANGELOG.md is readable."""
        assert os.access(self.CHANGELOG_PATH, os.R_OK), (
            f"File {self.CHANGELOG_PATH} is not readable. "
            "The CHANGELOG.md file must be readable."
        )

    def test_changelog_is_writable(self):
        """Verify CHANGELOG.md is writable by the agent user."""
        assert os.access(self.CHANGELOG_PATH, os.W_OK), (
            f"File {self.CHANGELOG_PATH} is not writable. "
            "The CHANGELOG.md file must be writable to add the changelog entry."
        )

    def test_changelog_has_unreleased_section(self):
        """Verify CHANGELOG.md contains the [Unreleased] section header."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "## [Unreleased]" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '## [Unreleased]' header. "
            "The CHANGELOG.md must have an Unreleased section to add entries to."
        )

    def test_changelog_has_version_2_3_1_section(self):
        """Verify CHANGELOG.md contains the [2.3.1] section."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "## [2.3.1]" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '## [2.3.1]' header. "
            "The CHANGELOG.md must have the 2.3.1 version section."
        )

    def test_changelog_has_version_2_3_0_section(self):
        """Verify CHANGELOG.md contains the [2.3.0] section."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "## [2.3.0]" in content, (
            f"File {self.CHANGELOG_PATH} does not contain '## [2.3.0]' header. "
            "The CHANGELOG.md must have the 2.3.0 version section."
        )

    def test_changelog_has_correct_structure(self):
        """Verify CHANGELOG.md has sections in correct order."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        unreleased_pos = content.find("## [Unreleased]")
        v231_pos = content.find("## [2.3.1]")
        v230_pos = content.find("## [2.3.0]")

        assert unreleased_pos < v231_pos < v230_pos, (
            f"File {self.CHANGELOG_PATH} does not have sections in correct order. "
            "Expected order: [Unreleased] -> [2.3.1] -> [2.3.0]"
        )

    def test_changelog_2_3_1_has_fixed_section(self):
        """Verify the 2.3.1 section has the expected Fixed content."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "Connection timeout handling for replicas" in content, (
            f"File {self.CHANGELOG_PATH} does not contain expected 2.3.1 fix entry. "
            "The changelog should mention 'Connection timeout handling for replicas'."
        )

    def test_changelog_2_3_0_has_added_section(self):
        """Verify the 2.3.0 section has the expected Added content."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read()

        assert "Support for PostgreSQL 16" in content, (
            f"File {self.CHANGELOG_PATH} does not contain expected 2.3.0 added entry. "
            "The changelog should mention 'Support for PostgreSQL 16'."
        )

    def test_changelog_does_not_have_incremental_backup(self):
        """Verify CHANGELOG.md does not already mention incremental backup."""
        with open(self.CHANGELOG_PATH, 'r') as f:
            content = f.read().lower()

        assert "incremental backup" not in content, (
            f"File {self.CHANGELOG_PATH} already contains 'incremental backup'. "
            "The initial state should not have the incremental backup entry yet."
        )

    def test_standard_tools_available_sed(self):
        """Verify sed is available."""
        result = subprocess.run(["which", "sed"], capture_output=True)
        assert result.returncode == 0, (
            "sed is not available. Standard text processing tools must be installed."
        )

    def test_standard_tools_available_awk(self):
        """Verify awk is available."""
        result = subprocess.run(["which", "awk"], capture_output=True)
        assert result.returncode == 0, (
            "awk is not available. Standard text processing tools must be installed."
        )

    def test_standard_tools_available_grep(self):
        """Verify grep is available."""
        result = subprocess.run(["which", "grep"], capture_output=True)
        assert result.returncode == 0, (
            "grep is not available. Standard text processing tools must be installed."
        )

    def test_standard_tools_available_cat(self):
        """Verify cat is available."""
        result = subprocess.run(["which", "cat"], capture_output=True)
        assert result.returncode == 0, (
            "cat is not available. Standard text processing tools must be installed."
        )

    def test_standard_tools_available_jq(self):
        """Verify jq is available."""
        result = subprocess.run(["which", "jq"], capture_output=True)
        assert result.returncode == 0, (
            "jq is not available. jq must be installed for JSON processing."
        )
