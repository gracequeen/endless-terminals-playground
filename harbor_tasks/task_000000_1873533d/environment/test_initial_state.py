# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the env-merge.sh script creation task.
"""

import os
import stat
import subprocess
import pytest


class TestDirectoryStructure:
    """Test that required directories exist and have correct permissions."""

    def test_bin_directory_exists(self):
        """Verify /home/user/bin/ directory exists."""
        bin_path = "/home/user/bin"
        assert os.path.isdir(bin_path), f"Directory {bin_path} does not exist"

    def test_bin_directory_is_writable(self):
        """Verify /home/user/bin/ directory is writable."""
        bin_path = "/home/user/bin"
        assert os.access(bin_path, os.W_OK), f"Directory {bin_path} is not writable"

    def test_env_merge_script_does_not_exist(self):
        """Verify env-merge.sh does not exist yet (student needs to create it)."""
        script_path = "/home/user/bin/env-merge.sh"
        assert not os.path.exists(script_path), f"Script {script_path} already exists - it should not exist yet"

    def test_project_directory_exists(self):
        """Verify /home/user/project/ directory exists."""
        project_path = "/home/user/project"
        assert os.path.isdir(project_path), f"Directory {project_path} does not exist"


class TestEnvDefaultsFile:
    """Test the .env.defaults file exists with correct content."""

    def test_env_defaults_exists(self):
        """Verify /home/user/project/.env.defaults exists."""
        file_path = "/home/user/project/.env.defaults"
        assert os.path.isfile(file_path), f"File {file_path} does not exist"

    def test_env_defaults_content(self):
        """Verify /home/user/project/.env.defaults has the expected content."""
        file_path = "/home/user/project/.env.defaults"
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse the content into key-value pairs
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        env_dict = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                env_dict[key] = value

        expected = {
            'DATABASE_URL': 'postgres://localhost/dev',
            'CACHE_TTL': '300',
            'DEBUG': 'false',
            'API_KEY': 'default-key-123'
        }

        assert env_dict == expected, (
            f".env.defaults content mismatch.\n"
            f"Expected: {expected}\n"
            f"Got: {env_dict}"
        )


class TestEnvLocalFile:
    """Test the .env.local file exists with correct content."""

    def test_env_local_exists(self):
        """Verify /home/user/project/.env.local exists."""
        file_path = "/home/user/project/.env.local"
        assert os.path.isfile(file_path), f"File {file_path} does not exist"

    def test_env_local_content(self):
        """Verify /home/user/project/.env.local has the expected content."""
        file_path = "/home/user/project/.env.local"
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse the content into key-value pairs
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        env_dict = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                env_dict[key] = value

        expected = {
            'DEBUG': 'true',
            'API_KEY': 'secret-prod-key-456',
            'NEW_FEATURE': 'enabled'
        }

        assert env_dict == expected, (
            f".env.local content mismatch.\n"
            f"Expected: {expected}\n"
            f"Got: {env_dict}"
        )


class TestRequiredTools:
    """Test that required tools (bash, awk, sed, sort, cat) are available."""

    @pytest.mark.parametrize("tool", ["bash", "awk", "sed", "sort", "cat"])
    def test_tool_available(self, tool):
        """Verify required tool is available in PATH."""
        result = subprocess.run(
            ["which", tool],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Tool '{tool}' is not available in PATH"

    def test_bash_is_executable(self):
        """Verify bash can execute a simple command."""
        result = subprocess.run(
            ["bash", "-c", "echo test"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "bash cannot execute simple commands"
        assert result.stdout.strip() == "test", "bash output unexpected"

    def test_awk_is_functional(self):
        """Verify awk can process input."""
        result = subprocess.run(
            ["bash", "-c", "echo 'a=b' | awk -F= '{print $1}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "awk is not functional"
        assert result.stdout.strip() == "a", "awk output unexpected"

    def test_sed_is_functional(self):
        """Verify sed can process input."""
        result = subprocess.run(
            ["bash", "-c", "echo 'hello' | sed 's/hello/world/'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sed is not functional"
        assert result.stdout.strip() == "world", "sed output unexpected"

    def test_sort_is_functional(self):
        """Verify sort can process input."""
        result = subprocess.run(
            ["bash", "-c", "echo -e 'b\\na' | sort"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sort is not functional"
        assert result.stdout.strip() == "a\nb", "sort output unexpected"

    def test_cat_is_functional(self):
        """Verify cat can read files."""
        result = subprocess.run(
            ["cat", "/home/user/project/.env.defaults"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "cat cannot read .env.defaults file"
