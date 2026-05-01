# test_final_state.py
"""
Tests to validate the final state after the student has completed the task.
Verifies that collect.py now runs successfully under Python 2.7 while maintaining
Python 3 compatibility and producing the expected output.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Test the final state of the system after task completion."""

    SCRIPT_PATH = "/home/user/sensors/collect.py"
    SENSORS_DIR = "/home/user/sensors"

    def test_script_still_exists(self):
        """Verify collect.py script still exists."""
        assert os.path.isfile(self.SCRIPT_PATH), \
            f"Script {self.SCRIPT_PATH} does not exist - it should not be deleted"

    def test_script_is_not_empty(self):
        """Verify collect.py is not empty or stubbed out."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Should have meaningful content, not just a stub
        assert len(content.strip()) > 100, \
            f"Script {self.SCRIPT_PATH} appears to be empty or stubbed out"

    def test_python2_runs_successfully(self):
        """Verify that python2 runs the script without errors (exit code 0)."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"python2 {self.SCRIPT_PATH} should exit 0 but got exit code {result.returncode}. " \
            f"stderr: {result.stderr}"

    def test_python2_no_syntax_error(self):
        """Verify python2 does not produce a SyntaxError."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        error_output = (result.stderr + result.stdout).lower()
        assert 'syntaxerror' not in error_output and 'syntax error' not in error_output, \
            f"python2 produced a SyntaxError: {result.stderr}"

    def test_python2_no_exceptions(self):
        """Verify python2 does not produce any exceptions."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        error_output = result.stderr.lower()
        # Check for common exception indicators
        exception_indicators = ['traceback', 'error:', 'exception']

        for indicator in exception_indicators:
            if indicator in error_output:
                # Allow for some stderr output that isn't an error
                # but fail if it looks like a Python traceback
                if 'traceback' in error_output:
                    pytest.fail(f"python2 produced an exception: {result.stderr}")

    def test_python2_output_contains_reading_from(self):
        """Verify python2 output contains 'Reading from' string."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert 'Reading from' in output, \
            f"python2 output should contain 'Reading from'. Got stdout: {result.stdout}, stderr: {result.stderr}"

    def test_python2_output_contains_sensor_1(self):
        """Verify python2 output contains 'sensor_1'."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert 'sensor_1' in output, \
            f"python2 output should contain 'sensor_1'. Got: {output}"

    def test_python2_output_contains_sensor_2(self):
        """Verify python2 output contains 'sensor_2'."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert 'sensor_2' in output, \
            f"python2 output should contain 'sensor_2'. Got: {output}"

    def test_python2_output_contains_sensor_3(self):
        """Verify python2 output contains 'sensor_3'."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert 'sensor_3' in output, \
            f"python2 output should contain 'sensor_3'. Got: {output}"

    def test_python2_output_contains_done(self):
        """Verify python2 output contains 'Done' string."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr
        assert 'Done' in output, \
            f"python2 output should contain 'Done'. Got: {output}"

    def test_python3_still_runs_successfully(self):
        """Verify that python3 still runs the script successfully (backward compatibility)."""
        result = subprocess.run(
            ['python3', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"python3 {self.SCRIPT_PATH} should still work but got exit code {result.returncode}. " \
            f"stderr: {result.stderr}"

    def test_python3_output_contains_expected_strings(self):
        """Verify python3 output still contains expected strings."""
        result = subprocess.run(
            ['python3', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr

        assert 'Reading from' in output, \
            f"python3 output should contain 'Reading from'. Got: {output}"
        assert 'Done' in output, \
            f"python3 output should contain 'Done'. Got: {output}"
        assert 'sensor_1' in output, \
            f"python3 output should contain 'sensor_1'. Got: {output}"
        assert 'sensor_2' in output, \
            f"python3 output should contain 'sensor_2'. Got: {output}"
        assert 'sensor_3' in output, \
            f"python3 output should contain 'sensor_3'. Got: {output}"

    def test_script_produces_actual_output(self):
        """Verify the script produces meaningful output (not stubbed)."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr

        # Should have multiple lines of output indicating actual work
        lines = [l for l in output.strip().split('\n') if l.strip()]
        assert len(lines) >= 3, \
            f"Script should produce multiple lines of output indicating sensor processing. " \
            f"Got only {len(lines)} lines: {output}"

    def test_script_has_no_fstrings(self):
        """Verify the script no longer contains f-strings (incompatible with Python 2)."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Simple check for f-string patterns
        # This isn't perfect but catches common cases
        import re
        fstring_pattern = r'[fF]["\'][^"\']*\{[^}]+\}[^"\']*["\']'
        matches = re.findall(fstring_pattern, content)

        assert len(matches) == 0, \
            f"Script still contains f-strings which are incompatible with Python 2: {matches}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
