# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task
of adding TZ=UTC to their .bashrc file.
"""

import os
import subprocess
import pytest


BASHRC_PATH = "/home/user/.bashrc"

EXPECTED_INITIAL_CONTENT = """# ~/.bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific aliases
alias ll='ls -la'
alias grep='grep --color=auto'

# Custom prompt
PS1='\\u@\\h:\\w\\$ '"""


class TestInitialState:
    """Tests to verify the initial state before the task is performed."""

    def test_bashrc_exists(self):
        """Verify that /home/user/.bashrc exists."""
        assert os.path.exists(BASHRC_PATH), f"{BASHRC_PATH} does not exist"

    def test_bashrc_is_file(self):
        """Verify that /home/user/.bashrc is a regular file."""
        assert os.path.isfile(BASHRC_PATH), f"{BASHRC_PATH} is not a regular file"

    def test_bashrc_is_writable(self):
        """Verify that /home/user/.bashrc is writable."""
        assert os.access(BASHRC_PATH, os.W_OK), f"{BASHRC_PATH} is not writable"

    def test_bashrc_contains_source_global_definitions(self):
        """Verify that .bashrc contains the source global definitions block."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()
        assert "# Source global definitions" in content, \
            ".bashrc is missing '# Source global definitions' comment"
        assert "if [ -f /etc/bashrc ]; then" in content, \
            ".bashrc is missing the /etc/bashrc sourcing if block"
        assert ". /etc/bashrc" in content, \
            ".bashrc is missing the '. /etc/bashrc' line"

    def test_bashrc_contains_alias_ll(self):
        """Verify that .bashrc contains the ll alias."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()
        assert "alias ll='ls -la'" in content, \
            ".bashrc is missing the 'alias ll='ls -la'' definition"

    def test_bashrc_contains_alias_grep(self):
        """Verify that .bashrc contains the grep alias."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()
        assert "alias grep='grep --color=auto'" in content, \
            ".bashrc is missing the 'alias grep='grep --color=auto'' definition"

    def test_bashrc_contains_ps1(self):
        """Verify that .bashrc contains the PS1 setting."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()
        assert "PS1='\\u@\\h:\\w\\$ '" in content, \
            ".bashrc is missing the PS1 prompt definition"

    def test_tz_not_set_in_bashrc(self):
        """Verify that TZ is NOT currently set/exported in .bashrc."""
        with open(BASHRC_PATH, 'r') as f:
            content = f.read()

        # Check for various forms of TZ export that should NOT be present
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            # Skip comments
            if stripped.startswith('#'):
                continue
            # Check for export TZ= or TZ= patterns
            assert not stripped.startswith('export TZ='), \
                f"TZ is already exported in .bashrc: '{line}'"
            assert not (stripped.startswith('TZ=') and 'export' in stripped), \
                f"TZ is already set and exported in .bashrc: '{line}'"
            # Also check for standalone TZ= followed by export TZ
            if stripped.startswith('TZ=') and not stripped.startswith('TZ=$'):
                # This could be a simple assignment, which is fine if not exported
                # But we should flag it as unexpected initial state
                assert 'export TZ' not in content, \
                    f"TZ appears to be set in .bashrc: '{line}'"

    def test_bash_is_available(self):
        """Verify that bash is available on the system."""
        result = subprocess.run(['which', 'bash'], capture_output=True, text=True)
        assert result.returncode == 0, "bash is not available on this system"
        assert result.stdout.strip(), "bash path is empty"

    def test_home_user_directory_exists(self):
        """Verify that /home/user directory exists."""
        assert os.path.isdir("/home/user"), "/home/user directory does not exist"

    def test_grep_finds_required_lines(self):
        """Verify that grep can find the required alias and PS1 lines."""
        result = subprocess.run(
            ['grep', '-E', "^alias ll=|^alias grep=|^PS1=", BASHRC_PATH],
            capture_output=True,
            text=True
        )
        lines = [l for l in result.stdout.strip().split('\n') if l]

        # Should find all three lines
        found_ll = any("alias ll=" in line for line in lines)
        found_grep = any("alias grep=" in line for line in lines)
        found_ps1 = any("PS1=" in line for line in lines)

        assert found_ll, "Could not find 'alias ll=' line in .bashrc"
        assert found_grep, "Could not find 'alias grep=' line in .bashrc"
        assert found_ps1, "Could not find 'PS1=' line in .bashrc"
