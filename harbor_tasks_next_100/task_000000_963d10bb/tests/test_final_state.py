# test_final_state.py
"""
Tests to validate the final state after the student has correctly archived
all 847 files from /data/projects to /backup/archive.tar.gz.
"""

import os
import subprocess
import tempfile
import shutil
import pytest


DATA_PROJECTS = "/data/projects"
BACKUP_DIR = "/backup"
ARCHIVE_PATH = "/backup/archive.tar.gz"


class TestArchiveExists:
    """Tests for the existence and basic validity of the archive."""

    def test_archive_file_exists(self):
        """Verify /backup/archive.tar.gz exists."""
        assert os.path.isfile(ARCHIVE_PATH), (
            f"Archive file {ARCHIVE_PATH} does not exist. "
            "The archive must be created at this exact path."
        )

    def test_archive_is_not_empty(self):
        """Verify the archive has substantial size (not just a few files)."""
        size = os.path.getsize(ARCHIVE_PATH)
        # With ~120MB of data compressed, should be at least several MB
        # Being conservative: at least 10MB compressed
        min_size = 10 * 1024 * 1024  # 10MB
        assert size >= min_size, (
            f"Archive size is {size / (1024*1024):.2f}MB, expected at least 10MB. "
            f"The archive appears to be incomplete (likely only contains a subset of files)."
        )

    def test_archive_is_valid_gzip(self):
        """Verify the archive is a valid gzip file."""
        result = subprocess.run(
            ["gzip", "-t", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Archive {ARCHIVE_PATH} is not a valid gzip file: {result.stderr}"
        )


class TestArchiveContents:
    """Tests for the contents of the archive."""

    def test_archive_contains_exactly_847_files(self):
        """Verify the archive contains exactly 847 files."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Failed to list archive contents: {result.stderr}"
        )

        # Count non-empty lines (file entries)
        lines = [l for l in result.stdout.strip().split('\n') if l]
        file_count = len(lines)

        assert file_count == 847, (
            f"Archive contains {file_count} entries, expected exactly 847. "
            f"The archive is incomplete - all files from /data/projects must be included."
        )

    def test_archive_contains_files_with_spaces(self):
        """Verify at least 40 files with spaces in names are archived."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to list archive: {result.stderr}"

        lines = result.stdout.strip().split('\n')
        files_with_spaces = sum(1 for l in lines if ' ' in l)

        assert files_with_spaces >= 40, (
            f"Archive contains {files_with_spaces} files with spaces in names, "
            f"expected at least 40. Files with special characters may not have been "
            f"archived correctly."
        )

    def test_archive_contains_files_with_quotes(self):
        """Verify at least 15 files with single quotes in names are archived."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to list archive: {result.stderr}"

        lines = result.stdout.strip().split('\n')
        files_with_quotes = sum(1 for l in lines if "'" in l)

        assert files_with_quotes >= 15, (
            f"Archive contains {files_with_quotes} files with single quotes in names, "
            f"expected at least 15. Files with special characters may not have been "
            f"archived correctly."
        )

    def test_archive_paths_correspond_to_data_projects(self):
        """Verify archived paths correspond to files under /data/projects."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to list archive: {result.stderr}"

        lines = [l for l in result.stdout.strip().split('\n') if l]

        # Check that paths reference the data/projects structure
        # Paths might be stored as absolute (/data/projects/...) or relative (data/projects/...)
        valid_paths = 0
        for line in lines:
            # Accept both absolute and relative paths
            if 'data/projects' in line or line.startswith('data/projects'):
                valid_paths += 1

        # All 847 files should have valid paths
        assert valid_paths == 847, (
            f"Only {valid_paths} of 847 archived files have paths referencing "
            f"data/projects. Archive structure may be incorrect."
        )


class TestArchiveExtraction:
    """Tests for successful extraction of the archive."""

    def test_archive_extracts_successfully(self):
        """Verify the archive can be extracted without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["tar", "-xzf", ARCHIVE_PATH, "-C", tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, (
                f"Failed to extract archive: {result.stderr}"
            )

    def test_extraction_produces_847_files(self):
        """Verify extraction produces exactly 847 files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract
            result = subprocess.run(
                ["tar", "-xzf", ARCHIVE_PATH, "-C", tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Extraction failed: {result.stderr}"

            # Count extracted files
            result = subprocess.run(
                ["find", tmpdir, "-type", "f"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"find failed: {result.stderr}"

            files = [f for f in result.stdout.strip().split('\n') if f]
            file_count = len(files)

            assert file_count == 847, (
                f"Extraction produced {file_count} files, expected 847. "
                f"The archive does not contain all required files."
            )

    def test_extracted_files_have_content(self):
        """Verify extracted files are not empty (have actual content)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract
            subprocess.run(
                ["tar", "-xzf", ARCHIVE_PATH, "-C", tmpdir],
                capture_output=True
            )

            # Check total size of extracted content
            result = subprocess.run(
                ["du", "-sb", tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0

            size_bytes = int(result.stdout.split()[0])
            size_mb = size_bytes / (1024 * 1024)

            # Should be approximately 120MB (allow 100-150MB range)
            assert 100 <= size_mb <= 150, (
                f"Extracted content is {size_mb:.1f}MB, expected ~120MB. "
                f"Files may be corrupted or truncated."
            )


class TestSourceDataIntact:
    """Tests to verify original source data is untouched."""

    def test_source_files_still_exist(self):
        """Verify all 847 source files still exist."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"find failed: {result.stderr}"

        files = [f for f in result.stdout.strip().split('\n') if f]
        file_count = len(files)

        assert file_count == 847, (
            f"Source directory now has {file_count} files, expected 847. "
            f"Original files in {DATA_PROJECTS} must not be modified or deleted."
        )

    def test_source_directory_structure_intact(self):
        """Verify source directory structure is intact."""
        assert os.path.isdir(DATA_PROJECTS), (
            f"{DATA_PROJECTS} no longer exists as a directory!"
        )

        entries = os.listdir(DATA_PROJECTS)
        subdirs = [e for e in entries if os.path.isdir(os.path.join(DATA_PROJECTS, e))]

        assert len(subdirs) >= 10, (
            f"Source directory structure appears modified. "
            f"Expected at least 10 subdirectories, found {len(subdirs)}."
        )

    def test_source_size_unchanged(self):
        """Verify source data size is approximately the same (~120MB)."""
        result = subprocess.run(
            ["du", "-sb", DATA_PROJECTS],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        size_bytes = int(result.stdout.split()[0])
        size_mb = size_bytes / (1024 * 1024)

        assert 100 <= size_mb <= 150, (
            f"Source data size is {size_mb:.1f}MB, expected ~120MB. "
            f"Original files may have been modified."
        )


class TestArchiveCompleteness:
    """Additional tests to ensure archive completeness and correctness."""

    def test_all_file_extensions_present(self):
        """Verify all expected file types are in the archive."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        contents = result.stdout

        extensions = ['.txt', '.log', '.dat', '.csv', '.json']
        for ext in extensions:
            assert ext in contents, (
                f"No {ext} files found in archive. "
                f"Archive may be missing some file types."
            )

    def test_archive_has_nested_paths(self):
        """Verify archive contains nested directory paths (not flat)."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        lines = result.stdout.strip().split('\n')

        # Check for paths with multiple directory levels
        deep_paths = 0
        for line in lines:
            # Count path separators to determine depth
            depth = line.count('/')
            if depth >= 4:  # e.g., data/projects/subdir1/subdir2/file
                deep_paths += 1

        assert deep_paths > 0, (
            "Archive doesn't appear to contain nested directory structure. "
            "Files should preserve their original directory hierarchy."
        )

    def test_no_duplicate_entries(self):
        """Verify archive doesn't have duplicate file entries."""
        result = subprocess.run(
            ["tar", "-tzf", ARCHIVE_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

        lines = [l for l in result.stdout.strip().split('\n') if l]
        unique_lines = set(lines)

        assert len(lines) == len(unique_lines), (
            f"Archive contains {len(lines) - len(unique_lines)} duplicate entries. "
            f"Each file should appear exactly once."
        )
