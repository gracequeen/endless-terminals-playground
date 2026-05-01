# test_final_state.py
"""
Tests to validate the final state of the monitoring stack after the student fixes the bug.
The collector should now run continuously without stopping after 5 cycles.
"""

import os
import pytest
import configparser
import subprocess
import json
import time


HOME = "/home/user"
MONITOR_DIR = os.path.join(HOME, "monitor")
CONFIG_DIR = os.path.join(MONITOR_DIR, "config")
DATA_DIR = os.path.join(MONITOR_DIR, "data")


class TestDirectoryStructurePreserved:
    """Test that the required directory structure is still intact."""

    def test_monitor_directory_exists(self):
        assert os.path.isdir(MONITOR_DIR), f"Monitor directory {MONITOR_DIR} does not exist"

    def test_config_directory_exists(self):
        assert os.path.isdir(CONFIG_DIR), f"Config directory {CONFIG_DIR} does not exist"

    def test_data_directory_exists(self):
        assert os.path.isdir(DATA_DIR), f"Data directory {DATA_DIR} does not exist"


class TestPythonScriptsPreserved:
    """Test that the required Python scripts still exist and are valid."""

    def test_collector_py_exists(self):
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        assert os.path.isfile(collector_path), f"collector.py not found at {collector_path}"

    def test_collector_is_valid_python(self):
        """Verify collector.py is still valid Python syntax."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        result = subprocess.run(
            ['python3', '-m', 'py_compile', collector_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"collector.py has syntax errors: {result.stderr}"

    def test_aggregator_py_exists(self):
        aggregator_path = os.path.join(MONITOR_DIR, "aggregator.py")
        assert os.path.isfile(aggregator_path), f"aggregator.py not found at {aggregator_path}"

    def test_alert_py_exists(self):
        alert_path = os.path.join(MONITOR_DIR, "alert.py")
        assert os.path.isfile(alert_path), f"alert.py not found at {alert_path}"


class TestConfigFilesPreserved:
    """Test that config files are preserved (sources.yaml and thresholds.yaml unchanged)."""

    def test_sources_yaml_exists(self):
        sources_path = os.path.join(CONFIG_DIR, "sources.yaml")
        assert os.path.isfile(sources_path), f"sources.yaml not found at {sources_path}"

    def test_thresholds_yaml_exists(self):
        thresholds_path = os.path.join(CONFIG_DIR, "thresholds.yaml")
        assert os.path.isfile(thresholds_path), f"thresholds.yaml not found at {thresholds_path}"

    def test_collector_conf_exists(self):
        collector_conf_path = os.path.join(CONFIG_DIR, "collector.conf")
        assert os.path.isfile(collector_conf_path), f"collector.conf not found at {collector_conf_path}"


class TestCollectorPyStructurePreserved:
    """Test that collector.py still has the required structure."""

    def test_collector_still_uses_configparser(self):
        """Verify collector.py still imports configparser (can't just delete all config handling)."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'configparser' in content, \
            "collector.py must still import configparser - can't delete all config handling"

    def test_collector_still_reads_collector_conf(self):
        """Verify collector.py still reads collector.conf."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'collector.conf' in content, \
            "collector.py must still reference collector.conf - can't delete all config handling"


class TestAntiShortcutGuards:
    """Test that the fix addresses the actual bug, not workarounds."""

    def test_run_sh_no_infinite_loop_wrapper(self):
        """Verify run.sh doesn't have an infinite restart wrapper added."""
        run_sh_path = os.path.join(MONITOR_DIR, "run.sh")
        if os.path.isfile(run_sh_path):
            result = subprocess.run(
                ['grep', '-c', '-E', 'while.*(true|True|1)'],
                stdin=open(run_sh_path),
                capture_output=True,
                text=True
            )
            # If grep finds matches, returncode is 0 and stdout has count
            if result.returncode == 0:
                count = int(result.stdout.strip())
                assert count == 0, \
                    f"run.sh has {count} infinite loop patterns - fix must address max_cycles, not wrap in restart loop"


class TestMaxCyclesBugFixed:
    """Test that the max_cycles bug has been fixed."""

    def test_max_cycles_is_zero_or_removed_in_config(self):
        """
        Check if the fix was in collector.conf by setting max_cycles to 0.
        This is one valid fix approach.
        """
        collector_conf_path = os.path.join(CONFIG_DIR, "collector.conf")
        config = configparser.ConfigParser()
        config.read(collector_conf_path)

        # Check if runtime section exists and max_cycles is set
        if config.has_section('runtime') and config.has_option('runtime', 'max_cycles'):
            max_cycles = config.getint('runtime', 'max_cycles')
            # If config still has max_cycles, it should be 0 or negative (infinite)
            config_fixed = max_cycles <= 0
        else:
            # max_cycles option removed or runtime section removed - also valid
            config_fixed = True

        # Also check if the fix was in collector.py by disabling the max_cycles check
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        # Look for signs that the max_cycles exit logic was disabled
        # Common fixes: commenting out the check, setting to 0, removing the exit
        code_fixed = False

        # If max_cycles check is commented out or removed
        lines = content.split('\n')
        active_max_cycles_exit = False
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue
            # Look for the problematic pattern: exit based on max_cycles
            if 'max_cycles' in stripped and 'sys.exit' in stripped:
                active_max_cycles_exit = True
            if 'max_cycles' in stripped and 'exit' in stripped and 'cycle_count' in stripped:
                active_max_cycles_exit = True

        # Check for the if block pattern
        in_max_cycles_block = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if 'if' in stripped and 'max_cycles' in stripped and 'cycle_count' in stripped:
                # Check if next non-comment line has exit
                for j in range(i + 1, min(i + 5, len(lines))):
                    next_stripped = lines[j].strip()
                    if next_stripped.startswith('#'):
                        continue
                    if 'exit' in next_stripped or 'sys.exit' in next_stripped:
                        active_max_cycles_exit = True
                    break

        if not active_max_cycles_exit:
            code_fixed = True

        assert config_fixed or code_fixed, \
            "Bug not fixed: max_cycles is still set to a positive value in config AND the exit logic is still active in code. " \
            "Fix by setting max_cycles=0 in collector.conf OR by disabling the max_cycles exit check in collector.py"


class TestCollectorRunsContinuously:
    """Test that the collector now runs continuously past the original 5-cycle limit."""

    def test_collector_runs_for_45_seconds(self):
        """
        Run collector.py with a 45-second timeout.
        If the bug is fixed, it should run until timeout kills it (exit 124).
        If the bug is NOT fixed, it will exit cleanly after ~25-30 seconds (exit 0).
        """
        # Clean up any existing metrics file first
        metrics_path = os.path.join(DATA_DIR, "metrics.jsonl")
        if os.path.exists(metrics_path):
            os.remove(metrics_path)

        # Run collector with timeout
        result = subprocess.run(
            ['timeout', '45', 'python3', 'collector.py'],
            cwd=MONITOR_DIR,
            capture_output=True,
            text=True
        )

        # Exit code 124 means timeout killed it (good - it was still running)
        # Exit code 0 means it exited on its own (bad - bug not fixed)
        assert result.returncode == 124, \
            f"collector.py exited with code {result.returncode} before 45-second timeout. " \
            f"Expected exit code 124 (killed by timeout). " \
            f"If exit code is 0, the max_cycles bug is not fixed - collector still stops after 5 cycles. " \
            f"stderr: {result.stderr}"

    def test_metrics_file_has_at_least_8_entries(self):
        """
        Verify that metrics.jsonl has at least 8 entries, proving the collector
        ran for more than 5 cycles (each cycle adds entries).
        """
        metrics_path = os.path.join(DATA_DIR, "metrics.jsonl")

        assert os.path.exists(metrics_path), \
            f"metrics.jsonl not found at {metrics_path} - collector may not have run"

        with open(metrics_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        entry_count = len(lines)
        assert entry_count >= 8, \
            f"metrics.jsonl has only {entry_count} entries, expected at least 8. " \
            f"This suggests collector stopped after 5 cycles (the bug). " \
            f"Fix the max_cycles limit in collector.conf or collector.py."

        # Verify entries are valid JSON
        for i, line in enumerate(lines[:8]):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Entry {i} in metrics.jsonl is not valid JSON: {e}")


class TestCollectorFunctionalityPreserved:
    """Test that collector.py still has its core functionality."""

    def test_collector_reads_sources_yaml(self):
        """Verify collector.py still reads sources.yaml."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'sources.yaml' in content or 'sources' in content, \
            "collector.py should still read sources configuration"

    def test_collector_writes_to_metrics_jsonl(self):
        """Verify collector.py still writes to metrics.jsonl."""
        collector_path = os.path.join(MONITOR_DIR, "collector.py")
        with open(collector_path, 'r') as f:
            content = f.read()

        assert 'metrics.jsonl' in content or 'metrics' in content, \
            "collector.py should still write to metrics file"
