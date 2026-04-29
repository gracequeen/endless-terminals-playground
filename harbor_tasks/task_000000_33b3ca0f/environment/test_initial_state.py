# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the ETL venv repair task.
"""

import os
import subprocess
import sys
import pytest


ETL_DIR = "/home/user/etl"
VENV_DIR = os.path.join(ETL_DIR, "venv")
DATA_RAW_DIR = os.path.join(ETL_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(ETL_DIR, "data", "processed")


class TestETLDirectoryStructure:
    """Test that the ETL directory and its contents exist."""

    def test_etl_directory_exists(self):
        assert os.path.isdir(ETL_DIR), f"ETL directory {ETL_DIR} does not exist"

    def test_run_sh_exists(self):
        run_sh = os.path.join(ETL_DIR, "run.sh")
        assert os.path.isfile(run_sh), f"run.sh not found at {run_sh}"

    def test_run_sh_is_executable(self):
        run_sh = os.path.join(ETL_DIR, "run.sh")
        assert os.access(run_sh, os.X_OK), f"run.sh at {run_sh} is not executable"

    def test_run_sh_content(self):
        run_sh = os.path.join(ETL_DIR, "run.sh")
        with open(run_sh, "r") as f:
            content = f.read()
        assert "#!/bin/bash" in content, "run.sh missing shebang"
        assert "source venv/bin/activate" in content or "source ./venv/bin/activate" in content, \
            "run.sh should source venv/bin/activate"
        assert "ingest.py" in content, "run.sh should run ingest.py"

    def test_ingest_py_exists(self):
        ingest_py = os.path.join(ETL_DIR, "ingest.py")
        assert os.path.isfile(ingest_py), f"ingest.py not found at {ingest_py}"

    def test_ingest_py_imports(self):
        ingest_py = os.path.join(ETL_DIR, "ingest.py")
        with open(ingest_py, "r") as f:
            content = f.read()
        assert "import pandas" in content or "from pandas" in content, \
            "ingest.py should import pandas"
        assert "pyarrow" in content, "ingest.py should reference pyarrow"
        assert "from transforms import" in content or "import transforms" in content, \
            "ingest.py should import from transforms module"

    def test_transforms_py_exists(self):
        transforms_py = os.path.join(ETL_DIR, "transforms.py")
        assert os.path.isfile(transforms_py), f"transforms.py not found at {transforms_py}"

    def test_transforms_py_has_clean_records(self):
        transforms_py = os.path.join(ETL_DIR, "transforms.py")
        with open(transforms_py, "r") as f:
            content = f.read()
        assert "def clean_records" in content, \
            "transforms.py should define clean_records function"
        assert "import pandas" in content or "from pandas" in content, \
            "transforms.py should import pandas"
        assert "import numpy" in content or "from numpy" in content, \
            "transforms.py should import numpy"

    def test_requirements_txt_exists(self):
        req_txt = os.path.join(ETL_DIR, "requirements.txt")
        assert os.path.isfile(req_txt), f"requirements.txt not found at {req_txt}"

    def test_requirements_txt_content(self):
        req_txt = os.path.join(ETL_DIR, "requirements.txt")
        with open(req_txt, "r") as f:
            content = f.read().lower()
        assert "pandas" in content, "requirements.txt should contain pandas"
        assert "pyarrow" in content, "requirements.txt should contain pyarrow"


class TestDataDirectories:
    """Test that data directories and input files exist."""

    def test_data_raw_directory_exists(self):
        assert os.path.isdir(DATA_RAW_DIR), f"data/raw directory not found at {DATA_RAW_DIR}"

    def test_records_csv_exists(self):
        records_csv = os.path.join(DATA_RAW_DIR, "records.csv")
        assert os.path.isfile(records_csv), f"records.csv not found at {records_csv}"

    def test_records_csv_has_content(self):
        records_csv = os.path.join(DATA_RAW_DIR, "records.csv")
        with open(records_csv, "r") as f:
            lines = f.readlines()
        # Should have header + 500 data rows
        assert len(lines) > 400, f"records.csv should have ~500 rows, found {len(lines) - 1} data rows"

    def test_records_csv_has_expected_columns(self):
        records_csv = os.path.join(DATA_RAW_DIR, "records.csv")
        with open(records_csv, "r") as f:
            header = f.readline().strip()
        expected_columns = ["id", "timestamp", "value", "status"]
        for col in expected_columns:
            assert col in header.lower(), f"records.csv header should contain '{col}' column"

    def test_data_processed_directory_exists(self):
        assert os.path.isdir(DATA_PROCESSED_DIR), \
            f"data/processed directory not found at {DATA_PROCESSED_DIR}"

    def test_data_processed_is_empty(self):
        contents = os.listdir(DATA_PROCESSED_DIR)
        assert len(contents) == 0, \
            f"data/processed should be empty initially, found: {contents}"


class TestVenvExists:
    """Test that the venv directory exists (but is broken)."""

    def test_venv_directory_exists(self):
        assert os.path.isdir(VENV_DIR), f"venv directory not found at {VENV_DIR}"

    def test_venv_bin_exists(self):
        venv_bin = os.path.join(VENV_DIR, "bin")
        assert os.path.isdir(venv_bin), f"venv/bin directory not found at {venv_bin}"

    def test_venv_activate_exists(self):
        activate = os.path.join(VENV_DIR, "bin", "activate")
        assert os.path.isfile(activate), f"venv/bin/activate not found at {activate}"

    def test_venv_pyvenv_cfg_exists(self):
        pyvenv_cfg = os.path.join(VENV_DIR, "pyvenv.cfg")
        assert os.path.isfile(pyvenv_cfg), f"venv/pyvenv.cfg not found at {pyvenv_cfg}"

    def test_venv_pyvenv_cfg_points_to_nonexistent_python(self):
        """The venv should be broken - pointing to a Python that doesn't exist."""
        pyvenv_cfg = os.path.join(VENV_DIR, "pyvenv.cfg")
        with open(pyvenv_cfg, "r") as f:
            content = f.read()
        # Extract the home path
        for line in content.split("\n"):
            if line.startswith("home"):
                home_path = line.split("=")[1].strip()
                # This path should NOT exist (broken venv)
                assert not os.path.isdir(home_path), \
                    f"venv pyvenv.cfg home path {home_path} should NOT exist (venv should be broken)"
                break


class TestSystemPython:
    """Test that system Python is available and properly configured."""

    def test_system_python3_exists(self):
        python3_path = "/usr/bin/python3"
        assert os.path.isfile(python3_path), f"System python3 not found at {python3_path}"

    def test_system_python3_is_executable(self):
        python3_path = "/usr/bin/python3"
        assert os.access(python3_path, os.X_OK), f"System python3 at {python3_path} is not executable"

    def test_system_python3_version(self):
        result = subprocess.run(
            ["/usr/bin/python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get python3 version"
        version_output = result.stdout.strip() or result.stderr.strip()
        assert "3.11" in version_output or "3.10" in version_output or "3.12" in version_output, \
            f"Expected Python 3.10+, got: {version_output}"

    def test_venv_module_available(self):
        result = subprocess.run(
            ["/usr/bin/python3", "-c", "import venv"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "venv module not available in system Python"

    def test_pip_available(self):
        result = subprocess.run(
            ["/usr/bin/python3", "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "pip not available in system Python"


class TestSystemLacksPackages:
    """Test that system Python does NOT have the required packages."""

    def test_system_python_no_pandas(self):
        result = subprocess.run(
            ["/usr/bin/python3", "-c", "import pandas"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "System Python should NOT have pandas installed (student needs to fix venv)"

    def test_system_python_no_pyarrow(self):
        result = subprocess.run(
            ["/usr/bin/python3", "-c", "import pyarrow"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "System Python should NOT have pyarrow installed (student needs to fix venv)"


class TestRunShFails:
    """Test that running the script fails in the initial state."""

    def test_run_sh_fails(self):
        """The run.sh script should fail due to broken venv."""
        result = subprocess.run(
            ["./run.sh"],
            cwd=ETL_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode != 0, \
            "run.sh should fail initially due to broken venv"

    def test_direct_python_ingest_fails(self):
        """Running ingest.py directly with system python should fail."""
        result = subprocess.run(
            ["/usr/bin/python3", "ingest.py"],
            cwd=ETL_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode != 0, \
            "Running ingest.py with system python should fail (no pandas)"
        assert "ModuleNotFoundError" in result.stderr or "No module named" in result.stderr, \
            f"Expected ModuleNotFoundError, got: {result.stderr}"


class TestDirectoryWritable:
    """Test that the ETL directory is writable."""

    def test_etl_directory_writable(self):
        assert os.access(ETL_DIR, os.W_OK), f"ETL directory {ETL_DIR} is not writable"

    def test_venv_directory_writable(self):
        assert os.access(VENV_DIR, os.W_OK), f"venv directory {VENV_DIR} is not writable"

    def test_data_processed_writable(self):
        assert os.access(DATA_PROCESSED_DIR, os.W_OK), \
            f"data/processed directory {DATA_PROCESSED_DIR} is not writable"
