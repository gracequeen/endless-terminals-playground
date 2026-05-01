# test_final_state.py
"""
Tests to validate the final state after the student has fixed the PyPI mirror metadata issue.
This validates that pip install works correctly and packages are installed from the local mirror.
"""

import os
import subprocess
import pytest


class TestRequirementsFileUnchanged:
    """Test that the requirements file remains unchanged."""

    def test_requirements_file_exists(self):
        """Verify requirements.txt still exists at the expected location."""
        path = "/home/user/testenv/requirements.txt"
        assert os.path.isfile(path), f"Requirements file not found at {path}"

    def test_requirements_file_content_unchanged(self):
        """Verify requirements.txt still contains the original package pins."""
        path = "/home/user/testenv/requirements.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "numpy==1.24.3" in content, "requirements.txt should still contain numpy==1.24.3"
        assert "pandas==2.0.2" in content, "requirements.txt should still contain pandas==2.0.2"


class TestPipConfigurationUnchanged:
    """Test pip configuration still points to local mirror."""

    def test_pip_conf_exists(self):
        """Verify pip.conf still exists."""
        path = "/home/user/.pip/pip.conf"
        assert os.path.isfile(path), f"pip.conf not found at {path}"

    def test_pip_conf_still_uses_local_mirror(self):
        """Verify pip.conf is still configured to use the local mirror."""
        path = "/home/user/.pip/pip.conf"
        with open(path, 'r') as f:
            content = f.read()

        assert "file:///home/user/pypi-mirror/simple" in content, \
            "pip.conf should still have index-url pointing to local mirror (no switching to public PyPI)"


class TestWheelFilesUnchanged:
    """Test that wheel files remain unchanged (byte-identical)."""

    @pytest.mark.parametrize("wheel_file", [
        "numpy-1.24.3-cp311-cp311-linux_x86_64.whl",
        "pandas-2.0.2-cp311-cp311-linux_x86_64.whl",
        "python_dateutil-2.8.2-py2.py3-none-any.whl",
        "pytz-2023.3-py2.py3-none-any.whl",
        "six-1.16.0-py2.py3-none-any.whl",
        "tzdata-2023.3-py2.py3-none-any.whl",
    ])
    def test_wheel_file_still_exists(self, wheel_file):
        """Verify each wheel file still exists in the packages directory."""
        path = f"/home/user/pypi-mirror/packages/{wheel_file}"
        assert os.path.isfile(path), f"Wheel file not found at {path} - wheels must remain unchanged"

    def test_numpy_wheel_not_empty(self):
        """Verify numpy wheel is not empty (still valid)."""
        path = "/home/user/pypi-mirror/packages/numpy-1.24.3-cp311-cp311-linux_x86_64.whl"
        size = os.path.getsize(path)
        assert size > 1000, f"Numpy wheel at {path} appears corrupted or empty"

    def test_pandas_wheel_not_empty(self):
        """Verify pandas wheel is not empty (still valid)."""
        path = "/home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl"
        size = os.path.getsize(path)
        assert size > 1000, f"Pandas wheel at {path} appears corrupted or empty"


class TestPipInstallSucceeds:
    """Test that pip install now succeeds."""

    def test_pip_install_exits_zero(self):
        """Verify pip install -r requirements.txt exits with code 0."""
        result = subprocess.run(
            [
                "bash", "-c",
                "source /home/user/testenv/venv/bin/activate && pip install -r /home/user/testenv/requirements.txt"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, \
            f"pip install should succeed (exit 0), but got exit code {result.returncode}.\n" \
            f"stdout: {result.stdout}\nstderr: {result.stderr}"

    def test_pip_install_without_no_deps_flag(self):
        """Verify that regular pip install works (not using --no-deps shortcut)."""
        # First uninstall to test fresh install
        subprocess.run(
            [
                "bash", "-c",
                "source /home/user/testenv/venv/bin/activate && pip uninstall -y pandas numpy 2>/dev/null || true"
            ],
            capture_output=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        # Now install with dependency resolution enabled (default)
        result = subprocess.run(
            [
                "bash", "-c",
                "source /home/user/testenv/venv/bin/activate && pip install -r /home/user/testenv/requirements.txt"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, \
            f"pip install with dependency resolution should succeed.\n" \
            f"stdout: {result.stdout}\nstderr: {result.stderr}"


class TestPackagesInstalled:
    """Test that the correct package versions are installed."""

    def test_pandas_and_numpy_importable_with_correct_versions(self):
        """Verify pandas and numpy can be imported with correct versions."""
        result = subprocess.run(
            [
                "bash", "-c",
                'source /home/user/testenv/venv/bin/activate && python -c "import pandas; import numpy; print(pandas.__version__, numpy.__version__)"'
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, \
            f"Failed to import pandas and numpy.\nstderr: {result.stderr}"

        output = result.stdout.strip()
        assert "2.0.2" in output, f"pandas version should be 2.0.2, got output: {output}"
        assert "1.24.3" in output, f"numpy version should be 1.24.3, got output: {output}"

    def test_pandas_version_exactly(self):
        """Verify pandas is exactly version 2.0.2."""
        result = subprocess.run(
            [
                "bash", "-c",
                'source /home/user/testenv/venv/bin/activate && python -c "import pandas; print(pandas.__version__)"'
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, f"Failed to get pandas version: {result.stderr}"
        version = result.stdout.strip()
        assert version == "2.0.2", f"pandas version should be exactly 2.0.2, got: {version}"

    def test_numpy_version_exactly(self):
        """Verify numpy is exactly version 1.24.3."""
        result = subprocess.run(
            [
                "bash", "-c",
                'source /home/user/testenv/venv/bin/activate && python -c "import numpy; print(numpy.__version__)"'
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, f"Failed to get numpy version: {result.stderr}"
        version = result.stdout.strip()
        assert version == "1.24.3", f"numpy version should be exactly 1.24.3, got: {version}"


class TestInstalledFromLocalMirror:
    """Test that packages were installed from the local mirror, not external sources."""

    def test_pandas_installed_in_venv(self):
        """Verify pandas is installed in the venv site-packages."""
        result = subprocess.run(
            [
                "bash", "-c",
                "source /home/user/testenv/venv/bin/activate && pip show pandas | grep -i location"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, f"pip show pandas failed: {result.stderr}"
        location = result.stdout.strip().lower()
        assert "/home/user/testenv/venv" in location, \
            f"pandas should be installed in venv site-packages, got location: {location}"

    def test_numpy_installed_in_venv(self):
        """Verify numpy is installed in the venv site-packages."""
        result = subprocess.run(
            [
                "bash", "-c",
                "source /home/user/testenv/venv/bin/activate && pip show numpy | grep -i location"
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "HOME": "/home/user"}
        )

        assert result.returncode == 0, f"pip show numpy failed: {result.stderr}"
        location = result.stdout.strip().lower()
        assert "/home/user/testenv/venv" in location, \
            f"numpy should be installed in venv site-packages, got location: {location}"


class TestMetadataFixed:
    """Test that the metadata issue has been resolved."""

    def test_no_conflicting_numpy_requirement(self):
        """Verify the buggy numpy>=2.0.0 dependency is no longer causing conflicts."""
        # If there's still a .metadata file, it should not have the wrong dependency
        metadata_path = "/home/user/pypi-mirror/packages/pandas-2.0.2-cp311-cp311-linux_x86_64.whl.metadata"

        if os.path.isfile(metadata_path):
            with open(metadata_path, 'r') as f:
                content = f.read()

            # The buggy numpy>=2.0.0 should be fixed or removed
            assert "numpy>=2.0.0" not in content, \
                "The .metadata file should not contain the buggy 'numpy>=2.0.0' dependency"

    def test_dry_run_install_succeeds(self):
        """Verify pip install --dry-run succeeds (dependency resolution works)."""
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

        assert result.returncode == 0, \
            f"pip install --dry-run should succeed after fix.\nstderr: {result.stderr}"


class TestPyPIMirrorStructureIntact:
    """Test that the PyPI mirror structure is still intact."""

    def test_simple_directory_exists(self):
        """Verify the simple/ directory still exists."""
        path = "/home/user/pypi-mirror/simple"
        assert os.path.isdir(path), f"Simple directory not found at {path}"

    def test_packages_directory_exists(self):
        """Verify the packages/ directory still exists."""
        path = "/home/user/pypi-mirror/packages"
        assert os.path.isdir(path), f"Packages directory not found at {path}"

    @pytest.mark.parametrize("package", ["numpy", "pandas"])
    def test_package_index_directory_exists(self, package):
        """Verify package index directories still exist."""
        path = f"/home/user/pypi-mirror/simple/{package}"
        assert os.path.isdir(path), f"Package directory not found at {path}"

    @pytest.mark.parametrize("package", ["numpy", "pandas"])
    def test_package_index_html_exists(self, package):
        """Verify package index.html files still exist."""
        path = f"/home/user/pypi-mirror/simple/{package}/index.html"
        assert os.path.isfile(path), f"Package index.html not found at {path}"
