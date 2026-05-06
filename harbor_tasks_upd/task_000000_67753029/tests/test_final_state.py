# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of finding orphaned nav entries in the MkDocs configuration.
"""

import os
import pytest
import yaml


HOME_DIR = "/home/user"
DOCS_SITE_DIR = "/home/user/docs-site"
MKDOCS_YML = "/home/user/docs-site/mkdocs.yml"
DOCS_DIR = "/home/user/docs-site/docs"
OUTPUT_FILE = "/home/user/orphaned-nav.txt"

# The expected orphaned nav entries (files in nav but missing from disk)
EXPECTED_ORPHANS = {
    "getting-started/migration.md",
    "api/endpoints.md",
    "api/legacy-v1.md",
    "tutorials/integrations.md",
}

# Files that SHOULD exist (unchanged from initial state)
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


class TestOutputFileExists:
    """Test that the output file exists and is properly formatted."""

    def test_output_file_exists(self):
        """Verify /home/user/orphaned-nav.txt exists."""
        assert os.path.isfile(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist. "
            "The task requires creating this file with orphaned nav entries."
        )

    def test_output_file_is_not_empty(self):
        """Verify the output file is not empty."""
        assert os.path.getsize(OUTPUT_FILE) > 0, (
            f"Output file {OUTPUT_FILE} is empty. "
            "It should contain the orphaned nav entries."
        )


class TestOutputFileContent:
    """Test that the output file contains exactly the expected orphaned entries."""

    def _read_output_lines(self):
        """Read and parse the output file, returning non-empty lines."""
        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()
        # Split by newlines and filter out empty lines
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        return lines

    def test_output_has_exactly_four_entries(self):
        """Verify the output file contains exactly 4 orphaned entries."""
        lines = self._read_output_lines()
        assert len(lines) == 4, (
            f"Output file should contain exactly 4 orphaned entries, "
            f"but found {len(lines)}: {lines}"
        )

    def test_output_contains_all_expected_orphans(self):
        """Verify all expected orphaned paths are in the output."""
        lines = self._read_output_lines()
        output_set = set(lines)

        missing_from_output = EXPECTED_ORPHANS - output_set
        assert not missing_from_output, (
            f"Output file is missing these expected orphaned entries: {missing_from_output}. "
            f"Found: {output_set}"
        )

    def test_output_contains_only_expected_orphans(self):
        """Verify no unexpected entries are in the output."""
        lines = self._read_output_lines()
        output_set = set(lines)

        unexpected_entries = output_set - EXPECTED_ORPHANS
        assert not unexpected_entries, (
            f"Output file contains unexpected entries: {unexpected_entries}. "
            f"Expected only: {EXPECTED_ORPHANS}"
        )

    def test_output_entries_match_exactly(self):
        """Verify the output contains exactly the expected orphans (comprehensive check)."""
        lines = self._read_output_lines()
        output_set = set(lines)

        assert output_set == EXPECTED_ORPHANS, (
            f"Output file content mismatch.\n"
            f"Expected: {sorted(EXPECTED_ORPHANS)}\n"
            f"Got: {sorted(output_set)}"
        )


class TestOutputEntriesAreValidOrphans:
    """Test that each entry in the output is actually an orphan (in nav but not on disk)."""

    def _extract_nav_paths(self, nav_item):
        """Recursively extract all file paths from nav structure."""
        paths = []
        if isinstance(nav_item, str):
            paths.append(nav_item)
        elif isinstance(nav_item, dict):
            for key, value in nav_item.items():
                if isinstance(value, str):
                    paths.append(value)
                elif isinstance(value, list):
                    for item in value:
                        paths.extend(self._extract_nav_paths(item))
        elif isinstance(nav_item, list):
            for item in nav_item:
                paths.extend(self._extract_nav_paths(item))
        return paths

    def _read_output_lines(self):
        """Read and parse the output file, returning non-empty lines."""
        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        return lines

    def test_each_output_entry_exists_in_nav(self):
        """Verify each path in output actually appears in mkdocs.yml nav section."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)

        nav_paths = set(self._extract_nav_paths(data['nav']))
        output_lines = self._read_output_lines()

        for path in output_lines:
            assert path in nav_paths, (
                f"Output entry '{path}' does not appear in the nav section of mkdocs.yml. "
                f"Only paths from the nav should be listed as orphans."
            )

    def test_each_output_entry_file_does_not_exist(self):
        """Verify each path in output does NOT exist as a file on disk."""
        output_lines = self._read_output_lines()

        for path in output_lines:
            full_path = os.path.join(DOCS_DIR, path)
            assert not os.path.exists(full_path), (
                f"Output entry '{path}' actually exists at {full_path}. "
                f"Only missing files should be listed as orphans."
            )


class TestInvariantsMkdocsYmlUnchanged:
    """Test that mkdocs.yml was not modified."""

    def test_mkdocs_yml_exists(self):
        """Verify mkdocs.yml still exists."""
        assert os.path.isfile(MKDOCS_YML), (
            f"mkdocs.yml at {MKDOCS_YML} no longer exists. "
            "The task should not modify or delete this file."
        )

    def test_mkdocs_yml_has_nav_section(self):
        """Verify mkdocs.yml still has nav section."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)
        assert 'nav' in data, "mkdocs.yml nav section is missing"

    def test_mkdocs_yml_nav_has_expected_structure(self):
        """Verify mkdocs.yml nav still has the expected entries."""
        with open(MKDOCS_YML, 'r') as f:
            data = yaml.safe_load(f)

        # Check that key entries are still present
        assert data.get('site_name') == 'Acme Docs', "site_name should be 'Acme Docs'"
        assert data.get('docs_dir') == 'docs', "docs_dir should be 'docs'"


class TestInvariantsDocsFilesUnchanged:
    """Test that existing docs files were not modified or deleted."""

    @pytest.mark.parametrize("file_path", EXISTING_FILES)
    def test_existing_file_still_present(self, file_path):
        """Verify each expected file still exists in the docs directory."""
        full_path = os.path.join(DOCS_DIR, file_path)
        assert os.path.isfile(full_path), (
            f"File {full_path} no longer exists. "
            "The task should not modify or delete existing documentation files."
        )


class TestInvariantsOrphanedFilesStillMissing:
    """Test that the orphaned files are still missing (not created by mistake)."""

    @pytest.mark.parametrize("file_path", list(EXPECTED_ORPHANS))
    def test_orphaned_file_still_missing(self, file_path):
        """Verify orphaned files were not accidentally created."""
        full_path = os.path.join(DOCS_DIR, file_path)
        assert not os.path.exists(full_path), (
            f"File {full_path} now exists but should still be missing. "
            "The task is to identify orphans, not create the missing files."
        )


class TestInvariantsGitUnchanged:
    """Test that git repository state was not modified."""

    def test_git_repo_still_exists(self):
        """Verify the .git directory still exists."""
        git_dir = os.path.join(DOCS_SITE_DIR, ".git")
        assert os.path.isdir(git_dir), (
            f"Git directory {git_dir} no longer exists. "
            "The task should not modify the git repository."
        )

    def test_docs_site_dir_still_exists(self):
        """Verify the docs-site directory still exists."""
        assert os.path.isdir(DOCS_SITE_DIR), (
            f"Docs site directory {DOCS_SITE_DIR} no longer exists."
        )
