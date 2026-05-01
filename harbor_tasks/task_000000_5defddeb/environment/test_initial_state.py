# test_initial_state.py
"""
Tests to validate the initial state before the student fixes the incremental backup script.
"""

import os
import subprocess
import stat
import pytest

HOME = "/home/user"
BACKUP_DIR = f"{HOME}/backup"
DATA_DIR = f"{HOME}/data"
STATE_DIR = f"{BACKUP_DIR}/state"
ARCHIVES_DIR = f"{BACKUP_DIR}/archives"
INCREMENTAL_SCRIPT = f"{BACKUP_DIR}/incremental.sh"
FULL_SCRIPT = f"{BACKUP_DIR}/full.sh"
TIMESTAMP_FILE = f"{STATE_DIR}/last_incremental"
REFERENCE_FILE = f"{STATE_DIR}/reference"


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_home_directory_exists(self):
        assert os.path.isdir(HOME), f"Home directory {HOME} does not exist"

    def test_backup_directory_exists(self):
        assert os.path.isdir(BACKUP_DIR), f"Backup directory {BACKUP_DIR} does not exist"

    def test_data_directory_exists(self):
        assert os.path.isdir(DATA_DIR), f"Data directory {DATA_DIR} does not exist"

    def test_state_directory_exists(self):
        assert os.path.isdir(STATE_DIR), f"State directory {STATE_DIR} does not exist"

    def test_archives_directory_exists(self):
        assert os.path.isdir(ARCHIVES_DIR), f"Archives directory {ARCHIVES_DIR} does not exist"


class TestScriptsExist:
    """Test that backup scripts exist and are executable."""

    def test_incremental_script_exists(self):
        assert os.path.isfile(INCREMENTAL_SCRIPT), f"Incremental backup script {INCREMENTAL_SCRIPT} does not exist"

    def test_incremental_script_is_executable(self):
        mode = os.stat(INCREMENTAL_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, f"Incremental script {INCREMENTAL_SCRIPT} is not executable"

    def test_full_script_exists(self):
        assert os.path.isfile(FULL_SCRIPT), f"Full backup script {FULL_SCRIPT} does not exist"

    def test_full_script_is_executable(self):
        mode = os.stat(FULL_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, f"Full script {FULL_SCRIPT} is not executable"

    def test_incremental_script_is_bash(self):
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            first_line = f.readline()
        assert first_line.strip().startswith('#!/bin/bash') or first_line.strip().startswith('#!/usr/bin/env bash'), \
            f"Incremental script does not have bash shebang, got: {first_line.strip()}"


class TestDataDirectory:
    """Test that data directory has expected content."""

    def test_data_directory_has_files(self):
        files = []
        for root, dirs, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        assert len(files) >= 40, f"Data directory should have ~50 files, found {len(files)}"

    def test_data_directory_has_config_files(self):
        """Check for presence of config files (.conf, .yaml)."""
        config_files = []
        for root, dirs, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                if filename.endswith('.conf') or filename.endswith('.yaml'):
                    config_files.append(os.path.join(root, filename))
        assert len(config_files) > 0, "Data directory should contain .conf or .yaml config files"

    def test_data_directory_has_larger_files(self):
        """Check for presence of larger binary files (>100KB)."""
        large_files = []
        for root, dirs, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.getsize(filepath) > 100 * 1024:  # > 100KB
                    large_files.append(filepath)
        assert len(large_files) > 0, "Data directory should contain some larger binary files"


class TestStateFiles:
    """Test that state tracking files exist."""

    def test_reference_file_exists(self):
        assert os.path.isfile(REFERENCE_FILE), f"Reference file {REFERENCE_FILE} does not exist"

    def test_timestamp_file_exists(self):
        assert os.path.isfile(TIMESTAMP_FILE), f"Timestamp file {TIMESTAMP_FILE} does not exist"


class TestFilesNewerThanReference:
    """Test that there are enough files newer than reference to trigger the bug."""

    def test_sufficient_files_newer_than_reference(self):
        """There should be at least 25 files newer than the reference file."""
        result = subprocess.run(
            ['find', DATA_DIR, '-type', 'f', '-newer', REFERENCE_FILE],
            capture_output=True,
            text=True
        )
        newer_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(newer_files) >= 25, \
            f"Expected at least 25 files newer than reference, found {len(newer_files)}"


class TestIncrementalScriptContent:
    """Test that the incremental script has the expected buggy structure."""

    def test_script_contains_backgrounded_tar(self):
        """The buggy script should have tar backgrounded with &."""
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        # Look for the pattern of tar with & at end of line (the bug)
        assert '&' in content, "Script should contain backgrounding operator &"
        # More specific: tar command followed by &
        import re
        pattern = r'tar.*&\s*$'
        matches = re.findall(pattern, content, re.MULTILINE)
        assert len(matches) > 0, "Script should have tar command backgrounded with & (the bug)"

    def test_script_uses_find_and_tar(self):
        """Script should use find piped to tar for incrementals."""
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        assert 'find' in content, "Script should use find command"
        assert 'tar' in content, "Script should use tar command"
        assert '-print0' in content or 'print0' in content, "Script should use -print0 for null-separated output"
        assert '--null' in content, "Script should use --null option for tar"

    def test_script_uses_state_tracking(self):
        """Script should use timestamp/reference approach."""
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        assert 'STATE_DIR' in content or 'state' in content.lower(), "Script should reference state directory"
        assert 'reference' in content, "Script should use reference file for timestamp tracking"
        assert '-newer' in content, "Script should use -newer option for find"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_bash_available(self):
        result = subprocess.run(['which', 'bash'], capture_output=True)
        assert result.returncode == 0, "bash is not available"

    def test_tar_available(self):
        result = subprocess.run(['which', 'tar'], capture_output=True)
        assert result.returncode == 0, "tar is not available"

    def test_gzip_available(self):
        result = subprocess.run(['which', 'gzip'], capture_output=True)
        assert result.returncode == 0, "gzip is not available"

    def test_find_available(self):
        result = subprocess.run(['which', 'find'], capture_output=True)
        assert result.returncode == 0, "find is not available"

    def test_gnu_tar_version(self):
        """Verify we have GNU tar."""
        result = subprocess.run(['tar', '--version'], capture_output=True, text=True)
        assert result.returncode == 0, "Failed to get tar version"
        assert 'GNU tar' in result.stdout, f"Expected GNU tar, got: {result.stdout}"


class TestDirectoryPermissions:
    """Test that directories are writable."""

    def test_backup_dir_writable(self):
        assert os.access(BACKUP_DIR, os.W_OK), f"{BACKUP_DIR} is not writable"

    def test_archives_dir_writable(self):
        assert os.access(ARCHIVES_DIR, os.W_OK), f"{ARCHIVES_DIR} is not writable"

    def test_state_dir_writable(self):
        assert os.access(STATE_DIR, os.W_OK), f"{STATE_DIR} is not writable"
