# test_final_state.py
"""
Tests to validate the final state after the student has fixed the SAST scan
suppression configuration. The scan should now pass (exit 0) with only 2
informational findings, not 4.
"""

import json
import os
import subprocess
import pytest


PROJECT_ROOT = "/home/user/project"
SECURITY_DIR = os.path.join(PROJECT_ROOT, ".security")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
SRC_DIR = os.path.join(PROJECT_ROOT, "src")


class TestScanNowPasses:
    """Verify that the scan now exits 0 after the fix."""

    def test_run_scan_exits_zero(self):
        """The scan should now pass (exit 0) after fixing the suppression config."""
        result = subprocess.run(
            ["./run_scan.sh"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, \
            f"Scan should exit 0 after fix, but got exit code {result.returncode}.\n" \
            f"stdout: {result.stdout}\nstderr: {result.stderr}"


class TestScanResultsCorrect:
    """Verify the scan results now contain exactly 2 findings (not 4)."""

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

    def test_scan_results_has_exactly_two_findings(self):
        """After fix, should have exactly 2 findings (informational ones only)."""
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

        assert len(findings) == 2, \
            f"Expected exactly 2 findings after fix (informational ones), found {len(findings)}. " \
            f"False positives should have been suppressed."

    def test_false_positives_are_suppressed(self):
        """The hardcoded-password and sqli false positives should no longer appear."""
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

        # These false positives should NOT be present anymore
        hardcoded_password_found = any('hardcoded-password' in rid.lower() for rid in rule_ids)
        sqli_found = any('sqli' in rid.lower() for rid in rule_ids)

        assert not hardcoded_password_found, \
            "Hardcoded-password false positive should have been suppressed but is still present"
        assert not sqli_found, \
            "SQL injection false positive should have been suppressed but is still present"


class TestAntiShortcutGuards:
    """Ensure the fix was done properly, not by disabling scanning entirely."""

    def test_grep_rule_id_count_is_two(self):
        """Using grep to count rule_id occurrences should return exactly 2."""
        results_path = os.path.join(REPORTS_DIR, "scan-results.json")
        result = subprocess.run(
            ["grep", "-c", '"check_id"', results_path],
            capture_output=True,
            text=True
        )
        # grep -c returns the count as a string
        # If no matches, grep exits 1 and outputs "0"
        count_str = result.stdout.strip()
        try:
            count = int(count_str)
        except ValueError:
            # Try alternative field name
            result2 = subprocess.run(
                ["grep", "-c", '"rule_id"', results_path],
                capture_output=True,
                text=True
            )
            count_str = result2.stdout.strip()
            count = int(count_str) if count_str else 0

        assert count == 2, \
            f"Expected exactly 2 findings (rule_id/check_id occurrences), got {count}. " \
            f"This proves false positives were suppressed, not all scanning disabled."

    def test_scanner_config_still_exists(self):
        """Scanner config must still exist."""
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        assert os.path.isfile(config_path), \
            f"Scanner config {config_path} must still exist - don't delete it!"

    def test_severity_threshold_still_warning(self):
        """severity_threshold must still be 'warning' (not weakened to 'error')."""
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        with open(config_path, 'r') as f:
            content = f.read().lower()

        assert "severity_threshold" in content, \
            "Scanner config must still have severity_threshold setting"

        # Check that it's set to warning, not error
        # Look for patterns like "severity_threshold: warning" or "severity_threshold:warning"
        import re
        match = re.search(r'severity_threshold\s*:\s*(\w+)', content)
        if match:
            threshold_value = match.group(1)
            assert threshold_value == "warning", \
                f"severity_threshold must remain 'warning', not '{threshold_value}'. " \
                f"Don't weaken the threshold to dodge findings!"

    def test_scanner_config_has_rules(self):
        """Scanner config must still specify semgrep rules (not empty ruleset)."""
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        with open(config_path, 'r') as f:
            content = f.read()

        # Should have some rules configured - look for common patterns
        has_rules = any(pattern in content.lower() for pattern in [
            'rules', 'config', 'p/', 'r/', 'auto', 'python'
        ])
        assert has_rules, \
            "Scanner config must still have rules configured - don't disable scanning!"

    def test_security_dir_still_has_config(self):
        """.security/ directory must still contain scanner-config.yaml."""
        assert os.path.isdir(SECURITY_DIR), \
            f"Security directory {SECURITY_DIR} must still exist"
        config_path = os.path.join(SECURITY_DIR, "scanner-config.yaml")
        assert os.path.isfile(config_path), \
            f"scanner-config.yaml must still exist in {SECURITY_DIR}"


class TestSourceCodeUnchanged:
    """Verify source code files were not modified to remove the 'vulnerabilities'."""

    def test_src_config_defaults_exists(self):
        defaults_path = os.path.join(SRC_DIR, "config", "defaults.py")
        assert os.path.isfile(defaults_path), \
            f"Source file {defaults_path} must still exist"

    def test_src_db_queries_exists(self):
        queries_path = os.path.join(SRC_DIR, "db", "queries.py")
        assert os.path.isfile(queries_path), \
            f"Source file {queries_path} must still exist"

    def test_src_config_defaults_has_content(self):
        """defaults.py should still have the code that triggers the false positive."""
        defaults_path = os.path.join(SRC_DIR, "config", "defaults.py")
        with open(defaults_path, 'r') as f:
            content = f.read()
        # Should still have some password-related config (the false positive trigger)
        assert len(content) > 10, \
            "defaults.py appears to have been emptied - source code must remain unchanged"

    def test_src_db_queries_has_content(self):
        """queries.py should still have the code that triggers the false positive."""
        queries_path = os.path.join(SRC_DIR, "db", "queries.py")
        with open(queries_path, 'r') as f:
            content = f.read()
        # Should still have SQL-related code (the false positive trigger)
        assert len(content) > 10, \
            "queries.py appears to have been emptied - source code must remain unchanged"


class TestScannerStillFunctional:
    """Verify the scanner is still actually running and catching things."""

    def test_informational_findings_still_present(self):
        """The 2 informational/legitimate findings should still appear."""
        results_path = os.path.join(REPORTS_DIR, "scan-results.json")
        with open(results_path, 'r') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'results' in data:
            findings = data['results']
        elif isinstance(data, list):
            findings = data
        else:
            pytest.fail("Unexpected scan results format")

        # Should have exactly 2 findings - the informational ones
        assert len(findings) == 2, \
            f"Scanner should still report 2 informational findings, got {len(findings)}"

    def test_semgrep_still_works(self):
        """Verify semgrep itself is still functional."""
        result = subprocess.run(
            ["semgrep", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "semgrep should still be functional"


class TestIgnoreFileFix:
    """Verify the ignore file is now being properly applied."""

    def test_semgrepignore_or_equivalent_exists(self):
        """Some form of ignore/suppression file should exist."""
        possible_ignore_files = [
            os.path.join(SECURITY_DIR, ".semgrepignore"),
            os.path.join(PROJECT_ROOT, ".semgrepignore"),
            os.path.join(SECURITY_DIR, "suppressions.yaml"),
        ]

        exists = any(os.path.isfile(f) for f in possible_ignore_files)
        assert exists, \
            "An ignore/suppression file should exist to suppress false positives"

    def test_run_scan_script_still_exists(self):
        """The run_scan.sh script should still exist."""
        script_path = os.path.join(PROJECT_ROOT, "run_scan.sh")
        assert os.path.isfile(script_path), \
            f"run_scan.sh script must still exist at {script_path}"

    def test_run_scan_script_still_executable(self):
        """The run_scan.sh script should still be executable."""
        script_path = os.path.join(PROJECT_ROOT, "run_scan.sh")
        assert os.access(script_path, os.X_OK), \
            f"run_scan.sh must still be executable"
