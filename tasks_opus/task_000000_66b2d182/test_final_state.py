# test_final_state.py
"""
Tests to validate the final state of the operating system after the student
has set up a Python virtual environment for a data cleaning project.
"""

import os
import re
import subprocess
import pytest


class TestVirtualEnvironmentStructure:
    """Tests to verify the virtual environment was created correctly."""

    def test_project_directory_exists(self):
        """Verify that the project directory exists."""
        project_dir = "/home/user/projects/dataset_cleanup"
        assert os.path.isdir(project_dir), (
            f"Project directory '{project_dir}' does not exist. "
            "The student should have created this directory."
        )

    def test_venv_directory_exists(self):
        """Verify that the virtual environment directory exists."""
        venv_path = "/home/user/projects/dataset_cleanup/data_cleaning_env"
        assert os.path.isdir(venv_path), (
            f"Virtual environment directory '{venv_path}' does not exist. "
            "The student should have created the virtual environment using "
            "'python3 -m venv /home/user/projects/dataset_cleanup/data_cleaning_env'."
        )

    def test_venv_bin_directory_exists(self):
        """Verify that the venv bin directory exists."""
        bin_path = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin"
        assert os.path.isdir(bin_path), (
            f"Virtual environment bin directory '{bin_path}' does not exist. "
            "The virtual environment was not created correctly."
        )

    def test_venv_activate_script_exists(self):
        """Verify that the activate script exists in the venv."""
        activate_path = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/activate"
        assert os.path.isfile(activate_path), (
            f"Activation script '{activate_path}' does not exist. "
            "The virtual environment was not created correctly."
        )

    def test_venv_python_interpreter_exists(self):
        """Verify that a Python interpreter exists in the venv."""
        venv_bin = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin"
        python_path = os.path.join(venv_bin, "python")
        python3_path = os.path.join(venv_bin, "python3")

        python_exists = os.path.exists(python_path) or os.path.exists(python3_path)
        assert python_exists, (
            f"No Python interpreter found in '{venv_bin}'. "
            "Expected 'python' or 'python3' to exist. "
            "The virtual environment was not created correctly."
        )

    def test_venv_pip_exists(self):
        """Verify that pip exists in the venv."""
        venv_bin = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin"
        pip_path = os.path.join(venv_bin, "pip")
        pip3_path = os.path.join(venv_bin, "pip3")

        pip_exists = os.path.exists(pip_path) or os.path.exists(pip3_path)
        assert pip_exists, (
            f"No pip found in '{venv_bin}'. "
            "Expected 'pip' or 'pip3' to exist. "
            "The virtual environment was not created correctly."
        )

    def test_venv_lib_directory_exists(self):
        """Verify that the lib directory structure exists in the venv."""
        venv_path = "/home/user/projects/dataset_cleanup/data_cleaning_env"
        lib_path = os.path.join(venv_path, "lib")
        assert os.path.isdir(lib_path), (
            f"Virtual environment lib directory '{lib_path}' does not exist. "
            "The virtual environment was not created correctly."
        )


class TestPandasInstallation:
    """Tests to verify that pandas is installed in the virtual environment."""

    def test_pandas_installed_in_venv(self):
        """Verify that pandas is installed in the virtual environment."""
        venv_pip = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/pip"
        if not os.path.exists(venv_pip):
            venv_pip = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/pip3"

        result = subprocess.run(
            [venv_pip, "show", "pandas"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "pandas is not installed in the virtual environment. "
            "The student should have activated the venv and run 'pip install pandas'. "
            f"Error: {result.stderr}"
        )

    def test_pandas_importable_in_venv(self):
        """Verify that pandas can be imported using the venv's Python."""
        venv_python = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/python"
        if not os.path.exists(venv_python):
            venv_python = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/python3"

        result = subprocess.run(
            [venv_python, "-c", "import pandas; print(pandas.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "pandas cannot be imported in the virtual environment. "
            f"Error: {result.stderr}"
        )


class TestSetupLogFile:
    """Tests to verify the setup log file is correctly created."""

    def test_log_file_exists(self):
        """Verify that the setup log file exists."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"
        assert os.path.isfile(log_path), (
            f"Setup log file '{log_path}' does not exist. "
            "The student should have created this file with the required information."
        )

    def test_log_file_has_four_lines(self):
        """Verify that the log file contains exactly 4 lines."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"
        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) == 4, (
            f"Setup log file should contain exactly 4 non-empty lines, but has {len(lines)}. "
            f"Lines found: {lines}"
        )

    def test_log_file_venv_path_line(self):
        """Verify that the VENV_PATH line is correct."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"
        expected_venv_path = "/home/user/projects/dataset_cleanup/data_cleaning_env"

        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) >= 1, "Log file is empty or missing lines."

        first_line = lines[0]
        assert first_line.startswith("VENV_PATH: "), (
            f"First line should start with 'VENV_PATH: ', but got: '{first_line}'"
        )

        venv_path_value = first_line.replace("VENV_PATH: ", "", 1)
        assert venv_path_value == expected_venv_path, (
            f"VENV_PATH should be '{expected_venv_path}', but got: '{venv_path_value}'"
        )

    def test_log_file_python_version_line(self):
        """Verify that the PYTHON_VERSION line has correct format."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"

        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) >= 2, "Log file is missing the PYTHON_VERSION line."

        second_line = lines[1]
        assert second_line.startswith("PYTHON_VERSION: "), (
            f"Second line should start with 'PYTHON_VERSION: ', but got: '{second_line}'"
        )

        version_value = second_line.replace("PYTHON_VERSION: ", "", 1)
        # Version should be digits and dots, like "3.10.12"
        version_pattern = r'^\d+\.\d+(\.\d+)?$'
        assert re.match(version_pattern, version_value), (
            f"PYTHON_VERSION should be a version number like '3.10.12', but got: '{version_value}'"
        )

    def test_log_file_pandas_installed_line(self):
        """Verify that the PANDAS_INSTALLED line is exactly 'yes'."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"

        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) >= 3, "Log file is missing the PANDAS_INSTALLED line."

        third_line = lines[2]
        assert third_line == "PANDAS_INSTALLED: yes", (
            f"Third line should be exactly 'PANDAS_INSTALLED: yes', but got: '{third_line}'"
        )

    def test_log_file_pandas_version_line(self):
        """Verify that the PANDAS_VERSION line has correct format."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"

        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) >= 4, "Log file is missing the PANDAS_VERSION line."

        fourth_line = lines[3]
        assert fourth_line.startswith("PANDAS_VERSION: "), (
            f"Fourth line should start with 'PANDAS_VERSION: ', but got: '{fourth_line}'"
        )

        version_value = fourth_line.replace("PANDAS_VERSION: ", "", 1)
        # Version should be digits and dots, like "2.0.3" or "1.5.3"
        version_pattern = r'^\d+\.\d+(\.\d+)?$'
        assert re.match(version_pattern, version_value), (
            f"PANDAS_VERSION should be a version number like '2.0.3', but got: '{version_value}'"
        )

    def test_log_file_pandas_version_matches_installed(self):
        """Verify that the pandas version in log matches what's actually installed."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"
        venv_python = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/python"
        if not os.path.exists(venv_python):
            venv_python = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/python3"

        # Get actual pandas version from venv
        result = subprocess.run(
            [venv_python, "-c", "import pandas; print(pandas.__version__)"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.skip("Could not determine actual pandas version")

        actual_version = result.stdout.strip()

        # Get version from log file
        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 4:
            pytest.fail("Log file doesn't have enough lines")

        fourth_line = lines[3]
        log_version = fourth_line.replace("PANDAS_VERSION: ", "", 1)

        assert log_version == actual_version, (
            f"PANDAS_VERSION in log ({log_version}) doesn't match "
            f"actually installed version ({actual_version})"
        )

    def test_log_file_python_version_matches_venv(self):
        """Verify that the Python version in log matches the venv's Python."""
        log_path = "/home/user/projects/dataset_cleanup/setup_log.txt"
        venv_python = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/python"
        if not os.path.exists(venv_python):
            venv_python = "/home/user/projects/dataset_cleanup/data_cleaning_env/bin/python3"

        # Get actual Python version from venv
        result = subprocess.run(
            [venv_python, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            pytest.skip("Could not determine actual Python version")

        actual_version = result.stdout.strip()

        # Get version from log file
        with open(log_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 2:
            pytest.fail("Log file doesn't have enough lines")

        second_line = lines[1]
        log_version = second_line.replace("PYTHON_VERSION: ", "", 1)

        assert log_version == actual_version, (
            f"PYTHON_VERSION in log ({log_version}) doesn't match "
            f"venv's Python version ({actual_version})"
        )