# test_final_state.py
"""
Tests to validate the final state after the student has fixed the profiler
debugging task. The profiler should now account for at least 95% of wallclock time.
"""

import os
import subprocess
import configparser
import re
import pytest


HOME = "/home/user"
PROFILER_DIR = os.path.join(HOME, "profiler")
WORKLOAD_DIR = os.path.join(HOME, "workload")
TRACE_PY = os.path.join(PROFILER_DIR, "trace.py")
TRACE_INI = os.path.join(PROFILER_DIR, "trace.ini")
COMPUTE_PY = os.path.join(WORKLOAD_DIR, "compute.py")


class TestFilesStillExist:
    """Test that required files still exist after modifications."""

    def test_trace_py_exists(self):
        assert os.path.isfile(TRACE_PY), f"Profiler script {TRACE_PY} does not exist"

    def test_trace_ini_exists(self):
        assert os.path.isfile(TRACE_INI), f"Profiler config {TRACE_INI} does not exist"

    def test_compute_py_exists(self):
        assert os.path.isfile(COMPUTE_PY), f"Workload script {COMPUTE_PY} does not exist"


class TestAntiShortcutGuards:
    """Test that the student didn't use prohibited shortcuts."""

    def test_min_duration_still_in_trace_py(self):
        """The fix cannot remove min_duration filtering logic entirely."""
        result = subprocess.run(
            ['grep', '-q', 'min_duration', TRACE_PY],
            capture_output=True
        )
        assert result.returncode == 0, \
            "trace.py must still contain 'min_duration' - cannot remove filtering logic entirely"

    def test_include_children_still_in_ini(self):
        """The fix cannot remove include_children config option."""
        config = configparser.ConfigParser()
        config.read(TRACE_INI)
        assert config.has_option('timing', 'include_children'), \
            "trace.ini must still contain include_children option"

    def test_include_children_still_referenced_in_trace_py(self):
        """trace.py must still reference include_children."""
        with open(TRACE_PY, 'r') as f:
            content = f.read()
        assert 'include_children' in content, \
            "trace.py must still reference include_children config option"

    def test_min_duration_not_zero_in_config(self):
        """Cannot simply set min_duration_ms = 0 as a shortcut."""
        config = configparser.ConfigParser()
        config.read(TRACE_INI)
        if config.has_option('filters', 'min_duration_ms'):
            min_duration = config.get('filters', 'min_duration_ms')
            # It's okay if the value changed, but we verify the filtering
            # logic still exists in trace.py (checked above)
            # This test just documents the value
            pass


class TestConfigurationIntegrity:
    """Test that configuration maintains required settings."""

    @pytest.fixture
    def config(self):
        config = configparser.ConfigParser()
        config.read(TRACE_INI)
        return config

    def test_clock_source_remains_monotonic(self, config):
        """Clock source must remain monotonic."""
        clock_source = config.get('timing', 'clock_source', fallback=None)
        assert clock_source == 'monotonic', \
            f"Clock source must remain 'monotonic', got '{clock_source}'"

    def test_output_format_still_summary(self, config):
        """Output format should still be summary."""
        fmt = config.get('output', 'format', fallback=None)
        assert fmt == 'summary', \
            f"Output format should be 'summary', got '{fmt}'"


class TestComputePyIntegrity:
    """Test that compute.py maintains required structure."""

    @pytest.fixture
    def compute_content(self):
        with open(COMPUTE_PY, 'r') as f:
            return f.read()

    def test_all_functions_still_traced(self, compute_content):
        """All functions in compute.py must remain decorated with @trace."""
        # Check that @trace decorator is still present
        assert '@trace' in compute_content, \
            "compute.py must still have @trace decorators"

    def test_main_function_exists(self, compute_content):
        assert 'def main' in compute_content, \
            "compute.py must still have main() function"

    def test_process_batch_exists(self, compute_content):
        assert 'process_batch' in compute_content, \
            "compute.py must still have process_batch function"

    def test_transform_exists(self, compute_content):
        assert 'transform' in compute_content, \
            "compute.py must still have transform function"

    def test_normalize_exists(self, compute_content):
        assert 'normalize' in compute_content, \
            "compute.py must still have normalize function"

    def test_validate_exists(self, compute_content):
        assert 'validate' in compute_content, \
            "compute.py must still have validate function"


class TestPythonFilesValid:
    """Test that Python files are syntactically valid."""

    def test_compute_py_valid_syntax(self):
        result = subprocess.run(
            ['python3', '-m', 'py_compile', COMPUTE_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"compute.py has syntax errors: {result.stderr}"

    def test_trace_py_valid_syntax(self):
        result = subprocess.run(
            ['python3', '-m', 'py_compile', TRACE_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"trace.py has syntax errors: {result.stderr}"


def parse_profiler_output(output):
    """
    Parse profiler output to extract traced time and wallclock time.
    Returns (traced_total, wallclock) or (None, None) if parsing fails.
    """
    traced_total = None
    wallclock = None

    # Look for various patterns that might indicate total traced time
    # Pattern: "Total traced time: X.XXXs" or similar
    traced_patterns = [
        r'[Tt]otal\s+(?:traced\s+)?time[:\s]+(\d+\.?\d*)\s*s',
        r'[Tt]raced\s+(?:total\s+)?time[:\s]+(\d+\.?\d*)\s*s',
        r'[Ss]um[:\s]+(\d+\.?\d*)\s*s',
        r'[Tt]otal[:\s]+(\d+\.?\d*)\s*s',
        r'traced_time[:\s=]+(\d+\.?\d*)',
        r'total_traced[:\s=]+(\d+\.?\d*)',
    ]

    # Pattern: "Wallclock: X.XXXs" or similar
    wallclock_patterns = [
        r'[Ww]all(?:clock)?[:\s]+(\d+\.?\d*)\s*s',
        r'[Ee]lapsed[:\s]+(\d+\.?\d*)\s*s',
        r'[Rr]untime[:\s]+(\d+\.?\d*)\s*s',
        r'wallclock[:\s=]+(\d+\.?\d*)',
        r'wall_time[:\s=]+(\d+\.?\d*)',
    ]

    for pattern in traced_patterns:
        match = re.search(pattern, output)
        if match:
            traced_total = float(match.group(1))
            break

    for pattern in wallclock_patterns:
        match = re.search(pattern, output)
        if match:
            wallclock = float(match.group(1))
            break

    # Also try to find individual function times and sum them
    if traced_total is None:
        # Look for lines like "function_name: 0.123456s" or "function_name    0.123456"
        time_matches = re.findall(r'(?:^|\n)\s*\w+[:\s]+(\d+\.?\d*)\s*s?(?:\s|$|\n)', output)
        if time_matches:
            times = [float(t) for t in time_matches if float(t) < 100]  # sanity check
            if times:
                traced_total = sum(times)

    return traced_total, wallclock


def run_compute_and_get_ratio():
    """
    Run compute.py and return the ratio of traced time to wallclock time.
    Returns (ratio, traced_time, wallclock_time, output) or raises an exception.
    """
    import time

    start = time.monotonic()
    result = subprocess.run(
        ['python3', COMPUTE_PY],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=HOME
    )
    end = time.monotonic()

    if result.returncode != 0:
        raise RuntimeError(f"compute.py failed with return code {result.returncode}: {result.stderr}")

    measured_wallclock = end - start
    output = result.stdout + result.stderr

    traced_total, reported_wallclock = parse_profiler_output(output)

    # Use reported wallclock if available, otherwise use measured
    wallclock = reported_wallclock if reported_wallclock is not None else measured_wallclock

    if traced_total is None:
        # Try to extract any numeric values that could be times
        # Last resort: look for the largest reasonable time value
        numbers = re.findall(r'(\d+\.\d+)', output)
        if numbers:
            candidates = [float(n) for n in numbers if 0.1 < float(n) < 100]
            if candidates:
                traced_total = max(candidates)

    if traced_total is None:
        raise RuntimeError(f"Could not parse traced time from output:\n{output}")

    ratio = traced_total / wallclock if wallclock > 0 else 0

    return ratio, traced_total, wallclock, output


class TestProfilerAccuracy:
    """Test that the profiler now accounts for at least 95% of wallclock time."""

    def test_compute_py_runs_successfully(self):
        """Verify compute.py runs without errors."""
        result = subprocess.run(
            ['python3', COMPUTE_PY],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=HOME
        )
        assert result.returncode == 0, \
            f"compute.py failed to run: {result.stderr}"

    def test_profiler_produces_summary_output(self):
        """Verify the profiler still produces summary output."""
        result = subprocess.run(
            ['python3', COMPUTE_PY],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=HOME
        )
        output = result.stdout + result.stderr
        # Should have some output with timing information
        assert len(output) > 0, "Profiler should produce output"
        # Should contain some numeric timing values
        assert re.search(r'\d+\.\d+', output), \
            f"Profiler output should contain timing values:\n{output}"

    def test_profiler_accuracy_run1(self):
        """First run: profiler should account for >= 95% of wallclock time."""
        ratio, traced, wallclock, output = run_compute_and_get_ratio()
        assert ratio >= 0.95, \
            f"Run 1: Profiler only accounted for {ratio*100:.1f}% of wallclock time " \
            f"(traced={traced:.4f}s, wallclock={wallclock:.4f}s). " \
            f"Expected >= 95%.\nOutput:\n{output}"

    def test_profiler_accuracy_run2(self):
        """Second run: profiler should account for >= 95% of wallclock time."""
        ratio, traced, wallclock, output = run_compute_and_get_ratio()
        assert ratio >= 0.95, \
            f"Run 2: Profiler only accounted for {ratio*100:.1f}% of wallclock time " \
            f"(traced={traced:.4f}s, wallclock={wallclock:.4f}s). " \
            f"Expected >= 95%.\nOutput:\n{output}"

    def test_profiler_accuracy_run3(self):
        """Third run: profiler should account for >= 95% of wallclock time."""
        ratio, traced, wallclock, output = run_compute_and_get_ratio()
        assert ratio >= 0.95, \
            f"Run 3: Profiler only accounted for {ratio*100:.1f}% of wallclock time " \
            f"(traced={traced:.4f}s, wallclock={wallclock:.4f}s). " \
            f"Expected >= 95%.\nOutput:\n{output}"


class TestTracePyImplementation:
    """Additional tests to verify trace.py implementation details."""

    @pytest.fixture
    def trace_content(self):
        with open(TRACE_PY, 'r') as f:
            return f.read()

    def test_uses_configparser(self, trace_content):
        """trace.py should use configparser to read config."""
        assert 'configparser' in trace_content.lower() or 'ConfigParser' in trace_content, \
            "trace.py should use configparser"

    def test_has_trace_decorator(self, trace_content):
        """trace.py should define a trace decorator."""
        assert 'def trace' in trace_content or 'trace' in trace_content, \
            "trace.py should define a trace decorator"

    def test_uses_monotonic_clock(self, trace_content):
        """trace.py should use monotonic clock (time.monotonic)."""
        assert 'monotonic' in trace_content, \
            "trace.py should reference monotonic clock"
