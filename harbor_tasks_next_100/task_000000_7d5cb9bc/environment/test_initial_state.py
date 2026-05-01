# test_initial_state.py
"""
Tests to validate the initial state before the student performs the task.
Verifies that the collect.py script exists with Python 3 syntax that fails under Python 2.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Test the initial state of the system before task completion."""

    SCRIPT_PATH = "/home/user/sensors/collect.py"
    SENSORS_DIR = "/home/user/sensors"

    def test_sensors_directory_exists(self):
        """Verify /home/user/sensors directory exists."""
        assert os.path.isdir(self.SENSORS_DIR), \
            f"Directory {self.SENSORS_DIR} does not exist"

    def test_sensors_directory_is_writable(self):
        """Verify /home/user/sensors directory is writable."""
        assert os.access(self.SENSORS_DIR, os.W_OK), \
            f"Directory {self.SENSORS_DIR} is not writable"

    def test_collect_py_exists(self):
        """Verify collect.py script exists."""
        assert os.path.isfile(self.SCRIPT_PATH), \
            f"Script {self.SCRIPT_PATH} does not exist"

    def test_collect_py_is_readable(self):
        """Verify collect.py script is readable."""
        assert os.access(self.SCRIPT_PATH, os.R_OK), \
            f"Script {self.SCRIPT_PATH} is not readable"

    def test_collect_py_has_content(self):
        """Verify collect.py has approximately 40 lines of content."""
        with open(self.SCRIPT_PATH, 'r') as f:
            lines = f.readlines()
        line_count = len(lines)
        # Allow some flexibility: ~40 lines means roughly 20-60 lines
        assert 15 <= line_count <= 80, \
            f"Script {self.SCRIPT_PATH} has {line_count} lines, expected ~40 lines"

    def test_collect_py_contains_print_statements(self):
        """Verify collect.py contains print statements with function syntax."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Check for print function calls (with parentheses)
        assert 'print(' in content, \
            f"Script {self.SCRIPT_PATH} does not contain print function calls"

    def test_collect_py_contains_fstring(self):
        """Verify collect.py contains at least one f-string (Python 3 syntax)."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Check for f-string syntax
        assert 'f"' in content or "f'" in content, \
            f"Script {self.SCRIPT_PATH} does not contain f-string syntax"

    def test_collect_py_has_sensor_reading_fstring(self):
        """Verify collect.py contains the specific f-string for sensor reading."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Check for the specific pattern mentioned in task
        assert 'Reading from' in content, \
            f"Script {self.SCRIPT_PATH} does not contain 'Reading from' text"

    def test_collect_py_has_flush_parameter(self):
        """Verify collect.py uses flush=True in at least one print."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        assert 'flush=True' in content or 'flush = True' in content, \
            f"Script {self.SCRIPT_PATH} does not contain print with flush=True"

    def test_collect_py_has_done_message(self):
        """Verify collect.py contains a 'Done' print statement."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        assert '"Done"' in content or "'Done'" in content, \
            f"Script {self.SCRIPT_PATH} does not contain 'Done' message"

    def test_python2_is_available(self):
        """Verify python2 is available on the system."""
        result = subprocess.run(
            ['which', 'python2'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "python2 is not available on this system"

    def test_python3_is_available(self):
        """Verify python3 is available on the system."""
        result = subprocess.run(
            ['which', 'python3'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "python3 is not available on this system"

    def test_python2_fails_on_script(self):
        """Verify that python2 fails to run the script (SyntaxError expected)."""
        result = subprocess.run(
            ['python2', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            f"python2 should fail on {self.SCRIPT_PATH} but it succeeded"

        # Check that it's a syntax error (either in stderr or the error message)
        error_output = result.stderr.lower()
        assert 'syntax' in error_output or 'error' in error_output, \
            f"python2 failed but not with expected syntax error. stderr: {result.stderr}"

    def test_python3_succeeds_on_script(self):
        """Verify that python3 runs the script successfully."""
        result = subprocess.run(
            ['python3', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"python3 should succeed on {self.SCRIPT_PATH} but failed with: {result.stderr}"

    def test_python3_output_contains_expected_strings(self):
        """Verify python3 output contains expected sensor-related strings."""
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

    def test_python3_output_contains_sensor_names(self):
        """Verify python3 output contains sensor names."""
        result = subprocess.run(
            ['python3', self.SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr

        # Check for sensor names
        assert 'sensor_1' in output or 'sensor1' in output.replace('_', ''), \
            f"python3 output should contain sensor_1. Got: {output}"
        assert 'sensor_2' in output or 'sensor2' in output.replace('_', ''), \
            f"python3 output should contain sensor_2. Got: {output}"
        assert 'sensor_3' in output or 'sensor3' in output.replace('_', ''), \
            f"python3 output should contain sensor_3. Got: {output}"

    def test_script_has_multiple_print_statements(self):
        """Verify script has approximately 4 print statements."""
        with open(self.SCRIPT_PATH, 'r') as f:
            content = f.read()

        # Count print( occurrences (rough count of print statements)
        print_count = content.count('print(')

        assert print_count >= 3, \
            f"Script should have at least 3-4 print statements, found {print_count}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
