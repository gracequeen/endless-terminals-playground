# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the SAST scan suppression configuration.
"""

import json
import os
import subprocess
import pytest


PROJECT_ROOT = "/home/user/project"
SECURITY_DIR = os.path.join(PROJECT_ROOT, ".security")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")


class TestProjectStructureExists:
    """Verify the basic project structure exists."""

    def test_project_root_exists(self):
        assert os.path.isdir(PROJECT_ROOT), \
            f"Project root directory {PROJECT_ROOT} does not exist"

    def test_security_dir_exists(self):
        assert os.path.isdir(SECURITY_DIR), \
            f"Security directory {SECURITY_DIR} does not exist"

    def test_reports_dir_exists(self):
        assert os.path.isdir(REPORTS_DIR), \
            f"Reports directory {REPORTS_DIR} does not exist"

    def test_src_dir_exists(self):
        assert os.path.isdir(SRC_DIR), \
            f"Source directory {SRC_DIR} does not exist"


class TestSecurityConfigFiles:
    """Verify security configuration files exist and have expected content."""

    def test_scanner_config_yaml_exists(self):
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        assert os.path.isfile(config_path), \
            f"Scanner config file {config_path} does not exist"

    def test_semgrepignore_exists(self):
        ignore_path = os.path.join(SECURITY_DIR, ".semgrepignore")
        assert os.path.isfile(ignore_path), \
            f"Semgrep ignore file {ignore_path} does not exist"

    def test_suppressions_yaml_exists(self):
        suppressions_path = os.path.join(SECURITY_DIR, "suppressions.yaml")
        assert os.path.isfile(suppressions_path), \
            f"Suppressions file {suppressions_path} does not exist"

    def test_scanner_config_has_ignore_file_setting(self):
        """Verify the scanner config references an ignore file (even if path is wrong)."""
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        with open(config_path, 'r') as f:
            content = f.read()
        assert "ignore_file" in content.lower() or "semgrepignore" in content.lower(), \
            "Scanner config should reference an ignore file setting"

    def test_scanner_config_has_severity_threshold(self):
        """Verify severity_threshold is set to warning."""
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        with open(config_path, 'r') as f:
            content = f.read()
        assert "severity_threshold" in content.lower(), \
            "Scanner config should have severity_threshold setting"
        assert "warning" in content.lower(), \
            "Scanner config severity_threshold should be set to 'warning'"


class TestRunScanScript:
    """Verify the scan script exists and is executable."""

    def test_run_scan_script_exists(self):
        script_path = os.path.join(PROJECT_ROOT, "run_scan.sh")
        assert os.path.isfile(script_path), \
            f"Run scan script {script_path} does not exist"

    def test_run_scan_script_is_executable(self):
        script_path = os.path.join(PROJECT_ROOT, "run_scan.sh")
        assert os.access(script_path, os.X_OK), \
            f"Run scan script {script_path} is not executable"


class TestScanResults:
    """Verify the scan results file exists and has expected findings."""

    def test_scan_results_file_exists(self):
        results_path = os.path.join(REPORTS_DIR, "scan-results.json")
        assert os.path.isfile(results_path), \
            f"Scan results file {results_path} does not exist"

    def test_scan_results_is_valid_json(self):
        results_path = os.path.join(REPORTS_DIR, "scan-results.json")
        with open(results_path, 'r') as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Scan results file is not valid JSON: {e}")

    def test_scan_results_has_four_findings(self):
        """Initial state should have 4 findings (2 false positives + 2 informational)."""
        results_path = os.path.join(REPORTS_DIR, "scan-results.json")
        with open(results_path, 'r') as f:
            data = json.load(f)

        # Semgrep results typically have a 'results' key
        if isinstance(data, dict) and 'results' in data:
            findings = data['results']
        elif isinstance(data, list):
            findings = data
        else:
            pytest.fail("Unexpected scan results format")

        assert len(findings) == 4, \
            f"Expected 4 findings in initial scan results, found {len(findings)}"

    def test_scan_results_contains_false_positive_rules(self):
        """Verify the two false positive rule IDs are present in findings."""
        results_path = os.path.join(REPORTS_DIR, "scan-results.json")
        with open(results_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'results' in data:
            findings = data['results']
        elif isinstance(data, list):
            findings = data
        else:
            pytest.fail("Unexpected scan results format")

        rule_ids = [f.get('check_id', f.get('rule_id', '')) for f in findings]

        # Check for the expected false positive rules
        hardcoded_password_found = any('hardcoded-password' in rid.lower() for rid in rule_ids)
        sqli_found = any('sqli' in rid.lower() or 'sql' in rid.lower() for rid in rule_ids)

        assert hardcoded_password_found, \
            "Expected hardcoded-password false positive finding not found in results"
        assert sqli_found, \
            "Expected SQL injection false positive finding not found in results"


class TestSourceCodeExists:
    """Verify source code files exist."""

    def test_src_config_defaults_exists(self):
        defaults_path = os.path.join(SRC_DIR, "config", "defaults.py")
        assert os.path.isfile(defaults_path), \
            f"Source file {defaults_path} does not exist (needed for hardcoded-password finding)"

    def test_src_db_queries_exists(self):
        queries_path = os.path.join(SRC_DIR, "db", "queries.py")
        assert os.path.isfile(queries_path), \
            f"Source file {queries_path} does not exist (needed for SQL injection finding)"


class TestToolsAvailable:
    """Verify required tools are installed and available."""

    def test_semgrep_is_installed(self):
        result = subprocess.run(
            ["which", "semgrep"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "semgrep is not installed or not in PATH"

    def test_semgrep_version(self):
        result = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Failed to get semgrep version"
        # Just verify it runs, don't enforce exact version

    def test_python3_is_installed(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Python 3 is not installed or not in PATH"

    def test_jq_is_installed(self):
        result = subprocess.run(
            ["which", "jq"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "jq is not installed or not in PATH"


class TestProjectIsWritable:
    """Verify the project directory is writable."""

    def test_project_root_is_writable(self):
        assert os.access(PROJECT_ROOT, os.W_OK), \
            f"Project root {PROJECT_ROOT} is not writable"

    def test_security_dir_is_writable(self):
        assert os.access(SECURITY_DIR, os.W_OK), \
            f"Security directory {SECURITY_DIR} is not writable"

    def test_reports_dir_is_writable(self):
        assert os.access(REPORTS_DIR, os.W_OK), \
            f"Reports directory {REPORTS_DIR} is not writable"


class TestScanCurrentlyFails:
    """Verify that running the scan currently exits nonzero (the problem state)."""

    def test_run_scan_exits_nonzero(self):
        """The scan should currently fail (exit nonzero) due to the bug."""
        result = subprocess.run(
            ["./run_scan.sh"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode != 0, \
            "Scan should currently exit nonzero (this is the bug state we need to fix)"
