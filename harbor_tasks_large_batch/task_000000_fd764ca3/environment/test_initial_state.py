# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the data reconciliation fix task.
"""

import os
import subprocess
import pytest
import csv


HOME = "/home/user"
PIPELINE_DIR = os.path.join(HOME, "pipeline")
INCOMING_DIR = os.path.join(PIPELINE_DIR, "incoming")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
LOGS_DIR = os.path.join(PIPELINE_DIR, "logs")

RECONCILE_SCRIPT = os.path.join(PIPELINE_DIR, "reconcile.py")
CONFIG_FILE = os.path.join(PIPELINE_DIR, "config.yaml")
LOG_FILE = os.path.join(LOGS_DIR, "reconcile.log")

VENDOR_A_CSV = os.path.join(INCOMING_DIR, "vendor_a.csv")
VENDOR_B_CSV = os.path.join(INCOMING_DIR, "vendor_b.csv")
VENDOR_C_CSV = os.path.join(INCOMING_DIR, "vendor_c.csv")


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_pipeline_directory_exists(self):
        assert os.path.isdir(PIPELINE_DIR), \
            f"Pipeline directory {PIPELINE_DIR} does not exist"

    def test_incoming_directory_exists(self):
        assert os.path.isdir(INCOMING_DIR), \
            f"Incoming directory {INCOMING_DIR} does not exist"

    def test_output_directory_exists(self):
        assert os.path.isdir(OUTPUT_DIR), \
            f"Output directory {OUTPUT_DIR} does not exist"

    def test_logs_directory_exists(self):
        assert os.path.isdir(LOGS_DIR), \
            f"Logs directory {LOGS_DIR} does not exist"


class TestRequiredFiles:
    """Test that required files exist."""

    def test_reconcile_script_exists(self):
        assert os.path.isfile(RECONCILE_SCRIPT), \
            f"Main script {RECONCILE_SCRIPT} does not exist"

    def test_config_yaml_exists(self):
        assert os.path.isfile(CONFIG_FILE), \
            f"Config file {CONFIG_FILE} does not exist"

    def test_vendor_a_csv_exists(self):
        assert os.path.isfile(VENDOR_A_CSV), \
            f"Vendor A CSV {VENDOR_A_CSV} does not exist"

    def test_vendor_b_csv_exists(self):
        assert os.path.isfile(VENDOR_B_CSV), \
            f"Vendor B CSV {VENDOR_B_CSV} does not exist"

    def test_vendor_c_csv_exists(self):
        assert os.path.isfile(VENDOR_C_CSV), \
            f"Vendor C CSV {VENDOR_C_CSV} does not exist"

    def test_log_file_exists(self):
        assert os.path.isfile(LOG_FILE), \
            f"Log file {LOG_FILE} does not exist"


class TestVendorACSV:
    """Test vendor_a.csv structure and content."""

    def test_vendor_a_has_correct_columns(self):
        with open(VENDOR_A_CSV, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
        expected_columns = ['id', 'timestamp', 'amount', 'status']
        assert header == expected_columns, \
            f"vendor_a.csv has columns {header}, expected {expected_columns}"

    def test_vendor_a_has_approximately_500_rows(self):
        with open(VENDOR_A_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            row_count = sum(1 for _ in reader)
        assert 495 <= row_count <= 505, \
            f"vendor_a.csv has {row_count} rows, expected ~500"

    def test_vendor_a_timestamps_are_unix(self):
        """Verify timestamps are Unix integers (numeric)."""
        with open(VENDOR_A_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 10:  # Check first 10 rows
                    break
                ts = row['timestamp']
                assert ts.isdigit() or (ts.replace('.', '', 1).isdigit()), \
                    f"vendor_a.csv row {i+1} has non-numeric timestamp: {ts}"

    def test_vendor_a_amounts_are_floats(self):
        """Verify amounts are bare floats without currency symbols."""
        with open(VENDOR_A_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 10:
                    break
                amount = row['amount']
                assert '$' not in amount, \
                    f"vendor_a.csv row {i+1} has currency symbol in amount: {amount}"
                try:
                    float(amount)
                except ValueError:
                    pytest.fail(f"vendor_a.csv row {i+1} amount is not a valid float: {amount}")


class TestVendorBCSV:
    """Test vendor_b.csv structure and content."""

    def test_vendor_b_has_correct_columns(self):
        with open(VENDOR_B_CSV, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
        expected_columns = ['id', 'timestamp', 'amount', 'status']
        assert header == expected_columns, \
            f"vendor_b.csv has columns {header}, expected {expected_columns}"

    def test_vendor_b_has_approximately_480_rows(self):
        with open(VENDOR_B_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            row_count = sum(1 for _ in reader)
        assert 475 <= row_count <= 485, \
            f"vendor_b.csv has {row_count} rows, expected ~480"

    def test_vendor_b_timestamps_are_unix(self):
        with open(VENDOR_B_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 10:
                    break
                ts = row['timestamp']
                assert ts.isdigit() or (ts.replace('.', '', 1).isdigit()), \
                    f"vendor_b.csv row {i+1} has non-numeric timestamp: {ts}"


class TestVendorCCSV:
    """Test vendor_c.csv - the problematic file with format issues."""

    def test_vendor_c_has_correct_columns(self):
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
        expected_columns = ['id', 'timestamp', 'amount', 'status']
        assert header == expected_columns, \
            f"vendor_c.csv has columns {header}, expected {expected_columns}"

    def test_vendor_c_has_approximately_520_rows(self):
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            row_count = sum(1 for _ in reader)
        assert 515 <= row_count <= 525, \
            f"vendor_c.csv has {row_count} rows, expected ~520"

    def test_vendor_c_timestamps_are_iso8601_strings(self):
        """Verify timestamps are ISO 8601 strings (the problematic format)."""
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.DictReader(f)
            iso_count = 0
            for i, row in enumerate(reader):
                if i >= 20:
                    break
                ts = row['timestamp']
                # ISO 8601 format contains 'T' and typically 'Z' or timezone
                if 'T' in ts or '-' in ts:
                    iso_count += 1
        assert iso_count > 0, \
            "vendor_c.csv timestamps should be ISO 8601 strings (contain 'T'), but none found"

    def test_vendor_c_amounts_have_currency_symbols(self):
        """Verify amounts have currency symbols (the problematic format)."""
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.DictReader(f)
            currency_count = 0
            for i, row in enumerate(reader):
                if i >= 20:
                    break
                amount = row['amount']
                if '$' in amount:
                    currency_count += 1
        assert currency_count > 0, \
            "vendor_c.csv amounts should have currency symbols ($), but none found"


class TestConfigFile:
    """Test config.yaml content."""

    def test_config_contains_timestamp_cutoff(self):
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
        assert 'timestamp_cutoff' in content, \
            "config.yaml should contain 'timestamp_cutoff' setting"
        assert '1700000000' in content, \
            "config.yaml timestamp_cutoff should be 1700000000"

    def test_config_contains_min_amount(self):
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
        assert 'min_amount' in content, \
            "config.yaml should contain 'min_amount' setting"
        assert '10' in content, \
            "config.yaml min_amount should be 10.0"


class TestReconcileScript:
    """Test reconcile.py script content and structure."""

    def test_reconcile_script_is_readable(self):
        with open(RECONCILE_SCRIPT, 'r') as f:
            content = f.read()
        assert len(content) > 100, \
            "reconcile.py seems too short to be a valid script"

    def test_reconcile_script_uses_pandas(self):
        with open(RECONCILE_SCRIPT, 'r') as f:
            content = f.read()
        assert 'pandas' in content or 'pd.' in content, \
            "reconcile.py should use pandas for data processing"

    def test_reconcile_script_reads_config(self):
        with open(RECONCILE_SCRIPT, 'r') as f:
            content = f.read()
        assert 'config' in content.lower() or 'yaml' in content.lower(), \
            "reconcile.py should read from config.yaml"

    def test_reconcile_script_is_executable_python(self):
        """Verify the script has valid Python syntax."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', RECONCILE_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"reconcile.py has syntax errors: {result.stderr}"


class TestLogFile:
    """Test that log file contains expected content from previous runs."""

    def test_log_shows_vendor_loads(self):
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        assert 'vendor_a' in content.lower() or '500' in content, \
            "Log should show vendor_a.csv was loaded"
        assert 'vendor_b' in content.lower() or '480' in content, \
            "Log should show vendor_b.csv was loaded"
        assert 'vendor_c' in content.lower() or '520' in content, \
            "Log should show vendor_c.csv was loaded"

    def test_log_shows_filtering_issue(self):
        """Log should show the filtering problem with vendor_c."""
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        # The log should show vendor_c contributes very few rows after filtering
        assert 'filter' in content.lower() or 'after' in content.lower(), \
            "Log should mention filtering step"

    def test_log_shows_low_merged_count(self):
        """Log should show the problematic low row count in merged output."""
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        # Should mention something about merged/output with small number
        assert 'merged' in content.lower() or 'output' in content.lower(), \
            "Log should mention merged output"


class TestPythonEnvironment:
    """Test Python environment is properly configured."""

    def test_python3_available(self):
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
        assert result.returncode == 0, "python3 is not available"
        assert 'Python 3' in result.stdout, \
            f"Expected Python 3, got: {result.stdout}"

    def test_pandas_installed(self):
        result = subprocess.run(
            ['python3', '-c', 'import pandas; print(pandas.__version__)'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"pandas is not installed: {result.stderr}"

    def test_pyyaml_installed(self):
        """YAML parsing library should be available for config reading."""
        result = subprocess.run(
            ['python3', '-c', 'import yaml; print(yaml.__version__)'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"PyYAML is not installed: {result.stderr}"


class TestPipelineWritable:
    """Test that pipeline directory is writable."""

    def test_pipeline_dir_is_writable(self):
        assert os.access(PIPELINE_DIR, os.W_OK), \
            f"{PIPELINE_DIR} is not writable"

    def test_output_dir_is_writable(self):
        assert os.access(OUTPUT_DIR, os.W_OK), \
            f"{OUTPUT_DIR} is not writable"

    def test_reconcile_script_is_writable(self):
        """Student needs to modify the script to fix the bug."""
        assert os.access(RECONCILE_SCRIPT, os.W_OK), \
            f"{RECONCILE_SCRIPT} is not writable"
