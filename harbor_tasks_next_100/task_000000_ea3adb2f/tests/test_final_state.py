# test_final_state.py
"""
Tests to validate the final state after the student fixes the solver.conf file.
This verifies the bug has been fixed and all other content remains unchanged.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Test the final state of the filesystem after the fix is applied."""

    CONF_FILE = "/home/user/optim/solver.conf"
    CONF_DIR = "/home/user/optim"

    def test_optim_directory_exists(self):
        """Verify the /home/user/optim directory still exists."""
        assert os.path.isdir(self.CONF_DIR), \
            f"Directory {self.CONF_DIR} does not exist"

    def test_solver_conf_exists(self):
        """Verify solver.conf file still exists."""
        assert os.path.isfile(self.CONF_FILE), \
            f"Config file {self.CONF_FILE} does not exist"

    def test_solver_conf_is_readable(self):
        """Verify solver.conf is readable."""
        assert os.access(self.CONF_FILE, os.R_OK), \
            f"Config file {self.CONF_FILE} is not readable"

    def test_no_quote_characters_in_file(self):
        """Verify there are no quote characters anywhere in the file (anti-shortcut guard)."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        quote_count = content.count('"')
        assert quote_count == 0, \
            f"Config file should have no quote characters, but found {quote_count}"

    def test_no_quote_characters_via_grep(self):
        """Verify no quote characters using grep (anti-shortcut guard)."""
        result = subprocess.run(
            ['grep', '-c', '"', self.CONF_FILE],
            capture_output=True,
            text=True
        )
        # grep -c returns 1 (exit code) when no matches found, 0 when matches found
        # The count output will be "0" if no matches
        if result.returncode == 0:
            # Matches were found
            count = int(result.stdout.strip())
            assert count == 0, \
                f"grep found {count} lines with quote characters - all quotes should be removed"
        # returncode 1 means no matches, which is what we want

    def test_max_iterations_line_is_correct(self):
        """Verify the max_iterations line is now correct without the trailing quote."""
        with open(self.CONF_FILE, 'r') as f:
            lines = f.readlines()

        # Find the max_iterations line
        max_iter_lines = [line.strip() for line in lines if 'max_iterations' in line]
        assert len(max_iter_lines) == 1, \
            f"Expected exactly one max_iterations line, found {len(max_iter_lines)}"

        max_iter_line = max_iter_lines[0]
        assert max_iter_line == "max_iterations = 5000", \
            f"Expected 'max_iterations = 5000' but found: '{max_iter_line}'"

    def test_max_iterations_via_grep(self):
        """Verify max_iterations line matches exactly using grep (anti-shortcut guard)."""
        result = subprocess.run(
            ['grep', 'max_iterations = 5000$', self.CONF_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "grep for 'max_iterations = 5000$' should match exactly one line"

        # Count the matches
        matches = [line for line in result.stdout.strip().split('\n') if line]
        assert len(matches) == 1, \
            f"Expected exactly one match for 'max_iterations = 5000$', found {len(matches)}"

    def test_value_is_5000(self):
        """Verify the max_iterations value is still 5000 (not changed to another number)."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()

        # Check that 5000 appears in the context of max_iterations
        assert "max_iterations = 5000" in content, \
            "The max_iterations value must be 5000"

    def test_comment_header_preserved(self):
        """Verify the comment header is preserved."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "# Solver configuration" in content, \
            "Config file is missing the '# Solver configuration' comment header - it should be preserved"

    def test_algorithm_setting_preserved(self):
        """Verify the algorithm setting is preserved."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "algorithm = simplex" in content, \
            "Config file is missing 'algorithm = simplex' setting - it should be preserved"

    def test_tolerance_setting_preserved(self):
        """Verify the tolerance setting is preserved."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "tolerance = 1e-8" in content, \
            "Config file is missing 'tolerance = 1e-8' setting - it should be preserved"

    def test_verbose_setting_preserved(self):
        """Verify the verbose setting is preserved."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "verbose = false" in content, \
            "Config file is missing 'verbose = false' setting - it should be preserved"

    def test_file_has_expected_structure(self):
        """Verify the file maintains its expected structure with all settings."""
        with open(self.CONF_FILE, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        # Should have 5 non-empty lines: comment + 4 settings
        expected_content = [
            "# Solver configuration",
            "algorithm = simplex",
            "max_iterations = 5000",
            "tolerance = 1e-8",
            "verbose = false"
        ]

        # Check each expected line is present
        for expected in expected_content:
            assert expected in lines, \
                f"Missing expected line: '{expected}'"

    def test_no_extra_content_added(self):
        """Verify no extra content was added to the file."""
        with open(self.CONF_FILE, 'r') as f:
            lines = f.readlines()

        # Original file had 5 lines, fixed file should still have 5 lines
        assert len(lines) == 5, \
            f"Expected 5 lines in config file (same as original), found {len(lines)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
