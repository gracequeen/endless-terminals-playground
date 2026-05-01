# test_initial_state.py
"""
Tests to validate the initial state before the student performs the git submodule initialization task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the OS/filesystem state before the task is performed."""

    def test_git_is_installed(self):
        """Verify git is installed and accessible."""
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "git is not installed or not accessible"

    def test_webapp_directory_exists(self):
        """Verify /home/user/webapp directory exists."""
        assert os.path.isdir("/home/user/webapp"), \
            "/home/user/webapp directory does not exist"

    def test_webapp_is_git_repository(self):
        """Verify /home/user/webapp is a git repository."""
        git_dir = "/home/user/webapp/.git"
        assert os.path.exists(git_dir), \
            "/home/user/webapp is not a git repository (.git not found)"

    def test_webapp_has_at_least_one_commit(self):
        """Verify the repository has at least one commit."""
        result = subprocess.run(
            ["git", "-C", "/home/user/webapp", "rev-parse", "HEAD"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "/home/user/webapp repository has no commits"

    def test_gitmodules_file_exists(self):
        """Verify .gitmodules file exists."""
        gitmodules_path = "/home/user/webapp/.gitmodules"
        assert os.path.isfile(gitmodules_path), \
            ".gitmodules file does not exist at /home/user/webapp/.gitmodules"

    def test_gitmodules_contains_submodule_config(self):
        """Verify .gitmodules contains the expected submodule configuration."""
        gitmodules_path = "/home/user/webapp/.gitmodules"
        with open(gitmodules_path, "r") as f:
            content = f.read()

        assert '[submodule "vendor/loglib"]' in content, \
            ".gitmodules does not contain [submodule \"vendor/loglib\"] section"
        assert 'path = vendor/loglib' in content, \
            ".gitmodules does not contain 'path = vendor/loglib'"
        assert 'url = https://github.com/gabime/spdlog.git' in content, \
            ".gitmodules does not contain 'url = https://github.com/gabime/spdlog.git'"

    def test_submodule_directory_does_not_exist(self):
        """Verify vendor/loglib directory does not exist (submodule not initialized)."""
        submodule_path = "/home/user/webapp/vendor/loglib"
        # The directory should either not exist or be empty
        if os.path.exists(submodule_path):
            # If it exists, it should be empty (just the placeholder)
            contents = os.listdir(submodule_path)
            assert len(contents) == 0, \
                f"vendor/loglib exists and is not empty: {contents}. Submodule appears to already be populated."
        # If it doesn't exist at all, that's also fine (expected state)

    def test_submodule_not_registered_in_git_config(self):
        """Verify the submodule is not yet registered in .git/config."""
        git_config_path = "/home/user/webapp/.git/config"
        if os.path.isfile(git_config_path):
            with open(git_config_path, "r") as f:
                content = f.read()
            assert '[submodule "vendor/loglib"]' not in content, \
                "Submodule is already registered in .git/config"

    def test_submodule_shows_as_uninitialized(self):
        """Verify git submodule status shows the submodule as uninitialized (leading '-')."""
        result = subprocess.run(
            ["git", "-C", "/home/user/webapp", "submodule", "status"],
            capture_output=True,
            text=True
        )
        # The command should succeed
        assert result.returncode == 0, \
            f"git submodule status failed: {result.stderr}"

        output = result.stdout.strip()
        if output:
            # If there's output, it should show uninitialized (leading '-')
            assert output.startswith('-'), \
                f"Submodule appears to be already initialized. Status: {output}"

    def test_webapp_is_writable(self):
        """Verify /home/user/webapp is writable."""
        assert os.access("/home/user/webapp", os.W_OK), \
            "/home/user/webapp is not writable"

    def test_vendor_directory_is_writable_or_creatable(self):
        """Verify vendor directory can be written to or created."""
        vendor_path = "/home/user/webapp/vendor"
        if os.path.exists(vendor_path):
            assert os.access(vendor_path, os.W_OK), \
                "/home/user/webapp/vendor exists but is not writable"
        else:
            # If vendor doesn't exist, webapp must be writable to create it
            assert os.access("/home/user/webapp", os.W_OK), \
                "/home/user/webapp is not writable, cannot create vendor directory"

    def test_network_access_to_github(self):
        """Verify network access to github.com is available."""
        # Try to reach github.com
        result = subprocess.run(
            ["git", "ls-remote", "--exit-code", "https://github.com/gabime/spdlog.git", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"Cannot access https://github.com/gabime/spdlog.git - network may be unavailable: {result.stderr}"
