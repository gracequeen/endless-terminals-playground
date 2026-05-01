# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the archiving task.
"""

import os
import subprocess
import pytest


HOME = "/home/user"
DATA_PROJECTS = "/data/projects"
BACKUP_DIR = "/backup"
ARCHIVE_PATH = "/backup/archive.tar.gz"


class TestDataProjectsDirectory:
    """Tests for the /data/projects directory structure and contents."""

    def test_data_projects_exists(self):
        """Verify /data/projects directory exists."""
        assert os.path.isdir(DATA_PROJECTS), (
            f"Directory {DATA_PROJECTS} does not exist. "
            "The source directory for archiving must be present."
        )

    def test_data_projects_is_readable(self):
        """Verify /data/projects is readable."""
        assert os.access(DATA_PROJECTS, os.R_OK), (
            f"Directory {DATA_PROJECTS} is not readable. "
            "Need read permissions to archive files."
        )

    def test_data_projects_has_subdirectories(self):
        """Verify /data/projects has top-level subdirectories."""
        entries = os.listdir(DATA_PROJECTS)
        subdirs = [e for e in entries if os.path.isdir(os.path.join(DATA_PROJECTS, e))]
        assert len(subdirs) >= 10, (
            f"Expected at least 10 top-level subdirectories in {DATA_PROJECTS}, "
            f"found {len(subdirs)}. Directory structure appears incomplete."
        )

    def test_file_count_is_847(self):
        """Verify exactly 847 regular files exist under /data/projects."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"find command failed: {result.stderr}"
        )
        file_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        assert file_count == 847, (
            f"Expected exactly 847 regular files in {DATA_PROJECTS}, "
            f"found {file_count}. The source data is incomplete or incorrect."
        )

    def test_total_size_approximately_120mb(self):
        """Verify total size of files is approximately 120MB."""
        result = subprocess.run(
            ["du", "-sb", DATA_PROJECTS],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"du command failed: {result.stderr}"

        # Parse size in bytes
        size_bytes = int(result.stdout.split()[0])
        size_mb = size_bytes / (1024 * 1024)

        # Allow some tolerance (100MB to 150MB)
        assert 100 <= size_mb <= 150, (
            f"Expected total size around 120MB, got {size_mb:.1f}MB. "
            "The source data size is outside expected range."
        )

    def test_files_with_spaces_exist(self):
        """Verify at least 40 files have spaces in their names."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "* *"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"find command failed: {result.stderr}"

        files_with_spaces = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        assert files_with_spaces >= 40, (
            f"Expected at least 40 files with spaces in names, found {files_with_spaces}. "
            "Test data should include files with spaces to verify proper handling."
        )

    def test_files_with_quotes_exist(self):
        """Verify at least 15 files have single quotes in their names."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "*'*"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"find command failed: {result.stderr}"

        files_with_quotes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        assert files_with_quotes >= 15, (
            f"Expected at least 15 files with single quotes in names, found {files_with_quotes}. "
            "Test data should include files with quotes to verify proper handling."
        )

    def test_no_symlinks_in_data(self):
        """Verify there are no symlinks in /data/projects."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "l"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"find command failed: {result.stderr}"

        symlinks = result.stdout.strip()
        assert symlinks == "", (
            f"Found symlinks in {DATA_PROJECTS} but there should be none: {symlinks}"
        )

    def test_all_files_readable(self):
        """Verify all files are readable by current user."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "!", "-readable"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"find command failed: {result.stderr}"

        unreadable = result.stdout.strip()
        assert unreadable == "", (
            f"Found unreadable files in {DATA_PROJECTS}: {unreadable}"
        )

    def test_nested_directory_depth(self):
        """Verify directory structure has appropriate nesting (2-5 levels)."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "d"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"find command failed: {result.stderr}"

        dirs = result.stdout.strip().split('\n') if result.stdout.strip() else []
        # Calculate max depth relative to /data/projects
        max_depth = 0
        for d in dirs:
            depth = d.count('/') - DATA_PROJECTS.count('/')
            if depth > max_depth:
                max_depth = depth

        assert max_depth >= 2, (
            f"Expected at least 2 levels of nesting, found max depth {max_depth}. "
            "Directory structure appears too shallow."
        )


class TestBackupDirectory:
    """Tests for the /backup directory."""

    def test_backup_dir_exists(self):
        """Verify /backup directory exists."""
        assert os.path.isdir(BACKUP_DIR), (
            f"Directory {BACKUP_DIR} does not exist. "
            "The backup destination directory must be present."
        )

    def test_backup_dir_writable(self):
        """Verify /backup directory is writable."""
        assert os.access(BACKUP_DIR, os.W_OK), (
            f"Directory {BACKUP_DIR} is not writable. "
            "Need write permissions to create the archive."
        )


class TestRequiredTools:
    """Tests for required tools being installed."""

    def test_gnu_tar_installed(self):
        """Verify GNU tar is installed."""
        result = subprocess.run(
            ["tar", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "tar command not found or failed"
        assert "GNU tar" in result.stdout, (
            f"Expected GNU tar, got: {result.stdout.split(chr(10))[0]}"
        )

    def test_gnu_find_installed(self):
        """Verify GNU find is installed."""
        result = subprocess.run(
            ["find", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "find command not found or failed"
        assert "GNU findutils" in result.stdout, (
            f"Expected GNU find, got: {result.stdout.split(chr(10))[0]}"
        )

    def test_gnu_xargs_installed(self):
        """Verify GNU xargs is installed."""
        result = subprocess.run(
            ["xargs", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "xargs command not found or failed"
        assert "GNU findutils" in result.stdout, (
            f"Expected GNU xargs, got: {result.stdout.split(chr(10))[0]}"
        )

    def test_gzip_available(self):
        """Verify gzip is available for tar compression."""
        result = subprocess.run(
            ["gzip", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gzip command not found or failed"


class TestFindOutputCorrect:
    """Verify that find correctly outputs all files (the bug is NOT in find)."""

    def test_find_with_print0_outputs_all_files(self):
        """Verify find -print0 outputs all 847 files correctly."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-print0"],
            capture_output=True
        )
        assert result.returncode == 0, f"find command failed: {result.stderr}"

        # Count null-separated entries
        output = result.stdout
        # Split by null byte and filter empty strings
        files = [f for f in output.split(b'\0') if f]

        assert len(files) == 847, (
            f"find -print0 should output 847 files, got {len(files)}. "
            "This confirms find is working correctly."
        )


class TestFileExtensions:
    """Verify the expected file types exist."""

    def test_txt_files_exist(self):
        """Verify .txt files exist in the data."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "*.txt"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        assert len(files) > 0, "Expected .txt files in /data/projects"

    def test_log_files_exist(self):
        """Verify .log files exist in the data."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "*.log"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        assert len(files) > 0, "Expected .log files in /data/projects"

    def test_dat_files_exist(self):
        """Verify .dat files exist in the data."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "*.dat"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        assert len(files) > 0, "Expected .dat files in /data/projects"

    def test_csv_files_exist(self):
        """Verify .csv files exist in the data."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "*.csv"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        assert len(files) > 0, "Expected .csv files in /data/projects"

    def test_json_files_exist(self):
        """Verify .json files exist in the data."""
        result = subprocess.run(
            ["find", DATA_PROJECTS, "-type", "f", "-name", "*.json"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        assert len(files) > 0, "Expected .json files in /data/projects"
