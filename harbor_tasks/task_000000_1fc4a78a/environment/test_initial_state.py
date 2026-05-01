# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student performs the task.
This verifies the monitoring directory structure, scripts, and yaml files exist as expected.
"""

import os
import stat
import subprocess
import pytest


class TestMonitoringDirectoryStructure:
    """Test that the monitoring directory and its structure exist."""

    def test_monitoring_directory_exists(self):
        """Verify /home/user/monitoring/ directory exists."""
        path = "/home/user/monitoring"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_monitoring_directory_writable(self):
        """Verify /home/user/monitoring/ is writable."""
        path = "/home/user/monitoring"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_alerts_directory_exists(self):
        """Verify /home/user/monitoring/alerts/ directory exists."""
        path = "/home/user/monitoring/alerts"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_platform_subdirectory_exists(self):
        """Verify /home/user/monitoring/alerts/platform/ directory exists."""
        path = "/home/user/monitoring/alerts/platform"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_infra_subdirectory_exists(self):
        """Verify /home/user/monitoring/alerts/infra/ directory exists."""
        path = "/home/user/monitoring/alerts/infra"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_app_subdirectory_exists(self):
        """Verify /home/user/monitoring/alerts/app/ directory exists."""
        path = "/home/user/monitoring/alerts/app"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestValidateAlertsScript:
    """Test that validate_alerts.sh exists and is properly configured."""

    def test_validate_alerts_script_exists(self):
        """Verify validate_alerts.sh exists."""
        path = "/home/user/monitoring/validate_alerts.sh"
        assert os.path.isfile(path), f"Script {path} does not exist"

    def test_validate_alerts_script_executable(self):
        """Verify validate_alerts.sh is executable."""
        path = "/home/user/monitoring/validate_alerts.sh"
        assert os.access(path, os.X_OK), f"Script {path} is not executable"

    def test_validate_alerts_script_contains_find_command(self):
        """Verify validate_alerts.sh contains a find command."""
        path = "/home/user/monitoring/validate_alerts.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'find' in content, f"Script {path} does not contain 'find' command"

    def test_validate_alerts_script_contains_maxdepth(self):
        """Verify validate_alerts.sh contains -maxdepth 1 (the bug)."""
        path = "/home/user/monitoring/validate_alerts.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert '-maxdepth 1' in content or 'maxdepth 1' in content, \
            f"Script {path} does not contain '-maxdepth 1' - the bug may not be present"

    def test_validate_alerts_script_references_check_yaml(self):
        """Verify validate_alerts.sh references check_yaml.py."""
        path = "/home/user/monitoring/validate_alerts.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'check_yaml.py' in content, f"Script {path} does not reference check_yaml.py"


class TestCheckYamlScript:
    """Test that check_yaml.py exists and has expected content."""

    def test_check_yaml_script_exists(self):
        """Verify check_yaml.py exists."""
        path = "/home/user/monitoring/check_yaml.py"
        assert os.path.isfile(path), f"Script {path} does not exist"

    def test_check_yaml_script_uses_yaml_safe_load(self):
        """Verify check_yaml.py uses yaml.safe_load."""
        path = "/home/user/monitoring/check_yaml.py"
        with open(path, 'r') as f:
            content = f.read()
        assert 'yaml.safe_load' in content, f"Script {path} does not use yaml.safe_load"

    def test_check_yaml_script_prints_ok(self):
        """Verify check_yaml.py prints OK for valid files."""
        path = "/home/user/monitoring/check_yaml.py"
        with open(path, 'r') as f:
            content = f.read()
        assert 'OK:' in content or '"OK:' in content or "'OK:" in content, \
            f"Script {path} does not print 'OK:' prefix"

    def test_check_yaml_script_prints_error(self):
        """Verify check_yaml.py prints ERROR for invalid files."""
        path = "/home/user/monitoring/check_yaml.py"
        with open(path, 'r') as f:
            content = f.read()
        assert 'ERROR:' in content or '"ERROR:' in content or "'ERROR:" in content, \
            f"Script {path} does not print 'ERROR:' prefix"


class TestYamlFilesExist:
    """Test that all expected yaml files exist in their subdirectories."""

    def test_cpu_high_yaml_exists(self):
        """Verify cpu_high.yaml exists in platform/."""
        path = "/home/user/monitoring/alerts/platform/cpu_high.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_memory_critical_yaml_exists(self):
        """Verify memory_critical.yaml exists in platform/."""
        path = "/home/user/monitoring/alerts/platform/memory_critical.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_disk_full_yaml_exists(self):
        """Verify disk_full.yaml exists in infra/ (this one has duplicate keys)."""
        path = "/home/user/monitoring/alerts/infra/disk_full.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_network_down_yaml_exists(self):
        """Verify network_down.yaml exists in infra/."""
        path = "/home/user/monitoring/alerts/infra/network_down.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_latency_spike_yaml_exists(self):
        """Verify latency_spike.yaml exists in app/."""
        path = "/home/user/monitoring/alerts/app/latency_spike.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_error_rate_yaml_exists(self):
        """Verify error_rate.yaml exists in app/ (this one has duplicate keys)."""
        path = "/home/user/monitoring/alerts/app/error_rate.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_queue_depth_yaml_exists(self):
        """Verify queue_depth.yaml exists in app/."""
        path = "/home/user/monitoring/alerts/app/queue_depth.yaml"
        assert os.path.isfile(path), f"YAML file {path} does not exist"

    def test_no_yaml_files_in_alerts_root(self):
        """Verify there are no yaml files directly in alerts/ (they're all in subdirs)."""
        alerts_dir = "/home/user/monitoring/alerts"
        yaml_files_in_root = [f for f in os.listdir(alerts_dir) 
                              if f.endswith('.yaml') and os.path.isfile(os.path.join(alerts_dir, f))]
        assert len(yaml_files_in_root) == 0, \
            f"Found yaml files directly in {alerts_dir}: {yaml_files_in_root}. They should be in subdirectories."


class TestPythonAndDependencies:
    """Test that required Python and dependencies are available."""

    def test_python3_available(self):
        """Verify python3 is installed and accessible."""
        result = subprocess.run(['which', 'python3'], capture_output=True, text=True)
        assert result.returncode == 0, "python3 is not installed or not in PATH"

    def test_pyyaml_installed(self):
        """Verify pyyaml module is installed."""
        result = subprocess.run(['python3', '-c', 'import yaml'], capture_output=True, text=True)
        assert result.returncode == 0, f"pyyaml module is not installed: {result.stderr}"

    def test_yamllint_not_installed(self):
        """Verify yamllint is NOT installed (per initial state)."""
        result = subprocess.run(['which', 'yamllint'], capture_output=True, text=True)
        assert result.returncode != 0, "yamllint should NOT be installed in initial state"


class TestCurrentBugBehavior:
    """Test that the current bug exists - script produces no output due to maxdepth."""

    def test_validate_script_produces_no_output(self):
        """Verify that running validate_alerts.sh currently produces no output (the bug)."""
        result = subprocess.run(
            ['bash', '/home/user/monitoring/validate_alerts.sh'],
            capture_output=True,
            text=True,
            cwd='/home/user/monitoring'
        )
        # The bug is that with -maxdepth 1, no files are found, so no output
        output = result.stdout.strip()
        assert output == "", \
            f"Expected no output (the bug), but got: {output}"

    def test_find_with_maxdepth_returns_nothing(self):
        """Verify find with -maxdepth 1 returns no yaml files."""
        result = subprocess.run(
            ['find', '/home/user/monitoring/alerts', '-maxdepth', '1', '-name', '*.yaml'],
            capture_output=True,
            text=True
        )
        found_files = result.stdout.strip()
        assert found_files == "", \
            f"Expected no files with -maxdepth 1, but found: {found_files}"

    def test_find_without_maxdepth_returns_files(self):
        """Verify find without -maxdepth 1 DOES return yaml files (proving the fix)."""
        result = subprocess.run(
            ['find', '/home/user/monitoring/alerts', '-name', '*.yaml'],
            capture_output=True,
            text=True
        )
        found_files = result.stdout.strip().split('\n')
        found_files = [f for f in found_files if f]  # Remove empty strings
        assert len(found_files) == 7, \
            f"Expected 7 yaml files without maxdepth restriction, found {len(found_files)}: {found_files}"


class TestCorruptedYamlFiles:
    """Test that the corrupted yaml files actually have duplicate keys."""

    def test_disk_full_yaml_has_duplicate_key(self):
        """Verify disk_full.yaml contains duplicate 'threshold:' key."""
        path = "/home/user/monitoring/alerts/infra/disk_full.yaml"
        with open(path, 'r') as f:
            content = f.read()
        # Count occurrences of 'threshold:' at the start of a line or after whitespace
        threshold_count = content.count('threshold:')
        assert threshold_count >= 2, \
            f"Expected duplicate 'threshold:' keys in {path}, found {threshold_count} occurrence(s)"

    def test_error_rate_yaml_has_duplicate_key(self):
        """Verify error_rate.yaml contains duplicate 'severity:' key."""
        path = "/home/user/monitoring/alerts/app/error_rate.yaml"
        with open(path, 'r') as f:
            content = f.read()
        # Count occurrences of 'severity:'
        severity_count = content.count('severity:')
        assert severity_count >= 2, \
            f"Expected duplicate 'severity:' keys in {path}, found {severity_count} occurrence(s)"
