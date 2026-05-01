# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student performs the action.
This validates the buggy PyPI mirror setup that causes pip install conflicts.
"""

import os
import subprocess
import pytest


class TestRequirementsFile:
    """Test that the requirements file exists with correct content."""

    def test_requirements_file_exists(self):
        """Verify requirements.txt exists at the expected location."""
        path = "/home/user/testenv/requirements.txt"
        assert os.path.isfile(path), f"Requirements file not found at {path}"

    def test_requirements_file_content(self):
        """Verify requirements.txt contains the expected package pins."""
        path = "/home/user/testenv/requirements.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "numpy==1.24.3" in content, "requirements.txt should contain numpy==1.24.3"
        assert "pandas==2.0.2" in content, "requirements.txt should contain pandas==2.0.2"


class TestPyPIMirrorStructure:
    """Test the PEP 503 simple repository structure exists."""

    def test_pypi_mirror_directory_exists(self):
        """Verify the pypi-mirror directory exists."""
        path = "/home/user/pypi-mirror"
        assert os.path.isdir(path), f"PyPI mirror directory not found at {path}"

    def test_simple_directory_exists(self):
        """Verify the simple/ directory exists."""
        path = "/home/user/pypi-mirror/simple"
        assert os.path.isdir(path), f"Simple directory not found at {path}"

    def test_packages_directory_exists(self):
        """Verify the packages/ directory exists."""
        path = "/home/user/pypi-mirror/packages"
        assert os.path.isdir(path), f"Packages directory not found at {path}"

    def test_main_index_html_exists(self):
        """Verify the main index.html exists."""
        path = "/home/user/pypi-mirror/simple/index.html"
        assert os.path.isfile(path), f"Main index.html not found at {path}"

    @pytest.mark.parametrize("package", [
        "numpy", "pandas", "python-dateutil", "pytz", "six", "tzdata"
    ])
    def test_package_index_directories_exist(self, package):
        """Verify each package has its index directory."""
        path = f"/home/user/pypi-mirror/simple/{package}"
        assert os.path.isdir(path), f"Package directory not found at {path}"

    @pytest.mark.parametrize("package", [
        "numpy", "pandas", "python-dateutil", "pytz", "six", "tzdata"
    ])
    def test_package_index_html_exists(self, package):
        """Verify each package has its index.html."""
        path = f"/home/user/pypi-mirror/simple/{package}/index.html"
        assert os.path.isfile(path), f"Package index.html not found at {path}"


class TestWheelFiles:
    """Test that all required wheel files are present."""

    @pytest.mark.parametrize("wheel_file", [
        "numpy-1.24.3-cp311-cp311-linux_x86_64.whl",
        "pandas-2.0.2-cp311-cp311-linux_x86_64.whl",
        "python_dateutil-2.8.2-py2.py3-none-any.whl",
        "pytz-2023.3-py2.py3-none-any.whl",
        "six-1.16.0-py2.py3-none-any.whl",
        "tzdata-2023.3-py2.py3-none-any.whl",
    ])
    def test_wheel_file_exists(self, wheel_file):
        """Verify each wheel file exists in the packages directory."""
        path = f"/home/user/pypi-mirror/packages/{wheel_file}"
        assert os.path.isfile(path), f"Wheel file not found at {path}"

    @pytest.mark.parametrize("wheel_file", [
        "numpy-1.24.3-cp311-cp311-linux_x86_64.whl",
        "pandas-2.0.2-cp311-cp311-linux_x86_64.whl",
    ])
    def test_wheel_file_not_empty(self, wheel_file):
        """Verify main wheel files are not empty."""
        path = f"/home/user/pypi-mirror/packages/{wheel_file}"
        size = os.path.getsize(path)
        assert size > 0, f"Wheel file {path} is empty"


class TestBuggyMetadata:
    """Test that the buggy metadata file exists with the incorrect dependency."""

    def test_pandas_metadata_file_exists(self):
        """Verify the .metadata file for pandas exists (PEP 658)."""
        path = "/home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl.metadata"
        assert os.path.isfile(path), f"Pandas metadata file not found at {path}"

    def test_pandas_metadata_has_wrong_numpy_dependency(self):
        """Verify the metadata file contains the buggy numpy>=2.0.0 dependency."""
        path = "/home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl.metadata"
        with open(path, 'r') as f:
            content = f.read()

        assert "numpy>=2.0.0" in content, \
            "Pandas metadata should contain the buggy 'numpy>=2.0.0' dependency"

    def test_pandas_index_html_has_data_core_metadata(self):
        """Verify pandas index.html references the metadata file."""
        path = "/home/user/pypi-mirror/simple/pandas/index.html"
        with open(path, 'r') as f:
            content = f.read()

        # Check for data-core-metadata or data-dist-info-metadata attribute
        has_metadata_attr = "data-core-metadata" in content or "data-dist-info-metadata" in content
        assert has_metadata_attr, \
            "Pandas index.html should have data-core-metadata or data-dist-info-metadata attribute"


class TestPipConfiguration:
    """Test pip configuration points to local mirror."""

    def test_pip_conf_exists(self):
        """Verify pip.conf exists."""
        path = "/home/user/.pip/pip.conf"
        assert os.path.isfile(path), f"pip.conf not found at {path}"

    def test_pip_conf_uses_local_mirror(self):
        """Verify pip.conf is configured to use the local mirror."""
        path = "/home/user/.pip/pip.conf"
        with open(path, 'r') as f:
            content = f.read()

        assert "file:///home/user/pypi-mirror/simple" in content, \
            "pip.conf should have index-url pointing to local mirror"


class TestPythonEnvironment:
    """Test Python and pip are properly installed."""

    def test_python3_installed(self):
        """Verify Python 3.11 is installed."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not installed"
        assert "3.11" in result.stdout or "3.11" in result.stderr, \
            f"Python 3.11 expected, got: {result.stdout}{result.stderr}"

    def test_pip_installed(self):
        """Verify pip is installed."""
        result = subprocess.run(
            ["pip", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "pip is not installed"


class TestVirtualEnvironment:
    """Test the virtual environment exists."""

    def test_venv_directory_exists(self):
        """Verify the venv directory exists."""
        path = "/home/user/testenv/venv"
        assert os.path.isdir(path), f"Virtual environment not found at {path}"

    def test_venv_python_exists(self):
        """Verify the venv has a Python executable."""
        path = "/home/user/testenv/venv/bin/python"
        assert os.path.isfile(path), f"venv Python not found at {path}"

    def test_venv_pip_exists(self):
        """Verify the venv has pip."""
        path = "/home/user/testenv/venv/bin/pip"
        assert os.path.isfile(path), f"venv pip not found at {path}"


class TestMirrorWritable:
    """Test that the mirror directory is writable."""

    def test_pypi_mirror_writable(self):
        """Verify the pypi-mirror directory is writable."""
        path = "/home/user/pypi-mirror"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_packages_directory_writable(self):
        """Verify the packages directory is writable."""
        path = "/home/user/pypi-mirror/packages"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_pandas_simple_directory_writable(self):
        """Verify the pandas simple directory is writable."""
        path = "/home/user/pypi-mirror/simple/pandas"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestInstallCurrentlyFails:
    """Test that pip install currently fails due to the bug."""

    def test_pip_install_fails_with_conflict(self):
        """Verify that pip install currently fails with version conflict."""
        # Run pip install in the venv with the local mirror
        result = subprocess.run(
            [
                "/home/user/testenv/venv/bin/pip", "install",
                "-r", "/home/user/testenv/requirements.txt",
                "--dry-run"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        # The install should fail due to the numpy version conflict
        assert result.returncode != 0, \
            "pip install should currently fail due to the buggy metadata"
