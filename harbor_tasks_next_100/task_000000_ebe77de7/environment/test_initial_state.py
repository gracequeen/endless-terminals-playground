# test_initial_state.py
"""
Tests to validate the initial state before the student performs the action.
Verifies that:
1. The venv exists and is a valid Python 3 virtual environment
2. The venv has pip but NOT requests
3. System Python has requests installed globally
4. The venv is writable
5. Python 3.10+ and pip are available
"""

import os
import subprocess
import sys
import stat
import pytest


VENV_PATH = "/home/user/webapp/venv"
VENV_PYTHON = f"{VENV_PATH}/bin/python"
VENV_PIP = f"{VENV_PATH}/bin/pip"
SYSTEM_PYTHON = "/usr/bin/python3"


class TestVenvExists:
    """Test that the virtual environment exists and is valid."""

    def test_venv_directory_exists(self):
        """The venv directory must exist."""
        assert os.path.isdir(VENV_PATH), f"Virtual environment directory {VENV_PATH} does not exist"

    def test_venv_bin_directory_exists(self):
        """The venv bin directory must exist."""
        bin_path = f"{VENV_PATH}/bin"
        assert os.path.isdir(bin_path), f"Virtual environment bin directory {bin_path} does not exist"

    def test_venv_python_executable_exists(self):
        """The venv Python executable must exist."""
        assert os.path.isfile(VENV_PYTHON), f"Virtual environment Python {VENV_PYTHON} does not exist"

    def test_venv_python_is_executable(self):
        """The venv Python must be executable."""
        assert os.access(VENV_PYTHON, os.X_OK), f"Virtual environment Python {VENV_PYTHON} is not executable"

    def test_venv_pip_exists(self):
        """The venv pip must exist."""
        assert os.path.isfile(VENV_PIP), f"Virtual environment pip {VENV_PIP} does not exist"

    def test_venv_has_pyvenv_cfg(self):
        """A valid venv should have pyvenv.cfg file."""
        pyvenv_cfg = f"{VENV_PATH}/pyvenv.cfg"
        assert os.path.isfile(pyvenv_cfg), f"pyvenv.cfg not found at {pyvenv_cfg} - not a valid venv"

    def test_venv_lib_directory_exists(self):
        """The venv lib directory must exist."""
        lib_path = f"{VENV_PATH}/lib"
        assert os.path.isdir(lib_path), f"Virtual environment lib directory {lib_path} does not exist"


class TestVenvDoesNotHaveRequests:
    """Test that the venv does NOT have requests installed."""

    def test_import_requests_fails_in_venv(self):
        """Importing requests in the venv should fail with ModuleNotFoundError."""
        result = subprocess.run(
            [VENV_PYTHON, "-c", "import requests"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            f"Expected import requests to fail in venv, but it succeeded. "
            f"requests should NOT be installed in the venv initially."
        )
        assert "ModuleNotFoundError" in result.stderr or "No module named" in result.stderr, (
            f"Expected ModuleNotFoundError when importing requests in venv. "
            f"Got: {result.stderr}"
        )

    def test_requests_not_in_venv_site_packages(self):
        """requests directory should not exist in venv site-packages."""
        import glob
        site_packages_pattern = f"{VENV_PATH}/lib/python*/site-packages/requests"
        matches = glob.glob(site_packages_pattern)
        assert len(matches) == 0, (
            f"requests package found in venv site-packages at {matches}. "
            f"It should NOT be installed initially."
        )


class TestSystemPythonHasRequests:
    """Test that system Python has requests installed."""

    def test_system_python_exists(self):
        """System Python must exist."""
        assert os.path.isfile(SYSTEM_PYTHON), f"System Python {SYSTEM_PYTHON} does not exist"

    def test_system_python_has_requests(self):
        """System Python should have requests installed."""
        result = subprocess.run(
            [SYSTEM_PYTHON, "-c", "import requests; print(requests.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"System Python should have requests installed. "
            f"Got error: {result.stderr}"
        )


class TestVenvWritable:
    """Test that the venv is writable by the current user."""

    def test_venv_directory_writable(self):
        """The venv directory must be writable."""
        assert os.access(VENV_PATH, os.W_OK), f"Virtual environment {VENV_PATH} is not writable"

    def test_venv_lib_writable(self):
        """The venv lib directory must be writable."""
        lib_path = f"{VENV_PATH}/lib"
        assert os.access(lib_path, os.W_OK), f"Virtual environment lib {lib_path} is not writable"

    def test_venv_site_packages_writable(self):
        """The venv site-packages directory must be writable."""
        import glob
        site_packages_pattern = f"{VENV_PATH}/lib/python*/site-packages"
        matches = glob.glob(site_packages_pattern)
        assert len(matches) > 0, f"No site-packages directory found matching {site_packages_pattern}"
        for sp in matches:
            assert os.access(sp, os.W_OK), f"site-packages {sp} is not writable"


class TestPythonVersion:
    """Test Python version requirements."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "python3 is not available"

    def test_python_version_3_10_plus(self):
        """Python 3.10+ must be available."""
        result = subprocess.run(
            ["python3", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get Python version"
        version = result.stdout.strip()
        major, minor = map(int, version.split('.'))
        assert major >= 3 and minor >= 10, f"Python 3.10+ required, got {version}"

    def test_venv_python_version_3_10_plus(self):
        """Venv Python must be 3.10+."""
        result = subprocess.run(
            [VENV_PYTHON, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to get venv Python version: {result.stderr}"
        version = result.stdout.strip()
        major, minor = map(int, version.split('.'))
        assert major >= 3 and minor >= 10, f"Venv Python 3.10+ required, got {version}"


class TestPipAvailable:
    """Test that pip is available."""

    def test_pip_available_system(self):
        """pip must be available on the system."""
        result = subprocess.run(
            ["pip3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "pip3 is not available on the system"

    def test_pip_available_in_venv(self):
        """pip must be available in the venv."""
        result = subprocess.run(
            [VENV_PIP, "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"pip is not available in venv: {result.stderr}"

    def test_venv_pip_works(self):
        """venv pip should be functional."""
        result = subprocess.run(
            [VENV_PIP, "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"venv pip list failed: {result.stderr}"
