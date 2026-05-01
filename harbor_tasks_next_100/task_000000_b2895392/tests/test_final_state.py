# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of pinning numpy to exactly 1.24.3 in requirements.txt.
"""

import os
import re
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    REQUIREMENTS_FILE = "/home/user/deploy/requirements.txt"
    DEPLOY_DIR = "/home/user/deploy"

    def test_requirements_file_exists(self):
        """Verify that requirements.txt still exists in the deploy directory."""
        assert os.path.isfile(self.REQUIREMENTS_FILE), (
            f"File {self.REQUIREMENTS_FILE} does not exist. "
            "The requirements.txt file must still exist after the task."
        )

    def test_requirements_file_has_five_lines(self):
        """Verify that requirements.txt has exactly 5 non-empty lines (no lines added or removed)."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            lines = [line for line in f.readlines() if line.strip()]
        assert len(lines) == 5, (
            f"Expected requirements.txt to have exactly 5 non-empty lines, but found {len(lines)}. "
            "No lines should be added or removed, only the numpy line should be modified."
        )

    def test_numpy_pinned_to_exact_version(self):
        """Verify that numpy is pinned to exactly 1.24.3."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            lines = [line.strip() for line in f.readlines()]

        numpy_lines = [line for line in lines if line.startswith('numpy')]
        assert len(numpy_lines) == 1, (
            f"Expected exactly one numpy line in requirements.txt, found {len(numpy_lines)}."
        )
        assert numpy_lines[0] == "numpy==1.24.3", (
            f"Expected numpy to be pinned to exactly '1.24.3' (line should be 'numpy==1.24.3'), "
            f"but found '{numpy_lines[0]}'. "
            "The numpy dependency must be pinned with '==' to version 1.24.3."
        )

    def test_numpy_pinned_grep_check(self):
        """Anti-shortcut guard: grep must match exactly one line with numpy==1.24.3."""
        result = subprocess.run(
            ["grep", "-E", "^numpy==1\\.24\\.3$", self.REQUIREMENTS_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"grep did not find a line matching '^numpy==1.24.3$' in {self.REQUIREMENTS_FILE}. "
            "The numpy line must be exactly 'numpy==1.24.3'."
        )
        matching_lines = [line for line in result.stdout.strip().split('\n') if line]
        assert len(matching_lines) == 1, (
            f"Expected exactly one line matching 'numpy==1.24.3', found {len(matching_lines)}."
        )

    def test_pandas_dependency_unchanged(self):
        """Verify that pandas>=2.0.0 is still present and unchanged."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "pandas>=2.0.0" in content, (
            "Expected 'pandas>=2.0.0' to still be present in requirements.txt. "
            "This dependency should not have been modified."
        )

    def test_scikit_learn_dependency_unchanged(self):
        """Verify that scikit-learn>=1.2.0 is still present and unchanged."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "scikit-learn>=1.2.0" in content, (
            "Expected 'scikit-learn>=1.2.0' to still be present in requirements.txt. "
            "This dependency should not have been modified."
        )

    def test_matplotlib_dependency_unchanged(self):
        """Verify that matplotlib>=3.7.0 is still present and unchanged."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "matplotlib>=3.7.0" in content, (
            "Expected 'matplotlib>=3.7.0' to still be present in requirements.txt. "
            "This dependency should not have been modified."
        )

    def test_requests_dependency_unchanged(self):
        """Verify that requests>=2.28.0 is still present and unchanged."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read()
        assert "requests>=2.28.0" in content, (
            "Expected 'requests>=2.28.0' to still be present in requirements.txt. "
            "This dependency should not have been modified."
        )

    def test_file_is_valid_requirements_format(self):
        """Verify that the file is still a valid pip requirements file format."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        # Basic validation: each line should be a valid package specifier
        # Valid patterns: package, package==version, package>=version, package<=version, etc.
        valid_pattern = re.compile(r'^[a-zA-Z0-9_-]+([<>=!]+[a-zA-Z0-9._-]+)?$')

        for line in lines:
            # Skip comments and empty lines
            if line.startswith('#') or not line:
                continue
            assert valid_pattern.match(line), (
                f"Line '{line}' does not appear to be a valid pip requirement format. "
                "The file must remain a valid pip requirements file."
            )

    def test_all_five_expected_packages_present(self):
        """Verify all five expected packages are present."""
        with open(self.REQUIREMENTS_FILE, 'r') as f:
            content = f.read().lower()

        expected_packages = ['pandas', 'numpy', 'scikit-learn', 'matplotlib', 'requests']
        for package in expected_packages:
            assert package in content, (
                f"Expected package '{package}' to be present in requirements.txt, but it was not found."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
