# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the memory analysis task.
"""

import os
import pytest
import re

HOME_DIR = "/home/user"
MEMSTATS_DIR = "/home/user/memstats"

# Expected file contents based on truth value
EXPECTED_FILES = {
    "host01.txt": {"MemTotal": 16384000, "MemAvailable": 8192000},
    "host02.txt": {"MemTotal": 32768000, "MemAvailable": 4915200},
    "host03.txt": "corrupted",  # Special case - corrupted file
    "host04.txt": {"MemTotal": 16384000, "MemAvailable": 2621440},
    "host05.txt": {"MemTotal": 8192000, "MemAvailable": 4096000},
    "host06.txt": {"MemTotal": 32768000, "MemAvailable": 5242880},
    "host07.txt": {"MemTotal": 16384000, "MemAvailable": 1638400},
    "host08.txt": {"MemTotal": 8192000, "MemAvailable": 2457600},
}


class TestMemstatsDirectoryExists:
    """Test that the memstats directory exists and is accessible."""

    def test_memstats_directory_exists(self):
        """Verify /home/user/memstats/ directory exists."""
        assert os.path.exists(MEMSTATS_DIR), (
            f"Directory {MEMSTATS_DIR} does not exist. "
            "The memstats directory must be present for the task."
        )

    def test_memstats_is_directory(self):
        """Verify /home/user/memstats/ is a directory, not a file."""
        assert os.path.isdir(MEMSTATS_DIR), (
            f"{MEMSTATS_DIR} exists but is not a directory. "
            "It must be a directory containing host memory stat files."
        )


class TestHostFilesExist:
    """Test that all 8 host files exist in the memstats directory."""

    @pytest.mark.parametrize("hostname", [f"host0{i}.txt" for i in range(1, 9)])
    def test_host_file_exists(self, hostname):
        """Verify each host file (host01.txt through host08.txt) exists."""
        filepath = os.path.join(MEMSTATS_DIR, hostname)
        assert os.path.exists(filepath), (
            f"File {filepath} does not exist. "
            f"Expected 8 host files (host01.txt through host08.txt) in {MEMSTATS_DIR}."
        )

    @pytest.mark.parametrize("hostname", [f"host0{i}.txt" for i in range(1, 9)])
    def test_host_file_is_file(self, hostname):
        """Verify each host file is a regular file."""
        filepath = os.path.join(MEMSTATS_DIR, hostname)
        assert os.path.isfile(filepath), (
            f"{filepath} exists but is not a regular file. "
            "Each host file must be a regular file containing meminfo data."
        )

    def test_exactly_eight_host_files(self):
        """Verify there are exactly 8 host files in the directory."""
        if not os.path.isdir(MEMSTATS_DIR):
            pytest.skip(f"{MEMSTATS_DIR} does not exist")

        txt_files = [f for f in os.listdir(MEMSTATS_DIR) if f.endswith('.txt')]
        host_files = [f for f in txt_files if re.match(r'host0[1-8]\.txt$', f)]

        assert len(host_files) == 8, (
            f"Expected exactly 8 host files (host01.txt through host08.txt), "
            f"found {len(host_files)}: {sorted(host_files)}"
        )


class TestValidHostFileContents:
    """Test that valid host files contain proper meminfo-style content."""

    def _parse_meminfo_value(self, content, key):
        """Parse a value from meminfo-style content."""
        pattern = rf'^{key}:\s+(\d+)\s+kB'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return int(match.group(1))
        return None

    @pytest.mark.parametrize("hostname,expected", [
        (name, data) for name, data in EXPECTED_FILES.items() 
        if data != "corrupted"
    ])
    def test_valid_host_has_memtotal(self, hostname, expected):
        """Verify valid host files contain MemTotal line."""
        filepath = os.path.join(MEMSTATS_DIR, hostname)
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        mem_total = self._parse_meminfo_value(content, "MemTotal")
        assert mem_total is not None, (
            f"File {filepath} does not contain a valid MemTotal line. "
            "Expected format: 'MemTotal:       <value> kB'"
        )
        assert mem_total == expected["MemTotal"], (
            f"File {filepath} has unexpected MemTotal value. "
            f"Expected {expected['MemTotal']} kB, found {mem_total} kB"
        )

    @pytest.mark.parametrize("hostname,expected", [
        (name, data) for name, data in EXPECTED_FILES.items() 
        if data != "corrupted"
    ])
    def test_valid_host_has_memavailable(self, hostname, expected):
        """Verify valid host files contain MemAvailable line."""
        filepath = os.path.join(MEMSTATS_DIR, hostname)
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        mem_available = self._parse_meminfo_value(content, "MemAvailable")
        assert mem_available is not None, (
            f"File {filepath} does not contain a valid MemAvailable line. "
            "Expected format: 'MemAvailable:   <value> kB'"
        )
        assert mem_available == expected["MemAvailable"], (
            f"File {filepath} has unexpected MemAvailable value. "
            f"Expected {expected['MemAvailable']} kB, found {mem_available} kB"
        )


class TestCorruptedHostFile:
    """Test that host03.txt is corrupted as expected."""

    def test_host03_exists(self):
        """Verify host03.txt exists."""
        filepath = os.path.join(MEMSTATS_DIR, "host03.txt")
        assert os.path.exists(filepath), (
            f"File {filepath} does not exist. "
            "host03.txt must exist (even though it's corrupted)."
        )

    def test_host03_has_memtotal(self):
        """Verify host03.txt has MemTotal line."""
        filepath = os.path.join(MEMSTATS_DIR, "host03.txt")
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        assert "MemTotal:" in content, (
            f"File {filepath} should contain a MemTotal line "
            "(even though it's corrupted, it should have at least this)."
        )

    def test_host03_missing_complete_memavailable(self):
        """Verify host03.txt does NOT have a complete MemAvailable line."""
        filepath = os.path.join(MEMSTATS_DIR, "host03.txt")
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        # Check for a complete MemAvailable line
        pattern = r'^MemAvailable:\s+\d+\s+kB'
        match = re.search(pattern, content, re.MULTILINE)

        assert match is None, (
            f"File {filepath} should be corrupted and NOT contain a complete "
            "MemAvailable line, but a complete line was found. "
            "The file should have a truncated 'MemAvai' instead."
        )

    def test_host03_has_truncated_memavailable(self):
        """Verify host03.txt has truncated MemAvai text."""
        filepath = os.path.join(MEMSTATS_DIR, "host03.txt")
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        # Should have "MemAvai" but not a complete "MemAvailable:" line with value
        assert "MemAvai" in content, (
            f"File {filepath} should contain truncated 'MemAvai' text "
            "to simulate corruption."
        )


class TestHomeDirectoryWritable:
    """Test that the home directory is writable for output."""

    def test_home_directory_exists(self):
        """Verify /home/user/ directory exists."""
        assert os.path.exists(HOME_DIR), (
            f"Home directory {HOME_DIR} does not exist."
        )

    def test_home_directory_is_writable(self):
        """Verify /home/user/ is writable."""
        assert os.access(HOME_DIR, os.W_OK), (
            f"Home directory {HOME_DIR} is not writable. "
            "The output file needs to be created here."
        )


class TestOutputFileDoesNotExist:
    """Test that the output file does not already exist."""

    def test_output_file_does_not_exist(self):
        """Verify /home/user/low_memory_report.txt does not exist yet."""
        output_path = os.path.join(HOME_DIR, "low_memory_report.txt")
        assert not os.path.exists(output_path), (
            f"Output file {output_path} already exists. "
            "It should not exist before the student performs the task."
        )


class TestRequiredToolsAvailable:
    """Test that required command-line tools are available."""

    @pytest.mark.parametrize("tool", ["bash", "awk", "sed", "grep", "sort", "python3"])
    def test_tool_available(self, tool):
        """Verify required tools are available in PATH."""
        import shutil
        path = shutil.which(tool)
        assert path is not None, (
            f"Required tool '{tool}' is not available in PATH. "
            "This tool may be needed to complete the task."
        )
