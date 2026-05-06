# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of finding orphaned nav entries in the MkDocs configuration.
"""

import os
import subprocess
import pytest
import yaml


HOME_DIR = "/home/user"
DOCS_SITE_DIR = "/home/user/docs-site"
MKDOCS_YML = "/home/user/docs-site/mkdocs.yml"
DOCS_DIR = "/home/user/docs-site/docs"

# Files that SHOULD exist
EXISTING_FILES = [
    "index.md",
    "getting-started/install.md",
    "getting-started/quickstart.md",
    "api/overview.md",
    "api/auth.md",
    "tutorials/basic.md",
    "tutorials/advanced.md",
    "contributing.md",
    "changelog.md",
]

# Files that should be MISSING (orphaned nav entries)
MISSING_FILES = [
    "getting-started/migration.md",
    "api/endpoints.md",
    "api/legacy-v1.md",
    "tutorials/integrations.md",
]


class TestDocsRepoExists:
    """Test that the docs-site repository exists and is properly structured."""

    def test_home_directory_exists(self):
        """Verify /home/user exists and is a directory."""
        assert os.path.isdir(HOME_DIR), f"Home directory {HOME_DIR} does not exist"

    def test_docs_site_directory_exists(self):
        """Verify /home/user/docs-site exists and is a directory."""
        assert os.path.isdir(DOCS_SITE_DIR), f"Docs site directory {DOCS_SITE_DIR} does not exist"

    def test_docs_site_is_git_repo(self):
        """Verify /home/user/docs-site is a git repository."""
        git_dir = os.path.join(DOCS_SITE_DIR, ".git")
        assert os.path.isdir(git_dir), f"{DOCS_SITE_DIR} is not a git repository (no .git directory)"

    def test_docs_directory_exists(self):
        """Verify /home/user/docs-site/docs exists and is a directory."""
        assert os.path.isdir(DOCS_DIR), f"Docs directory {DOCS_DIR} does not exist"


class TestMkdocsYmlExists:
    """Test that mkdocs.yml exists and has the expected structure."""

    def test_mkdocs_yml_exists(self):
        """Verify mkdocs.yml file exists."""
        assert os.path.isfile(MKDOCS_YML), f"MkDocs config file {MKDOCS_YML} does not exist"

    def test_mkdocs_yml_is_valid_yaml(self):
        """Verify mkdocs.yml is valid YAML."""
        with open(MKDOCS_YML, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, "mkdocs.yml is empty or invalid"
            except yaml.YAMLError as e:
                pytest.fail(f"mkdocs.yml is not valid YAML: {e}")

    def test_mkdocs_yml_has_nav_section(self):
        """Verify mkdocs.yml contains a 'nav' key."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)
        assert 'nav' in data, "mkdocs.yml does not contain a 'nav' section"
        assert isinstance(data['nav'], list), "nav section should be a list"

    def test_mkdocs_yml_has_docs_dir(self):
        """Verify mkdocs.yml specifies docs_dir."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)
        assert 'docs_dir' in data, "mkdocs.yml does not specify docs_dir"
        assert data['docs_dir'] == 'docs', "docs_dir should be 'docs'"

    def test_mkdocs_yml_has_site_name(self):
        """Verify mkdocs.yml has a site_name."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)
        assert 'site_name' in data, "mkdocs.yml does not contain site_name"


class TestExistingDocsFiles:
    """Test that the expected documentation files exist."""

    @pytest.mark.parametrize("file_path", EXISTING_FILES)
    def test_existing_file_present(self, file_path):
        """Verify each expected file exists in the docs directory."""
        full_path = os.path.join(DOCS_DIR, file_path)
        assert os.path.isfile(full_path), f"Expected file {full_path} does not exist"


class TestMissingDocsFiles:
    """Test that the orphaned files are actually missing (as expected for the task)."""

    @pytest.mark.parametrize("file_path", MISSING_FILES)
    def test_missing_file_not_present(self, file_path):
        """Verify each orphaned file does NOT exist in the docs directory."""
        full_path = os.path.join(DOCS_DIR, file_path)
        assert not os.path.exists(full_path), f"File {full_path} should NOT exist (it's supposed to be an orphaned nav entry)"


class TestNavContainsExpectedPaths:
    """Test that the nav section contains all the expected paths (both existing and missing)."""

    def _extract_nav_paths(self, nav_item):
        """Recursively extract all file paths from nav structure."""
        paths = []
        if isinstance(nav_item, str):
            # Direct path
            paths.append(nav_item)
        elif isinstance(nav_item, dict):
            for key, value in nav_item.items():
                if isinstance(value, str):
                    # Single file: "Title: path.md"
                    paths.append(value)
                elif isinstance(value, list):
                    # Nested section
                    for item in value:
                        paths.extend(self._extract_nav_paths(item))
        elif isinstance(nav_item, list):
            for item in nav_item:
                paths.extend(self._extract_nav_paths(item))
        return paths

    def test_nav_contains_existing_files(self):
        """Verify nav section references all existing files."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)

        nav_paths = self._extract_nav_paths(data['nav'])

        for expected_file in EXISTING_FILES:
            assert expected_file in nav_paths, f"Nav section should contain {expected_file}"

    def test_nav_contains_missing_files(self):
        """Verify nav section references all the orphaned (missing) files."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)

        nav_paths = self._extract_nav_paths(data['nav'])

        for missing_file in MISSING_FILES:
            assert missing_file in nav_paths, f"Nav section should contain orphaned entry {missing_file}"


class TestDirectoryStructure:
    """Test that required subdirectories exist."""

    def test_getting_started_dir_exists(self):
        """Verify getting-started subdirectory exists."""
        path = os.path.join(DOCS_DIR, "getting-started")
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_api_dir_exists(self):
        """Verify api subdirectory exists."""
        path = os.path.join(DOCS_DIR, "api")
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_tutorials_dir_exists(self):
        """Verify tutorials subdirectory exists."""
        path = os.path.join(DOCS_DIR, "tutorials")
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestGitRepository:
    """Test git repository state."""

    def test_git_is_functional(self):
        """Verify git commands work in the repository."""
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=DOCS_SITE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Git is not functional in {DOCS_SITE_DIR}: {result.stderr}"

    def test_git_has_commits(self):
        """Verify the repository has at least one commit."""
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=DOCS_SITE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Repository has no commits: {result.stderr}"


class TestHomeWritable:
    """Test that home directory is writable for output file."""

    def test_home_is_writable(self):
        """Verify /home/user is writable."""
        assert os.access(HOME_DIR, os.W_OK), f"{HOME_DIR} is not writable"
