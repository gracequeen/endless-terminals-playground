# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the backup script fix task.
"""

import os
import stat
import subprocess
import pytest


HOME = "/home/user"
BACKUP_DIR = os.path.join(HOME, "backup")
COMPRESS_SCRIPT = os.path.join(BACKUP_DIR, "compress.sh")
SIMULATE_SCRIPT = os.path.join(BACKUP_DIR, "simulate_remote_extract.sh")
TESTDATA_DIR = os.path.join(BACKUP_DIR, "testdata")


class TestCompressScriptExists:
    """Tests for /home/user/backup/compress.sh"""

    def test_compress_script_exists(self):
        """compress.sh must exist"""
        assert os.path.exists(COMPRESS_SCRIPT), (
            f"compress.sh not found at {COMPRESS_SCRIPT}"
        )

    def test_compress_script_is_file(self):
        """compress.sh must be a regular file"""
        assert os.path.isfile(COMPRESS_SCRIPT), (
            f"{COMPRESS_SCRIPT} exists but is not a regular file"
        )

    def test_compress_script_is_executable(self):
        """compress.sh must be executable"""
        mode = os.stat(COMPRESS_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, (
            f"{COMPRESS_SCRIPT} is not executable by owner"
        )

    def test_compress_script_has_shebang(self):
        """compress.sh must start with #!/bin/bash"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash", (
            f"compress.sh should have '#!/bin/bash' shebang, got: {first_line}"
        )

    def test_compress_script_has_set_e(self):
        """compress.sh must contain 'set -e'"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "set -e" in content, (
            "compress.sh should contain 'set -e' for error handling"
        )

    def test_compress_script_has_rsyncable_flag(self):
        """compress.sh must currently contain --rsyncable flag (the bug)"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "--rsyncable" in content, (
            "compress.sh should contain '--rsyncable' flag (this is the bug to fix)"
        )

    def test_compress_script_uses_gzip(self):
        """compress.sh must use gzip command"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "gzip" in content, (
            "compress.sh should use gzip for compression"
        )

    def test_compress_script_uses_tar(self):
        """compress.sh must use tar command"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "tar" in content, (
            "compress.sh should use tar for archiving"
        )


class TestSimulateRemoteExtractScript:
    """Tests for /home/user/backup/simulate_remote_extract.sh"""

    def test_simulate_script_exists(self):
        """simulate_remote_extract.sh must exist"""
        assert os.path.exists(SIMULATE_SCRIPT), (
            f"simulate_remote_extract.sh not found at {SIMULATE_SCRIPT}"
        )

    def test_simulate_script_is_file(self):
        """simulate_remote_extract.sh must be a regular file"""
        assert os.path.isfile(SIMULATE_SCRIPT), (
            f"{SIMULATE_SCRIPT} exists but is not a regular file"
        )

    def test_simulate_script_is_executable(self):
        """simulate_remote_extract.sh must be executable"""
        mode = os.stat(SIMULATE_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, (
            f"{SIMULATE_SCRIPT} is not executable by owner"
        )

    def test_simulate_script_is_read_only(self):
        """simulate_remote_extract.sh should be read-only (chmod 555)"""
        mode = os.stat(SIMULATE_SCRIPT).st_mode
        # Check that write bits are not set for user, group, or others
        write_bits = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
        assert not (mode & write_bits), (
            f"{SIMULATE_SCRIPT} should be read-only (chmod 555) but has write permissions"
        )

    def test_simulate_script_checks_rsyncable(self):
        """simulate_remote_extract.sh must check for rsyncable markers"""
        with open(SIMULATE_SCRIPT, 'r') as f:
            content = f.read()
        assert "00 00 ff ff" in content, (
            "simulate_remote_extract.sh should check for rsyncable sync flush markers"
        )

    def test_simulate_script_has_size_check(self):
        """simulate_remote_extract.sh must have 2MB size threshold"""
        with open(SIMULATE_SCRIPT, 'r') as f:
            content = f.read()
        assert "2000000" in content, (
            "simulate_remote_extract.sh should have 2MB (2000000 bytes) threshold check"
        )


class TestTestDataDirectory:
    """Tests for /home/user/backup/testdata/"""

    def test_testdata_dir_exists(self):
        """testdata directory must exist"""
        assert os.path.exists(TESTDATA_DIR), (
            f"testdata directory not found at {TESTDATA_DIR}"
        )

    def test_testdata_is_directory(self):
        """testdata must be a directory"""
        assert os.path.isdir(TESTDATA_DIR), (
            f"{TESTDATA_DIR} exists but is not a directory"
        )

    def test_testdata_has_files(self):
        """testdata directory must contain files"""
        files = []
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            files.extend(filenames)
        assert len(files) > 0, (
            f"{TESTDATA_DIR} should contain test files but is empty"
        )

    def test_testdata_has_approximately_50_files(self):
        """testdata directory should contain ~50 files"""
        files = []
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            files.extend(filenames)
        # Allow some flexibility: 40-60 files
        assert 40 <= len(files) <= 60, (
            f"{TESTDATA_DIR} should contain ~50 files, found {len(files)}"
        )

    def test_testdata_has_approximately_8mb(self):
        """testdata directory should total ~8MB uncompressed"""
        total_size = 0
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        # Allow 6MB to 10MB range
        min_size = 6 * 1024 * 1024  # 6MB
        max_size = 10 * 1024 * 1024  # 10MB
        assert min_size <= total_size <= max_size, (
            f"{TESTDATA_DIR} should total ~8MB, found {total_size / (1024*1024):.2f}MB"
        )


class TestBackupDirectory:
    """Tests for /home/user/backup/ directory"""

    def test_backup_dir_exists(self):
        """backup directory must exist"""
        assert os.path.exists(BACKUP_DIR), (
            f"backup directory not found at {BACKUP_DIR}"
        )

    def test_backup_dir_is_directory(self):
        """backup must be a directory"""
        assert os.path.isdir(BACKUP_DIR), (
            f"{BACKUP_DIR} exists but is not a directory"
        )

    def test_backup_dir_is_writable(self):
        """backup directory must be writable"""
        assert os.access(BACKUP_DIR, os.W_OK), (
            f"{BACKUP_DIR} should be writable"
        )


class TestRequiredTools:
    """Tests for required system tools"""

    def test_bash_available(self):
        """bash must be available"""
        result = subprocess.run(
            ["which", "bash"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "bash is not available on the system"

    def test_tar_available(self):
        """tar must be available"""
        result = subprocess.run(
            ["which", "tar"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "tar is not available on the system"

    def test_gzip_available(self):
        """gzip must be available"""
        result = subprocess.run(
            ["which", "gzip"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gzip is not available on the system"

    def test_gunzip_available(self):
        """gunzip must be available"""
        result = subprocess.run(
            ["which", "gunzip"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gunzip is not available on the system"

    def test_zcat_available(self):
        """zcat must be available"""
        result = subprocess.run(
            ["which", "zcat"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "zcat is not available on the system"

    def test_gzip_supports_rsyncable(self):
        """gzip must support --rsyncable flag"""
        result = subprocess.run(
            ["gzip", "--help"],
            capture_output=True,
            text=True
        )
        # Check both stdout and stderr as help may go to either
        output = result.stdout + result.stderr
        assert "rsyncable" in output.lower(), (
            "gzip does not appear to support --rsyncable flag"
        )

    def test_gzip_version(self):
        """gzip should be version 1.12 or compatible"""
        result = subprocess.run(
            ["gzip", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get gzip version"
        # Just verify we can get version info, exact version may vary
        assert "gzip" in result.stdout.lower(), (
            "Unexpected gzip version output"
        )


class TestBugReproduction:
    """Tests to verify the bug can be reproduced with current setup"""

    def test_compress_script_runs(self):
        """compress.sh should be runnable"""
        result = subprocess.run(
            ["bash", "-n", COMPRESS_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"compress.sh has syntax errors: {result.stderr}"
        )

    def test_simulate_script_runs(self):
        """simulate_remote_extract.sh should be runnable (syntax check)"""
        result = subprocess.run(
            ["bash", "-n", SIMULATE_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"simulate_remote_extract.sh has syntax errors: {result.stderr}"
        )
