# test_final_state.py
"""
Tests to validate the final state after the student has fixed the dashboard
checksum verification issues. The dashboard should now run successfully.
"""

import os
import re
import subprocess
import hashlib
import json
import pytest


HOME = "/home/user"
MONITOR_DIR = os.path.join(HOME, "monitor")
CONFIG_DIR = os.path.join(MONITOR_DIR, "config")
DASHBOARD_PATH = os.path.join(MONITOR_DIR, "dashboard.py")
CHECKSUMS_PATH = os.path.join(CONFIG_DIR, "checksums.sha256")
MANIFEST_PATH = os.path.join(CONFIG_DIR, "manifest.json")
SCHEMA_METRICS_PATH = os.path.join(CONFIG_DIR, "schema_metrics.json")
SCHEMA_LOGS_PATH = os.path.join(CONFIG_DIR, "schema_logs.json")
SCHEMA_TRACES_PATH = os.path.join(CONFIG_DIR, "schema_traces.json")


class TestDashboardExecutesSuccessfully:
    """Test that the dashboard now runs without errors."""

    def test_dashboard_exits_with_zero(self):
        """Dashboard should exit with code 0 (success)."""
        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        assert result.returncode == 0, (
            f"Dashboard should exit with code 0, but got {result.returncode}. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_dashboard_shows_metrics_summary(self):
        """Dashboard output should contain 'Metrics Summary'."""
        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        combined_output = result.stdout + result.stderr
        assert 'Metrics Summary' in combined_output or 'metrics summary' in combined_output.lower(), (
            f"Dashboard output should contain 'Metrics Summary'. "
            f"Output: {combined_output}"
        )

    def test_dashboard_lists_all_services(self):
        """Dashboard output should list all three services."""
        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        combined_output = result.stdout + result.stderr
        expected_services = ['metrics-api', 'logs-collector', 'traces-exporter']

        for service in expected_services:
            assert service in combined_output, (
                f"Dashboard output should list service '{service}'. "
                f"Output: {combined_output}"
            )

    def test_dashboard_no_integrity_errors(self):
        """Dashboard output should not contain any integrity errors."""
        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        combined_output = result.stdout + result.stderr
        assert 'Integrity error' not in combined_output, (
            f"Dashboard should not show any integrity errors. "
            f"Output: {combined_output}"
        )


class TestVerificationLogicStillPresent:
    """Test that checksum verification logic was not removed/bypassed."""

    def test_dashboard_still_has_verification_code(self):
        """Dashboard should still contain checksum verification logic."""
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        # Count occurrences of verification-related keywords
        checksum_keywords = ['verify_checksums', 'SHA256', 'checksum', 'hashlib']
        count = sum(1 for kw in checksum_keywords if kw in content)

        assert count >= 2, (
            f"Dashboard must still contain checksum verification logic. "
            f"Expected at least 2 of {checksum_keywords} to be present, found {count}. "
            "Verification logic should not be removed or bypassed."
        )

    def test_verify_checksums_function_exists(self):
        """The verify_checksums function should still exist."""
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        assert 'def verify_checksums' in content or 'verify_checksums' in content, (
            "Dashboard should still contain verify_checksums function or call. "
            "The verification logic should not be removed."
        )

    def test_checksums_file_still_exists(self):
        """The checksums.sha256 file should not be deleted."""
        assert os.path.isfile(CHECKSUMS_PATH), (
            f"Checksums file should still exist at {CHECKSUMS_PATH}. "
            "The fix should not involve deleting the checksums file."
        )


class TestSchemaFilesUnchanged:
    """Test that schema files were not modified (invariants)."""

    def test_manifest_json_unchanged(self):
        """manifest.json should still define the three services."""
        with open(MANIFEST_PATH, 'r') as f:
            data = json.load(f)

        # Check that it still defines the three services
        services = ['metrics-api', 'logs-collector', 'traces-exporter']

        # The manifest should reference these services somehow
        content_str = json.dumps(data)
        for service in services:
            assert service in content_str, (
                f"manifest.json should still define service '{service}'. "
                "The manifest content should not be changed."
            )

    def test_schema_files_exist(self):
        """All schema files should still exist."""
        schema_files = [SCHEMA_METRICS_PATH, SCHEMA_LOGS_PATH, SCHEMA_TRACES_PATH]
        for path in schema_files:
            assert os.path.isfile(path), (
                f"Schema file should still exist at {path}"
            )


class TestChecksumsFileCorrectness:
    """Test that checksums.sha256 now has correct checksums."""

    def test_checksums_match_actual_files(self):
        """All checksums in the file should match actual file hashes."""
        with open(CHECKSUMS_PATH, 'r') as f:
            content = f.read()

        # Parse BSD-style checksums
        pattern = r'SHA256 \(([^)]+)\) = ([a-f0-9]+)'
        matches = re.findall(pattern, content)

        assert len(matches) >= 4, (
            f"Checksums file should contain at least 4 entries, found {len(matches)}"
        )

        for filename, stored_hash in matches:
            filepath = os.path.join(CONFIG_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()

                # The stored hash (after proper parsing) should match actual
                stored_hash_clean = stored_hash.strip()
                assert stored_hash_clean == actual_hash, (
                    f"Checksum mismatch for {filename}: "
                    f"stored={stored_hash_clean}, actual={actual_hash}"
                )

    def test_schema_logs_checksum_is_correct(self):
        """schema_logs.json should now have the correct checksum."""
        with open(CHECKSUMS_PATH, 'r') as f:
            content = f.read()

        match = re.search(r'SHA256 \(schema_logs\.json\) = ([a-f0-9]+)', content)
        assert match, "Could not find schema_logs.json entry in checksums file"

        stored_hash = match.group(1).strip()

        with open(SCHEMA_LOGS_PATH, 'rb') as f:
            actual_hash = hashlib.sha256(f.read()).hexdigest()

        assert stored_hash == actual_hash, (
            f"schema_logs.json checksum should now be correct. "
            f"Stored: {stored_hash}, Actual: {actual_hash}"
        )


class TestBugsFixed:
    """Test that both bugs have been addressed."""

    def test_no_trailing_space_issue(self):
        """
        Either the trailing space was removed from checksums.sha256,
        or the parsing code was fixed to handle it properly.
        The dashboard running successfully proves this is fixed.
        """
        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        # If dashboard runs successfully, the trailing space issue is resolved
        assert result.returncode == 0, (
            f"Dashboard should run successfully, indicating trailing space issue is fixed. "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_verification_actually_runs(self):
        """
        Verify that checksum verification is actually being performed,
        not just bypassed. We do this by checking the code still has
        the verification logic and the dashboard succeeds.
        """
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        # Check that verification logic exists
        has_hashlib = 'hashlib' in content
        has_sha256 = 'sha256' in content.lower() or 'SHA256' in content
        has_verify = 'verify' in content.lower()

        assert has_hashlib or has_sha256, (
            "Dashboard should still use hashlib or SHA256 for verification"
        )

        # Run dashboard and confirm it works
        result = subprocess.run(
            ['python3', DASHBOARD_PATH],
            capture_output=True,
            text=True,
            cwd=MONITOR_DIR
        )

        assert result.returncode == 0, (
            "Dashboard should run successfully with verification enabled"
        )


class TestAntiShortcutGuards:
    """Tests to ensure the fix wasn't a shortcut/bypass."""

    def test_verification_keywords_count(self):
        """
        grep -c "verify_checksums|SHA256|checksum" should return at least 2
        """
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        keywords = ['verify_checksums', 'SHA256', 'checksum']
        count = 0
        for keyword in keywords:
            if keyword in content:
                count += content.count(keyword)

        # We need at least 2 occurrences total
        assert count >= 2, (
            f"Dashboard should contain at least 2 occurrences of verification keywords "
            f"(verify_checksums, SHA256, checksum). Found {count}. "
            "This suggests verification logic may have been removed."
        )

    def test_verify_checksums_not_always_true(self):
        """Verify that verify_checksums doesn't always return True."""
        with open(DASHBOARD_PATH, 'r') as f:
            content = f.read()

        # Look for suspicious patterns that would bypass verification
        suspicious_patterns = [
            r'def verify_checksums.*:\s*return True',
            r'verify_checksums\s*=\s*lambda.*True',
            r'def verify_checksums.*:\s*pass',
        ]

        for pattern in suspicious_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                # Check if it's a trivial bypass
                matched_text = match.group(0)
                if 'return True' in matched_text and len(matched_text) < 50:
                    pytest.fail(
                        f"verify_checksums appears to be bypassed with always-True return. "
                        f"Found: {matched_text}"
                    )

    def test_checksums_file_not_empty(self):
        """Checksums file should not be empty or trivial."""
        with open(CHECKSUMS_PATH, 'r') as f:
            content = f.read()

        assert len(content.strip()) > 100, (
            "Checksums file should not be empty or trivially small. "
            f"Content length: {len(content.strip())}"
        )

        # Should have at least 4 SHA256 entries
        sha_count = content.count('SHA256')
        assert sha_count >= 4, (
            f"Checksums file should have at least 4 SHA256 entries, found {sha_count}"
        )
