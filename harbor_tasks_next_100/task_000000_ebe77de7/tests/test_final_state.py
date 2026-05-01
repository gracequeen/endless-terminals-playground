# test_final_state.py
"""
Tests to validate the final state after the student has completed the task.
Verifies that:
1. requests is properly installed in the venv
2. import requests works in the venv
3. The venv structure remains intact
4. System Python's requests installation is unchanged
"""

import os
import subprocess
import glob
import pytest


VENV_PATH = "/home/user/webapp/venv"
VENV_PYTHON = f"{VENV_PATH}/bin/python"
VENV_PIP = f"{VENV_PATH}/bin/pip"
SYSTEM_PYTHON = "/usr/bin/python3"


class TestRequestsInstalledInVenv:
    """Test that requests is properly installed in the venv."""

    def test_import_requests_succeeds_in_venv(self):
        """Importing requests in the venv should succeed."""
        result = subprocess.run(
            [VENV_PYTHON, "-c", "import requests; print(requests.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Expected import requests to succeed in venv, but it failed. "
            f"stderr: {result.stderr}"
        )
        # Check that a version string was printed (should be something like "2.31.0")
        version = result.stdout.strip()
        assert version, "requests.__version__ should print a version string"
        # Basic validation that it looks like a version number
        assert any(c.isdigit() for c in version), (
            f"Expected a version string with digits, got: {version}"
        )

    def test_requests_directory_in_venv_site_packages(self):
        """requests directory should exist in venv site-packages."""
        site_packages_pattern = f"{VENV_PATH}/lib/python*/site-packages/"
        site_packages_dirs = glob.glob(site_packages_pattern)
        assert len(site_packages_dirs) > 0, (
            f"No site-packages directory found matching {site_packages_pattern}"
        )

        # Check that requests directory exists in at least one site-packages
        requests_found = False
        for sp in site_packages_dirs:
            requests_dir = os.path.join(sp, "requests")
            if os.path.isdir(requests_dir):
                requests_found = True
                break

        assert requests_found, (
            f"requests package directory not found in venv site-packages. "
            f"Checked: {site_packages_dirs}. "
            f"The package must be properly installed via pip, not symlinked or copied manually."
        )

    def test_requests_in_pip_list(self):
        """requests should appear in pip list output."""
        result = subprocess.run(
            [VENV_PIP, "list"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"pip list failed: {result.stderr}"

        # Check that requests appears in the output (case-insensitive)
        pip_output_lower = result.stdout.lower()
        assert "requests" in pip_output_lower, (
            f"requests not found in venv pip list output. "
            f"Output was:\n{result.stdout}"
        )


class TestVenvStructureIntact:
    """Test that the venv structure remains intact."""

    def test_venv_directory_exists(self):
        """The venv directory must still exist."""
        assert os.path.isdir(VENV_PATH), (
            f"Virtual environment directory {VENV_PATH} no longer exists. "
            f"The venv should not be deleted and recreated."
        )

    def test_venv_python_exists(self):
        """The venv Python executable must still exist."""
        assert os.path.isfile(VENV_PYTHON), (
            f"Virtual environment Python {VENV_PYTHON} no longer exists."
        )

    def test_venv_pip_exists(self):
        """The venv pip must still exist."""
        assert os.path.isfile(VENV_PIP), (
            f"Virtual environment pip {VENV_PIP} no longer exists."
        )

    def test_pyvenv_cfg_exists(self):
        """pyvenv.cfg should still exist (venv not recreated)."""
        pyvenv_cfg = f"{VENV_PATH}/pyvenv.cfg"
        assert os.path.isfile(pyvenv_cfg), (
            f"pyvenv.cfg not found at {pyvenv_cfg}. "
            f"The venv structure should remain intact."
        )

    def test_venv_lib_exists(self):
        """The venv lib directory must still exist."""
        lib_path = f"{VENV_PATH}/lib"
        assert os.path.isdir(lib_path), (
            f"Virtual environment lib directory {lib_path} no longer exists."
        )

    def test_venv_bin_exists(self):
        """The venv bin directory must still exist."""
        bin_path = f"{VENV_PATH}/bin"
        assert os.path.isdir(bin_path), (
            f"Virtual environment bin directory {bin_path} no longer exists."
        )


class TestSystemPythonUnchanged:
    """Test that system Python's requests installation is unchanged."""

    def test_system_python_still_has_requests(self):
        """System Python should still have requests installed."""
        result = subprocess.run(
            [SYSTEM_PYTHON, "-c", "import requests; print(requests.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"System Python should still have requests installed. "
            f"Got error: {result.stderr}"
        )


class TestRequestsProperlyInstalled:
    """Additional tests to ensure requests was properly installed (not hacked in)."""

    def test_requests_has_init_file(self):
        """requests package should have __init__.py file."""
        site_packages_pattern = f"{VENV_PATH}/lib/python*/site-packages/requests/__init__.py"
        matches = glob.glob(site_packages_pattern)
        assert len(matches) > 0, (
            f"requests/__init__.py not found. "
            f"The package should be properly installed via pip."
        )

    def test_requests_dependencies_installed(self):
        """requests dependencies (like urllib3, charset_normalizer) should also be installed."""
        # requests depends on urllib3, so if it's properly installed via pip,
        # urllib3 should also be present
        result = subprocess.run(
            [VENV_PYTHON, "-c", "import urllib3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"urllib3 (a requests dependency) not found in venv. "
            f"This suggests requests was not properly installed via pip. "
            f"stderr: {result.stderr}"
        )

    def test_requests_can_be_used(self):
        """requests should be functional (can access its components)."""
        result = subprocess.run(
            [VENV_PYTHON, "-c", "from requests import Session; s = Session(); print('OK')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"requests package is not functional. "
            f"stderr: {result.stderr}"
        )
        assert "OK" in result.stdout, (
            f"requests package test did not produce expected output. "
            f"stdout: {result.stdout}"
        )
