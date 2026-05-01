# test_initial_state.py
"""
Tests to validate the initial state of the monitoring stack before the student fixes the bug.
"""

import os
import pytest
import configparser
import subprocess


HOME = "/home/user"
MONITOR_DIR = os.path.join(HOME, "monitor")
CONFIG_DIR = os.path.join(MONITOR_DIR, "config")
DATA_DIR = os.path.join(MONITOR_DIR, "data")
LOGS_DIR = os.path.join(MONITOR_DIR, "logs")


class TestDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_monitor_directory_exists(self):
        assert os.path.isdir(MONITOR_DIR), f"Monitor directory {MONITOR_DIR} does not exist"

    def test_config_directory_exists(self):
        assert os.path.isdir(CONFIG_DIR), f"Config directory {CONFIG_DIR} does not exist"

    def test_data_directory_exists(self):
        assert os.path.isdir(DATA_DIR), f"Data directory {DATA_DIR} does not exist"

    def test_data_directory_is_writable(self):
        assert os.access(DATA_DIR, os.W_OK), f"Data directory {DATA_DIR} is not writable"

    def test_monitor_directory_is_writable(self):
        assert os.access(MONITOR_DIR, os.W_OK), f"Monitor directory {MONITOR_DIR} is not writable"


class TestPythonScripts:
    """Test that the required Python scripts exist."""

    def test_collector_py_exists(self):
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        assert os.path.isfile(collector_path), f"collector.py not found at {collector_path}"

    def test_aggregator_py_exists(self):
        aggregator_path = os.path.join(MONITOR_DIR, "aggregator.py")
        assert os.path.isfile(aggregator_path), f"aggregator.py not found at {aggregator_path}"

    def test_alert_py_exists(self):
        alert_path = os.path.join(MONITOR_DIR, "alert.py")
        assert os.path.isfile(alert_path), f"alert.py not found at {alert_path}"

    def test_run_sh_exists(self):
        run_sh_path = os.path.join(MONITOR_DIR, "run.sh")
        assert os.path.isfile(run_sh_path), f"run.sh not found at {run_sh_path}"


class TestConfigFiles:
    """Test that the required config files exist and have expected content."""

    def test_sources_yaml_exists(self):
        sources_path = os.path.join(CONFIG_DIR, "sources.yaml")
        assert os.path.isfile(sources_path), f"sources.yaml not found at {sources_path}"

    def test_thresholds_yaml_exists(self):
        thresholds_path = os.path.join(CONFIG_DIR, "thresholds.yaml")
        assert os.path.isfile(thresholds_path), f"thresholds.yaml not found at {thresholds_path}"

    def test_collector_conf_exists(self):
        collector_conf_path = os.path.join(CONFIG_DIR, "collector.conf")
        assert os.path.isfile(collector_conf_path), f"collector.conf not found at {collector_conf_path}"

    def test_collector_conf_has_runtime_section(self):
        """Verify collector.conf has a [runtime] section with max_cycles."""
        collector_conf_path = os.path.join(CONFIG_DIR, "collector.conf")
        config = configparser.ConfigParser()
        config.read(collector_conf_path)

        assert 'runtime' in config.sections(), \
            f"collector.conf does not have a [runtime] section. Sections found: {config.sections()}"

    def test_collector_conf_has_max_cycles_set_to_5(self):
        """Verify the bug exists: max_cycles is set to 5 (the problematic value)."""
        collector_conf_path = os.path.join(CONFIG_DIR, "collector.conf")
        config = configparser.ConfigParser()
        config.read(collector_conf_path)

        assert config.has_option('runtime', 'max_cycles'), \
            "collector.conf [runtime] section does not have max_cycles option"

        max_cycles = config.getint('runtime', 'max_cycles')
        assert max_cycles == 5, \
            f"Expected max_cycles to be 5 (the bug), but found {max_cycles}"


class TestCollectorPyStructure:
    """Test that collector.py has the expected structure with the bug."""

    def test_collector_uses_configparser(self):
        """Verify collector.py imports and uses configparser."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'configparser' in content, \
            "collector.py does not import configparser"

    def test_collector_reads_collector_conf(self):
        """Verify collector.py reads collector.conf."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'collector.conf' in content, \
            "collector.py does not reference collector.conf"

    def test_collector_has_max_cycles_logic(self):
        """Verify collector.py has the max_cycles exit logic (the bug)."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'max_cycles' in content, \
            "collector.py does not contain max_cycles logic"

    def test_collector_is_valid_python(self):
        """Verify collector.py is valid Python syntax."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        result = subprocess.run(
            ['python3', '-m', 'py_compile', collector_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"collector.py has syntax errors: {result.stderr}"


class TestPythonEnvironment:
    """Test that Python environment is properly set up."""

    def test_python3_available(self):
        """Verify Python 3 is available."""
        result = subprocess.run(
            ['python3', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"
        assert 'Python 3' in result.stdout, f"Unexpected Python version: {result.stdout}"

    def test_pyyaml_installed(self):
        """Verify PyYAML is installed."""
        result = subprocess.run(
            ['python3', '-c', 'import yaml'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"PyYAML is not installed: {result.stderr}"


class TestNoProcessesRunning:
    """Test that no collector processes are currently running."""

    def test_no_collector_process_running(self):
        """Verify no collector.py process is currently running."""
        result = subprocess.run(
            ['pgrep', '-f', 'collector.py'],
            capture_output=True,
            text=True
        )
        # pgrep returns 1 if no processes found, which is what we want
        assert result.returncode == 1, \
            f"collector.py process is already running (should not be): {result.stdout}"


class TestDataDirectoryInitialState:
    """Test that data directory is in expected initial state."""

    def test_data_directory_empty_or_no_metrics(self):
        """Verify data directory doesn't have metrics.jsonl or it's empty."""
        metrics_path = os.path.join(DATA_DIR, "metrics.jsonl")
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                content = f.read().strip()
            # It's okay if the file exists but is empty
            assert content == "", \
                f"metrics.jsonl already has content, should be empty initially: {len(content)} bytes"


class TestRunShStructure:
    """Test run.sh doesn't have infinite loop wrapper."""

    def test_run_sh_no_infinite_loop(self):
        """Verify run.sh doesn't have a while true loop wrapper."""
        run_sh_path = os.path.join(MONITOR_DIR, "run.sh")
        result = subprocess.run(
            ['grep', '-c', 'while.*[Tt]rue', run_sh_path],
            capture_output=True,
            text=True
        )
        # grep -c returns the count; we want 0 or it fails with exit 1
        if result.returncode == 0:
            count = int(result.stdout.strip())
            assert count == 0, \
                f"run.sh has {count} 'while true' patterns, expected 0"
        # If grep returns 1, it means no matches found, which is fine
