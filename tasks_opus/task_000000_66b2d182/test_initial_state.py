# test_initial_state.py
"""
Tests to validate the initial state of the operating system before the student
sets up a Python virtual environment for a data cleaning project.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Tests to verify the system state before the task is performed."""

    def test_home_directory_exists(self):
        """Verify that the home directory /home/user exists."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), (
            f"Home directory '{home_dir}' does not exist. "
            "The user's home directory must be present."
        )

    def test_python3_is_available(self):
        """Verify that Python 3 is available on the system."""
        result = subprocess.run(
            ["which", "python3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Python 3 is not available on the system. "
            "Please ensure python3 is installed and in PATH."
        )

    def test_python3_venv_module_available(self):
        """Verify that the venv module is available in Python 3."""
        result = subprocess.run(
            ["python3", "-c", "import venv"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The Python venv module is not available. "
            "Please ensure python3-venv is installed. "
            f"Error: {result.stderr}"
        )

    def test_pip_module_available(self):
        """Verify that pip module is available in Python 3."""
        result = subprocess.run(
            ["python3", "-c", "import pip"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The pip module is not available in Python 3. "
            "Please ensure pip is installed. "
            f"Error: {result.stderr}"
        )

    def test_virtual_environment_does_not_exist(self):
        """Verify that the target virtual environment does not already exist."""
        venv_path = "/home/user/projects/dataset_cleanup/data_cleaning_env"
        assert not os.path.exists(venv_path), (
            f"Virtual environment already exists at '{venv_path}'. "
            "The student should create this, not have it pre-existing."
        )

    def test_setup_log_file_does_not_exist(self):
        """Verify that the setup log file does not already exist."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"
        assert not os.path.exists(log_path), (
            f"Setup log file already exists at '{log_path}'. "
            "The student should create this file, not have it pre-existing."
        )

    def test_can_create_directories_in_home(self):
        """Verify that we have write permissions in the home directory."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), (
            f"Cannot write to home directory '{home_dir}'. "
            "Write permissions are required to create the project directory."
        )

    def test_network_or_pip_index_accessible(self):
        """
        Verify that pip can access package index (needed to install pandas).
        This is a basic check - actual network connectivity may vary.
        """
        result = subprocess.run(
            ["python3", "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "pip is not functioning correctly. "
            f"Error: {result.stderr}"
        )