# test_final_state.py
"""
Tests to validate the final state after the student has completed the Python 2 to Python 3 migration task.
"""

import pytest
import os
import json
import subprocess
import re


class TestFinalState:
    """Test the final state of the system after the task is performed."""

    def test_script_exists(self):
        """Verify the metric_agg.py script still exists."""
        script_path = "/home/user/dashboards/metric_agg.py"
        assert os.path.isfile(script_path), (
            f"Script {script_path} does not exist. "
            "The script must remain in place after the fix."
        )

    def test_sample_metrics_json_unchanged(self):
        """Verify the sample_metrics.json file is unchanged."""
        json_path = "/home/user/dashboards/sample_metrics.json"
        assert os.path.isfile(json_path), (
            f"File {json_path} does not exist. "
            "The JSON file should not have been deleted."
        )

        with open(json_path, 'r') as f:
            data = json.load(f)

        # Verify the expected values are unchanged
        assert data.get("cpu") == [45, 52, 48, 51], (
            f"cpu values are {data.get('cpu')}, expected [45, 52, 48, 51]. "
            "The sample_metrics.json file should not be modified."
        )
        assert data.get("mem") == [2048, 2100, 2080, 2095], (
            f"mem values are {data.get('mem')}, expected [2048, 2100, 2080, 2095]. "
            "The sample_metrics.json file should not be modified."
        )
        assert data.get("requests") == [1200, 1350, 1280, 1400], (
            f"requests values are {data.get('requests')}, expected [1200, 1350, 1280, 1400]. "
            "The sample_metrics.json file should not be modified."
        )

    def test_script_runs_successfully_with_python3(self):
        """Verify that python3 /home/user/dashboards/metric_agg.py exits with code 0."""
        script_path = "/home/user/dashboards/metric_agg.py"

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd="/home/user/dashboards"
        )

        assert result.returncode == 0, (
            f"Script {script_path} failed with exit code {result.returncode}. "
            f"Expected exit code 0.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_script_output_contains_cpu_average(self):
        """Verify the script output contains the correct cpu average (49.0 or 49)."""
        script_path = "/home/user/dashboards/metric_agg.py"

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd="/home/user/dashboards"
        )

        output = result.stdout + result.stderr

        # Expected average: (45 + 52 + 48 + 51) / 4 = 196 / 4 = 49.0
        # Accept various representations: 49, 49.0, 49.00
        cpu_pattern = re.compile(r'cpu[:\s]+49(\.0+)?', re.IGNORECASE)
        assert cpu_pattern.search(output), (
            f"Script output does not contain expected cpu average of 49.0 (or 49).\n"
            f"Output was:\n{output}"
        )

    def test_script_output_contains_mem_average(self):
        """Verify the script output contains the correct mem average (2080.75)."""
        script_path = "/home/user/dashboards/metric_agg.py"

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd="/home/user/dashboards"
        )

        output = result.stdout + result.stderr

        # Expected average: (2048 + 2100 + 2080 + 2095) / 4 = 8323 / 4 = 2080.75
        # Accept various representations: 2080.75, 2080.8, 2080.750, etc.
        mem_pattern = re.compile(r'mem[:\s]+2080\.7', re.IGNORECASE)
        assert mem_pattern.search(output), (
            f"Script output does not contain expected mem average of 2080.75 (or similar).\n"
            f"Output was:\n{output}"
        )

    def test_script_output_contains_requests_average(self):
        """Verify the script output contains the correct requests average (1307.5)."""
        script_path = "/home/user/dashboards/metric_agg.py"

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd="/home/user/dashboards"
        )

        output = result.stdout + result.stderr

        # Expected average: (1200 + 1350 + 1280 + 1400) / 4 = 5230 / 4 = 1307.5
        # Accept various representations: 1307.5, 1307.50, etc.
        requests_pattern = re.compile(r'requests[:\s]+1307\.5', re.IGNORECASE)
        assert requests_pattern.search(output), (
            f"Script output does not contain expected requests average of 1307.5 (or similar).\n"
            f"Output was:\n{output}"
        )

    def test_all_print_statements_converted_to_python3_syntax(self):
        """Verify all print statements use Python 3 function syntax."""
        script_path = "/home/user/dashboards/metric_agg.py"

        with open(script_path, 'r') as f:
            content = f.read()

        # Look for Python 2 print statement syntax (print followed by space and string literal, not parenthesis)
        # Pattern: 'print "' or "print '" without parenthesis immediately after print
        py2_print_pattern = re.compile(r'\bprint\s+["\']')
        py2_matches = py2_print_pattern.findall(content)

        assert len(py2_matches) == 0, (
            f"Script still contains {len(py2_matches)} Python 2 style print statement(s). "
            f"All print statements must be converted to Python 3 function syntax: print(...).\n"
            f"Found patterns: {py2_matches}"
        )

        # Also check for print with variable without parentheses
        # e.g., 'print variable' or 'print some_var'
        py2_print_var_pattern = re.compile(r'\bprint\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s|$|,)')

        # Filter out false positives - lines that have print( later
        lines = content.split('\n')
        py2_style_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('print ') and not stripped.startswith('print('):
                # Check it's not a comment
                if not stripped.startswith('#'):
                    py2_style_lines.append(stripped)

        assert len(py2_style_lines) == 0, (
            f"Script still contains Python 2 style print statement(s):\n"
            f"{py2_style_lines}\n"
            f"All print statements must use Python 3 function syntax: print(...)"
        )

    def test_script_is_valid_python3_syntax(self):
        """Verify the script has valid Python 3 syntax by compiling it."""
        script_path = "/home/user/dashboards/metric_agg.py"

        with open(script_path, 'r') as f:
            content = f.read()

        try:
            compile(content, script_path, 'exec')
        except SyntaxError as e:
            pytest.fail(
                f"Script {script_path} has invalid Python 3 syntax: {e}\n"
                f"Line {e.lineno}: {e.text}"
            )

    def test_fix_is_in_script_not_wrapper(self):
        """Verify the fix is in metric_agg.py itself, not a wrapper script."""
        script_path = "/home/user/dashboards/metric_agg.py"

        with open(script_path, 'r') as f:
            content = f.read()

        # Check that the script still contains the core logic (reading JSON, computing averages)
        # and isn't just a wrapper that calls another script or uses eval/exec tricks

        # Should contain json-related code
        assert 'json' in content.lower() or 'load' in content, (
            f"Script {script_path} doesn't appear to contain JSON loading logic. "
            "The fix should be in the original script, not a replacement."
        )

        # Should not be using eval/exec to run the original code
        suspicious_patterns = [
            r'\bexec\s*\(',
            r'\beval\s*\(',
            r'subprocess.*metric_agg',
            r'2to3',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, content):
                # Allow legitimate uses, but flag suspicious ones
                if 'exec(' in content or 'eval(' in content:
                    # Check if it's being used to run the whole script
                    if 'open(' in content and ('exec' in content or 'eval' in content):
                        lines_with_exec = [l for l in content.split('\n') if 'exec' in l or 'eval' in l]
                        # If exec/eval is used with file reading, that's suspicious
                        if any('read' in l for l in lines_with_exec):
                            pytest.fail(
                                f"Script appears to use exec/eval to run code from a file. "
                                "The fix should modify the print statements directly."
                            )

    def test_script_preserves_aggregation_logic(self):
        """Verify the script still performs the same aggregation (averaging)."""
        script_path = "/home/user/dashboards/metric_agg.py"

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            cwd="/home/user/dashboards"
        )

        output = result.stdout + result.stderr

        # Extract all numbers from output that could be averages
        # We expect to find 49 (or 49.0), 2080.75 (or similar), and 1307.5 (or similar)

        # Check that all three expected averages appear in some form
        found_cpu = bool(re.search(r'\b49(\.0*)?\b', output))
        found_mem = bool(re.search(r'\b2080\.7\d*\b', output))
        found_requests = bool(re.search(r'\b1307\.5\d*\b', output))

        assert found_cpu, (
            f"Could not find cpu average (49 or 49.0) in output.\n"
            f"Output was:\n{output}"
        )
        assert found_mem, (
            f"Could not find mem average (2080.75 or similar) in output.\n"
            f"Output was:\n{output}"
        )
        assert found_requests, (
            f"Could not find requests average (1307.5 or similar) in output.\n"
            f"Output was:\n{output}"
        )
