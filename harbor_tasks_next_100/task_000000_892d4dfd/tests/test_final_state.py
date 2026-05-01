# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of pinning mlflow to exactly 2.9.2 in requirements.txt.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    REQUIREMENTS_PATH = "/home/user/tracking/requirements.txt"
    TRACKING_DIR = "/home/user/tracking"

    def test_tracking_directory_exists(self):
        """The /home/user/tracking directory must still exist."""
        assert os.path.isdir(self.TRACKING_DIR), (
            f"Directory {self.TRACKING_DIR} does not exist."
        )

    def test_requirements_file_exists(self):
        """The requirements.txt file must still exist."""
        assert os.path.isfile(self.REQUIREMENTS_PATH), (
            f"File {self.REQUIREMENTS_PATH} does not exist."
        )

    def test_requirements_file_has_exactly_5_lines(self):
        """The requirements.txt file must have exactly 5 lines (no lines added or removed)."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = f.readlines()
        assert len(lines) == 5, (
            f"Expected exactly 5 lines in {self.REQUIREMENTS_PATH}, "
            f"but found {len(lines)} lines. No lines should be added or removed."
        )

    def test_requirements_file_has_trailing_newline(self):
        """The requirements.txt file must end with a trailing newline."""
        with open(self.REQUIREMENTS_PATH, 'rb') as f:
            content = f.read()
        assert content.endswith(b'\n'), (
            f"File {self.REQUIREMENTS_PATH} does not end with a trailing newline. "
            "The trailing newline must be preserved."
        )

    def test_mlflow_pinned_to_exact_version(self):
        """The mlflow line must be pinned to exactly 2.9.2."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'mlflow==2.9.2' in lines, (
            f"Expected 'mlflow==2.9.2' as a line in {self.REQUIREMENTS_PATH}, "
            f"but not found. Current lines: {lines}"
        )

    def test_old_mlflow_specifier_removed(self):
        """The old mlflow>=2.0 specifier must no longer be present."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'mlflow>=2.0' not in lines, (
            f"Found 'mlflow>=2.0' in {self.REQUIREMENTS_PATH}, "
            "but it should have been replaced with 'mlflow==2.9.2'."
        )

    def test_mlflow_line_appears_exactly_once(self):
        """The mlflow==2.9.2 line must appear exactly once."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        mlflow_count = sum(1 for line in lines if line == 'mlflow==2.9.2')
        assert mlflow_count == 1, (
            f"Expected exactly one 'mlflow==2.9.2' line, but found {mlflow_count}."
        )

    def test_numpy_line_unchanged(self):
        """The numpy==1.24.3 line must remain unchanged."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'numpy==1.24.3' in lines, (
            f"Expected 'numpy==1.24.3' in {self.REQUIREMENTS_PATH}, "
            "but not found. This line should not have been modified."
        )

    def test_pandas_line_unchanged(self):
        """The pandas>=2.0,<3.0 line must remain unchanged."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'pandas>=2.0,<3.0' in lines, (
            f"Expected 'pandas>=2.0,<3.0' in {self.REQUIREMENTS_PATH}, "
            "but not found. This line should not have been modified."
        )

    def test_scikit_learn_line_unchanged(self):
        """The scikit-learn==1.3.0 line must remain unchanged."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'scikit-learn==1.3.0' in lines, (
            f"Expected 'scikit-learn==1.3.0' in {self.REQUIREMENTS_PATH}, "
            "but not found. This line should not have been modified."
        )

    def test_boto3_line_unchanged(self):
        """The boto3>=1.28.0 line must remain unchanged."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
        assert 'boto3>=1.28.0' in lines, (
            f"Expected 'boto3>=1.28.0' in {self.REQUIREMENTS_PATH}, "
            "but not found. This line should not have been modified."
        )

    def test_line_order_preserved(self):
        """The lines must be in the correct order."""
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            lines = [line.strip() for line in f.readlines()]

        expected_order = [
            'numpy==1.24.3',
            'pandas>=2.0,<3.0',
            'mlflow==2.9.2',
            'scikit-learn==1.3.0',
            'boto3>=1.28.0'
        ]

        assert lines == expected_order, (
            f"Lines are not in the expected order.\n"
            f"Expected: {expected_order}\n"
            f"Actual: {lines}"
        )

    def test_exact_final_content(self):
        """The requirements.txt file must have the exact expected final content."""
        expected_content = (
            "numpy==1.24.3\n"
            "pandas>=2.0,<3.0\n"
            "mlflow==2.9.2\n"
            "scikit-learn==1.3.0\n"
            "boto3>=1.28.0\n"
        )
        with open(self.REQUIREMENTS_PATH, 'r') as f:
            actual_content = f.read()
        assert actual_content == expected_content, (
            f"File {self.REQUIREMENTS_PATH} does not have the expected final content.\n"
            f"Expected:\n{repr(expected_content)}\n"
            f"Actual:\n{repr(actual_content)}"
        )

    def test_grep_mlflow_exact_match(self):
        """Anti-shortcut: grep must find exactly one line matching '^mlflow==2\\.9\\.2$'."""
        result = subprocess.run(
            ['grep', '-E', '^mlflow==2\\.9\\.2$', self.REQUIREMENTS_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"grep did not find 'mlflow==2.9.2' as an exact line in {self.REQUIREMENTS_PATH}. "
            f"stderr: {result.stderr}"
        )
        matching_lines = result.stdout.strip().split('\n')
        assert len(matching_lines) == 1, (
            f"Expected exactly one line matching 'mlflow==2.9.2', "
            f"but found {len(matching_lines)}: {matching_lines}"
        )

    def test_wc_line_count(self):
        """Anti-shortcut: wc -l must report exactly 5 lines."""
        result = subprocess.run(
            ['wc', '-l', self.REQUIREMENTS_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"wc -l failed on {self.REQUIREMENTS_PATH}. stderr: {result.stderr}"
        )
        # wc -l output format: "5 /path/to/file"
        line_count = int(result.stdout.strip().split()[0])
        assert line_count == 5, (
            f"Expected 5 lines according to 'wc -l', but found {line_count}."
        )
