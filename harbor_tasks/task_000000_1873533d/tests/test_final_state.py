# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the env-merge.sh script creation task.
"""

import os
import stat
import subprocess
import tempfile
import pytest


class TestScriptExists:
    """Test that the script exists and has correct permissions."""

    def test_script_exists(self):
        """Verify /home/user/bin/env-merge.sh exists."""
        script_path = "/home/user/bin/env-merge.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist"

    def test_script_is_file(self):
        """Verify /home/user/bin/env-merge.sh is a regular file."""
        script_path = "/home/user/bin/env-merge.sh"
        assert os.path.isfile(script_path), f"{script_path} is not a regular file"

    def test_script_is_executable(self):
        """Verify /home/user/bin/env-merge.sh has executable permission."""
        script_path = "/home/user/bin/env-merge.sh"
        assert os.access(script_path, os.X_OK), f"Script {script_path} is not executable (missing +x permission)"


class TestOriginalFilesUnchanged:
    """Test that original .env files remain unchanged."""

    def test_env_defaults_unchanged(self):
        """Verify /home/user/project/.env.defaults has not been modified."""
        file_path = "/home/user/project/.env.defaults"
        with open(file_path, 'r') as f:
            content = f.read()

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
            f".env.defaults has been modified.\n"
            f"Expected: {expected}\n"
            f"Got: {env_dict}"
        )

    def test_env_local_unchanged(self):
        """Verify /home/user/project/.env.local has not been modified."""
        file_path = "/home/user/project/.env.local"
        with open(file_path, 'r') as f:
            content = f.read()

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
            f".env.local has been modified.\n"
            f"Expected: {expected}\n"
            f"Got: {env_dict}"
        )


class TestScriptFunctionality:
    """Test that the script works correctly with the provided files."""

    def test_script_exits_zero(self):
        """Verify script exits with code 0 when run with valid arguments."""
        result = subprocess.run(
            ["/home/user/bin/env-merge.sh",
             "/home/user/project/.env.defaults",
             "/home/user/project/.env.local"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Script exited with code {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_merged_output_contains_all_keys(self):
        """Verify merged output contains all expected keys."""
        result = subprocess.run(
            ["/home/user/bin/env-merge.sh",
             "/home/user/project/.env.defaults",
             "/home/user/project/.env.local"],
            capture_output=True,
            text=True
        )

        output = result.stdout
        lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        env_dict = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                env_dict[key] = value

        expected_keys = {'DATABASE_URL', 'CACHE_TTL', 'DEBUG', 'API_KEY', 'NEW_FEATURE'}
        actual_keys = set(env_dict.keys())

        assert expected_keys == actual_keys, (
            f"Output keys mismatch.\n"
            f"Expected keys: {expected_keys}\n"
            f"Got keys: {actual_keys}\n"
            f"Missing: {expected_keys - actual_keys}\n"
            f"Extra: {actual_keys - expected_keys}"
        )

    def test_merged_output_correct_values(self):
        """Verify merged output has correct values with second file winning conflicts."""
        result = subprocess.run(
            ["/home/user/bin/env-merge.sh",
             "/home/user/project/.env.defaults",
             "/home/user/project/.env.local"],
            capture_output=True,
            text=True
        )

        output = result.stdout
        lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        env_dict = {}
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                env_dict[key] = value

        expected = {
            'DATABASE_URL': 'postgres://localhost/dev',
            'CACHE_TTL': '300',
            'DEBUG': 'true',  # Overridden by .env.local
            'API_KEY': 'secret-prod-key-456',  # Overridden by .env.local
            'NEW_FEATURE': 'enabled'  # Only in .env.local
        }

        assert env_dict == expected, (
            f"Merged output values incorrect.\n"
            f"Expected: {expected}\n"
            f"Got: {env_dict}"
        )

    def test_no_duplicate_keys(self):
        """Verify output contains no duplicate keys."""
        result = subprocess.run(
            ["/home/user/bin/env-merge.sh",
             "/home/user/project/.env.defaults",
             "/home/user/project/.env.local"],
            capture_output=True,
            text=True
        )

        output = result.stdout
        lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
        keys = []
        for line in lines:
            if '=' in line:
                key, _ = line.split('=', 1)
                keys.append(key)

        duplicates = [k for k in keys if keys.count(k) > 1]
        assert len(duplicates) == 0, (
            f"Output contains duplicate keys: {set(duplicates)}\n"
            f"All keys found: {keys}"
        )


class TestScriptNotHardcoded:
    """Test that the script works with arbitrary .env files, not just the specific ones."""

    def test_script_with_different_files(self):
        """Verify script works with different .env files (not hardcoded)."""
        # Create temporary test files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f1:
            f1.write("FOO=bar\nBAZ=original\nONLY_FIRST=yes\n")
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f2:
            f2.write("BAZ=overridden\nQUX=new\n")
            temp_file2 = f2.name

        try:
            result = subprocess.run(
                ["/home/user/bin/env-merge.sh", temp_file1, temp_file2],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, (
                f"Script failed with different files. Exit code: {result.returncode}\n"
                f"stderr: {result.stderr}"
            )

            output = result.stdout
            lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
            env_dict = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key] = value

            expected = {
                'FOO': 'bar',
                'BAZ': 'overridden',  # Second file wins
                'ONLY_FIRST': 'yes',
                'QUX': 'new'
            }

            assert env_dict == expected, (
                f"Script appears to be hardcoded to specific files.\n"
                f"Expected: {expected}\n"
                f"Got: {env_dict}"
            )

        finally:
            os.unlink(temp_file1)
            os.unlink(temp_file2)

    def test_script_with_empty_first_file(self):
        """Verify script handles empty first file correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f1:
            f1.write("")
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f2:
            f2.write("KEY=value\n")
            temp_file2 = f2.name

        try:
            result = subprocess.run(
                ["/home/user/bin/env-merge.sh", temp_file1, temp_file2],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, (
                f"Script failed with empty first file. Exit code: {result.returncode}\n"
                f"stderr: {result.stderr}"
            )

            output = result.stdout
            lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
            env_dict = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key] = value

            assert 'KEY' in env_dict and env_dict['KEY'] == 'value', (
                f"Script did not handle empty first file correctly.\n"
                f"Expected KEY=value in output, got: {env_dict}"
            )

        finally:
            os.unlink(temp_file1)
            os.unlink(temp_file2)

    def test_script_with_empty_second_file(self):
        """Verify script handles empty second file correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f1:
            f1.write("KEY=value\n")
            temp_file1 = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f2:
            f2.write("")
            temp_file2 = f2.name

        try:
            result = subprocess.run(
                ["/home/user/bin/env-merge.sh", temp_file1, temp_file2],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, (
                f"Script failed with empty second file. Exit code: {result.returncode}\n"
                f"stderr: {result.stderr}"
            )

            output = result.stdout
            lines = [line.strip() for line in output.strip().split('\n') if line.strip()]
            env_dict = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key] = value

            assert 'KEY' in env_dict and env_dict['KEY'] == 'value', (
                f"Script did not handle empty second file correctly.\n"
                f"Expected KEY=value in output, got: {env_dict}"
            )

        finally:
            os.unlink(temp_file1)
            os.unlink(temp_file2)
