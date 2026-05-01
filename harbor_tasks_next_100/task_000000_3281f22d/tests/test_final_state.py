# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed
the task of adding TZ=UTC to their .bashrc file.
"""

import os
import subprocess
import re
import pytest


BASHRC_PATH = "/home/user/.bashrc"


class TestFinalState:
    """Tests to verify the final state after the task is performed."""

    def test_bashrc_exists(self):
        """Verify that /home/user/.bashrc still exists."""
        assert os.path.exists(BASHRC_PATH), f"{BASHRC_PATH} does not exist"

    def test_bashrc_is_file(self):
        """Verify that /home/user/.bashrc is still a regular file."""
        assert os.path.isfile(BASHRC_PATH), f"{BASHRC_PATH} is not a regular file"

    def test_bashrc_contains_tz_export(self):
        """Verify that .bashrc contains a line that exports TZ=UTC."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()

        # Look for various valid forms of exporting TZ=UTC
        # e.g., export TZ=UTC, export TZ="UTC", export TZ='UTC', TZ=UTC; export TZ, etc.
        lines = content.split('\n')
        found_tz_export = False

        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue

            # Check for 'export TZ=UTC' or 'export TZ="UTC"' or 'export TZ='UTC''
            if re.match(r'^export\s+TZ=["\']?UTC["\']?\s*$', stripped):
                found_tz_export = True
                break

            # Check for 'TZ=UTC; export TZ' or similar patterns
            if re.match(r'^TZ=["\']?UTC["\']?\s*;\s*export\s+TZ\s*$', stripped):
                found_tz_export = True
                break

            # Check for 'TZ=UTC export TZ' pattern
            if re.match(r'^TZ=["\']?UTC["\']?\s+export\s+TZ\s*$', stripped):
                found_tz_export = True
                break

            # Check for 'export TZ=UTC' with potential inline comment
            if re.match(r'^export\s+TZ=["\']?UTC["\']?\s*(#.*)?$', stripped):
                found_tz_export = True
                break

        assert found_tz_export, \
            f".bashrc does not contain a valid TZ=UTC export. Content:\n{content}"

    def test_tz_value_in_new_bash_shell(self):
        """Verify that TZ is set to UTC in a new interactive bash shell."""
        # Use bash -i to start an interactive shell which sources .bashrc
        # We need to run as the user whose .bashrc we're testing
        result = subprocess.run(
            ['bash', '-i', '-c', 'echo $TZ'],
            capture_output=True,
            text=True,
            cwd='/home/user',
            env={'HOME': '/home/user', 'USER': 'user'}
        )

        tz_value = result.stdout.strip()
        assert tz_value == 'UTC', \
            f"TZ is not set to 'UTC' in interactive bash shell. Got: '{tz_value}'"

    def test_original_source_global_definitions_preserved(self):
        """Verify that .bashrc still contains the source global definitions block."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()

        assert "# Source global definitions" in content, \
            ".bashrc is missing '# Source global definitions' comment"
        assert "if [ -f /etc/bashrc ]; then" in content, \
            ".bashrc is missing the /etc/bashrc sourcing if block"
        assert ". /etc/bashrc" in content or "source /etc/bashrc" in content, \
            ".bashrc is missing the sourcing of /etc/bashrc"

    def test_original_alias_ll_preserved(self):
        """Verify that .bashrc still contains the ll alias."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()

        assert "alias ll='ls -la'" in content, \
            ".bashrc is missing the 'alias ll='ls -la'' definition - original content was clobbered"

    def test_original_alias_grep_preserved(self):
        """Verify that .bashrc still contains the grep alias."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()

        assert "alias grep='grep --color=auto'" in content, \
            ".bashrc is missing the 'alias grep='grep --color=auto'' definition - original content was clobbered"

    def test_original_ps1_preserved(self):
        """Verify that .bashrc still contains the PS1 setting."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()

        assert "PS1='\\u@\\h:\\w\\$ '" in content, \
            ".bashrc is missing the PS1 prompt definition - original content was clobbered"

    def test_grep_finds_all_required_original_lines(self):
        """Verify that grep can find all three required original lines (anti-clobber check)."""
        result = subprocess.run(
            ['grep', '-E', "^alias ll=|^alias grep=|^PS1=", BASHRC_PATH],
            capture_output=True,
            text=True
        )

        lines = [l for l in result.stdout.strip().split('\n') if l]

        found_ll = any("alias ll=" in line for line in lines)
        found_grep = any("alias grep=" in line for line in lines)
        found_ps1 = any("PS1=" in line for line in lines)

        assert found_ll, \
            "Could not find 'alias ll=' line in .bashrc - original content was clobbered"
        assert found_grep, \
            "Could not find 'alias grep=' line in .bashrc - original content was clobbered"
        assert found_ps1, \
            "Could not find 'PS1=' line in .bashrc - original content was clobbered"

        # All three should be present
        assert len([l for l in [found_ll, found_grep, found_ps1] if l]) == 3, \
            "Not all three original lines (alias ll, alias grep, PS1) are preserved in .bashrc"

    def test_aliases_functional_in_new_shell(self):
        """Verify that the aliases are still functional in a new shell."""
        # Test that 'll' alias is defined
        result = subprocess.run(
            ['bash', '-i', '-c', 'alias ll'],
            capture_output=True,
            text=True,
            cwd='/home/user',
            env={'HOME': '/home/user', 'USER': 'user'}
        )

        assert result.returncode == 0, \
            f"'ll' alias is not defined in new shell. Error: {result.stderr}"
        assert 'ls -la' in result.stdout or "ls -la" in result.stdout, \
            f"'ll' alias does not expand to 'ls -la'. Got: {result.stdout}"

    def test_bashrc_is_valid_shell_syntax(self):
        """Verify that .bashrc has valid shell syntax."""
        result = subprocess.run(
            ['bash', '-n', BASHRC_PATH],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, \
            f".bashrc has syntax errors: {result.stderr}"
