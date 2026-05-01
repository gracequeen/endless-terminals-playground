# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed the task.
This verifies that the release script passes and the changelog/package.json are correctly updated.
"""

import json
import os
import re
import subprocess
from datetime import datetime
import pytest


DOCS_SITE_PATH = "/home/user/docs-site"
PACKAGE_JSON_PATH = os.path.join(DOCS_SITE_PATH, "package.json")
CHANGELOG_PATH = os.path.join(DOCS_SITE_PATH, "CHANGELOG.md")
RELEASE_SCRIPT_PATH = os.path.join(DOCS_SITE_PATH, "scripts", "release.js")


class TestReleaseScriptPasses:
    """Test that the release script now passes."""

    def test_npm_run_release_succeeds(self):
        """npm run release must now succeed with exit code 0."""
        result = subprocess.run(
            ["npm", "run", "release"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"npm run release failed with exit code {result.returncode}. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestPackageJsonVersion:
    """Test that package.json has been updated correctly."""

    def test_package_json_valid_json(self):
        """package.json must still be valid JSON."""
        with open(PACKAGE_JSON_PATH, "r") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"package.json is not valid JSON: {e}")

    def test_package_json_version_is_0_8_0(self):
        """package.json version must be 0.8.0 (minor bump from 0.7.2 due to feat commits)."""
        with open(PACKAGE_JSON_PATH, "r") as f:
            data = json.load(f)
        assert "version" in data, "package.json does not have a 'version' field"
        assert data["version"] == "0.8.0", (
            f"Expected version 0.8.0 (minor bump for feat commits), got {data['version']}"
        )


class TestChangelogNewSection:
    """Test that CHANGELOG.md has the new 0.8.0 section."""

    def test_changelog_has_0_8_0_section(self):
        """CHANGELOG.md must have a new 0.8.0 section."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "[0.8.0]" in content, "CHANGELOG.md is missing the new 0.8.0 section"

    def test_changelog_0_8_0_has_valid_iso_date(self):
        """The 0.8.0 section header must have a valid ISO date format (YYYY-MM-DD)."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Look for the 0.8.0 section header with ISO date
        pattern = r"##\s*\[0\.8\.0\]\s*-\s*(\d{4}-\d{2}-\d{2})"
        match = re.search(pattern, content)
        assert match, (
            "The 0.8.0 section header does not have a valid ISO date format. "
            "Expected format: '## [0.8.0] - YYYY-MM-DD'"
        )

        # Validate that the date is actually valid
        date_str = match.group(1)
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pytest.fail(f"The date '{date_str}' in 0.8.0 section is not a valid date")

    def test_changelog_0_8_0_contains_webhook_content(self):
        """The 0.8.0 section must contain content about webhooks (from feat commit)."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Find the 0.8.0 section content (between 0.8.0 header and next ## header or end)
        pattern = r"##\s*\[0\.8\.0\].*?(?=##\s*\[|$)"
        match = re.search(pattern, content, re.DOTALL)
        assert match, "Could not find 0.8.0 section"

        section_content = match.group(0).lower()
        assert "webhook" in section_content, (
            "The 0.8.0 section does not contain 'webhook' content from the feat commit. "
            "The release script should have included the webhook tutorial feature."
        )

    def test_changelog_0_8_0_contains_search_content(self):
        """The 0.8.0 section must contain content about search (from feat commit)."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Find the 0.8.0 section content
        pattern = r"##\s*\[0\.8\.0\].*?(?=##\s*\[|$)"
        match = re.search(pattern, content, re.DOTALL)
        assert match, "Could not find 0.8.0 section"

        section_content = match.group(0).lower()
        assert "search" in section_content, (
            "The 0.8.0 section does not contain 'search' content from the feat commit. "
            "The release script should have included the full-text search feature."
        )

    def test_changelog_0_8_0_is_at_top(self):
        """The 0.8.0 section must be at the top of the version sections."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Find all version section headers
        version_headers = re.findall(r"##\s*\[(\d+\.\d+\.\d+)\]", content)
        assert len(version_headers) >= 5, (
            f"Expected at least 5 version sections, found {len(version_headers)}"
        )
        assert version_headers[0] == "0.8.0", (
            f"The 0.8.0 section is not at the top. First version found: {version_headers[0]}"
        )


class TestChangelogPreservedSections:
    """Test that all previous changelog sections are preserved."""

    def test_changelog_has_all_old_sections(self):
        """CHANGELOG.md must still have all the old version sections."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        expected_versions = ["0.7.2", "0.7.1", "0.7.0", "0.6.0"]
        for version in expected_versions:
            assert f"[{version}]" in content, (
                f"CHANGELOG.md is missing the preserved section for version {version}"
            )

    def test_changelog_section_count(self):
        """CHANGELOG.md must have at least 4 old version sections (0.7.x and 0.6.0)."""
        result = subprocess.run(
            ["grep", "-c", r"^## \[0\.", CHANGELOG_PATH],
            capture_output=True,
            text=True
        )
        # grep -c returns the count as a string
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count >= 4, (
            f"Expected at least 4 version sections starting with 0.x, found {count}. "
            "Old sections may have been deleted."
        )

    def test_changelog_0_7_2_content_preserved(self):
        """The 0.7.2 section content must be preserved."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "mobile navigation" in content.lower(), (
            "Content about 'mobile navigation' from 0.7.2 section is missing"
        )

    def test_changelog_0_7_1_content_preserved(self):
        """The 0.7.1 section content must be preserved."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "dark mode" in content.lower(), (
            "Content about 'dark mode' from 0.7.1 section is missing"
        )

    def test_changelog_0_6_0_content_preserved(self):
        """The 0.6.0 section content must be preserved."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "api reference" in content.lower(), (
            "Content about 'API reference' from 0.6.0 section is missing"
        )


class TestMalformedDateFixed:
    """Test that the malformed date was fixed (not worked around)."""

    def test_no_october_28_text_date(self):
        """The malformed 'October 28' date format must be fixed."""
        result = subprocess.run(
            ["grep", "October 28", CHANGELOG_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "The malformed date 'October 28' is still present in CHANGELOG.md. "
            "The fix should convert it to ISO format (2024-10-28), not work around the validation."
        )

    def test_0_7_0_section_exists(self):
        """The 0.7.0 section must still exist (not deleted as a workaround)."""
        result = subprocess.run(
            ["grep", "0.7.0", CHANGELOG_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 0.7.0 section appears to be missing from CHANGELOG.md. "
            "The section should be preserved with a corrected date format."
        )

    def test_0_7_0_has_iso_date(self):
        """The 0.7.0 section must now have an ISO date format."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Check for 0.7.0 with ISO date format
        pattern = r"##\s*\[0\.7\.0\]\s*-\s*2024-10-28"
        match = re.search(pattern, content)
        assert match, (
            "The 0.7.0 section header does not have the expected ISO date format. "
            "Expected: '## [0.7.0] - 2024-10-28'"
        )


class TestReleaseScriptUnmodified:
    """Test that the release script was not modified (fix is in data, not validator)."""

    def test_release_script_exists(self):
        """The release script must still exist."""
        assert os.path.isfile(RELEASE_SCRIPT_PATH), (
            f"Release script {RELEASE_SCRIPT_PATH} does not exist"
        )

    def test_release_script_still_validates(self):
        """The release script should still perform changelog validation."""
        with open(RELEASE_SCRIPT_PATH, "r") as f:
            content = f.read()

        # The script should still contain validation logic
        assert "validation" in content.lower() or "validate" in content.lower() or "regex" in content.lower() or "pattern" in content.lower(), (
            "The release script appears to have had its validation logic removed. "
            "The fix should be in the changelog data, not by disabling validation."
        )


class TestGitHistoryUnchanged:
    """Test that Git history was not modified."""

    def test_v0_7_2_tag_still_exists(self):
        """The v0.7.2 tag must still exist."""
        result = subprocess.run(
            ["git", "tag", "-l", "v0.7.2"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert "v0.7.2" in result.stdout, "Tag v0.7.2 no longer exists"

    def test_commits_since_tag_unchanged(self):
        """The commits since v0.7.2 should still be present."""
        result = subprocess.run(
            ["git", "log", "v0.7.2..HEAD", "--oneline"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get git log"
        # Should have at least the original 4 commits (may have more from release)
        commits = [c for c in result.stdout.strip().split("\n") if c]
        assert len(commits) >= 4, (
            f"Expected at least 4 commits since v0.7.2, found {len(commits)}. "
            "Git history may have been modified."
        )


class TestChangelogStructure:
    """Test the overall structure of the changelog."""

    def test_changelog_has_header(self):
        """CHANGELOG.md must still have the standard header."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "# Changelog" in content, "CHANGELOG.md is missing '# Changelog' header"

    def test_all_version_headers_have_iso_dates(self):
        """All version section headers should have ISO date format."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Find all version headers
        headers = re.findall(r"##\s*\[\d+\.\d+\.\d+\]\s*-\s*(.+)", content)

        iso_date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        for date_str in headers:
            date_str = date_str.strip()
            assert re.match(iso_date_pattern, date_str), (
                f"Version header date '{date_str}' is not in ISO format (YYYY-MM-DD)"
            )
