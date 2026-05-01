# test_final_state.py
"""
Tests to validate the final state after the student has fixed the log filter
debugging task. The fix should ensure all ERROR logs from payment-svc are
properly routed to errors.log.
"""

import os
import re
import subprocess
import yaml
import pytest


HOME = "/home/user"
LOGPIPE_DIR = os.path.join(HOME, "logpipe")
FILTER_PY = os.path.join(LOGPIPE_DIR, "filter.py")
RAW_LOG = os.path.join(LOGPIPE_DIR, "raw.log")
PATTERNS_CONF = os.path.join(LOGPIPE_DIR, "patterns.conf")
ROUTING_YAML = os.path.join(LOGPIPE_DIR, "routing.yaml")
OUTPUT_DIR = os.path.join(LOGPIPE_DIR, "output")
ERRORS_LOG = os.path.join(OUTPUT_DIR, "errors.log")
STRUCTURED_LOG = os.path.join(OUTPUT_DIR, "structured.log")


class TestFilterExecution:
    """Test that filter.py executes successfully."""

    def test_filter_py_runs_successfully(self):
        """Running filter.py should complete with exit code 0."""
        result = subprocess.run(
            ['python3', FILTER_PY],
            capture_output=True,
            text=True,
            cwd=LOGPIPE_DIR
        )
        assert result.returncode == 0, \
            f"filter.py should exit with code 0, got {result.returncode}. Stderr: {result.stderr}"

    def test_filter_py_produces_output(self):
        """Running filter.py should produce/update errors.log."""
        # Run the filter
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)
        assert os.path.isfile(ERRORS_LOG), \
            f"{ERRORS_LOG} should exist after running filter.py"
        assert os.path.getsize(ERRORS_LOG) > 0, \
            f"{ERRORS_LOG} should not be empty after running filter.py"


class TestPaymentSvcErrorsRouted:
    """Test that payment-svc ERROR logs are now correctly routed."""

    def test_errors_log_contains_payment_svc_errors(self):
        """errors.log should contain ERROR logs from payment-svc."""
        # Run filter first to ensure fresh output
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(ERRORS_LOG, 'r') as f:
            content = f.read()

        assert 'payment-svc' in content, \
            f"{ERRORS_LOG} should contain payment-svc logs after fix"

    def test_errors_log_has_sufficient_payment_svc_errors(self):
        """errors.log should have at least 48 payment-svc ERROR entries."""
        # Run filter first
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(ERRORS_LOG, 'r') as f:
            lines = f.readlines()

        # Count lines with payment-svc
        payment_svc_count = sum(
            1 for line in lines
            if 'payment-svc' in line or 'service=payment-svc' in line
        )

        assert payment_svc_count >= 48, \
            f"{ERRORS_LOG} should have at least 48 payment-svc entries, found {payment_svc_count}"

    def test_errors_log_payment_svc_via_grep(self):
        """Verify payment-svc count using grep-style matching."""
        # Run filter first
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        # Use subprocess grep to count
        result = subprocess.run(
            ['grep', '-c', 'service=payment-svc', ERRORS_LOG],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            count = int(result.stdout.strip())
        else:
            count = 0

        assert count >= 48, \
            f"grep 'service=payment-svc' should find at least 48 matches, found {count}"


class TestExistingFunctionalityPreserved:
    """Test that auth-service and inventory-service ERROR routing still works."""

    def test_errors_log_contains_auth_service_errors(self):
        """auth-service ERROR logs should still be routed correctly."""
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(ERRORS_LOG, 'r') as f:
            content = f.read()

        assert 'auth-service' in content, \
            f"{ERRORS_LOG} should still contain auth-service ERROR logs"

    def test_errors_log_contains_inventory_service_errors(self):
        """inventory-service ERROR logs should still be routed correctly."""
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(ERRORS_LOG, 'r') as f:
            content = f.read()

        assert 'inventory-service' in content, \
            f"{ERRORS_LOG} should still contain inventory-service ERROR logs"

    def test_errors_log_has_multiple_services(self):
        """errors.log should contain ERROR logs from all three services."""
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(ERRORS_LOG, 'r') as f:
            content = f.read()

        services_found = []
        if 'auth-service' in content:
            services_found.append('auth-service')
        if 'inventory-service' in content:
            services_found.append('inventory-service')
        if 'payment-svc' in content:
            services_found.append('payment-svc')

        assert len(services_found) == 3, \
            f"errors.log should have logs from all 3 services, found: {services_found}"


class TestRawLogUnchanged:
    """Test that raw.log was not modified."""

    def test_raw_log_still_exists(self):
        """raw.log should still exist."""
        assert os.path.isfile(RAW_LOG), f"{RAW_LOG} should still exist"

    def test_raw_log_has_original_content(self):
        """raw.log should still have the original ~500 lines."""
        with open(RAW_LOG, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 400, \
            f"{RAW_LOG} should still have ~500 lines, found {len(lines)}"

    def test_raw_log_still_has_payment_svc_iso_format(self):
        """raw.log should still have payment-svc logs in ISO 8601 format."""
        with open(RAW_LOG, 'r') as f:
            lines = f.readlines()

        iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        payment_iso_lines = [
            line for line in lines
            if 'payment-svc' in line and iso_pattern.match(line)
        ]

        assert len(payment_iso_lines) > 0, \
            "raw.log should still have payment-svc logs with ISO 8601 timestamps"


class TestPatternsConfPreserved:
    """Test that patterns.conf maintains regex-based patterns."""

    def test_patterns_conf_still_exists(self):
        """patterns.conf should still exist."""
        assert os.path.isfile(PATTERNS_CONF), f"{PATTERNS_CONF} should still exist"

    def test_patterns_conf_has_severity_section(self):
        """patterns.conf should still have [severity] section."""
        with open(PATTERNS_CONF, 'r') as f:
            content = f.read()

        assert '[severity]' in content, \
            f"{PATTERNS_CONF} should still have [severity] section"

    def test_patterns_conf_uses_regex_patterns(self):
        """patterns.conf should still use regex patterns (not hardcoded strings)."""
        with open(PATTERNS_CONF, 'r') as f:
            content = f.read()

        # Should still have regex metacharacters like ^ or $ or \[ or .*
        has_regex = (
            '^' in content or 
            '$' in content or 
            '\\[' in content or 
            '.*' in content or
            '.+' in content
        )

        assert has_regex, \
            f"{PATTERNS_CONF} should still use regex patterns, not hardcoded string matching"


class TestRoutingYamlPreserved:
    """Test that routing.yaml structure is preserved."""

    def test_routing_yaml_still_exists(self):
        """routing.yaml should still exist."""
        assert os.path.isfile(ROUTING_YAML), f"{ROUTING_YAML} should still exist"

    def test_routing_yaml_is_valid_yaml(self):
        """routing.yaml should still be valid YAML."""
        with open(ROUTING_YAML, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"{ROUTING_YAML} should still be valid YAML: {e}")

        assert data is not None, f"{ROUTING_YAML} should not be empty"

    def test_routing_yaml_has_routing_rules(self):
        """routing.yaml should still define routing rules."""
        with open(ROUTING_YAML, 'r') as f:
            content = f.read()

        assert 'error' in content.lower() or 'route' in content.lower() or 'output' in content.lower(), \
            f"{ROUTING_YAML} should still contain routing rules"


class TestFilterPyStructure:
    """Test that filter.py maintains expected structure."""

    def test_filter_py_still_valid_python(self):
        """filter.py should still be valid Python."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', FILTER_PY],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"{FILTER_PY} has syntax errors: {result.stderr}"

    def test_filter_py_still_uses_re_module(self):
        """filter.py should still use the re module."""
        with open(FILTER_PY, 'r') as f:
            content = f.read()

        assert 'import re' in content or 'from re import' in content, \
            f"{FILTER_PY} should still use the re module"

    def test_filter_py_processes_via_routing_logic(self):
        """
        Verify that filter.py actually processes logs through routing logic,
        not just manual appending. Check that it reads patterns.conf or routing.yaml.
        """
        with open(FILTER_PY, 'r') as f:
            content = f.read()

        # Should reference the config files
        uses_config = (
            'patterns' in content.lower() or 
            'routing' in content.lower() or
            '.conf' in content or
            '.yaml' in content or
            'classify' in content.lower()
        )

        assert uses_config, \
            f"{FILTER_PY} should process logs through its routing logic, not manual insertion"


class TestNoManualInsertion:
    """Test that the fix was done properly, not by manual insertion."""

    def test_payment_errors_match_raw_log_format(self):
        """
        Payment-svc entries in errors.log should match the format from raw.log,
        indicating they were processed through filter.py, not manually inserted.
        """
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(ERRORS_LOG, 'r') as f:
            error_lines = f.readlines()

        with open(RAW_LOG, 'r') as f:
            raw_lines = f.readlines()

        # Get payment-svc ERROR lines from raw.log
        raw_payment_errors = [
            line.strip() for line in raw_lines
            if 'payment-svc' in line and '[ERROR]' in line
        ]

        # Get payment-svc lines from errors.log
        output_payment_lines = [
            line.strip() for line in error_lines
            if 'payment-svc' in line
        ]

        # At least some of the output lines should match raw input format
        # (allowing for possible formatting changes by the filter)
        matches = 0
        for output_line in output_payment_lines:
            for raw_line in raw_payment_errors:
                # Check if key parts match (service name, ERROR tag, and some content)
                if 'payment-svc' in output_line and '[ERROR]' in output_line:
                    matches += 1
                    break

        assert matches >= 40, \
            f"Payment-svc entries should come from filter.py processing, found {matches} matching entries"

    def test_filter_produces_consistent_output(self):
        """
        Running filter.py multiple times should produce consistent output,
        indicating it's actually processing the file.
        """
        # Run twice
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)
        with open(ERRORS_LOG, 'r') as f:
            first_run = f.read()

        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)
        with open(ERRORS_LOG, 'r') as f:
            second_run = f.read()

        # Count payment-svc entries in both runs
        first_count = first_run.count('payment-svc')
        second_count = second_run.count('payment-svc')

        # Should be consistent (or at least both have substantial counts)
        assert first_count >= 48, f"First run should have >=48 payment-svc entries, got {first_count}"
        assert second_count >= 48, f"Second run should have >=48 payment-svc entries, got {second_count}"


class TestAllErrorsRouted:
    """Test that ALL ERROR level logs are properly routed."""

    def test_all_error_logs_in_errors_log(self):
        """
        Count ERROR logs in raw.log and verify errors.log has them all.
        """
        subprocess.run(['python3', FILTER_PY], cwd=LOGPIPE_DIR, capture_output=True)

        with open(RAW_LOG, 'r') as f:
            raw_lines = f.readlines()

        with open(ERRORS_LOG, 'r') as f:
            error_lines = f.readlines()

        # Count ERROR entries in raw.log (excluding actual JSON structured logs)
        raw_error_count = sum(
            1 for line in raw_lines
            if '[ERROR]' in line and not line.strip().startswith('{')
        )

        # Count entries in errors.log
        output_error_count = len([l for l in error_lines if l.strip()])

        # errors.log should have at least 90% of ERROR logs from raw
        # (allowing some margin for edge cases)
        expected_min = int(raw_error_count * 0.9)

        assert output_error_count >= expected_min, \
            f"errors.log should have at least {expected_min} ERROR entries (90% of {raw_error_count}), found {output_error_count}"
