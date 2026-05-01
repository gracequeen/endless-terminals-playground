# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
creates the Makefile for the dataprep project.
"""

import os
import subprocess
import pytest


class TestDirectoryStructure:
    """Test that required directories exist and are accessible."""

    def test_dataprep_directory_exists(self):
        """Verify /home/user/dataprep/ exists."""
        path = "/home/user/dataprep"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_dataprep_directory_is_writable(self):
        """Verify /home/user/dataprep/ is writable."""
        path = "/home/user/dataprep"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_scripts_directory_exists(self):
        """Verify /home/user/dataprep/scripts/ exists."""
        path = "/home/user/dataprep/scripts"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_output_directory_exists(self):
        """Verify /home/user/dataprep/output/ exists."""
        path = "/home/user/dataprep/output"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestRequiredFiles:
    """Test that required files exist with expected content."""

    def test_convert_script_exists(self):
        """Verify /home/user/dataprep/scripts/convert.py exists."""
        path = "/home/user/dataprep/scripts/convert.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_convert_script_is_readable(self):
        """Verify /home/user/dataprep/scripts/convert.py is readable."""
        path = "/home/user/dataprep/scripts/convert.py"
        assert os.access(path, os.R_OK), f"File {path} is not readable"

    def test_convert_script_prints_converting(self):
        """Verify convert.py prints 'converting...' when run."""
        result = subprocess.run(
            ["python3", "/home/user/dataprep/scripts/convert.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert "converting..." in result.stdout, (
            f"convert.py should print 'converting...' but got: {result.stdout}"
        )

    def test_dummy1_csv_exists(self):
        """Verify /home/user/dataprep/output/dummy1.csv exists."""
        path = "/home/user/dataprep/output/dummy1.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_dummy2_csv_exists(self):
        """Verify /home/user/dataprep/output/dummy2.csv exists."""
        path = "/home/user/dataprep/output/dummy2.csv"
        assert os.path.isfile(path), f"File {path} does not exist"


class TestMakefileDoesNotExist:
    """Test that the Makefile does NOT exist (student needs to create it)."""

    def test_makefile_does_not_exist(self):
        """Verify /home/user/dataprep/Makefile does NOT exist."""
        path = "/home/user/dataprep/Makefile"
        assert not os.path.exists(path), (
            f"Makefile at {path} already exists - it should not exist in initial state"
        )


class TestRequiredToolsInstalled:
    """Test that required tools (make, python3) are installed."""

    def test_make_is_installed(self):
        """Verify make is installed and accessible."""
        result = subprocess.run(
            ["which", "make"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "make is not installed or not in PATH"

    def test_make_version_works(self):
        """Verify make --version works."""
        result = subprocess.run(
            ["make", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"make --version failed: {result.stderr}"

    def test_python3_is_installed(self):
        """Verify python3 is installed and accessible."""
        result = subprocess.run(
            ["which", "python3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "python3 is not installed or not in PATH"

    def test_python3_version_works(self):
        """Verify python3 --version works."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"python3 --version failed: {result.stderr}"
