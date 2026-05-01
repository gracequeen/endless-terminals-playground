# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the ETL debugging task.
"""

import os
import subprocess
import pytest


class TestScriptExecutesSuccessfully:
    """Test that the ingest script now runs without errors."""

    def test_ingest_script_exits_zero(self):
        """Running the ingest script should now succeed with exit code 0."""
        result = subprocess.run(
            ["python3", "/home/user/pipeline/ingest.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/pipeline"
        )
        assert result.returncode == 0, \
            f"The ingest script should succeed (exit 0), but failed with:\n" \
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"


class TestOutputFileExists:
    """Test that the output parquet file exists and is valid."""

    def test_parquet_file_exists(self):
        """The output parquet file must exist."""
        assert os.path.isfile("/home/user/output/daily_summary.parquet"), \
            "Output file /home/user/output/daily_summary.parquet does not exist"

    def test_parquet_file_is_valid(self):
        """The output file must be a valid parquet file readable by pandas."""
        result = subprocess.run(
            ["python3", "-c",
             "import pandas as pd; df = pd.read_parquet('/home/user/output/daily_summary.parquet'); print('OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Failed to read parquet file with pandas:\n{result.stderr}"
        assert "OK" in result.stdout, \
            f"Unexpected output when reading parquet: {result.stdout}"


class TestParquetContent:
    """Test that the parquet file has the expected structure and content."""

    def test_parquet_has_date_column(self):
        """The parquet must have a 'date' column (or similar)."""
        result = subprocess.run(
            ["python3", "-c",
             "import pandas as pd; df = pd.read_parquet('/home/user/output/daily_summary.parquet'); print(list(df.columns))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read parquet: {result.stderr}"
        columns_str = result.stdout.strip().lower()
        assert "date" in columns_str, \
            f"Parquet should have a 'date' column, found columns: {result.stdout.strip()}"

    def test_parquet_has_count_column(self):
        """The parquet must have a count/aggregation column."""
        result = subprocess.run(
            ["python3", "-c",
             "import pandas as pd; df = pd.read_parquet('/home/user/output/daily_summary.parquet'); print(list(df.columns))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read parquet: {result.stderr}"
        columns_str = result.stdout.strip().lower()
        # Accept various common names for count columns
        has_count_col = any(name in columns_str for name in ['count', 'event_count', 'num_events', 'total', 'size'])
        assert has_count_col, \
            f"Parquet should have a count/aggregation column, found columns: {result.stdout.strip()}"

    def test_parquet_has_multiple_dates(self):
        """The parquet must have multiple rows (one per unique date)."""
        result = subprocess.run(
            ["python3", "-c",
             "import pandas as pd; df = pd.read_parquet('/home/user/output/daily_summary.parquet'); print(len(df))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to read parquet: {result.stderr}"
        row_count = int(result.stdout.strip())
        assert row_count >= 10, \
            f"Parquet should have at least 10 rows (dates), found: {row_count}"

    def test_parquet_is_aggregated(self):
        """The parquet must have fewer rows than the source CSV (it's aggregated)."""
        # Get source CSV row count
        csv_result = subprocess.run(
            ["wc", "-l", "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        csv_lines = int(csv_result.stdout.strip().split()[0])
        csv_data_rows = csv_lines - 1  # Subtract header

        # Get parquet row count
        parquet_result = subprocess.run(
            ["python3", "-c",
             "import pandas as pd; df = pd.read_parquet('/home/user/output/daily_summary.parquet'); print(len(df))"],
            capture_output=True,
            text=True
        )
        assert parquet_result.returncode == 0, f"Failed to read parquet: {parquet_result.stderr}"
        parquet_rows = int(parquet_result.stdout.strip())

        assert parquet_rows < csv_data_rows, \
            f"Parquet should be aggregated (fewer rows than source). " \
            f"Source has {csv_data_rows} data rows, parquet has {parquet_rows} rows"


class TestDataPreservation:
    """Test that the fix preserves data (doesn't just delete problematic rows)."""

    def test_total_count_preserves_most_rows(self):
        """The sum of counts must be >= 490 (preserving nearly all ~500 source rows)."""
        # First, find the count column name
        col_result = subprocess.run(
            ["python3", "-c",
             "import pandas as pd; df = pd.read_parquet('/home/user/output/daily_summary.parquet'); print(list(df.columns))"],
            capture_output=True,
            text=True
        )
        assert col_result.returncode == 0, f"Failed to read parquet: {col_result.stderr}"

        # Try to sum the count column (try common names)
        sum_result = subprocess.run(
            ["python3", "-c", """
import pandas as pd
df = pd.read_parquet('/home/user/output/daily_summary.parquet')
# Find the count column (not the date column)
count_col = None
for col in df.columns:
    col_lower = col.lower()
    if 'count' in col_lower or col_lower in ['size', 'total', 'num_events', 'event_count']:
        count_col = col
        break
if count_col is None:
    # If no obvious count column, use the numeric column that's not date
    for col in df.columns:
        if df[col].dtype in ['int64', 'int32', 'float64', 'float32']:
            if 'date' not in col.lower():
                count_col = col
                break
if count_col:
    print(int(df[count_col].sum()))
else:
    print(len(df))  # Fallback
"""],
            capture_output=True,
            text=True
        )
        assert sum_result.returncode == 0, \
            f"Failed to compute sum: {sum_result.stderr}"

        total_count = int(sum_result.stdout.strip())
        assert total_count >= 490, \
            f"Total event count should be >= 490 (preserving most of ~500 rows), " \
            f"but got {total_count}. The fix should handle mixed date formats, " \
            f"not delete problematic rows."


class TestSourceDataUnchanged:
    """Test that the source CSV was not modified."""

    def test_events_csv_still_exists(self):
        """The source CSV must still exist."""
        assert os.path.isfile("/home/user/data/events.csv"), \
            "Source file /home/user/data/events.csv is missing"

    def test_events_csv_still_has_mixed_formats(self):
        """The source CSV must still contain mixed date formats (read-only)."""
        # Check for ISO format dates
        result_iso = subprocess.run(
            ["grep", "-c", "-E", r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}",
             "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        iso_count = int(result_iso.stdout.strip()) if result_iso.returncode == 0 else 0

        # Check for US format dates
        result_us = subprocess.run(
            ["grep", "-c", "-E", r"[0-9]{2}/[0-9]{2}/[0-9]{4}.*[AP]M",
             "/home/user/data/events.csv"],
            capture_output=True,
            text=True
        )
        us_count = int(result_us.stdout.strip()) if result_us.returncode == 0 else 0

        assert iso_count > 0, "Source CSV should still contain ISO format dates"
        assert us_count > 0, \
            "Source CSV should still contain US format dates (it's read-only)"


class TestPandasVersionNotDowngraded:
    """Test that pandas was not downgraded as a workaround."""

    def test_pandas_still_version_2x(self):
        """pandas must still be version 2.x (not downgraded to 1.5.x)."""
        result = subprocess.run(
            ["python3", "-c", "import pandas; print(pandas.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to check pandas version: {result.stderr}"
        version = result.stdout.strip()
        assert version.startswith("2."), \
            f"pandas version should still be 2.x (not downgraded), got: {version}"


class TestScriptStillUsesCorrectPaths:
    """Test that the script still uses the required input/output paths."""

    def test_script_reads_from_correct_path(self):
        """The script must still read from /home/user/data/events.csv."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        # Check that the script references the correct input path
        assert "events.csv" in content or "/home/user/data" in content, \
            "Script should still read from events.csv in /home/user/data"

    def test_script_writes_to_correct_path(self):
        """The script must still write to /home/user/output/daily_summary.parquet."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        assert "daily_summary.parquet" in content or "/home/user/output" in content, \
            "Script should still write to daily_summary.parquet in /home/user/output"


class TestScriptStillPerformsAggregation:
    """Test that the script still performs date-based aggregation."""

    def test_script_still_has_groupby_or_aggregation(self):
        """The script must still perform grouping/aggregation."""
        with open("/home/user/pipeline/ingest.py", "r") as f:
            content = f.read()
        has_aggregation = any(term in content for term in [
            'groupby', 'group_by', 'resample', 'agg', 'count', 'sum'
        ])
        assert has_aggregation, \
            "Script should still perform aggregation (groupby, count, etc.)"
