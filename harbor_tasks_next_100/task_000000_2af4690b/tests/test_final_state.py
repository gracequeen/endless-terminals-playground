# test_final_state.py
"""
Tests to validate the final state after the student has initialized the git submodule.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Validate the OS/filesystem state after the task is performed."""

    def test_submodule_directory_exists(self):
        """Verify /home/user/webapp/vendor/loglib directory exists."""
        submodule_path = "/home/user/webapp/vendor/loglib"
        assert os.path.isdir(submodule_path), \
            f"Submodule directory {submodule_path} does not exist. " \
            "Run 'git submodule init' and 'git submodule update' in /home/user/webapp"

    def test_submodule_directory_is_populated(self):
        """Verify vendor/loglib is populated with repository contents."""
        submodule_path = "/home/user/webapp/vendor/loglib"
        assert os.path.isdir(submodule_path), \
            f"Submodule directory {submodule_path} does not exist"

        contents = os.listdir(submodule_path)
        assert len(contents) > 0, \
            f"Submodule directory {submodule_path} is empty. " \
            "The submodule was not properly updated."

    def test_submodule_has_git_tracking(self):
        """Verify vendor/loglib has .git file or directory (proper git submodule)."""
        submodule_path = "/home/user/webapp/vendor/loglib"
        git_path = os.path.join(submodule_path, ".git")

        assert os.path.exists(git_path), \
            f"{git_path} does not exist. The submodule was not properly initialized via git. " \
            "A manual clone into vendor/loglib is not sufficient."

    def test_submodule_is_spdlog_repository(self):
        """Verify the submodule contains spdlog repository content."""
        submodule_path = "/home/user/webapp/vendor/loglib"

        # spdlog should have certain characteristic files
        # Check for CMakeLists.txt which is present in spdlog
        cmake_file = os.path.join(submodule_path, "CMakeLists.txt")
        include_dir = os.path.join(submodule_path, "include")

        has_cmake = os.path.isfile(cmake_file)
        has_include = os.path.isdir(include_dir)

        assert has_cmake or has_include, \
            f"Submodule at {submodule_path} does not appear to contain spdlog repository. " \
            "Expected CMakeLists.txt or include/ directory."

    def test_submodule_status_shows_initialized(self):
        """Verify git submodule status shows the submodule as initialized (no leading '-')."""
        result = subprocess.run(
            ["git", "-C", "/home/user/webapp", "submodule", "status"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"git submodule status failed: {result.stderr}"

        output = result.stdout.strip()
        assert output, \
            "git submodule status returned empty output. No submodules found."

        # Check that the output does NOT start with '-' (uninitialized)
        # A properly initialized submodule shows commit hash without prefix or with '+' if modified
        assert not output.startswith('-'), \
            f"Submodule is still uninitialized (status starts with '-'). " \
            f"Status: {output}\n" \
            "Run 'git submodule init' and 'git submodule update' in /home/user/webapp"

    def test_submodule_status_contains_vendor_loglib(self):
        """Verify git submodule status mentions vendor/loglib."""
        result = subprocess.run(
            ["git", "-C", "/home/user/webapp", "submodule", "status"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"git submodule status failed: {result.stderr}"

        output = result.stdout
        assert "vendor/loglib" in output, \
            f"Submodule status does not show vendor/loglib. Output: {output}"

    def test_gitmodules_file_unchanged(self):
        """Verify .gitmodules file still contains the expected configuration."""
        gitmodules_path = "/home/user/webapp/.gitmodules"
        assert os.path.isfile(gitmodules_path), \
            ".gitmodules file is missing"

        with open(gitmodules_path, "r") as f:
            content = f.read()

        assert '[submodule "vendor/loglib"]' in content, \
            ".gitmodules was modified - missing [submodule \"vendor/loglib\"] section"
        assert 'path = vendor/loglib' in content, \
            ".gitmodules was modified - missing 'path = vendor/loglib'"
        assert 'url = https://github.com/gabime/spdlog.git' in content, \
            ".gitmodules was modified - missing 'url = https://github.com/gabime/spdlog.git'"

    def test_webapp_still_git_repository(self):
        """Verify /home/user/webapp is still a valid git repository."""
        result = subprocess.run(
            ["git", "-C", "/home/user/webapp", "status"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"/home/user/webapp is no longer a valid git repository: {result.stderr}"

    def test_submodule_is_valid_git_repo(self):
        """Verify the submodule directory is a valid git repository."""
        submodule_path = "/home/user/webapp/vendor/loglib"

        result = subprocess.run(
            ["git", "-C", submodule_path, "rev-parse", "--git-dir"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"vendor/loglib is not a valid git repository: {result.stderr}. " \
            "The submodule must be initialized via git, not manually cloned."

    def test_submodule_not_just_manual_clone(self):
        """
        Verify the submodule was properly initialized via git submodule commands,
        not just a manual git clone into the directory.
        """
        # A properly initialized submodule will be tracked by the parent repo
        result = subprocess.run(
            ["git", "-C", "/home/user/webapp", "submodule", "status", "--recursive"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"git submodule status failed: {result.stderr}"

        output = result.stdout.strip()

        # The output should contain a commit hash (40 hex chars) for vendor/loglib
        # without a leading '-' which would indicate uninitialized
        lines = output.split('\n')
        found_loglib = False
        for line in lines:
            if 'vendor/loglib' in line:
                found_loglib = True
                # Line should start with space or '+' (if modified), not '-'
                stripped = line.lstrip()
                assert not line.lstrip(' ').startswith('-'), \
                    f"Submodule vendor/loglib is not properly initialized. Status line: {line}"
                break

        assert found_loglib, \
            f"vendor/loglib not found in submodule status output: {output}"
