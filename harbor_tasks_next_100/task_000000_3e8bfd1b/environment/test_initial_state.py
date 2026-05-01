# test_initial_state.py
"""
Tests to validate the initial state of the operating system before the student
creates the Makefile for the data pipeline task.
"""

import os
import subprocess
import pytest


class TestDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_reports_directory_exists(self):
        """Verify /home/user/reports/ exists."""
        path = "/home/user/reports"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_reports_directory_is_writable(self):
        """Verify /home/user/reports/ is writable."""
        path = "/home/user/reports"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_raw_directory_exists(self):
        """Verify /home/user/reports/raw/ exists."""
        path = "/home/user/reports/raw"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_cleaned_directory_exists(self):
        """Verify /home/user/reports/cleaned/ exists."""
        path = "/home/user/reports/cleaned"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_cleaned_directory_is_empty(self):
        """Verify /home/user/reports/cleaned/ is empty."""
        path = "/home/user/reports/cleaned"
        contents = os.listdir(path)
        assert len(contents) == 0, f"Directory {path} should be empty but contains: {contents}"

    def test_final_directory_exists(self):
        """Verify /home/user/reports/final/ exists."""
        path = "/home/user/reports/final"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_final_directory_is_empty(self):
        """Verify /home/user/reports/final/ is empty."""
        path = "/home/user/reports/final"
        contents = os.listdir(path)
        assert len(contents) == 0, f"Directory {path} should be empty but contains: {contents}"


class TestRawCSVFiles:
    """Test that the required raw CSV files exist."""

    def test_sales_q1_csv_exists(self):
        """Verify sales_q1.csv exists in raw/."""
        path = "/home/user/reports/raw/sales_q1.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_sales_q2_csv_exists(self):
        """Verify sales_q2.csv exists in raw/."""
        path = "/home/user/reports/raw/sales_q2.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_inventory_csv_exists(self):
        """Verify inventory.csv exists in raw/."""
        path = "/home/user/reports/raw/inventory.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_raw_directory_has_exactly_three_csv_files(self):
        """Verify raw/ contains exactly three CSV files."""
        path = "/home/user/reports/raw"
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        expected = {'sales_q1.csv', 'sales_q2.csv', 'inventory.csv'}
        assert set(csv_files) == expected, f"Expected CSV files {expected}, found {csv_files}"


class TestPythonScripts:
    """Test that the required Python scripts exist."""

    def test_clean_py_exists(self):
        """Verify clean.py exists."""
        path = "/home/user/reports/clean.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_clean_py_is_readable(self):
        """Verify clean.py is readable."""
        path = "/home/user/reports/clean.py"
        assert os.access(path, os.R_OK), f"File {path} is not readable"

    def test_aggregate_py_exists(self):
        """Verify aggregate.py exists."""
        path = "/home/user/reports/aggregate.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_aggregate_py_is_readable(self):
        """Verify aggregate.py is readable."""
        path = "/home/user/reports/aggregate.py"
        assert os.access(path, os.R_OK), f"File {path} is not readable"


class TestSystemDependencies:
    """Test that required system tools are installed."""

    def test_python3_is_installed(self):
        """Verify Python 3.x is installed."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not installed or not accessible"
        assert "Python 3" in result.stdout, f"Expected Python 3.x, got: {result.stdout}"

    def test_make_is_installed(self):
        """Verify make is installed."""
        result = subprocess.run(
            ["make", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "make is not installed or not accessible"


class TestNoMakefileExists:
    """Test that no Makefile exists yet (student needs to create it)."""

    def test_makefile_does_not_exist(self):
        """Verify Makefile does not exist yet."""
        path = "/home/user/reports/Makefile"
        assert not os.path.exists(path), f"Makefile already exists at {path} - student should create this"

    def test_makefile_lowercase_does_not_exist(self):
        """Verify makefile (lowercase) does not exist."""
        path = "/home/user/reports/makefile"
        assert not os.path.exists(path), f"makefile already exists at {path} - student should create this"


class TestScriptsFunctional:
    """Test that the Python scripts are functional."""

    def test_clean_py_has_valid_python_syntax(self):
        """Verify clean.py has valid Python syntax."""
        path = "/home/user/reports/clean.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"clean.py has syntax errors: {result.stderr}"

    def test_aggregate_py_has_valid_python_syntax(self):
        """Verify aggregate.py has valid Python syntax."""
        path = "/home/user/reports/aggregate.py"
        result = subprocess.run(
            ["python3", "-m", "py_compile", path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"aggregate.py has syntax errors: {result.stderr}"


class TestRawCSVFilesHaveContent:
    """Test that raw CSV files have actual content."""

    def test_sales_q1_csv_has_content(self):
        """Verify sales_q1.csv has content."""
        path = "/home/user/reports/raw/sales_q1.csv"
        size = os.path.getsize(path)
        assert size > 0, f"File {path} is empty"

    def test_sales_q2_csv_has_content(self):
        """Verify sales_q2.csv has content."""
        path = "/home/user/reports/raw/sales_q2.csv"
        size = os.path.getsize(path)
        assert size > 0, f"File {path} is empty"

    def test_inventory_csv_has_content(self):
        """Verify inventory.csv has content."""
        path = "/home/user/reports/raw/inventory.csv"
        size = os.path.getsize(path)
        assert size > 0, f"File {path} is empty"
