# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the profiler debugging task.
"""

import os
import subprocess
import configparser
import pytest


HOME = "/home/user"
PROFILER_DIR = os.path.join(HOME, "profiler")
WORKLOAD_DIR = os.path.join(HOME, "workload")
TRACE_PY = os.path.join(PROFILER_DIR, "trace.py")
TRACE_INI = os.path.join(PROFILER_DIR, "trace.ini")
COMPUTE_PY = os.path.join(WORKLOAD_DIR, "compute.py")


class TestDirectoriesExist:
    """Test that required directories exist."""

    def test_home_directory_exists(self):
        assert os.path.isdir(HOME), f"Home directory {HOME} does not exist"

    def test_profiler_directory_exists(self):
        assert os.path.isdir(PROFILER_DIR), f"Profiler directory {PROFILER_DIR} does not exist"

    def test_workload_directory_exists(self):
        assert os.path.isdir(WORKLOAD_DIR), f"Workload directory {WORKLOAD_DIR} does not exist"


class TestFilesExist:
    """Test that required files exist."""

    def test_trace_py_exists(self):
        assert os.path.isfile(TRACE_PY), f"Profiler script {TRACE_PY} does not exist"

    def test_trace_ini_exists(self):
        assert os.path.isfile(TRACE_INI), f"Profiler config {TRACE_INI} does not exist"

    def test_compute_py_exists(self):
        assert os.path.isfile(COMPUTE_PY), f"Workload script {COMPUTE_PY} does not exist"


class TestFilesWritable:
    """Test that files are writable (student needs to modify them)."""

    def test_trace_py_writable(self):
        assert os.access(TRACE_PY, os.W_OK), f"Profiler script {TRACE_PY} is not writable"

    def test_trace_ini_writable(self):
        assert os.access(TRACE_INI, os.W_OK), f"Profiler config {TRACE_INI} is not writable"


class TestTraceIniConfiguration:
    """Test that trace.ini has the expected configuration structure."""

    @pytest.fixture
    def config(self):
        config = configparser.ConfigParser()
        config.read(TRACE_INI)
        return config

    def test_timing_section_exists(self, config):
        assert 'timing' in config.sections(), "trace.ini missing [timing] section"

    def test_output_section_exists(self, config):
        assert 'output' in config.sections(), "trace.ini missing [output] section"

    def test_filters_section_exists(self, config):
        assert 'filters' in config.sections(), "trace.ini missing [filters] section"

    def test_clock_source_is_monotonic(self, config):
        clock_source = config.get('timing', 'clock_source', fallback=None)
        assert clock_source == 'monotonic', \
            f"Expected clock_source = monotonic, got {clock_source}"

    def test_include_children_exists(self, config):
        include_children = config.get('timing', 'include_children', fallback=None)
        assert include_children is not None, "trace.ini missing include_children option"
        assert include_children.lower() == 'yes', \
            f"Expected include_children = yes, got {include_children}"

    def test_aggregation_is_cumulative(self, config):
        aggregation = config.get('timing', 'aggregation', fallback=None)
        assert aggregation == 'cumulative', \
            f"Expected aggregation = cumulative, got {aggregation}"

    def test_format_is_summary(self, config):
        fmt = config.get('output', 'format', fallback=None)
        assert fmt == 'summary', f"Expected format = summary, got {fmt}"

    def test_min_duration_ms_exists(self, config):
        min_duration = config.get('filters', 'min_duration_ms', fallback=None)
        assert min_duration is not None, "trace.ini missing min_duration_ms option"
        # Should be 0.1 initially (the problematic value)
        assert float(min_duration) == 0.1, \
            f"Expected min_duration_ms = 0.1, got {min_duration}"


class TestTracePyContent:
    """Test that trace.py has expected content/structure."""

    @pytest.fixture
    def trace_content(self):
        with open(TRACE_PY, 'r') as f:
            return f.read()

    def test_trace_decorator_defined(self, trace_content):
        assert 'def trace' in trace_content or '@' in trace_content, \
            "trace.py should define a trace decorator"

    def test_references_config_file(self, trace_content):
        # Should read from trace.ini
        assert 'trace.ini' in trace_content or 'configparser' in trace_content.lower() or 'ConfigParser' in trace_content, \
            "trace.py should reference configuration"

    def test_references_include_children(self, trace_content):
        assert 'include_children' in trace_content, \
            "trace.py should reference include_children config option"

    def test_references_min_duration(self, trace_content):
        assert 'min_duration' in trace_content, \
            "trace.py should reference min_duration filter"


class TestComputePyContent:
    """Test that compute.py has expected structure."""

    @pytest.fixture
    def compute_content(self):
        with open(COMPUTE_PY, 'r') as f:
            return f.read()

    def test_imports_trace(self, compute_content):
        assert 'trace' in compute_content, \
            "compute.py should import from the profiler"

    def test_has_main_function(self, compute_content):
        assert 'def main' in compute_content, \
            "compute.py should have a main() function"

    def test_has_trace_decorators(self, compute_content):
        assert '@trace' in compute_content, \
            "compute.py should have @trace decorators on functions"

    def test_has_process_batch(self, compute_content):
        assert 'process_batch' in compute_content, \
            "compute.py should have process_batch function"

    def test_has_transform(self, compute_content):
        assert 'transform' in compute_content, \
            "compute.py should have transform function"

    def test_has_normalize(self, compute_content):
        assert 'normalize' in compute_content, \
            "compute.py should have normalize function"

    def test_has_validate(self, compute_content):
        assert 'validate' in compute_content, \
            "compute.py should have validate function"


class TestPythonEnvironment:
    """Test Python environment is set up correctly."""

    def test_python3_available(self):
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        assert result.returncode == 0, "python3 is not available"

    def test_python_version_311_or_higher(self):
        result = subprocess.run(['python3', '-c', 'import sys; print(sys.version_info[:2])'],
                                capture_output=True, text=True)
        assert result.returncode == 0, "Failed to check Python version"
        version = eval(result.stdout.strip())
        assert version >= (3, 11), f"Python 3.11+ required, got {version}"

    def test_compute_py_is_valid_python(self):
        result = subprocess.run(['python3', '-m', 'py_compile', COMPUTE_PY],
                                capture_output=True, text=True)
        assert result.returncode == 0, f"compute.py has syntax errors: {result.stderr}"

    def test_trace_py_is_valid_python(self):
        result = subprocess.run(['python3', '-m', 'py_compile', TRACE_PY],
                                capture_output=True, text=True)
        assert result.returncode == 0, f"trace.py has syntax errors: {result.stderr}"


class TestInitialBugCondition:
    """Test that the initial buggy state exists (profiler underreports time)."""

    def test_compute_py_runs(self):
        """Verify compute.py can be executed (even if profiler is buggy)."""
        result = subprocess.run(
            ['python3', COMPUTE_PY],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=HOME
        )
        assert result.returncode == 0, \
            f"compute.py failed to run: {result.stderr}"

    def test_profiler_produces_output(self):
        """Verify the profiler produces some summary output."""
        result = subprocess.run(
            ['python3', COMPUTE_PY],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=HOME
        )
        # The profiler should print something (summary format)
        output = result.stdout + result.stderr
        # Should have some timing output
        assert len(output) > 0, "Profiler should produce some output"
