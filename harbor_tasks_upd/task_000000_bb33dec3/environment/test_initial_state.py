# test_initial_state.py
"""
Tests to validate the initial state before the student performs the Python 2 to Python 3 migration task.
"""

import pytest
import os
import json
import subprocess
import shutil


class TestInitialState:
    """Test the initial state of the system before the task is performed."""

    def test_dashboards_directory_exists(self):
        """Verify the dashboards directory exists."""
        dashboards_dir = "/home/user/dashboards"
        assert os.path.isdir(dashboards_dir), (
            f"Directory {dashboards_dir} does not exist. "
            "The dashboards directory must be present for this task."
        )

    def test_dashboards_directory_is_writable(self):
        """Verify the dashboards directory is writable."""
        dashboards_dir = "/home/user/dashboards"
        assert os.access(dashboards_dir, os.W_OK), (
            f"Directory {dashboards_dir} is not writable. "
            "The student needs write access to modify the script."
        )

    def test_metric_agg_script_exists(self):
        """Verify the metric_agg.py script exists."""
        script_path = "/home/user/dashboards/metric_agg.py"
        assert os.path.isfile(script_path), (
            f"Script {script_path} does not exist. "
            "The Python 2 script must be present for the migration task."
        )

    def test_metric_agg_script_is_readable(self):
        """Verify the metric_agg.py script is readable."""
        script_path = "/home/user/dashboards/metric_agg.py"
        assert os.access(script_path, os.R_OK), (
            f"Script {script_path} is not readable. "
            "The student needs read access to view and modify the script."
        )

    def test_metric_agg_script_has_reasonable_size(self):
        """Verify the script is approximately 40 lines (reasonable size)."""
        script_path = "/home/user/dashboards/metric_agg.py"
        with open(script_path, 'r') as f:
            lines = f.readlines()
        # Allow some flexibility: between 20 and 80 lines
        assert 20 <= len(lines) <= 80, (
            f"Script {script_path} has {len(lines)} lines, expected approximately 40 lines. "
            "The script should be a small Python 2 script."
        )

    def test_metric_agg_contains_python2_print_statements(self):
        """Verify the script contains Python 2 style print statements."""
        script_path = "/home/user/dashboards/metric_agg.py"
        with open(script_path, 'r') as f:
            content = f.read()

        # Look for Python 2 print statement syntax (print followed by space and string, not parenthesis)
        # Pattern: 'print "' or "print '" without parenthesis
        import re
        py2_print_pattern = re.compile(r'\bprint\s+["\']')
        matches = py2_print_pattern.findall(content)

        assert len(matches) >= 1, (
            f"Script {script_path} does not contain Python 2 style print statements. "
            "Expected print statements like 'print \"text\"' without parentheses."
        )

    def test_metric_agg_has_multiple_print_statements(self):
        """Verify the script has approximately 5 print statements."""
        script_path = "/home/user/dashboards/metric_agg.py"
        with open(script_path, 'r') as f:
            content = f.read()

        import re
        # Count all print occurrences (both py2 and py3 style)
        print_count = len(re.findall(r'\bprint\b', content))

        assert print_count >= 3, (
            f"Script {script_path} has only {print_count} print statements. "
            "Expected at least 3 print statements in the script."
        )

    def test_sample_metrics_json_exists(self):
        """Verify the sample_metrics.json file exists."""
        json_path = "/home/user/dashboards/sample_metrics.json"
        assert os.path.isfile(json_path), (
            f"File {json_path} does not exist. "
            "The sample metrics JSON file must be present for the script to work."
        )

    def test_sample_metrics_json_is_valid(self):
        """Verify the sample_metrics.json contains valid JSON."""
        json_path = "/home/user/dashboards/sample_metrics.json"
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"File {json_path} contains invalid JSON: {e}. "
                "The JSON file must be valid for the script to process it."
            )

    def test_sample_metrics_json_has_expected_structure(self):
        """Verify the sample_metrics.json has the expected keys and structure."""
        json_path = "/home/user/dashboards/sample_metrics.json"
        with open(json_path, 'r') as f:
            data = json.load(f)

        expected_keys = {"cpu", "mem", "requests"}
        actual_keys = set(data.keys())

        assert expected_keys == actual_keys, (
            f"File {json_path} has keys {actual_keys}, expected {expected_keys}. "
            "The JSON file must contain cpu, mem, and requests arrays."
        )

        for key in expected_keys:
            assert isinstance(data[key], list), (
                f"Key '{key}' in {json_path} should be a list, got {type(data[key]).__name__}."
            )
            assert all(isinstance(x, (int, float)) for x in data[key]), (
                f"Key '{key}' in {json_path} should contain only numbers."
            )

    def test_sample_metrics_json_has_expected_values(self):
        """Verify the sample_metrics.json has the expected values for computing averages."""
        json_path = "/home/user/dashboards/sample_metrics.json"
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Verify the expected values that will produce the expected averages
        assert data["cpu"] == [45, 52, 48, 51], (
            f"cpu values are {data['cpu']}, expected [45, 52, 48, 51]"
        )
        assert data["mem"] == [2048, 2100, 2080, 2095], (
            f"mem values are {data['mem']}, expected [2048, 2100, 2080, 2095]"
        )
        assert data["requests"] == [1200, 1350, 1280, 1400], (
            f"requests values are {data['requests']}, expected [1200, 1350, 1280, 1400]"
        )

    def test_python3_is_available(self):
        """Verify python3 interpreter is available."""
        python3_path = shutil.which("python3")
        assert python3_path is not None, (
            "python3 interpreter is not available in PATH. "
            "Python 3 must be installed for this task."
        )

    def test_python2_is_not_available(self):
        """Verify python2 interpreter is NOT available."""
        python2_path = shutil.which("python2")
        python_path = shutil.which("python")

        # Check if 'python' points to python2
        if python_path:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True
            )
            version_output = result.stdout + result.stderr
            if "Python 2" in version_output:
                pytest.fail(
                    "python command points to Python 2. "
                    "Only Python 3 should be available for this task."
                )

        assert python2_path is None, (
            "python2 interpreter is available. "
            "Only Python 3 should be available for this task (no python2 installed)."
        )

    def test_script_fails_with_python3_syntax_error(self):
        """Verify that running the script with python3 currently fails with SyntaxError."""
        script_path = "/home/user/dashboards/metric_agg.py"

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd="/home/user/dashboards"
        )

        assert result.returncode != 0, (
            f"Script {script_path} unexpectedly succeeded with python3. "
            "The script should fail with a SyntaxError due to Python 2 print statements."
        )

        # Check that it's a SyntaxError related to print
        error_output = result.stderr + result.stdout
        assert "SyntaxError" in error_output or "syntax" in error_output.lower(), (
            f"Script {script_path} failed but not with a SyntaxError. "
            f"Error output: {error_output[:500]}"
        )

    def test_script_does_not_have_other_py2_only_constructs(self):
        """Verify the script doesn't have other Python 2 only constructs besides print."""
        script_path = "/home/user/dashboards/metric_agg.py"
        with open(script_path, 'r') as f:
            content = f.read()

        import re

        # Check for common Python 2 only constructs that would need fixing
        # (besides print statements which we already checked)

        # Check for 'xrange' (Python 2 only)
        assert 'xrange' not in content, (
            f"Script contains 'xrange' which is Python 2 only. "
            "The task description says only print statements need fixing."
        )

        # Check for 'raw_input' (Python 2 only)
        assert 'raw_input' not in content, (
            f"Script contains 'raw_input' which is Python 2 only. "
            "The task description says only print statements need fixing."
        )

        # Check for 'except Exception, e:' syntax (Python 2 only)
        py2_except_pattern = re.compile(r'except\s+\w+\s*,\s*\w+\s*:')
        assert not py2_except_pattern.search(content), (
            f"Script contains Python 2 style exception handling. "
            "The task description says only print statements need fixing."
        )
