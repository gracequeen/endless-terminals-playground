# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the ETL debugging task.
"""

import os
import subprocess
import pytest


class TestDirectoriesExist:
    """Test that required directories exist."""

    def test_pipeline_directory_exists(self):
        """The /home/user/pipeline directory must exist."""
        assert os.path.isdir("/home/user/pipeline"), \
            "Directory /home/user/pipeline does not exist"

    def test_data_directory_exists(self):
        """The /home/user/data directory must exist."""
        assert os.path.isdir("/home/user/data"), \
            "Directory /home/user/data does not exist"

    def test_output_directory_exists(self):
        """The /home/user/output directory must exist and be writable."""
        assert os.path.isdir("/home/user/output"), \
            "Directory /home/user/output does not exist"
        assert os.access("/home/user/output", os.W_OK), \
            "Directory /home/user/output is not writable"


class TestRequiredFilesExist:
    """Test that required files exist with correct permissions."""

    def test_ingest_script_exists(self):
        """The ingest.py script must exist."""
        assert os.path.isfile("/home/user/pipeline/ingest.py"), \
            "File /home/user/pipeline/ingest.py does not exist"

    def test_ingest_script_is_writable(self):
        """The ingest.py script must be writable (so student can fix it)."""
        assert os.access("/home/user/pipeline/ingest.py", os.W_OK), \
            "File /home/user/pipeline/ingest.py is not writable"

    def test_events_csv_exists(self):
        """The events.csv data file must exist."""
        assert os.path.isfile("/home/user/data/events.csv"), \
            "File /home/user/data/events.csv does not exist"

    def test_events_csv_is_readable(self):
        """The events.csv data file must be readable."""
        assert os.access("/home/user/data/events.csv", os.R_OK), \
            "File /home/user/data/events.csv is not readable"

    def test_requirements_txt_exists(self):
        """The requirements.txt file must exist."""
        assert os.path.isfile("/home/user/pipeline/requirements.txt"), \
            "File /home/user/pipeline/requirements.txt does not exist"


class TestEventsCSVContent:
    """Test that the events.csv has the expected structure and mixed formats."""

    def test_csv_has_expected_columns(self):
        """The CSV must have the expected columns."""
        result = subprocess.run(
            ["head", "-1", "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        header = result.stdout.strip().lower()
        assert "event_id" in header, "CSV missing 'event_id' column"
        assert "timestamp" in header, "CSV missing 'timestamp' column"
        assert "user_id" in header, "CSV missing 'user_id' column"
        assert "event_type" in header, "CSV missing 'event_type' column"

    def test_csv_has_sufficient_rows(self):
        """The CSV must have approximately 500 rows."""
        result = subprocess.run(
            ["wc", "-l", "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip().split()[0])
        # Account for header row, expect ~500 data rows
        assert line_count >= 400, \
            f"CSV has only {line_count} lines, expected ~500+ (including header)"

    def test_csv_has_mixed_date_formats(self):
        """The CSV must contain mixed date formats (the root cause of the issue)."""
        # Check for ISO format dates (YYYY-MM-DD)
        result_iso = subprocess.run(
            ["grep", "-E", r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}",
             "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        assert result_iso.returncode == 0, \
            "CSV does not contain ISO format dates (YYYY-MM-DD HH:MM:SS)"

        # Check for US format dates (MM/DD/YYYY with AM/PM)
        result_us = subprocess.run(
            ["grep", "-E", r"[0-9]{2}/[0-9]{2}/[0-9]{4}.*[AP]M",
             "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        assert result_us.returncode == 0, \
            "CSV does not contain US format dates (MM/DD/YYYY with AM/PM) - " \
            "the mixed format issue is missing"


class TestPythonEnvironment:
    """Test that Python and required packages are available."""

    def test_python_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"
        assert "3.11" in result.stdout or "3.11" in result.stderr, \
            f"Expected Python 3.11, got: {result.stdout}{result.stderr}"

    def test_pandas_installed(self):
        """pandas must be installed."""
        result = subprocess.run(
            ["python3", "-c", "import pandas; print(pandas.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"pandas is not installed: {result.stderr}"

    def test_pandas_version_is_2x(self):
        """pandas must be version 2.x (not downgraded)."""
        result = subprocess.run(
            ["python3", "-c", "import pandas; print(pandas.__version__)"],
            capture_output=True,
            text=True
        )
        version = result.stdout.strip()
        assert version.startswith("2."), \
            f"pandas version should be 2.x, got: {version}"

    def test_pyarrow_installed(self):
        """pyarrow must be installed (for parquet support)."""
        result = subprocess.run(
            ["python3", "-c", "import pyarrow"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"pyarrow is not installed: {result.stderr}"

    def test_pip_available(self):
        """pip must be available."""
        result = subprocess.run(
            ["pip", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "pip is not available"


class TestIngestScriptContent:
    """Test that the ingest script has the expected structure."""

    def test_script_reads_events_csv(self):
        """The script must read from /home/user/data/events.csv."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        assert "events.csv" in content or "/home/user/data" in content, \
            "Script does not appear to read from events.csv"

    def test_script_writes_parquet(self):
        """The script must write to parquet format."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        assert "parquet" in content.lower(), \
            "Script does not appear to write parquet output"

    def test_script_uses_datetime_parsing(self):
        """The script must use datetime parsing."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        assert "to_datetime" in content or "datetime" in content, \
            "Script does not appear to parse datetime"

    def test_script_has_specific_format(self):
        """The script must use the specific format string that causes the issue."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        assert "%Y-%m-%d %H:%M:%S" in content, \
            "Script does not contain the expected datetime format string"


class TestRequirementsTxt:
    """Test that requirements.txt shows the pandas update."""

    def test_requirements_shows_pandas_2x(self):
        """requirements.txt should show pandas 2.x version."""
        with open("/home/user/pipeline/requirements.txt", "r") as f:
            content = f.read().lower()
        assert "pandas" in content, \
            "requirements.txt does not mention pandas"


class TestScriptCurrentlyFails:
    """Test that the script currently fails as expected."""

    def test_ingest_script_fails(self):
        """Running the ingest script should currently fail."""
        result = subprocess.run(
            ["python3", "/home/user/pipeline/ingest.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/pipeline"
        )
        assert result.returncode != 0, \
            "The ingest script should currently fail, but it succeeded"

    def test_ingest_script_fails_with_datetime_error(self):
        """The failure should be related to datetime parsing."""
        result = subprocess.run(
            ["python3", "/home/user/pipeline/ingest.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/pipeline"
        )
        error_output = result.stderr + result.stdout
        # Check for datetime-related error messages
        datetime_error_indicators = [
            "doesn't match format",
            "time data",
            "ValueError",
            "datetime",
            "format"
        ]
        has_datetime_error = any(
            indicator.lower() in error_output.lower()
            for indicator in datetime_error_indicators
        )
        assert has_datetime_error, \
            f"Expected datetime parsing error, got: {error_output}"


class TestOutputNotYetPresent:
    """Test that the output file does not yet exist."""

    def test_parquet_output_not_present(self):
        """The output parquet file should not exist yet."""
        assert not os.path.exists("/home/user/output/daily_summary.parquet"), \
            "Output file /home/user/output/daily_summary.parquet already exists - " \
            "it should not exist in the initial state"
