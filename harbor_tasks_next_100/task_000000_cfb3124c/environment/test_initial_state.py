# test_initial_state.py
"""
Tests to validate the initial state of the operating system before the student
performs the disk usage breakdown task.
"""

import os
import subprocess
import pytest


class TestVarDataDirectory:
    """Tests for /var/data directory structure."""

    def test_var_data_exists(self):
        """Verify /var/data directory exists."""
        assert os.path.exists("/var/data"), "/var/data directory does not exist"
        assert os.path.isdir("/var/data"), "/var/data exists but is not a directory"

    def test_var_data_subdirectories_exist(self):
        """Verify all required subdirectories exist under /var/data."""
        required_subdirs = ["logs", "cache", "uploads", "backups", "tmp"]
        for subdir in required_subdirs:
            full_path = os.path.join("/var/data", subdir)
            assert os.path.exists(full_path), f"Subdirectory {full_path} does not exist"
            assert os.path.isdir(full_path), f"{full_path} exists but is not a directory"

    def test_var_data_subdirectories_have_content(self):
        """Verify subdirectories contain files (non-empty)."""
        required_subdirs = ["logs", "cache", "uploads", "backups", "tmp"]
        for subdir in required_subdirs:
            full_path = os.path.join("/var/data", subdir)
            # Check that directory is not empty (has some content)
            contents = os.listdir(full_path)
            assert len(contents) > 0, f"Subdirectory {full_path} is empty, expected files"

    def test_var_data_readable(self):
        """Verify /var/data is readable."""
        assert os.access("/var/data", os.R_OK), "/var/data is not readable"

    def test_var_data_subdirectories_readable(self):
        """Verify all subdirectories are readable."""
        required_subdirs = ["logs", "cache", "uploads", "backups", "tmp"]
        for subdir in required_subdirs:
            full_path = os.path.join("/var/data", subdir)
            assert os.access(full_path, os.R_OK), f"Subdirectory {full_path} is not readable"


class TestHomeUserDirectory:
    """Tests for /home/user directory."""

    def test_home_user_exists(self):
        """Verify /home/user directory exists."""
        assert os.path.exists("/home/user"), "/home/user directory does not exist"
        assert os.path.isdir("/home/user"), "/home/user exists but is not a directory"

    def test_home_user_writable(self):
        """Verify /home/user is writable."""
        assert os.access("/home/user", os.W_OK), "/home/user is not writable"

    def test_report_file_does_not_exist(self):
        """Verify /home/user/report.txt does not exist yet."""
        report_path = "/home/user/report.txt"
        assert not os.path.exists(report_path), (
            f"{report_path} already exists - it should not exist in initial state"
        )


class TestRequiredTools:
    """Tests for required command-line tools."""

    def test_du_available(self):
        """Verify du command is available."""
        result = subprocess.run(
            ["which", "du"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "du command is not available in PATH"

    def test_sort_available(self):
        """Verify sort command is available."""
        result = subprocess.run(
            ["which", "sort"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sort command is not available in PATH"

    def test_du_works_on_var_data(self):
        """Verify du can be run on /var/data."""
        result = subprocess.run(
            ["du", "-h", "--max-depth=1", "/var/data"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"du command failed on /var/data: {result.stderr}"
        )
        # Verify output contains expected subdirectory names
        output = result.stdout
        for subdir in ["logs", "cache", "uploads", "backups", "tmp"]:
            assert subdir in output, (
                f"du output does not contain expected subdirectory '{subdir}'"
            )


class TestDiskUsageSizes:
    """Tests to verify approximate disk usage sizes match expected values."""

    def get_dir_size_bytes(self, path):
        """Get directory size in bytes using du."""
        result = subprocess.run(
            ["du", "-sb", path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return int(result.stdout.split()[0])
        return 0

    def test_backups_is_largest(self):
        """Verify backups directory is the largest (~2.1GB)."""
        backups_size = self.get_dir_size_bytes("/var/data/backups")
        # Should be around 2.1GB (allow range 1.5GB to 3GB)
        min_size = 1.5 * 1024 * 1024 * 1024  # 1.5GB
        max_size = 3 * 1024 * 1024 * 1024    # 3GB
        assert min_size <= backups_size <= max_size, (
            f"backups directory size {backups_size} bytes is not in expected range "
            f"(1.5GB - 3GB for ~2.1GB expected)"
        )

    def test_cache_is_second_largest(self):
        """Verify cache directory is substantial (~1.2GB)."""
        cache_size = self.get_dir_size_bytes("/var/data/cache")
        # Should be around 1.2GB (allow range 800MB to 2GB)
        min_size = 800 * 1024 * 1024   # 800MB
        max_size = 2 * 1024 * 1024 * 1024  # 2GB
        assert min_size <= cache_size <= max_size, (
            f"cache directory size {cache_size} bytes is not in expected range "
            f"(800MB - 2GB for ~1.2GB expected)"
        )

    def test_tmp_is_smallest(self):
        """Verify tmp directory is the smallest (~50MB)."""
        tmp_size = self.get_dir_size_bytes("/var/data/tmp")
        # Should be around 50MB (allow range 10MB to 200MB)
        min_size = 10 * 1024 * 1024   # 10MB
        max_size = 200 * 1024 * 1024  # 200MB
        assert min_size <= tmp_size <= max_size, (
            f"tmp directory size {tmp_size} bytes is not in expected range "
            f"(10MB - 200MB for ~50MB expected)"
        )

    def test_size_ordering(self):
        """Verify relative size ordering: backups > cache > logs > uploads > tmp."""
        sizes = {
            "backups": self.get_dir_size_bytes("/var/data/backups"),
            "cache": self.get_dir_size_bytes("/var/data/cache"),
            "logs": self.get_dir_size_bytes("/var/data/logs"),
            "uploads": self.get_dir_size_bytes("/var/data/uploads"),
            "tmp": self.get_dir_size_bytes("/var/data/tmp"),
        }

        # backups should be largest
        assert sizes["backups"] > sizes["cache"], (
            f"backups ({sizes['backups']}) should be larger than cache ({sizes['cache']})"
        )
        # cache should be larger than logs
        assert sizes["cache"] > sizes["logs"], (
            f"cache ({sizes['cache']}) should be larger than logs ({sizes['logs']})"
        )
        # tmp should be smallest
        assert sizes["tmp"] < sizes["uploads"], (
            f"tmp ({sizes['tmp']}) should be smaller than uploads ({sizes['uploads']})"
        )
        assert sizes["tmp"] < sizes["logs"], (
            f"tmp ({sizes['tmp']}) should be smaller than logs ({sizes['logs']})"
        )
