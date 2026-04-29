# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the ETL venv repair task.
"""

import os
import subprocess
import pytest


ETL_DIR = "/home/user/etl"
VENV_DIR = os.path.join(ETL_DIR, "venv")
DATA_RAW_DIR = os.path.join(ETL_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(ETL_DIR, "data", "processed")
OUTPUT_PARQUET = os.path.join(DATA_PROCESSED_DIR, "output.parquet")
RECORDS_CSV = os.path.join(DATA_RAW_DIR, "records.csv")


class TestRunShSucceeds:
    """Test that run.sh executes successfully."""

    def test_run_sh_exits_zero(self):
        """The run.sh script should now exit with code 0."""
        result = subprocess.run(
            ["./run.sh"],
            cwd=ETL_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, \
            f"run.sh should exit 0 after fix. Exit code: {result.returncode}\nstderr: {result.stderr}\nstdout: {result.stdout}"


class TestOutputParquetExists:
    """Test that the output parquet file exists and is valid."""

    def test_output_parquet_file_exists(self):
        """output.parquet should exist in data/processed/."""
        assert os.path.isfile(OUTPUT_PARQUET), \
            f"Output parquet file not found at {OUTPUT_PARQUET}"

    def test_output_parquet_not_empty(self):
        """output.parquet should not be empty."""
        size = os.path.getsize(OUTPUT_PARQUET)
        assert size > 0, f"Output parquet file is empty (size: {size} bytes)"

    def test_output_parquet_has_reasonable_size(self):
        """output.parquet should have a reasonable size for ~400+ rows."""
        size = os.path.getsize(OUTPUT_PARQUET)
        # A parquet file with 400+ rows and 4 columns should be at least a few KB
        assert size > 1000, \
            f"Output parquet file seems too small ({size} bytes) for expected data"


class TestVenvWorks:
    """Test that the venv is properly configured and working."""

    def test_venv_python_exists(self):
        """venv should have a working python executable."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        # Could also be python3
        venv_python3 = os.path.join(VENV_DIR, "bin", "python3")
        assert os.path.isfile(venv_python) or os.path.isfile(venv_python3), \
            f"venv python not found at {venv_python} or {venv_python3}"

    def test_venv_python_runs(self):
        """venv python should execute without errors."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, \
            f"venv python failed to run: {result.stderr}"

    def test_venv_has_pandas(self):
        """venv should have pandas installed."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", "import pandas; print(pandas.__version__)"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"venv should have pandas installed. Error: {result.stderr}"

    def test_venv_has_pyarrow(self):
        """venv should have pyarrow installed."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", "import pyarrow; print(pyarrow.__version__)"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"venv should have pyarrow installed. Error: {result.stderr}"

    def test_venv_has_numpy(self):
        """venv should have numpy installed (needed by transforms.py)."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", "import numpy; print(numpy.__version__)"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"venv should have numpy installed. Error: {result.stderr}"


class TestParquetContent:
    """Test that the parquet file contains valid transformed data."""

    def test_parquet_row_count_within_range(self):
        """Parquet should have >= 400 and < 500 rows (after cleaning)."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", 
             f"import pyarrow.parquet as pq; t = pq.read_table('{OUTPUT_PARQUET}'); print(len(t))"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"Failed to read parquet file: {result.stderr}"

        row_count = int(result.stdout.strip())
        assert row_count >= 400, \
            f"Parquet should have at least 400 rows after cleaning, found {row_count}"
        assert row_count < 500, \
            f"Parquet should have fewer than 500 rows (some should be filtered), found {row_count}"

    def test_parquet_has_expected_columns(self):
        """Parquet should have the expected columns from the source data."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", 
             f"import pyarrow.parquet as pq; t = pq.read_table('{OUTPUT_PARQUET}'); print(t.column_names)"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"Failed to read parquet columns: {result.stderr}"

        columns_str = result.stdout.strip().lower()
        # Check for expected columns (id, timestamp, value, status)
        for col in ["id", "timestamp", "value", "status"]:
            assert col in columns_str, \
                f"Expected column '{col}' not found in parquet. Columns: {columns_str}"

    def test_parquet_is_valid_parquet_format(self):
        """Verify the file is actually a valid parquet file."""
        venv_python = os.path.join(VENV_DIR, "bin", "python")
        if not os.path.isfile(venv_python):
            venv_python = os.path.join(VENV_DIR, "bin", "python3")

        result = subprocess.run(
            [venv_python, "-c", 
             f"import pyarrow.parquet as pq; pq.read_table('{OUTPUT_PARQUET}'); print('valid')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0 and "valid" in result.stdout, \
            f"File is not a valid parquet file: {result.stderr}"


class TestSourceFilesUnchanged:
    """Test that source files remain unchanged (invariants)."""

    def test_records_csv_unchanged(self):
        """records.csv should still exist and have ~500 rows."""
        assert os.path.isfile(RECORDS_CSV), \
            f"Source file records.csv missing at {RECORDS_CSV}"

        with open(RECORDS_CSV, "r") as f:
            lines = f.readlines()
        # Should have header + ~500 data rows
        row_count = len(lines) - 1  # subtract header
        assert row_count >= 490 and row_count <= 510, \
            f"records.csv should have ~500 rows, found {row_count}"

    def test_ingest_py_exists(self):
        """ingest.py should still exist."""
        ingest_py = os.path.join(ETL_DIR, "ingest.py")
        assert os.path.isfile(ingest_py), \
            f"ingest.py should still exist at {ingest_py}"

    def test_transforms_py_exists(self):
        """transforms.py should still exist."""
        transforms_py = os.path.join(ETL_DIR, "transforms.py")
        assert os.path.isfile(transforms_py), \
            f"transforms.py should still exist at {transforms_py}"

    def test_run_sh_exists(self):
        """run.sh should still exist."""
        run_sh = os.path.join(ETL_DIR, "run.sh")
        assert os.path.isfile(run_sh), \
            f"run.sh should still exist at {run_sh}"

    def test_run_sh_still_uses_venv(self):
        """run.sh should still activate venv (not modified to bypass it)."""
        run_sh = os.path.join(ETL_DIR, "run.sh")
        with open(run_sh, "r") as f:
            content = f.read()
        assert "venv" in content and "activate" in content, \
            "run.sh should still use venv activation (not bypassed)"


class TestNoSystemPackageInstall:
    """Test that packages were not installed to system Python."""

    def test_system_python_no_pandas(self):
        """System Python should NOT have pandas (use venv instead)."""
        result = subprocess.run(
            ["/usr/bin/python3", "-c", "import pandas"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # This should fail - pandas should only be in venv
        assert result.returncode != 0, \
            "pandas should NOT be installed in system Python (should be in venv only)"

    def test_system_python_no_pyarrow(self):
        """System Python should NOT have pyarrow (use venv instead)."""
        result = subprocess.run(
            ["/usr/bin/python3", "-c", "import pyarrow"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # This should fail - pyarrow should only be in venv
        assert result.returncode != 0, \
            "pyarrow should NOT be installed in system Python (should be in venv only)"


class TestPipelineRerunnable:
    """Test that the pipeline can be run again successfully."""

    def test_run_sh_idempotent(self):
        """Running run.sh again should still succeed."""
        # First, remove the output to test fresh run
        if os.path.exists(OUTPUT_PARQUET):
            os.remove(OUTPUT_PARQUET)

        result = subprocess.run(
            ["./run.sh"],
            cwd=ETL_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 0, \
            f"run.sh should be rerunnable. Exit code: {result.returncode}\nstderr: {result.stderr}"

        assert os.path.isfile(OUTPUT_PARQUET), \
            "output.parquet should be recreated after rerun"
