# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student
performs the log filter debugging task.
"""

import os
import re
import pytest
import subprocess
import yaml


HOME = "/home/user"
LOGPIPE_DIR = os.path.join(HOME, "logpipe")
FILTER_PY = os.path.join(LOGPIPE_DIR, "filter.py")
RAW_LOG = os.path.join(LOGPIPE_DIR, "raw.log")
PATTERNS_CONF = os.path.join(LOGPIPE_DIR, "patterns.conf")
ROUTING_YAML = os.path.join(LOGPIPE_DIR, "routing.yaml")
OUTPUT_DIR = os.path.join(LOGPIPE_DIR, "output")
ERRORS_LOG = os.path.join(OUTPUT_DIR, "errors.log")


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_logpipe_directory_exists(self):
        assert os.path.isdir(LOGPIPE_DIR), f"Directory {LOGPIPE_DIR} does not exist"

    def test_output_directory_exists(self):
        assert os.path.isdir(OUTPUT_DIR), f"Directory {OUTPUT_DIR} does not exist"

    def test_logpipe_directory_writable(self):
        assert os.access(LOGPIPE_DIR, os.W_OK), f"Directory {LOGPIPE_DIR} is not writable"


class TestRequiredFiles:
    """Test that all required files exist."""

    def test_filter_py_exists(self):
        assert os.path.isfile(FILTER_PY), f"File {FILTER_PY} does not exist"

    def test_raw_log_exists(self):
        assert os.path.isfile(RAW_LOG), f"File {RAW_LOG} does not exist"

    def test_patterns_conf_exists(self):
        assert os.path.isfile(PATTERNS_CONF), f"File {PATTERNS_CONF} does not exist"

    def test_routing_yaml_exists(self):
        assert os.path.isfile(ROUTING_YAML), f"File {ROUTING_YAML} does not exist"


class TestFilterPyContent:
    """Test that filter.py has the expected structure and bug."""

    def test_filter_py_is_python_script(self):
        with open(FILTER_PY, 'r') as f:
            content = f.read()
        # Should be a Python file (either has shebang or imports)
        assert 'import' in content or 'def ' in content, \
            f"{FILTER_PY} does not appear to be a valid Python script"

    def test_filter_py_has_classify_line_function(self):
        with open(FILTER_PY, 'r') as f:
            content = f.read()
        assert 'def classify_line' in content, \
            f"{FILTER_PY} should contain a classify_line function"

    def test_filter_py_has_faulty_structured_heuristic(self):
        """The bug: faulty heuristic that misclassifies ISO 8601 timestamps."""
        with open(FILTER_PY, 'r') as f:
            content = f.read()
        # Check for the faulty heuristic pattern
        # Looking for the 'T' in line check that causes the bug
        assert "'T'" in content or '"T"' in content, \
            f"{FILTER_PY} should contain the faulty 'T' character check for structured log detection"

    def test_filter_py_uses_re_module(self):
        with open(FILTER_PY, 'r') as f:
            content = f.read()
        assert 'import re' in content or 'from re import' in content, \
            f"{FILTER_PY} should use the re module for regex matching"

    def test_filter_py_is_executable_as_python(self):
        """Test that filter.py can at least be parsed by Python."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', FILTER_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"{FILTER_PY} has syntax errors: {result.stderr}"


class TestRawLogContent:
    """Test that raw.log has the expected content structure."""

    def test_raw_log_has_sufficient_lines(self):
        with open(RAW_LOG, 'r') as f:
            lines = f.readlines()
        assert len(lines) >= 400, \
            f"{RAW_LOG} should have approximately 500 lines, found {len(lines)}"

    def test_raw_log_has_auth_service_logs(self):
        with open(RAW_LOG, 'r') as f:
            content = f.read()
        assert 'auth-service' in content, \
            f"{RAW_LOG} should contain logs from auth-service"

    def test_raw_log_has_inventory_service_logs(self):
        with open(RAW_LOG, 'r') as f:
            content = f.read()
        assert 'inventory-service' in content, \
            f"{RAW_LOG} should contain logs from inventory-service"

    def test_raw_log_has_payment_svc_logs(self):
        with open(RAW_LOG, 'r') as f:
            content = f.read()
        assert 'payment-svc' in content, \
            f"{RAW_LOG} should contain logs from payment-svc"

    def test_raw_log_has_error_level_logs(self):
        with open(RAW_LOG, 'r') as f:
            content = f.read()
        assert '[ERROR]' in content, \
            f"{RAW_LOG} should contain ERROR level logs"

    def test_raw_log_has_payment_svc_error_logs(self):
        """Verify there are ERROR logs from payment-svc in raw.log."""
        with open(RAW_LOG, 'r') as f:
            lines = f.readlines()
        payment_error_count = sum(
            1 for line in lines 
            if 'payment-svc' in line and '[ERROR]' in line
        )
        assert payment_error_count >= 40, \
            f"{RAW_LOG} should have ~50 ERROR logs from payment-svc, found {payment_error_count}"

    def test_raw_log_has_iso8601_timestamps_for_payment(self):
        """Verify payment-svc logs use ISO 8601 format with T separator."""
        with open(RAW_LOG, 'r') as f:
            lines = f.readlines()
        # ISO 8601 format: 2024-01-15T10:23:47+00:00
        iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        payment_iso_lines = [
            line for line in lines 
            if 'payment-svc' in line and iso_pattern.match(line)
        ]
        assert len(payment_iso_lines) > 0, \
            "payment-svc logs should use ISO 8601 timestamp format (timestamp before severity)"

    def test_raw_log_auth_service_format_differs(self):
        """Verify auth-service logs have severity bracket first."""
        with open(RAW_LOG, 'r') as f:
            lines = f.readlines()
        # auth-service format: [ERROR] 2024-01-15 10:23:45 service=auth-service
        bracket_first_pattern = re.compile(r'^\[(ERROR|WARN|INFO|DEBUG)\]')
        auth_bracket_first = [
            line for line in lines 
            if 'auth-service' in line and bracket_first_pattern.match(line)
        ]
        assert len(auth_bracket_first) > 0, \
            "auth-service logs should have severity bracket at the start of the line"


class TestPatternsConfContent:
    """Test that patterns.conf has the expected structure."""

    def test_patterns_conf_has_severity_section(self):
        with open(PATTERNS_CONF, 'r') as f:
            content = f.read()
        assert '[severity]' in content, \
            f"{PATTERNS_CONF} should have a [severity] section"

    def test_patterns_conf_has_service_section(self):
        with open(PATTERNS_CONF, 'r') as f:
            content = f.read()
        assert '[service]' in content, \
            f"{PATTERNS_CONF} should have a [service] section"

    def test_patterns_conf_has_error_pattern(self):
        with open(PATTERNS_CONF, 'r') as f:
            content = f.read()
        assert 'ERROR' in content and r'\[ERROR\]' in content, \
            f"{PATTERNS_CONF} should have an ERROR severity pattern with regex"

    def test_patterns_conf_has_payment_service_pattern(self):
        with open(PATTERNS_CONF, 'r') as f:
            content = f.read()
        assert 'payment-svc' in content, \
            f"{PATTERNS_CONF} should have a pattern for payment-svc"


class TestRoutingYamlContent:
    """Test that routing.yaml is valid and has expected structure."""

    def test_routing_yaml_is_valid_yaml(self):
        with open(ROUTING_YAML, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"{ROUTING_YAML} is not valid YAML: {e}")
        assert data is not None, f"{ROUTING_YAML} should not be empty"

    def test_routing_yaml_has_routing_rules(self):
        with open(ROUTING_YAML, 'r') as f:
            content = f.read()
        # Should mention errors.log or error routing
        assert 'error' in content.lower(), \
            f"{ROUTING_YAML} should contain error routing rules"


class TestCurrentOutputState:
    """Test the current (buggy) state of output files."""

    def test_errors_log_exists(self):
        assert os.path.isfile(ERRORS_LOG), \
            f"{ERRORS_LOG} should exist (with partial results from previous runs)"

    def test_errors_log_has_auth_service_errors(self):
        """Auth-service ERROR logs should be present (working correctly)."""
        with open(ERRORS_LOG, 'r') as f:
            content = f.read()
        assert 'auth-service' in content, \
            f"{ERRORS_LOG} should contain auth-service ERROR logs (these work correctly)"

    def test_errors_log_missing_payment_svc_errors(self):
        """Payment-svc ERROR logs should be missing or sparse (this is the bug)."""
        with open(ERRORS_LOG, 'r') as f:
            lines = f.readlines()
        payment_error_count = sum(
            1 for line in lines 
            if 'payment-svc' in line
        )
        # The bug causes ~40% to be dropped, so we should see very few or none
        assert payment_error_count < 30, \
            f"{ERRORS_LOG} should be missing most payment-svc errors (found {payment_error_count}, bug not present?)"


class TestPythonEnvironment:
    """Test that required Python packages are available."""

    def test_python3_available(self):
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        assert result.returncode == 0, "Python 3 should be available"

    def test_pyyaml_installed(self):
        result = subprocess.run(
            ['python3', '-c', 'import yaml'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "PyYAML should be installed (import yaml should work)"

    def test_re_module_available(self):
        result = subprocess.run(
            ['python3', '-c', 'import re'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "re module should be available (stdlib)"
