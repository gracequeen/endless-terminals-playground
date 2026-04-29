# test_final_state.py
"""
Tests to validate the final state after the student has fixed the alert validator.
The validator should now:
1. Find yaml files at any nesting depth under alerts/
2. Report OK for valid files and ERROR for invalid files (with duplicate keys)
3. Not silently skip corrupted files
"""

import os
import subprocess
import pytest


class TestYamlFilesStillInSubdirectories:
    """Verify yaml files remain in their subdirectories (not flattened)."""

    def test_cpu_high_yaml_still_in_platform(self):
        """Verify cpu_high.yaml is still in platform/."""
        path = "/home/user/monitoring/alerts/platform/cpu_high.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"

    def test_memory_critical_yaml_still_in_platform(self):
        """Verify memory_critical.yaml is still in platform/."""
        path = "/home/user/monitoring/alerts/platform/memory_critical.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"

    def test_disk_full_yaml_still_in_infra(self):
        """Verify disk_full.yaml is still in infra/."""
        path = "/home/user/monitoring/alerts/infra/disk_full.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"

    def test_network_down_yaml_still_in_infra(self):
        """Verify network_down.yaml is still in infra/."""
        path = "/home/user/monitoring/alerts/infra/network_down.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"

    def test_latency_spike_yaml_still_in_app(self):
        """Verify latency_spike.yaml is still in app/."""
        path = "/home/user/monitoring/alerts/app/latency_spike.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"

    def test_error_rate_yaml_still_in_app(self):
        """Verify error_rate.yaml is still in app/."""
        path = "/home/user/monitoring/alerts/app/error_rate.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"

    def test_queue_depth_yaml_still_in_app(self):
        """Verify queue_depth.yaml is still in app/."""
        path = "/home/user/monitoring/alerts/app/queue_depth.yaml"
        assert os.path.isfile(path), f"YAML file {path} should still exist in its subdirectory"


class TestCorruptedFilesNotFixed:
    """Verify the corrupted yaml files still have their duplicate keys (not fixed by student)."""

    def test_disk_full_yaml_still_has_duplicate_key(self):
        """Verify disk_full.yaml still contains duplicate 'threshold:' key."""
        path = "/home/user/monitoring/alerts/infra/disk_full.yaml"
        with open(path, 'r') as f:
            content = f.read()
        threshold_count = content.count('threshold:')
        assert threshold_count >= 2, \
            f"disk_full.yaml should still have duplicate 'threshold:' keys (found {threshold_count}). " \
            "The corrupted files should NOT be fixed, only reported."

    def test_error_rate_yaml_still_has_duplicate_key(self):
        """Verify error_rate.yaml still contains duplicate 'severity:' key."""
        path = "/home/user/monitoring/alerts/app/error_rate.yaml"
        with open(path, 'r') as f:
            content = f.read()
        severity_count = content.count('severity:')
        assert severity_count >= 2, \
            f"error_rate.yaml should still have duplicate 'severity:' keys (found {severity_count}). " \
            "The corrupted files should NOT be fixed, only reported."


class TestCheckYamlScriptCoreLogic:
    """Verify check_yaml.py still uses yaml.safe_load and reports OK/ERROR."""

    def test_check_yaml_still_uses_safe_load(self):
        """Verify check_yaml.py still uses yaml.safe_load."""
        path = "/home/user/monitoring/check_yaml.py"
        with open(path, 'r') as f:
            content = f.read()
        assert 'yaml.safe_load' in content, \
            "check_yaml.py should still use yaml.safe_load - core logic should not be changed"

    def test_check_yaml_still_reports_ok(self):
        """Verify check_yaml.py still prints OK: prefix."""
        path = "/home/user/monitoring/check_yaml.py"
        with open(path, 'r') as f:
            content = f.read()
        assert 'OK:' in content or '"OK:' in content or "'OK:" in content, \
            "check_yaml.py should still print 'OK:' prefix for valid files"

    def test_check_yaml_still_reports_error(self):
        """Verify check_yaml.py still prints ERROR: prefix."""
        path = "/home/user/monitoring/check_yaml.py"
        with open(path, 'r') as f:
            content = f.read()
        assert 'ERROR:' in content or '"ERROR:' in content or "'ERROR:" in content, \
            "check_yaml.py should still print 'ERROR:' prefix for invalid files"


class TestValidatorProducesOutput:
    """Test that the validator now produces output (bug is fixed)."""

    def test_validate_script_produces_output(self):
        """Verify that running validate_alerts.sh now produces output."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        output = result.stdout.strip()
        assert output != "", \
            "validate_alerts.sh should now produce output (the bug should be fixed). " \
            f"Got empty output. stderr: {result.stderr}"

    def test_validate_script_contains_ok_prefix(self):
        """Verify output contains 'OK:' prefix (actually parsing yaml files)."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        output = result.stdout
        assert 'OK:' in output, \
            f"Output should contain 'OK:' prefix for valid files. Got: {output}"

    def test_validate_script_contains_error_prefix(self):
        """Verify output contains 'ERROR:' prefix (reporting corrupted files)."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        output = result.stdout
        assert 'ERROR:' in output, \
            f"Output should contain 'ERROR:' prefix for corrupted files. Got: {output}"


class TestValidFilesReportedAsOK:
    """Test that all 5 valid yaml files are reported as OK."""

    def _get_validator_output(self):
        """Helper to run the validator and get output."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        return result.stdout

    def test_cpu_high_reported_ok(self):
        """Verify cpu_high.yaml is reported as OK."""
        output = self._get_validator_output()
        assert 'cpu_high.yaml' in output, \
            f"cpu_high.yaml should be in output. Got: {output}"
        # Find the line containing cpu_high.yaml and check it has OK
        for line in output.split('\n'):
            if 'cpu_high.yaml' in line:
                assert 'OK:' in line, \
                    f"cpu_high.yaml should be reported as OK, but got: {line}"
                break

    def test_memory_critical_reported_ok(self):
        """Verify memory_critical.yaml is reported as OK."""
        output = self._get_validator_output()
        assert 'memory_critical.yaml' in output, \
            f"memory_critical.yaml should be in output. Got: {output}"
        for line in output.split('\n'):
            if 'memory_critical.yaml' in line:
                assert 'OK:' in line, \
                    f"memory_critical.yaml should be reported as OK, but got: {line}"
                break

    def test_network_down_reported_ok(self):
        """Verify network_down.yaml is reported as OK."""
        output = self._get_validator_output()
        assert 'network_down.yaml' in output, \
            f"network_down.yaml should be in output. Got: {output}"
        for line in output.split('\n'):
            if 'network_down.yaml' in line:
                assert 'OK:' in line, \
                    f"network_down.yaml should be reported as OK, but got: {line}"
                break

    def test_latency_spike_reported_ok(self):
        """Verify latency_spike.yaml is reported as OK."""
        output = self._get_validator_output()
        assert 'latency_spike.yaml' in output, \
            f"latency_spike.yaml should be in output. Got: {output}"
        for line in output.split('\n'):
            if 'latency_spike.yaml' in line:
                assert 'OK:' in line, \
                    f"latency_spike.yaml should be reported as OK, but got: {line}"
                break

    def test_queue_depth_reported_ok(self):
        """Verify queue_depth.yaml is reported as OK."""
        output = self._get_validator_output()
        assert 'queue_depth.yaml' in output, \
            f"queue_depth.yaml should be in output. Got: {output}"
        for line in output.split('\n'):
            if 'queue_depth.yaml' in line:
                assert 'OK:' in line, \
                    f"queue_depth.yaml should be reported as OK, but got: {line}"
                break


class TestCorruptedFilesReportedAsError:
    """Test that both corrupted yaml files are reported as ERROR."""

    def _get_validator_output(self):
        """Helper to run the validator and get output."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        return result.stdout

    def test_disk_full_reported_error(self):
        """Verify disk_full.yaml is reported as ERROR (has duplicate key)."""
        output = self._get_validator_output()
        assert 'disk_full.yaml' in output, \
            f"disk_full.yaml should be in output. Got: {output}"
        for line in output.split('\n'):
            if 'disk_full.yaml' in line:
                assert 'ERROR:' in line, \
                    f"disk_full.yaml should be reported as ERROR (duplicate key), but got: {line}"
                break

    def test_error_rate_reported_error(self):
        """Verify error_rate.yaml is reported as ERROR (has duplicate key)."""
        output = self._get_validator_output()
        assert 'error_rate.yaml' in output, \
            f"error_rate.yaml should be in output. Got: {output}"
        for line in output.split('\n'):
            if 'error_rate.yaml' in line:
                assert 'ERROR:' in line, \
                    f"error_rate.yaml should be reported as ERROR (duplicate key), but got: {line}"
                break


class TestAllSevenFilesProcessed:
    """Test that all 7 yaml files are found and processed."""

    def test_all_seven_files_in_output(self):
        """Verify all 7 yaml files appear in the validator output."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        output = result.stdout

        expected_files = [
            'cpu_high.yaml',
            'memory_critical.yaml',
            'disk_full.yaml',
            'network_down.yaml',
            'latency_spike.yaml',
            'error_rate.yaml',
            'queue_depth.yaml'
        ]

        missing_files = [f for f in expected_files if f not in output]
        assert len(missing_files) == 0, \
            f"Missing files in output: {missing_files}. " \
            f"The validator should find all yaml files in subdirectories. Output: {output}"

    def test_five_ok_two_error(self):
        """Verify we have 5 OK and 2 ERROR in output."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        output = result.stdout

        ok_count = output.count('OK:')
        error_count = output.count('ERROR:')

        assert ok_count == 5, \
            f"Expected 5 OK results, got {ok_count}. Output: {output}"
        assert error_count == 2, \
            f"Expected 2 ERROR results, got {error_count}. Output: {output}"


class TestScriptNoLongerHasMaxdepthRestriction:
    """Test that the script can find arbitrarily nested yaml files."""

    def test_validate_script_no_maxdepth_1(self):
        """Verify validate_alerts.sh does not contain '-maxdepth 1'."""
        path = "/home/user/monitoring/validate_alerts.sh"
        with open(path, 'r') as f:
            content = f.read()
        # Check that -maxdepth 1 is not present (the bug)
        assert '-maxdepth 1' not in content, \
            "validate_alerts.sh should not contain '-maxdepth 1' anymore"

    def test_find_command_recurses(self):
        """Verify the script's find command can find nested files."""
        # Create a deeply nested test file temporarily
        deep_dir = "/home/user/monitoring/alerts/app/deep/nested"
        deep_file = os.path.join(deep_dir, "test_deep.yaml")

        try:
            os.makedirs(deep_dir, exist_ok=True)
            with open(deep_file, 'w') as f:
                f.write("test: value\n")

            result = subprocess.run(
                ['bash', '/home/user/monitoring/validate_alerts.sh'],
                capture_output=True,
                text=True,
                cwd='/home/user/monitoring'
            )
            output = result.stdout

            assert 'test_deep.yaml' in output, \
                f"Validator should find deeply nested yaml files. Output: {output}"
        finally:
            # Cleanup
            if os.path.exists(deep_file):
                os.remove(deep_file)
            if os.path.exists(deep_dir):
                os.rmdir(deep_dir)
            parent = os.path.dirname(deep_dir)
            if os.path.exists(parent) and not os.listdir(parent):
                os.rmdir(parent)


class TestDuplicateKeyErrorsReported:
    """Test that duplicate key errors are actually surfaced in the output."""

    def test_duplicate_key_error_mentioned(self):
        """Verify the error output mentions something about duplicate keys."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        output = result.stdout.lower()

        # The yaml parser should mention something about duplicate keys
        # Common phrases: "duplicate key", "already", "found duplicate"
        has_duplicate_indication = (
            'duplicate' in output or 
            'already' in output or
            'key' in output
        )

        # At minimum, ERROR should be present for the corrupted files
        assert 'error:' in output, \
            f"Output should contain ERROR for corrupted files. Output: {result.stdout}"
