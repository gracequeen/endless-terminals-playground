# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of pinning mlflow to exactly 2.9.2 in requirements.txt.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    REQUIREMENTS_PATH = "/home/user/tracking/requirements.txt"
    TRACKING_DIR = "/home/user/tracking"

    def test_tracking_directory_exists(self):
        """The /home/user/tracking directory must exist."""
        assert os.path.isdir(self.TRACKING_DIR), (
            f"Directory {self.TRACKING_DIR} does not exist. "
            "Please create the tracking directory first."
        )

    def test_tracking_directory_is_writable(self):
        """The /home/user/tracking directory must be writable."""
        assert os.access(self.TRACKING_DIR, os.W_OK), (
            f"Directory {self.TRACKING_DIR} is not writable. "
            "Please ensure write permissions are set."
        )

    def test_requirements_file_exists(self):
        """The requirements.txt file must exist."""
        assert os.path.isfile(self.REQUIREMENTS_PATH), (
            f"File {self.REQUIREMENTS_PATH} does not exist. "
            "Please create the requirements.txt file first."
        )

    def test_requirements_file_is_readable(self):
        """The requirements.txt file must be readable."""
        assert os.access(self.REQUIREMENTS_PATH, os.R_OK), (
            f"File {self.REQUIREMENTS_PATH} is not readable. "
            "Please ensure read permissions are set."
        )

    def test_requirements_file_is_writable(self):
        """The requirements.txt file must be writable."""
        assert os.access(self.REQUIREMENTS_PATH, os.W_OK), (
            f"File {self.REQUIREMENTS_PATH} is not writable. "
            "Please ensure write permissions are set."
        )

    def test_requirements_file_has_correct_line_count(self):
        """The requirements.txt file must have exactly 5 lines."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 5, (
            f"Expected 5 lines in {self.REQUIREMENTS_PATH}, "
            f"but found {len(lines)} lines."
        )

    def test_requirements_file_has_trailing_newline(self):
        """The requirements.txt file must end with a trailing newline."""
        with open(self.REQUIREMENTS_PATH, 'rb') as f:
            content = f.read()
        assert content.endswith(b'\n'), (
            f"File {self.REQUIREMENTS_PATH} does not end with a trailing newline."
        )

    def test_numpy_line_present(self):
        """The numpy==1.24.3 line must be present."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            content = f.read()
        assert 'numpy==1.24.3' in content, (
            f"Expected 'numpy==1.24.3' in {self.REQUIREMENTS_PATH}, but not found."
        )

    def test_pandas_line_present(self):
        """The pandas>=2.0,<3.0 line must be present."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            content = f.read()
        assert 'pandas>=2.0,<3.0' in content, (
            f"Expected 'pandas>=2.0,<3.0' in {self.REQUIREMENTS_PATH}, but not found."
        )

    def test_mlflow_line_present_with_old_specifier(self):
        """The mlflow>=2.0 line must be present (initial state before change)."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'mlflow>=2.0' in lines, (
            f"Expected 'mlflow>=2.0' as a line in {self.REQUIREMENTS_PATH}, "
            "but not found. This is the initial state that needs to be changed."
        )

    def test_scikit_learn_line_present(self):
        """The scikit-learn==1.3.0 line must be present."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            content = f.read()
        assert 'scikit-learn==1.3.0' in content, (
            f"Expected 'scikit-learn==1.3.0' in {self.REQUIREMENTS_PATH}, but not found."
        )

    def test_boto3_line_present(self):
        """The boto3>=1.28.0 line must be present."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            content = f.read()
        assert 'boto3>=1.28.0' in content, (
            f"Expected 'boto3>=1.28.0' in {self.REQUIREMENTS_PATH}, but not found."
        )

    def test_exact_initial_content(self):
        """The requirements.txt file must have the exact expected initial content."""
        expected_content = (
            "numpy==1.24.3\n"
            "pandas>=2.0,<3.0\n"
            "mlflow>=2.0\n"
            "scikit-learn==1.3.0\n"
            "boto3>=1.28.0\n"
        )
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            actual_content = f.read()
        assert actual_content == expected_content, (
            f"File {self.REQUIREMENTS_PATH} does not have the expected initial content.\n"
            f"Expected:\n{repr(expected_content)}\n"
            f"Actual:\n{repr(actual_content)}"
        )

    def test_mlflow_pinned_version_not_present_yet(self):
        """The mlflow==2.9.2 line should NOT be present yet (initial state)."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'mlflow==2.9.2' not in lines, (
            f"Found 'mlflow==2.9.2' in {self.REQUIREMENTS_PATH}, "
            "but this should not be present in the initial state. "
            "The task is to change 'mlflow>=2.0' to 'mlflow==2.9.2'."
        )
