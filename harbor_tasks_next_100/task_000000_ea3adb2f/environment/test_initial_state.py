# test_initial_state.py
"""
Tests to validate the initial state before the student fixes the solver.conf file.
This verifies the buggy state exists as expected.
"""

import os
import pytest


class TestInitialState:
    """Test the initial state of the filesystem before the fix is applied."""

    CONF_FILE = "/home/user/optim/solver.conf"
    CONF_DIR = "/home/user/optim"

    def test_optim_directory_exists(self):
        """Verify the /home/user/optim directory exists."""
        assert os.path.isdir(self.CONF_DIR), \
            f"Directory {self.CONF_DIR} does not exist"

    def test_optim_directory_is_writable(self):
        """Verify the /home/user/optim directory is writable."""
        assert os.access(self.CONF_DIR, os.W_OK), \
            f"Directory {self.CONF_DIR} is not writable"

    def test_solver_conf_exists(self):
        """Verify solver.conf file exists."""
        assert os.path.isfile(self.CONF_FILE), \
            f"Config file {self.CONF_FILE} does not exist"

    def test_solver_conf_is_readable(self):
        """Verify solver.conf is readable."""
        assert os.access(self.CONF_FILE, os.R_OK), \
            f"Config file {self.CONF_FILE} is not readable"

    def test_solver_conf_is_writable(self):
        """Verify solver.conf is writable (needed for the fix)."""
        assert os.access(self.CONF_FILE, os.W_OK), \
            f"Config file {self.CONF_FILE} is not writable"

    def test_solver_conf_has_comment_header(self):
        """Verify the config file has the expected comment header."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "# Solver configuration" in content, \
            "Config file is missing the '# Solver configuration' comment header"

    def test_solver_conf_has_algorithm_setting(self):
        """Verify the config file has the algorithm setting."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "algorithm = simplex" in content, \
            "Config file is missing 'algorithm = simplex' setting"

    def test_solver_conf_has_buggy_max_iterations(self):
        """Verify the config file has the buggy max_iterations line with trailing quote."""
        with open(self.CONF_FILE, 'r') as f:
            lines = f.readlines()

        # Find the max_iterations line
        max_iter_lines = [line for line in lines if 'max_iterations' in line]
        assert len(max_iter_lines) == 1, \
            f"Expected exactly one max_iterations line, found {len(max_iter_lines)}"

        max_iter_line = max_iter_lines[0].strip()
        assert 'max_iterations = 5000"' in max_iter_line, \
            f"Expected buggy line 'max_iterations = 5000\"' but found: '{max_iter_line}'"

    def test_solver_conf_has_quote_character(self):
        """Verify the config file contains at least one quote character (the bug)."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        quote_count = content.count('"')
        assert quote_count > 0, \
            "Config file should have at least one quote character (the bug to fix)"

    def test_solver_conf_has_tolerance_setting(self):
        """Verify the config file has the tolerance setting."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "tolerance = 1e-8" in content, \
            "Config file is missing 'tolerance = 1e-8' setting"

    def test_solver_conf_has_verbose_setting(self):
        """Verify the config file has the verbose setting."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "verbose = false" in content, \
            "Config file is missing 'verbose = false' setting"

    def test_solver_conf_has_value_5000(self):
        """Verify the max_iterations value is 5000 (not some other number)."""
        with open(self.CONF_FILE, 'r') as f:
            content = f.read()
        assert "5000" in content, \
            "Config file should contain the value 5000 for max_iterations"

    def test_solver_conf_line_count(self):
        """Verify the config file has the expected number of lines."""
        with open(self.CONF_FILE, 'r') as f:
            lines = f.readlines()
        # Expected: comment, algorithm, max_iterations, tolerance, verbose = 5 lines
        assert len(lines) == 5, \
            f"Expected 5 lines in config file, found {len(lines)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
