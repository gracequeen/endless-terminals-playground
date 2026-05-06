# test_final_state.py
"""
Tests to validate the final state of the system after the student has created
the diskmon.sh script that checks disk usage and exits appropriately.
"""

import os
import stat
import subprocess
import tempfile
import pytest


class TestScriptExists:
    """Test that the script exists and has correct permissions."""

    def test_diskmon_script_exists(self):
        """Verify /home/user/bin/diskmon.sh exists."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), (
            f"Script {script_path} does not exist. "
            "You need to create the diskmon.sh script."
        )

    def test_diskmon_script_is_file(self):
        """Verify /home/user/bin/diskmon.sh is a regular file."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.isfile(script_path), (
            f"{script_path} exists but is not a regular file. "
            "The script must be a regular file, not a directory or symlink."
        )

    def test_diskmon_script_is_executable(self):
        """Verify /home/user/bin/diskmon.sh has executable permission."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        file_stat = os.stat(script_path)
        is_executable = bool(file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        assert is_executable, (
            f"Script {script_path} is not executable. "
            "Run 'chmod +x /home/user/bin/diskmon.sh' to make it executable."
        )


class TestScriptContent:
    """Test that the script contains required elements (anti-shortcut guards)."""

    def test_script_contains_df_command(self):
        """Verify script contains 'df' command - must parse actual disk usage."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        with open(script_path, 'r') as f:
            content = f.read()

        assert 'df' in content, (
            "Script does not contain 'df' command. "
            "The script must use 'df' to check actual disk usage, not hardcode values."
        )

    def test_script_has_conditional_logic(self):
        """Verify script has conditional logic - not just unconditional exit."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        with open(script_path, 'r') as f:
            content = f.read()

        # Check for various forms of conditional logic
        has_conditional = any([
            'if ' in content or 'if[' in content,
            'test ' in content,
            '[ ' in content or '[[' in content,
            'while ' in content,
            'for ' in content,
            # awk-based conditionals
            ('awk' in content and ('>' in content or '<' in content or '>=' in content)),
            # grep with exit status check
            ('grep' in content and ('$?' in content or '||' in content or '&&' in content)),
            # Direct comparison in shell
            '-gt' in content or '-ge' in content or '-lt' in content or '-le' in content,
        ])

        assert has_conditional, (
            "Script does not appear to have conditional logic. "
            "The script must check disk usage and conditionally exit, "
            "not just unconditionally exit 0 or exit 1."
        )


class TestScriptExecution:
    """Test that the script executes correctly."""

    def test_script_runs_without_error_via_bash(self):
        """Verify script can be run with 'bash /home/user/bin/diskmon.sh'."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Script should exit with 0 or 1, not other error codes
        assert result.returncode in [0, 1], (
            f"Script exited with unexpected code {result.returncode}. "
            f"Expected 0 (all filesystems <80%) or 1 (some filesystem >=80%). "
            f"Stderr: {result.stderr}"
        )

    def test_script_runs_without_error_directly(self):
        """Verify script can be run directly as executable."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        result = subprocess.run(
            [script_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Script should exit with 0 or 1, not other error codes
        assert result.returncode in [0, 1], (
            f"Script exited with unexpected code {result.returncode}. "
            f"Expected 0 (all filesystems <80%) or 1 (some filesystem >=80%). "
            f"Stderr: {result.stderr}"
        )

    def test_script_produces_minimal_output(self):
        """Verify script produces no or minimal stdout output."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Allow empty or very minimal output (some implementations might output nothing)
        stdout_lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
        assert len(stdout_lines) <= 1, (
            f"Script produces too much output. Expected minimal/no output. "
            f"Got stdout: {result.stdout}"
        )


class TestScriptLogic:
    """Test that the script correctly checks disk usage thresholds."""

    def _get_current_max_usage(self):
        """Get the current maximum disk usage percentage from df."""
        result = subprocess.run(
            ["df", "-P"],
            capture_output=True,
            text=True
        )

        max_usage = 0
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5:
                usage_str = parts[4].rstrip('%')
                try:
                    usage = int(usage_str)
                    max_usage = max(max_usage, usage)
                except ValueError:
                    continue
        return max_usage

    def test_script_exit_code_matches_disk_state(self):
        """Verify script exit code correctly reflects actual disk usage."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        # Get actual max disk usage
        max_usage = self._get_current_max_usage()

        # Run the script
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Verify exit code matches expected state
        if max_usage >= 80:
            assert result.returncode == 1, (
                f"Script exited with code {result.returncode} but max disk usage is {max_usage}% (>=80%). "
                "Script should exit 1 when any filesystem is at or above 80% usage."
            )
        else:
            assert result.returncode == 0, (
                f"Script exited with code {result.returncode} but max disk usage is {max_usage}% (<80%). "
                "Script should exit 0 when all filesystems are below 80% usage."
            )

    def test_script_detects_high_usage_with_mock(self):
        """Test script behavior by creating a mock df that reports high usage."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        # Read the script content
        with open(script_path, 'r') as f:
            script_content = f.read()

        # Create a temporary directory with a mock df
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_df = os.path.join(tmpdir, "df")

            # Create mock df that reports 85% usage
            with open(mock_df, 'w') as f:
                f.write('''#!/bin/bash
echo "Filesystem     1K-blocks    Used Available Use% Mounted on"
echo "/dev/sda1      100000000 85000000  15000000  85% /"
''')
            os.chmod(mock_df, 0o755)

            # Run script with modified PATH
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"

            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )

            assert result.returncode == 1, (
                f"Script exited with code {result.returncode} when mock df reports 85% usage. "
                "Script should exit 1 when any filesystem is at or above 80% usage."
            )

    def test_script_detects_low_usage_with_mock(self):
        """Test script behavior by creating a mock df that reports low usage."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        # Create a temporary directory with a mock df
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_df = os.path.join(tmpdir, "df")

            # Create mock df that reports 50% usage
            with open(mock_df, 'w') as f:
                f.write('''#!/bin/bash
echo "Filesystem     1K-blocks    Used Available Use% Mounted on"
echo "/dev/sda1      100000000 50000000  50000000  50% /"
''')
            os.chmod(mock_df, 0o755)

            # Run script with modified PATH
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"

            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )

            assert result.returncode == 0, (
                f"Script exited with code {result.returncode} when mock df reports 50% usage. "
                "Script should exit 0 when all filesystems are below 80% usage."
            )

    def test_script_handles_exactly_80_percent(self):
        """Test script correctly handles exactly 80% usage (should exit 1)."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        # Create a temporary directory with a mock df
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_df = os.path.join(tmpdir, "df")

            # Create mock df that reports exactly 80% usage
            with open(mock_df, 'w') as f:
                f.write('''#!/bin/bash
echo "Filesystem     1K-blocks    Used Available Use% Mounted on"
echo "/dev/sda1      100000000 80000000  20000000  80% /"
''')
            os.chmod(mock_df, 0o755)

            # Run script with modified PATH
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"

            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )

            assert result.returncode == 1, (
                f"Script exited with code {result.returncode} when mock df reports exactly 80% usage. "
                "Script should exit 1 when any filesystem is at or above 80% usage (>=80%)."
            )

    def test_script_handles_79_percent(self):
        """Test script correctly handles 79% usage (should exit 0)."""
        script_path = "/home/user/bin/diskmon.sh"
        assert os.path.exists(script_path), f"Script {script_path} does not exist."

        # Create a temporary directory with a mock df
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_df = os.path.join(tmpdir, "df")

            # Create mock df that reports 79% usage
            with open(mock_df, 'w') as f:
                f.write('''#!/bin/bash
echo "Filesystem     1K-blocks    Used Available Use% Mounted on"
echo "/dev/sda1      100000000 79000000  21000000  79% /"
''')
            os.chmod(mock_df, 0o755)

            # Run script with modified PATH
            env = os.environ.copy()
            env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"

            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )

            assert result.returncode == 0, (
                f"Script exited with code {result.returncode} when mock df reports 79% usage. "
                "Script should exit 0 when all filesystems are below 80% usage."
            )
