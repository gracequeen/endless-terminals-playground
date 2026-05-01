# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
creates the Makefile for gprof profiling.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the student performs the task."""

    def test_profiling_directory_exists(self):
        """Verify /home/user/profiling/ directory exists."""
        path = "/home/user/profiling"
        assert os.path.exists(path), f"Directory {path} does not exist"
        assert os.path.isdir(path), f"{path} exists but is not a directory"

    def test_profiling_directory_is_writable(self):
        """Verify /home/user/profiling/ directory is writable."""
        path = "/home/user/profiling"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_bench_c_exists(self):
        """Verify /home/user/profiling/bench.c exists."""
        path = "/home/user/profiling/bench.c"
        assert os.path.exists(path), f"Source file {path} does not exist"
        assert os.path.isfile(path), f"{path} exists but is not a regular file"

    def test_bench_c_is_readable(self):
        """Verify /home/user/profiling/bench.c is readable."""
        path = "/home/user/profiling/bench.c"
        assert os.access(path, os.R_OK), f"Source file {path} is not readable"

    def test_bench_c_is_valid_c_program(self):
        """Verify /home/user/profiling/bench.c contains valid C code that compiles."""
        source_path = "/home/user/profiling/bench.c"

        # Read the file to check it has content
        with open(source_path, 'r') as f:
            content = f.read()

        assert len(content.strip()) > 0, f"{source_path} is empty"
        assert 'main' in content, f"{source_path} does not appear to contain a main function"

        # Try to compile it with gcc to verify it's valid C
        result = subprocess.run(
            ['gcc', '-fsyntax-only', source_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"{source_path} is not a valid C program. "
            f"gcc syntax check failed with: {result.stderr}"
        )

    def test_gcc_is_installed(self):
        """Verify gcc is installed and available in PATH."""
        result = subprocess.run(
            ['which', 'gcc'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gcc is not installed or not available in PATH"

        # Also verify gcc actually works
        result = subprocess.run(
            ['gcc', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gcc is in PATH but fails to run --version"

    def test_no_makefile_exists(self):
        """Verify no Makefile currently exists in /home/user/profiling/."""
        makefile_path = "/home/user/profiling/Makefile"
        assert not os.path.exists(makefile_path), (
            f"Makefile already exists at {makefile_path}. "
            "It should not exist in the initial state."
        )

        # Also check for lowercase 'makefile' variant
        makefile_lower_path = "/home/user/profiling/makefile"
        assert not os.path.exists(makefile_lower_path), (
            f"makefile already exists at {makefile_lower_path}. "
            "It should not exist in the initial state."
        )

    def test_make_is_installed(self):
        """Verify make is installed (needed to use the Makefile later)."""
        result = subprocess.run(
            ['which', 'make'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "make is not installed or not available in PATH"
