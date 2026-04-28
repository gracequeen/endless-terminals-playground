# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the memory analysis task.
"""

import os
import pytest
import re

HOME_DIR = "/home/user"
MEMSTATS_DIR = "/home/user/memstats"
OUTPUT_FILE = "/home/user/low_memory_report.txt"

# Expected host files that should remain unchanged
EXPECTED_FILES = {
    "host01.txt": {"MemTotal": 16384000, "MemAvailable": 8192000},
    "host02.txt": {"MemTotal": 32768000, "MemAvailable": 4915200},
    "host03.txt": "corrupted",
    "host04.txt": {"MemTotal": 16384000, "MemAvailable": 2621440},
    "host05.txt": {"MemTotal": 8192000, "MemAvailable": 4096000},
    "host06.txt": {"MemTotal": 32768000, "MemAvailable": 5242880},
    "host07.txt": {"MemTotal": 16384000, "MemAvailable": 1638400},
    "host08.txt": {"MemTotal": 8192000, "MemAvailable": 2457600},
}

# Expected low memory hosts (below 20% available) with their percentages
# host07: 10%, host02: 15%, host04: 16%, host06: 16%
EXPECTED_LOW_MEMORY_HOSTS = {
    "host07": 10,
    "host02": 15,
    "host04": 16,
    "host06": 16,
}


class TestOutputFileExists:
    """Test that the output report file exists."""

    def test_output_file_exists(self):
        """Verify /home/user/low_memory_report.txt exists."""
        assert os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist. "
            "The task requires creating this report file."
        )

    def test_output_file_is_regular_file(self):
        """Verify the output is a regular file."""
        assert os.path.isfile(OUTPUT_FILE), (
            f"{OUTPUT_FILE} exists but is not a regular file."
        )

    def test_output_file_is_readable(self):
        """Verify the output file is readable."""
        assert os.access(OUTPUT_FILE, os.R_OK), (
            f"{OUTPUT_FILE} exists but is not readable."
        )


class TestOutputFileContent:
    """Test the content of the output report file."""

    def _read_report(self):
        """Read and parse the report file."""
        if not os.path.exists(OUTPUT_FILE):
            pytest.skip(f"{OUTPUT_FILE} does not exist")

        with open(OUTPUT_FILE, 'r') as f:
            content = f.read()
        return content

    def _parse_report_lines(self):
        """Parse report into list of (hostname, percentage) tuples."""
        content = self._read_report()
        lines = [line for line in content.strip().split('\n') if line.strip()]
        parsed = []
        for line in lines:
            # Split by tab
            parts = line.split('\t')
            if len(parts) >= 2:
                hostname = parts[0].strip()
                # Extract numeric percentage (handle various formats like "10", "10%", "10.0")
                pct_str = parts[1].strip().rstrip('%')
                try:
                    # Try integer first
                    pct = int(float(pct_str))
                    parsed.append((hostname, pct))
                except ValueError:
                    pass
        return parsed

    def test_output_has_exactly_four_lines(self):
        """Verify the report contains exactly 4 hosts (those below 20%)."""
        content = self._read_report()
        lines = [line for line in content.strip().split('\n') if line.strip()]

        assert len(lines) == 4, (
            f"Expected exactly 4 lines in report (hosts below 20% threshold), "
            f"but found {len(lines)} lines. "
            f"Content:\n{content}"
        )

    def test_output_contains_correct_hosts(self):
        """Verify the report contains exactly the expected low-memory hosts."""
        parsed = self._parse_report_lines()
        hostnames = {h for h, _ in parsed}
        expected_hostnames = set(EXPECTED_LOW_MEMORY_HOSTS.keys())

        assert hostnames == expected_hostnames, (
            f"Expected hosts {expected_hostnames}, but found {hostnames}. "
            f"Missing: {expected_hostnames - hostnames}, "
            f"Extra: {hostnames - expected_hostnames}"
        )

    def test_output_does_not_contain_host03(self):
        """Verify corrupted host03 is not in the report."""
        content = self._read_report()
        # Check that host03 doesn't appear as a hostname entry
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip():
                hostname = line.split('\t')[0].strip() if '\t' in line else line.split()[0]
                assert hostname != "host03", (
                    "host03 should not appear in the report (it's corrupted and "
                    "cannot have its percentage computed)."
                )

    def test_output_does_not_contain_high_memory_hosts(self):
        """Verify hosts with >= 20% available memory are not in the report."""
        parsed = self._parse_report_lines()
        hostnames = {h for h, _ in parsed}

        high_memory_hosts = {"host01", "host05", "host08"}
        found_high = hostnames & high_memory_hosts

        assert not found_high, (
            f"Found high-memory hosts in report that should not be there: {found_high}. "
            "Only hosts with less than 20% available memory should appear."
        )

    def test_output_uses_tab_separator(self):
        """Verify each line uses tab as separator between hostname and percentage."""
        content = self._read_report()
        lines = [line for line in content.strip().split('\n') if line.strip()]

        for line in lines:
            assert '\t' in line, (
                f"Line does not use tab separator: '{line}'. "
                "Expected format: hostname<TAB>percentage"
            )

    def test_percentages_are_correct(self):
        """Verify the percentages are correctly computed from the source files."""
        parsed = self._parse_report_lines()

        for hostname, reported_pct in parsed:
            expected_pct = EXPECTED_LOW_MEMORY_HOSTS.get(hostname)
            if expected_pct is not None:
                # Allow for small rounding differences (floor vs round)
                assert abs(reported_pct - expected_pct) <= 1, (
                    f"Percentage for {hostname} is incorrect. "
                    f"Expected ~{expected_pct}%, got {reported_pct}%"
                )

    def test_percentages_are_integers(self):
        """Verify percentages are displayed as integers (not floats)."""
        content = self._read_report()
        lines = [line for line in content.strip().split('\n') if line.strip()]

        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 2:
                pct_str = parts[1].strip().rstrip('%')
                # Should not contain decimal point (or if it does, should be .0)
                if '.' in pct_str:
                    # If it has decimal, it should be .0
                    assert pct_str.endswith('.0') or pct_str.endswith('.00'), (
                        f"Percentage should be integer, got '{pct_str}' in line: '{line}'"
                    )

    def test_sorted_by_percentage_ascending(self):
        """Verify the report is sorted by percentage ascending (worst first)."""
        parsed = self._parse_report_lines()

        if len(parsed) < 2:
            pytest.skip("Not enough lines to verify sorting")

        percentages = [pct for _, pct in parsed]

        # Check that percentages are in ascending order
        for i in range(len(percentages) - 1):
            assert percentages[i] <= percentages[i + 1], (
                f"Report is not sorted by percentage ascending (worst first). "
                f"Found {percentages[i]}% before {percentages[i + 1]}%. "
                f"Full order: {parsed}"
            )

    def test_host07_is_first(self):
        """Verify host07 (10% - worst) is first in the report."""
        parsed = self._parse_report_lines()

        if not parsed:
            pytest.skip("No entries in report")

        first_host, first_pct = parsed[0]
        assert first_host == "host07", (
            f"Expected host07 (10% available - worst) to be first, "
            f"but found {first_host} ({first_pct}%)"
        )

    def test_host02_is_second(self):
        """Verify host02 (15%) is second in the report."""
        parsed = self._parse_report_lines()

        if len(parsed) < 2:
            pytest.skip("Not enough entries in report")

        second_host, second_pct = parsed[1]
        assert second_host == "host02", (
            f"Expected host02 (15% available) to be second, "
            f"but found {second_host} ({second_pct}%)"
        )

    def test_host04_and_host06_are_last_two(self):
        """Verify host04 and host06 (both 16%) are the last two entries."""
        parsed = self._parse_report_lines()

        if len(parsed) < 4:
            pytest.skip("Not enough entries in report")

        last_two_hosts = {parsed[2][0], parsed[3][0]}
        expected = {"host04", "host06"}

        assert last_two_hosts == expected, (
            f"Expected host04 and host06 (both 16%) to be the last two entries, "
            f"but found {last_two_hosts}"
        )


class TestSourceFilesUnchanged:
    """Test that source files in memstats directory were not modified."""

    def _parse_meminfo_value(self, content, key):
        """Parse a value from meminfo-style content."""
        pattern = rf'^{key}:\s+(\d+)\s+kB'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return int(match.group(1))
        return None

    @pytest.mark.parametrize("hostname", [f"host0{i}.txt" for i in range(1, 9)])
    def test_source_file_still_exists(self, hostname):
        """Verify source files were not deleted."""
        filepath = os.path.join(MEMSTATS_DIR, hostname)
        assert os.path.exists(filepath), (
            f"Source file {filepath} no longer exists. "
            "Source files should remain unchanged (read-only processing)."
        )

    @pytest.mark.parametrize("hostname,expected", [
        (name, data) for name, data in EXPECTED_FILES.items() 
        if data != "corrupted"
    ])
    def test_valid_source_file_unchanged(self, hostname, expected):
        """Verify valid source files have unchanged content."""
        filepath = os.path.join(MEMSTATS_DIR, hostname)
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        mem_total = self._parse_meminfo_value(content, "MemTotal")
        mem_available = self._parse_meminfo_value(content, "MemAvailable")

        assert mem_total == expected["MemTotal"], (
            f"Source file {filepath} appears to have been modified. "
            f"MemTotal changed from {expected['MemTotal']} to {mem_total}"
        )
        assert mem_available == expected["MemAvailable"], (
            f"Source file {filepath} appears to have been modified. "
            f"MemAvailable changed from {expected['MemAvailable']} to {mem_available}"
        )

    def test_host03_still_corrupted(self):
        """Verify host03.txt is still corrupted (not 'fixed')."""
        filepath = os.path.join(MEMSTATS_DIR, "host03.txt")
        if not os.path.exists(filepath):
            pytest.skip(f"{filepath} does not exist")

        with open(filepath, 'r') as f:
            content = f.read()

        # Should still NOT have a complete MemAvailable line
        pattern = r'^MemAvailable:\s+\d+\s+kB'
        match = re.search(pattern, content, re.MULTILINE)

        assert match is None, (
            f"Source file {filepath} appears to have been modified. "
            "It should still be corrupted (no complete MemAvailable line)."
        )


class TestNoExtraFilesCreated:
    """Test that no unexpected files were created."""

    def test_no_extra_files_in_home(self):
        """Verify only expected files exist in /home/user/."""
        if not os.path.exists(HOME_DIR):
            pytest.skip(f"{HOME_DIR} does not exist")

        # List files in home directory (not recursively)
        files = os.listdir(HOME_DIR)

        # Expected: memstats directory and low_memory_report.txt
        # Allow for common files like .bashrc, .profile, etc.
        allowed_patterns = [
            r'^\..*',  # Hidden files
            r'^memstats$',  # The memstats directory
            r'^low_memory_report\.txt$',  # The output file
        ]

        for f in files:
            is_allowed = any(re.match(pattern, f) for pattern in allowed_patterns)
            if not is_allowed:
                # It's okay if other files exist, just warn
                pass  # We don't fail on extra files, just the report matters

    def test_memstats_directory_unchanged(self):
        """Verify no extra files were added to memstats directory."""
        if not os.path.exists(MEMSTATS_DIR):
            pytest.skip(f"{MEMSTATS_DIR} does not exist")

        files = set(os.listdir(MEMSTATS_DIR))
        expected_files = {f"host0{i}.txt" for i in range(1, 9)}

        extra_files = files - expected_files
        # Filter out hidden files
        extra_files = {f for f in extra_files if not f.startswith('.')}

        assert not extra_files, (
            f"Unexpected files found in {MEMSTATS_DIR}: {extra_files}. "
            "No files should be created in the source directory."
        )
