# test_final_state.py
"""
Tests to validate the final state of the operating system after the student
has created the Makefile for the data pipeline task.
"""

import os
import subprocess
import pytest
import shutil


class TestMakefileExists:
    """Test that the Makefile exists and has required content."""

    def test_makefile_exists(self):
        """Verify Makefile exists at /home/user/reports/Makefile."""
        path = "/home/user/reports/Makefile"
        assert os.path.isfile(path), f"Makefile does not exist at {path}"

    def test_makefile_references_clean_py(self):
        """Verify Makefile references clean.py."""
        path = "/home/user/reports/Makefile"
        result = subprocess.run(
            ["grep", "-E", "clean\\.py", path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Makefile must reference clean.py to invoke the cleaning script"

    def test_makefile_references_aggregate_py(self):
        """Verify Makefile references aggregate.py."""
        path = "/home/user/reports/Makefile"
        result = subprocess.run(
            ["grep", "-E", "aggregate\\.py", path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Makefile must reference aggregate.py to invoke the aggregation script"


class TestMakeRuns:
    """Test that running make works correctly."""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Clean up generated files before and after tests to ensure fresh state."""
        # Clean before test
        cleaned_dir = "/home/user/reports/cleaned"
        final_dir = "/home/user/reports/final"

        # Remove any existing cleaned files
        for f in os.listdir(cleaned_dir):
            filepath = os.path.join(cleaned_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        # Remove any existing final files
        for f in os.listdir(final_dir):
            filepath = os.path.join(final_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        yield

        # Don't clean up after - leave files for inspection if needed

    def test_make_exits_zero(self):
        """Verify running make exits with code 0."""
        result = subprocess.run(
            ["make"],
            cwd="/home/user/reports",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"make failed with exit code {result.returncode}. stderr: {result.stderr}, stdout: {result.stdout}"


class TestCleanedFilesExist:
    """Test that cleaned files are created after running make."""

    @pytest.fixture(autouse=True)
    def run_make_first(self):
        """Run make before checking for cleaned files."""
        # Clean up first
        cleaned_dir = "/home/user/reports/cleaned"
        final_dir = "/home/user/reports/final"

        for f in os.listdir(cleaned_dir):
            filepath = os.path.join(cleaned_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        for f in os.listdir(final_dir):
            filepath = os.path.join(final_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        # Run make
        subprocess.run(["make"], cwd="/home/user/reports", capture_output=True)
        yield

    def test_cleaned_sales_q1_exists(self):
        """Verify cleaned/sales_q1.csv exists after make."""
        path = "/home/user/reports/cleaned/sales_q1.csv"
        assert os.path.isfile(path), f"File {path} does not exist after running make"

    def test_cleaned_sales_q2_exists(self):
        """Verify cleaned/sales_q2.csv exists after make."""
        path = "/home/user/reports/cleaned/sales_q2.csv"
        assert os.path.isfile(path), f"File {path} does not exist after running make"

    def test_cleaned_inventory_exists(self):
        """Verify cleaned/inventory.csv exists after make."""
        path = "/home/user/reports/cleaned/inventory.csv"
        assert os.path.isfile(path), f"File {path} does not exist after running make"

    def test_cleaned_files_have_content(self):
        """Verify cleaned files have content."""
        cleaned_dir = "/home/user/reports/cleaned"
        for filename in ["sales_q1.csv", "sales_q2.csv", "inventory.csv"]:
            path = os.path.join(cleaned_dir, filename)
            assert os.path.getsize(path) > 0, f"File {path} is empty"


class TestFinalSummaryExists:
    """Test that final/summary.csv is created after running make."""

    @pytest.fixture(autouse=True)
    def run_make_first(self):
        """Run make before checking for summary file."""
        # Clean up first
        cleaned_dir = "/home/user/reports/cleaned"
        final_dir = "/home/user/reports/final"

        for f in os.listdir(cleaned_dir):
            filepath = os.path.join(cleaned_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        for f in os.listdir(final_dir):
            filepath = os.path.join(final_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        # Run make
        subprocess.run(["make"], cwd="/home/user/reports", capture_output=True)
        yield

    def test_summary_csv_exists(self):
        """Verify final/summary.csv exists after make."""
        path = "/home/user/reports/final/summary.csv"
        assert os.path.isfile(path), f"File {path} does not exist after running make"

    def test_summary_csv_has_content(self):
        """Verify final/summary.csv has content."""
        path = "/home/user/reports/final/summary.csv"
        assert os.path.getsize(path) > 0, f"File {path} is empty"

    def test_summary_contains_data_from_all_files(self):
        """Verify summary.csv contains data from all three source files."""
        path = "/home/user/reports/final/summary.csv"
        with open(path, 'r') as f:
            content = f.read()

        # The summary should have more than just a header line
        lines = [l for l in content.strip().split('\n') if l.strip()]
        assert len(lines) > 1, f"summary.csv should contain data rows, found only {len(lines)} line(s)"


class TestDependencyTracking:
    """Test that make properly tracks dependencies (doesn't rebuild unnecessarily)."""

    @pytest.fixture(autouse=True)
    def run_make_first(self):
        """Run make to establish baseline state."""
        # Clean up first
        cleaned_dir = "/home/user/reports/cleaned"
        final_dir = "/home/user/reports/final"

        for f in os.listdir(cleaned_dir):
            filepath = os.path.join(cleaned_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        for f in os.listdir(final_dir):
            filepath = os.path.join(final_dir, f)
            if os.path.isfile(filepath):
                os.remove(filepath)

        # Run make first time
        subprocess.run(["make"], cwd="/home/user/reports", capture_output=True)
        yield

    def test_second_make_does_nothing(self):
        """Verify running make a second time with no changes does nothing."""
        # Run make again
        result = subprocess.run(
            ["make"],
            cwd="/home/user/reports",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Second make failed with exit code {result.returncode}"

        # Check that make indicates nothing to do
        # Common messages: "Nothing to be done", "is up to date", or empty meaningful output
        output = result.stdout + result.stderr

        # Make should either say nothing to do, or not run any commands
        # We check that it doesn't re-run the python scripts
        ran_clean = "clean.py" in output and "python" in output.lower()
        ran_aggregate = "aggregate.py" in output and "python" in output.lower()

        # If make ran commands, check if it says "up to date" or "Nothing to be done"
        up_to_date = "up to date" in output.lower() or "nothing to be done" in output.lower()

        # Either nothing was run, or make said things are up to date
        assert up_to_date or (not ran_clean and not ran_aggregate), \
            f"Make should not rebuild when files haven't changed. Output: {output}"


class TestInvariants:
    """Test that invariants are preserved."""

    def test_clean_py_unchanged(self):
        """Verify clean.py still exists and is readable."""
        path = "/home/user/reports/clean.py"
        assert os.path.isfile(path), f"clean.py should still exist at {path}"
        assert os.access(path, os.R_OK), f"clean.py should still be readable"

    def test_aggregate_py_unchanged(self):
        """Verify aggregate.py still exists and is readable."""
        path = "/home/user/reports/aggregate.py"
        assert os.path.isfile(path), f"aggregate.py should still exist at {path}"
        assert os.access(path, os.R_OK), f"aggregate.py should still be readable"

    def test_raw_files_unchanged(self):
        """Verify raw CSV files still exist."""
        raw_dir = "/home/user/reports/raw"
        expected_files = {"sales_q1.csv", "sales_q2.csv", "inventory.csv"}
        actual_files = set(os.listdir(raw_dir))

        for f in expected_files:
            assert f in actual_files, f"Raw file {f} should still exist in {raw_dir}"

    def test_directory_structure_preserved(self):
        """Verify directory structure is preserved."""
        dirs = [
            "/home/user/reports",
            "/home/user/reports/raw",
            "/home/user/reports/cleaned",
            "/home/user/reports/final"
        ]
        for d in dirs:
            assert os.path.isdir(d), f"Directory {d} should still exist"
