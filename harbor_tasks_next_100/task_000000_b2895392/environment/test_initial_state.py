# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of pinning numpy to exactly 1.24.3 in requirements.txt.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    REQUIREMENTS_FILE = "/home/user/deploy/requirements.txt"
    DEPLOY_DIR = "/home/user/deploy"

    def test_deploy_directory_exists(self):
        """Verify that /home/user/deploy directory exists."""
        assert os.path.isdir(self.DEPLOY_DIR), (
            f"Directory {self.DEPLOY_DIR} does not exist. "
            "The deploy directory must exist before performing the task."
        )

    def test_deploy_directory_is_writable(self):
        """Verify that /home/user/deploy directory is writable."""
        assert os.access(self.DEPLOY_DIR, os.W_OK), (
            f"Directory {self.DEPLOY_DIR} is not writable. "
            "The deploy directory must be writable to modify requirements.txt."
        )

    def test_requirements_file_exists(self):
        """Verify that requirements.txt exists in the deploy directory."""
        assert os.path.isfile(self.REQUIREMENTS_FILE), (
            f"File {self.REQUIREMENTS_FILE} does not exist. "
            "The requirements.txt file must exist before performing the task."
        )

    def test_requirements_file_is_readable(self):
        """Verify that requirements.txt is readable."""
        assert os.access(self.REQUIREMENTS_FILE, os.R_OK), (
            f"File {self.REQUIREMENTS_FILE} is not readable. "
            "The requirements.txt file must be readable."
        )

    def test_requirements_file_is_writable(self):
        """Verify that requirements.txt is writable."""
        assert os.access(self.REQUIREMENTS_FILE, os.W_OK), (
            f"File {self.REQUIREMENTS_FILE} is not writable. "
            "The requirements.txt file must be writable to modify it."
        )

    def test_requirements_file_has_five_lines(self):
        """Verify that requirements.txt has exactly 5 lines."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            lines = [line for line in f.readlines() if line.strip()]
        assert len(lines) == 5, (
            f"Expected requirements.txt to have 5 non-empty lines, but found {len(lines)}. "
            "The file should contain: pandas, numpy, scikit-learn, matplotlib, requests."
        )

    def test_pandas_dependency_present(self):
        """Verify that pandas>=2.0.0 is in requirements.txt."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "pandas>=2.0.0" in content, (
            "Expected 'pandas>=2.0.0' to be present in requirements.txt. "
            "This dependency should exist in the initial state."
        )

    def test_numpy_dependency_present_unpinned(self):
        """Verify that numpy is in requirements.txt (unpinned in initial state)."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            lines = [line.strip() for line in f.readlines()]

        # Check that there's a line that is just "numpy" (unpinned)
        numpy_lines = [line for line in lines if line.startswith('numpy')]
        assert len(numpy_lines) == 1, (
            f"Expected exactly one numpy line in requirements.txt, found {len(numpy_lines)}."
        )
        assert numpy_lines[0] == "numpy", (
            f"Expected numpy to be unpinned (just 'numpy'), but found '{numpy_lines[0]}'. "
            "In the initial state, numpy should not have a version specifier."
        )

    def test_scikit_learn_dependency_present(self):
        """Verify that scikit-learn>=1.2.0 is in requirements.txt."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "scikit-learn>=1.2.0" in content, (
            "Expected 'scikit-learn>=1.2.0' to be present in requirements.txt. "
            "This dependency should exist in the initial state."
        )

    def test_matplotlib_dependency_present(self):
        """Verify that matplotlib>=3.7.0 is in requirements.txt."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "matplotlib>=3.7.0" in content, (
            "Expected 'matplotlib>=3.7.0' to be present in requirements.txt. "
            "This dependency should exist in the initial state."
        )

    def test_requests_dependency_present(self):
        """Verify that requests>=2.28.0 is in requirements.txt."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "requests>=2.28.0" in content, (
            "Expected 'requests>=2.28.0' to be present in requirements.txt. "
            "This dependency should exist in the initial state."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
