# test_initial_state.py
"""
Tests to validate the initial state before the student performs the pip freeze task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state of the system before the task is performed."""

    def test_webapp_directory_exists(self):
        """Verify /home/user/webapp/ directory exists."""
        webapp_path = "/home/user/webapp"
        assert os.path.exists(webapp_path), f"Directory {webapp_path} does not exist"
        assert os.path.isdir(webapp_path), f"{webapp_path} is not a directory"

    def test_webapp_directory_is_writable(self):
        """Verify /home/user/webapp/ directory is writable."""
        webapp_path = "/home/user/webapp"
        assert os.access(webapp_path, os.W_OK), f"Directory {webapp_path} is not writable"

    def test_venv_directory_exists(self):
        """Verify the virtual environment directory exists."""
        venv_path = "/home/user/webapp/venv"
        assert os.path.exists(venv_path), f"Virtual environment directory {venv_path} does not exist"
        assert os.path.isdir(venv_path), f"{venv_path} is not a directory"

    def test_venv_python_executable_exists(self):
        """Verify the venv Python executable exists."""
        python_path = "/home/user/webapp/venv/bin/python"
        assert os.path.exists(python_path), f"Python executable {python_path} does not exist"
        assert os.access(python_path, os.X_OK), f"Python executable {python_path} is not executable"

    def test_venv_pip_executable_exists(self):
        """Verify pip is available in the venv."""
        pip_path = "/home/user/webapp/venv/bin/pip"
        assert os.path.exists(pip_path), f"pip executable {pip_path} does not exist"
        assert os.access(pip_path, os.X_OK), f"pip executable {pip_path} is not executable"

    def test_python_version_is_311_or_higher(self):
        """Verify Python version is 3.11+."""
        python_path = "/home/user/webapp/venv/bin/python"
        result = subprocess.run(
            [python_path, "--version"],
            capture_output=True,
            text=True
        )
        version_output = result.stdout.strip()
        # Parse version like "Python 3.11.4"
        version_str = version_output.replace("Python ", "")
        parts = version_str.split(".")
        major = int(parts[0])
        minor = int(parts[1])
        assert major == 3 and minor >= 11, f"Python version must be 3.11+, got {version_output}"

    def test_flask_is_installed_with_correct_version(self):
        """Verify flask==2.3.2 is installed in the venv."""
        pip_path = "/home/user/webapp/venv/bin/pip"
        result = subprocess.run(
            [pip_path, "show", "flask"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "flask is not installed in the venv"
        assert "Version: 2.3.2" in result.stdout, f"flask version should be 2.3.2, got: {result.stdout}"

    def test_requests_is_installed_with_correct_version(self):
        """Verify requests==2.31.0 is installed in the venv."""
        pip_path = "/home/user/webapp/venv/bin/pip"
        result = subprocess.run(
            [pip_path, "show", "requests"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "requests is not installed in the venv"
        assert "Version: 2.31.0" in result.stdout, f"requests version should be 2.31.0, got: {result.stdout}"

    def test_gunicorn_is_installed_with_correct_version(self):
        """Verify gunicorn==21.2.0 is installed in the venv."""
        pip_path = "/home/user/webapp/venv/bin/pip"
        result = subprocess.run(
            [pip_path, "show", "gunicorn"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gunicorn is not installed in the venv"
        assert "Version: 21.2.0" in result.stdout, f"gunicorn version should be 21.2.0, got: {result.stdout}"

    def test_requirements_txt_does_not_exist(self):
        """Verify requirements.txt does not exist yet (student needs to create it)."""
        requirements_path = "/home/user/webapp/requirements.txt"
        assert not os.path.exists(requirements_path), (
            f"requirements.txt already exists at {requirements_path}. "
            "It should not exist before the student performs the task."
        )

    def test_pip_freeze_works(self):
        """Verify pip freeze command works in the venv."""
        pip_path = "/home/user/webapp/venv/bin/pip"
        result = subprocess.run(
            [pip_path, "freeze"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"pip freeze failed: {result.stderr}"
        # Should have some output (packages are installed)
        assert len(result.stdout.strip()) > 0, "pip freeze returned no packages"

    def test_venv_has_multiple_packages_installed(self):
        """Verify the venv has multiple packages (including dependencies)."""
        pip_path = "/home/user/webapp/venv/bin/pip"
        result = subprocess.run(
            [pip_path, "freeze"],
            capture_output=True,
            text=True
        )
        packages = [line for line in result.stdout.strip().split("\n") if line]
        # Flask, requests, gunicorn plus their dependencies should give us more than 3 packages
        assert len(packages) >= 3, (
            f"Expected at least 3 packages installed (flask, requests, gunicorn), "
            f"but found {len(packages)}: {packages}"
        )
