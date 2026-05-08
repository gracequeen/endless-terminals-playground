# test_initial_state.py
"""
Tests to validate the initial state before the student performs the pip cache purge task.
"""

import os
import subprocess
import pytest


class TestPipCacheInitialState:
    """Tests to verify the initial state of the pip cache directory."""

    def test_pip_cache_directory_exists(self):
        """Verify that /home/user/.cache/pip directory exists."""
        pip_cache_path = "/home/user/.cache/pip"
        assert os.path.exists(pip_cache_path), (
            f"Directory {pip_cache_path} does not exist. "
            "The pip cache directory should exist before the task."
        )
        assert os.path.isdir(pip_cache_path), (
            f"{pip_cache_path} exists but is not a directory."
        )

    def test_pip_cache_wheels_directory_exists(self):
        """Verify that /home/user/.cache/pip/wheels directory exists."""
        wheels_path = "/home/user/.cache/pip/wheels"
        assert os.path.exists(wheels_path), (
            f"Directory {wheels_path} does not exist. "
            "The pip wheels cache directory should exist with cached files."
        )
        assert os.path.isdir(wheels_path), (
            f"{wheels_path} exists but is not a directory."
        )

    def test_pip_cache_http_directory_exists(self):
        """Verify that /home/user/.cache/pip/http directory exists."""
        http_path = "/home/user/.cache/pip/http"
        assert os.path.exists(http_path), (
            f"Directory {http_path} does not exist. "
            "The pip http cache directory should exist with cached files."
        )
        assert os.path.isdir(http_path), (
            f"{http_path} exists but is not a directory."
        )

    def test_pip_cache_contains_files(self):
        """Verify that the pip cache directory contains cached files."""
        pip_cache_path = "/home/user/.cache/pip"

        # Walk through the directory and count files
        file_count = 0
        for root, dirs, files in os.walk(pip_cache_path):
            file_count += len(files)

        assert file_count > 0, (
            f"Directory {pip_cache_path} is empty. "
            "The pip cache should contain cached files before the task."
        )

    def test_pip_cache_is_writable(self):
        """Verify that /home/user/.cache/pip is writable by the user."""
        pip_cache_path = "/home/user/.cache/pip"
        assert os.access(pip_cache_path, os.W_OK), (
            f"Directory {pip_cache_path} is not writable. "
            "The user must have write permissions to purge the cache."
        )

    def test_parent_cache_directory_exists(self):
        """Verify that /home/user/.cache directory exists."""
        cache_path = "/home/user/.cache"
        assert os.path.exists(cache_path), (
            f"Directory {cache_path} does not exist. "
            "The parent .cache directory should exist."
        )
        assert os.path.isdir(cache_path), (
            f"{cache_path} exists but is not a directory."
        )


class TestPipInstallation:
    """Tests to verify pip is properly installed and available."""

    def test_pip3_is_installed(self):
        """Verify that pip3 is installed and available."""
        result = subprocess.run(
            ["which", "pip3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "pip3 is not installed or not in PATH. "
            "pip3 must be available to run 'pip3 cache purge'."
        )

    def test_pip_is_installed(self):
        """Verify that pip is installed and available."""
        result = subprocess.run(
            ["which", "pip"],
            capture_output=True,
            text=True
        )
        # pip or pip3 should be available
        if result.returncode != 0:
            # Check if pip3 is available as fallback
            result_pip3 = subprocess.run(
                ["which", "pip3"],
                capture_output=True,
                text=True
            )
            assert result_pip3.returncode == 0, (
                "Neither pip nor pip3 is installed or in PATH. "
                "pip must be available to run 'pip cache purge'."
            )

    def test_pip_version_supports_cache_command(self):
        """Verify that pip version supports the 'cache' command (pip >= 20.1)."""
        result = subprocess.run(
            ["pip3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "Failed to get pip3 version. pip3 must be properly installed."
        )

        # Parse version from output like "pip 22.0.2 from /usr/lib/python3/dist-packages/pip (python 3.10)"
        version_output = result.stdout.strip()
        try:
            version_str = version_output.split()[1]
            major_version = int(version_str.split('.')[0])
            minor_version = int(version_str.split('.')[1])

            # pip cache command was added in pip 20.1
            assert major_version >= 20, (
                f"pip version {version_str} is too old. "
                "pip >= 20.1 is required for 'pip cache purge' command."
            )
            if major_version == 20:
                assert minor_version >= 1, (
                    f"pip version {version_str} is too old. "
                    "pip >= 20.1 is required for 'pip cache purge' command."
                )
        except (IndexError, ValueError) as e:
            pytest.fail(f"Could not parse pip version from: {version_output}. Error: {e}")

    def test_pip_cache_command_exists(self):
        """Verify that 'pip cache' command is available."""
        result = subprocess.run(
            ["pip3", "cache", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "'pip3 cache' command is not available. "
            "pip must support the cache subcommand for this task."
        )
        assert "purge" in result.stdout.lower(), (
            "'pip3 cache purge' subcommand is not available. "
            "The purge option must be available in pip cache command."
        )
