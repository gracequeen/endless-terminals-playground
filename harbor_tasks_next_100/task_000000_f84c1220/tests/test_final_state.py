# test_final_state.py
"""
Tests to validate the final state after the student has completed the pip freeze task.
"""

import os
import re
import subprocess
import pytest


class TestFinalState:
    """Validate the final state of the system after the task is performed."""

    def test_requirements_txt_exists(self):
        """Verify /home/user/webapp/requirements.txt exists."""
        requirements_path = "/home/user/webapp/requirements.txt"
        assert os.path.exists(requirements_path), (
            f"requirements.txt does not exist at {requirements_path}. "
            "Student needs to create this file using pip freeze."
        )
        assert os.path.isfile(requirements_path), (
            f"{requirements_path} exists but is not a regular file."
        )

    def test_requirements_txt_is_not_empty(self):
        """Verify requirements.txt has content."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            content = f.read().strip()
        assert len(content) > 0, (
            "requirements.txt exists but is empty. "
            "It should contain pinned package versions."
        )

    def test_flask_pinned_correctly(self):
        """Verify flask==2.3.2 is in requirements.txt."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            content = f.read().lower()

        # Check for flask==2.3.2 (case-insensitive)
        assert "flask==2.3.2" in content, (
            "requirements.txt must contain 'flask==2.3.2' (exact pinned version). "
            f"Current content does not include this package with correct version."
        )

    def test_requests_pinned_correctly(self):
        """Verify requests==2.31.0 is in requirements.txt."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            content = f.read().lower()

        assert "requests==2.31.0" in content, (
            "requirements.txt must contain 'requests==2.31.0' (exact pinned version). "
            f"Current content does not include this package with correct version."
        )

    def test_gunicorn_pinned_correctly(self):
        """Verify gunicorn==21.2.0 is in requirements.txt."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            content = f.read().lower()

        assert "gunicorn==21.2.0" in content, (
            "requirements.txt must contain 'gunicorn==21.2.0' (exact pinned version). "
            f"Current content does not include this package with correct version."
        )

    def test_no_version_ranges_or_specifiers_other_than_equals(self):
        """Verify no version specifiers other than == are used."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            lines = f.readlines()

        # Pattern to match lines with version specifiers other than ==
        # This matches package names followed by >=, <=, ~=, >, <, != but NOT ==
        bad_specifiers_pattern = re.compile(r'^[a-zA-Z0-9_-]+\s*(>=|<=|~=|>(?!=)|<(?!=)|!=)')

        bad_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if bad_specifiers_pattern.match(line):
                bad_lines.append(line)

        assert len(bad_lines) == 0, (
            f"Found version specifiers other than == (compliance requires exact pinning): {bad_lines}"
        )

    def test_no_bare_package_names_without_versions(self):
        """Verify no bare package names without version specifiers."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            lines = f.readlines()

        # Pattern to match bare package names (no version specifier at all)
        bare_package_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$')

        bare_packages = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Skip lines that are just comments or empty
            if bare_package_pattern.match(line):
                bare_packages.append(line)

        assert len(bare_packages) == 0, (
            f"Found bare package names without version pinning (compliance requires pinned versions): {bare_packages}"
        )

    def test_all_entries_use_double_equals(self):
        """Verify all package entries use == format."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            lines = f.readlines()

        # Pattern for valid pinned package: package==version
        valid_pattern = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*==.+$')

        invalid_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            if not valid_pattern.match(line):
                invalid_lines.append(line)

        assert len(invalid_lines) == 0, (
            f"Found entries not in 'package==version' format: {invalid_lines}. "
            "All packages must be pinned with exact versions using ==."
        )

    def test_venv_still_functional(self):
        """Verify the venv at /home/user/webapp/venv/ remains functional."""
        python_path = "/home/user/webapp/venv/bin/python"
        assert os.path.exists(python_path), (
            f"Python executable {python_path} no longer exists. "
            "The venv should remain functional after the task."
        )

        result = subprocess.run(
            [python_path, "-c", "print('hello')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"venv Python is not functional: {result.stderr}"
        )

    def test_original_packages_still_installed(self):
        """Verify original packages are still installed (no packages uninstalled)."""
        pip_path = "/home/user/webapp/venv/bin/pip"

        # Check flask
        result = subprocess.run(
            [pip_path, "show", "flask"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "flask is no longer installed in the venv"
        assert "Version: 2.3.2" in result.stdout, "flask version changed"

        # Check requests
        result = subprocess.run(
            [pip_path, "show", "requests"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "requests is no longer installed in the venv"
        assert "Version: 2.31.0" in result.stdout, "requests version changed"

        # Check gunicorn
        result = subprocess.run(
            [pip_path, "show", "gunicorn"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gunicorn is no longer installed in the venv"
        assert "Version: 21.2.0" in result.stdout, "gunicorn version changed"

    def test_requirements_has_reasonable_package_count(self):
        """Verify requirements.txt has a reasonable number of packages (including dependencies)."""
        requirements_path = "/home/user/webapp/requirements.txt"
        with open(requirements_path, "r") as f:
            lines = f.readlines()

        # Count non-empty, non-comment lines
        package_lines = [
            line.strip() for line in lines 
            if line.strip() and not line.strip().startswith('#')
        ]

        # Flask, requests, gunicorn plus their dependencies should give us several packages
        assert len(package_lines) >= 3, (
            f"Expected at least 3 packages in requirements.txt "
            f"(flask, requests, gunicorn and their dependencies), "
            f"but found only {len(package_lines)} entries."
        )

    def test_anti_shortcut_no_non_equals_specifiers(self):
        """Anti-shortcut: grep for version specifiers other than == returns no matches."""
        requirements_path = "/home/user/webapp/requirements.txt"

        # Run the anti-shortcut check from the truth
        result = subprocess.run(
            ["grep", "-E", r"^[a-zA-Z0-9_-]+[><=~]", requirements_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            # Found some matches, now filter out lines that are just ==
            lines_with_specifiers = result.stdout.strip().split('\n')
            bad_lines = [line for line in lines_with_specifiers if '==' not in line or 
                        re.search(r'(>=|<=|~=|>(?!=)|<(?!=)|!=)', line)]
            assert len(bad_lines) == 0, (
                f"Found non-== version specifiers (compliance violation): {bad_lines}"
            )

    def test_anti_shortcut_no_bare_packages(self):
        """Anti-shortcut: grep for bare package names returns no matches."""
        requirements_path = "/home/user/webapp/requirements.txt"

        # Run the anti-shortcut check from the truth
        result = subprocess.run(
            ["grep", "-E", r"^[a-zA-Z0-9_-]+$", requirements_path],
            capture_output=True,
            text=True
        )

        # If grep returns 0, it found matches (which is bad)
        if result.returncode == 0 and result.stdout.strip():
            bare_packages = result.stdout.strip().split('\n')
            assert False, (
                f"Found bare package names without versions (compliance violation): {bare_packages}"
            )
