# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has created the Makefile for gprof profiling.
"""

import os
import subprocess
import pytest


class TestMakefileExists:
    """Validate that the Makefile exists and has required content."""

    def test_makefile_exists(self):
        """Verify /home/user/profiling/Makefile exists."""
        path = "/home/user/profiling/Makefile"
        assert os.path.exists(path), f"Makefile does not exist at {path}"
        assert os.path.isfile(path), f"{path} exists but is not a regular file"

    def test_makefile_has_optimization_and_profiling_flags(self):
        """Verify Makefile contains both -O2 and -pg flags for compilation."""
        path = "/home/user/profiling/Makefile"

        result = subprocess.run(
            ['grep', '-E', r'\-O2.*\-pg|\-pg.*\-O2', path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Makefile does not contain both -O2 and -pg flags in the same line. "
            f"Both flags are required for gprof profiling with optimization."
        )

    def test_makefile_has_clean_target(self):
        """Verify Makefile contains a clean target."""
        path = "/home/user/profiling/Makefile"

        result = subprocess.run(
            ['grep', '-E', r'^clean\s*:', path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Makefile does not contain a 'clean' target. "
            f"Expected a line starting with 'clean:' or 'clean :'"
        )


class TestMakeBuildsBenchmark:
    """Validate that 'make' successfully builds the benchmark binary."""

    def test_make_succeeds(self):
        """Verify 'make' completes successfully with exit code 0."""
        # First clean up any existing bench binary
        bench_path = "/home/user/profiling/bench"
        if os.path.exists(bench_path):
            os.remove(bench_path)

        result = subprocess.run(
            ['make'],
            cwd='/home/user/profiling',
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"'make' failed with exit code {result.returncode}. "
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_bench_binary_exists_after_make(self):
        """Verify bench binary exists after running make."""
        # Run make first to ensure binary is built
        subprocess.run(
            ['make'],
            cwd='/home/user/profiling',
            capture_output=True
        )

        bench_path = "/home/user/profiling/bench"
        assert os.path.exists(bench_path), (
            f"After running 'make', the bench binary does not exist at {bench_path}"
        )

    def test_bench_binary_is_executable(self):
        """Verify bench binary is executable after running make."""
        # Run make first to ensure binary is built
        subprocess.run(
            ['make'],
            cwd='/home/user/profiling',
            capture_output=True
        )

        bench_path = "/home/user/profiling/bench"
        assert os.path.exists(bench_path), f"bench binary does not exist at {bench_path}"
        assert os.access(bench_path, os.X_OK), (
            f"bench binary at {bench_path} is not executable"
        )

    def test_bench_binary_runs_without_crash(self):
        """Verify bench binary runs without immediate crash."""
        # Run make first to ensure binary is built
        subprocess.run(
            ['make'],
            cwd='/home/user/profiling',
            capture_output=True
        )

        bench_path = "/home/user/profiling/bench"
        assert os.path.exists(bench_path), f"bench binary does not exist at {bench_path}"

        # Run the binary - it should complete without crashing
        # Use timeout to prevent hanging on infinite loops
        result = subprocess.run(
            [bench_path],
            cwd='/home/user/profiling',
            capture_output=True,
            text=True,
            timeout=30
        )
        # Exit code 0 indicates successful execution
        assert result.returncode == 0, (
            f"bench binary crashed or failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )


class TestMakeClean:
    """Validate that 'make clean' removes the bench binary."""

    def test_make_clean_succeeds(self):
        """Verify 'make clean' completes successfully with exit code 0."""
        # First ensure bench exists by running make
        subprocess.run(
            ['make'],
            cwd='/home/user/profiling',
            capture_output=True
        )

        result = subprocess.run(
            ['make', 'clean'],
            cwd='/home/user/profiling',
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"'make clean' failed with exit code {result.returncode}. "
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_bench_removed_after_make_clean(self):
        """Verify bench binary does not exist after 'make clean'."""
        # First ensure bench exists by running make
        subprocess.run(
            ['make'],
            cwd='/home/user/profiling',
            capture_output=True
        )

        bench_path = "/home/user/profiling/bench"
        assert os.path.exists(bench_path), (
            "bench binary should exist after 'make' but before 'make clean'"
        )

        # Now run make clean
        subprocess.run(
            ['make', 'clean'],
            cwd='/home/user/profiling',
            capture_output=True
        )

        assert not os.path.exists(bench_path), (
            f"After running 'make clean', the bench binary still exists at {bench_path}. "
            f"The clean target should remove it."
        )


class TestSourceFileInvariant:
    """Validate that the source file remains unchanged."""

    def test_bench_c_still_exists(self):
        """Verify /home/user/profiling/bench.c still exists."""
        path = "/home/user/profiling/bench.c"
        assert os.path.exists(path), (
            f"Source file {path} no longer exists. "
            f"It should not have been modified or deleted."
        )

    def test_bench_c_is_valid_c_program(self):
        """Verify /home/user/profiling/bench.c is still a valid C program."""
        source_path = "/home/user/profiling/bench.c"

        with open(source_path, 'r') as f:
            content = f.read()

        assert len(content.strip()) > 0, f"{source_path} is empty"
        assert 'main' in content, f"{source_path} does not contain a main function"

        # Verify it still compiles
        result = subprocess.run(
            ['gcc', '-fsyntax-only', source_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"{source_path} is no longer a valid C program. "
            f"gcc syntax check failed with: {result.stderr}"
        )
