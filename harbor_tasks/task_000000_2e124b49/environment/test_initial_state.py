# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies the docs-site repository is set up correctly with the changelog validation bug.
"""

import json
import os
import subprocess
import pytest


DOCS_SITE_PATH = "/home/user/docs-site"
PACKAGE_JSON_PATH = os.path.join(DOCS_SITE_PATH, "package.json")
CHANGELOG_PATH = os.path.join(DOCS_SITE_PATH, "CHANGELOG.md")
RELEASE_SCRIPT_PATH = os.path.join(DOCS_SITE_PATH, "scripts", "release.js")


class TestDirectoryStructure:
    """Test that the required directories and files exist."""

    def test_docs_site_directory_exists(self):
        """The docs-site directory must exist."""
        assert os.path.isdir(DOCS_SITE_PATH), f"Directory {DOCS_SITE_PATH} does not exist"

    def test_package_json_exists(self):
        """package.json must exist in the docs-site directory."""
        assert os.path.isfile(PACKAGE_JSON_PATH), f"File {PACKAGE_JSON_PATH} does not exist"

    def test_changelog_exists(self):
        """CHANGELOG.md must exist in the docs-site directory."""
        assert os.path.isfile(CHANGELOG_PATH), f"File {CHANGELOG_PATH} does not exist"

    def test_release_script_exists(self):
        """The release script must exist."""
        assert os.path.isfile(RELEASE_SCRIPT_PATH), f"File {RELEASE_SCRIPT_PATH} does not exist"

    def test_node_modules_exists(self):
        """node_modules directory must exist (dependencies installed)."""
        node_modules_path = os.path.join(DOCS_SITE_PATH, "node_modules")
        assert os.path.isdir(node_modules_path), f"Directory {node_modules_path} does not exist - npm install may not have been run"


class TestNodeEnvironment:
    """Test that Node.js and npm are available."""

    def test_node_available(self):
        """Node.js must be available."""
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "Node.js is not available"
        assert result.stdout.strip().startswith("v"), f"Unexpected node version output: {result.stdout}"

    def test_node_version_20(self):
        """Node.js version should be v20.x."""
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        assert version.startswith("v20"), f"Expected Node.js v20.x, got {version}"

    def test_npm_available(self):
        """npm must be available."""
        result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "npm is not available"


class TestPackageJson:
    """Test the package.json configuration."""

    def test_package_json_valid_json(self):
        """package.json must be valid JSON."""
        with open(PACKAGE_JSON_PATH, "r") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"package.json is not valid JSON: {e}")

    def test_package_json_version_is_0_7_2(self):
        """package.json version must be 0.7.2."""
        with open(PACKAGE_JSON_PATH, "r") as f:
            data = json.load(f)
        assert "version" in data, "package.json does not have a 'version' field"
        assert data["version"] == "0.7.2", f"Expected version 0.7.2, got {data['version']}"

    def test_package_json_has_release_script(self):
        """package.json must have a 'release' script defined."""
        with open(PACKAGE_JSON_PATH, "r") as f:
            data = json.load(f)
        assert "scripts" in data, "package.json does not have a 'scripts' section"
        assert "release" in data["scripts"], "package.json does not have a 'release' script"


class TestGitRepository:
    """Test the Git repository state."""

    def test_is_git_repository(self):
        """docs-site must be a Git repository."""
        git_dir = os.path.join(DOCS_SITE_PATH, ".git")
        assert os.path.isdir(git_dir), f"{DOCS_SITE_PATH} is not a Git repository (no .git directory)"

    def test_has_v0_7_2_tag(self):
        """The repository must have a v0.7.2 tag."""
        result = subprocess.run(
            ["git", "tag", "-l", "v0.7.2"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to list git tags"
        assert "v0.7.2" in result.stdout, "Tag v0.7.2 does not exist"

    def test_has_commits_since_tag(self):
        """There must be commits since the v0.7.2 tag."""
        result = subprocess.run(
            ["git", "log", "v0.7.2..HEAD", "--oneline"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get git log"
        commits = result.stdout.strip().split("\n")
        commits = [c for c in commits if c]  # Filter empty lines
        assert len(commits) >= 4, f"Expected at least 4 commits since v0.7.2, found {len(commits)}"

    def test_commits_include_feat_commits(self):
        """There must be feat commits since the tag (for minor version bump)."""
        result = subprocess.run(
            ["git", "log", "v0.7.2..HEAD", "--pretty=format:%s"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get git log"
        commit_messages = result.stdout.strip().split("\n")
        feat_commits = [m for m in commit_messages if m.startswith("feat")]
        assert len(feat_commits) >= 2, f"Expected at least 2 feat commits, found {len(feat_commits)}"


class TestChangelog:
    """Test the CHANGELOG.md content and the bug condition."""

    def test_changelog_has_header(self):
        """CHANGELOG.md must have the standard header."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "# Changelog" in content, "CHANGELOG.md is missing '# Changelog' header"

    def test_changelog_has_version_sections(self):
        """CHANGELOG.md must have the expected version sections."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        expected_versions = ["0.7.2", "0.7.1", "0.7.0", "0.6.0"]
        for version in expected_versions:
            assert f"[{version}]" in content, f"CHANGELOG.md is missing section for version {version}"

    def test_changelog_has_malformed_date(self):
        """CHANGELOG.md must have the malformed date 'October 28, 2024' (the bug)."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        assert "October 28, 2024" in content, (
            "CHANGELOG.md does not contain 'October 28, 2024' - the bug condition is not present. "
            "The 0.7.0 section should have a non-ISO date format."
        )

    def test_changelog_0_7_0_has_malformed_header(self):
        """The 0.7.0 section header must use the malformed date format."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()
        # Check that the malformed format is in a section header
        assert "## [0.7.0] - October 28, 2024" in content, (
            "The 0.7.0 section header does not have the expected malformed date format. "
            "Expected: '## [0.7.0] - October 28, 2024'"
        )

    def test_changelog_has_proper_content(self):
        """CHANGELOG.md must have the expected content under sections."""
        with open(CHANGELOG_PATH, "r") as f:
            content = f.read()

        # Check for some expected content
        assert "mobile navigation" in content.lower(), "Missing content about mobile navigation in 0.7.2"
        assert "dark mode" in content.lower(), "Missing content about dark mode in 0.7.1"
        assert "search" in content.lower(), "Missing content about search in 0.7.0"


class TestReleaseScriptFails:
    """Test that the release script currently fails (the bug exists)."""

    def test_npm_run_release_fails(self):
        """npm run release must currently fail with exit code 1."""
        result = subprocess.run(
            ["npm", "run", "release"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            "npm run release succeeded but should fail due to changelog validation error. "
            "The bug condition may not be properly set up."
        )

    def test_release_failure_mentions_validation(self):
        """The release script failure should mention validation."""
        result = subprocess.run(
            ["npm", "run", "release"],
            cwd=DOCS_SITE_PATH,
            capture_output=True,
            text=True
        )
        combined_output = result.stdout + result.stderr
        # The error message should mention validation
        assert "validation" in combined_output.lower() or "failed" in combined_output.lower(), (
            f"Release script failed but error message doesn't mention validation. Output: {combined_output}"
        )


class TestDirectoryWritable:
    """Test that the docs-site directory is writable."""

    def test_docs_site_writable(self):
        """The docs-site directory must be writable."""
        assert os.access(DOCS_SITE_PATH, os.W_OK), f"{DOCS_SITE_PATH} is not writable"

    def test_changelog_writable(self):
        """CHANGELOG.md must be writable."""
        assert os.access(CHANGELOG_PATH, os.W_OK), f"{CHANGELOG_PATH} is not writable"

    def test_package_json_writable(self):
        """package.json must be writable."""
        assert os.access(PACKAGE_JSON_PATH, os.W_OK), f"{PACKAGE_JSON_PATH} is not writable"
