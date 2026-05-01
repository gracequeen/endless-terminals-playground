# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has created the Makefile for the dataprep project.
"""

import os
import subprocess
import pytest


class TestMakefileExists:
    """Test that the Makefile exists and is valid."""

    def test_makefile_exists(self):
        """Verify /home/user/dataprep/Makefile exists."""
        path = "/home/user/dataprep/Makefile"
        assert os.path.isfile(path), f"Makefile at {path} does not exist"

    def test_makefile_is_readable(self):
        """Verify /home/user/dataprep/Makefile is readable."""
        path = "/home/user/dataprep/Makefile"
        assert os.access(path, os.R_OK), f"Makefile at {path} is not readable"

    def test_makefile_contains_clean_target(self):
        """Verify Makefile contains 'clean' as a target name."""
        path = "/home/user/dataprep/Makefile"
        with open(path, 'r') as f:
            content = f.read()
        # Check for clean: as a target definition
        assert "clean" in content, "Makefile must contain 'clean' target"

    def test_makefile_contains_process_target(self):
        """Verify Makefile contains 'process' as a target name."""
        path = "/home/user/dataprep/Makefile"
        with open(path, 'r') as f:
            content = f.read()
        assert "process" in content, "Makefile must contain 'process' target"

    def test_makefile_contains_all_target(self):
        """Verify Makefile contains 'all' as a target name."""
        path = "/home/user/dataprep/Makefile"
        with open(path, 'r') as f:
            content = f.read()
        assert "all" in content, "Makefile must contain 'all' target"


class TestMakeClean:
    """Test that 'make clean' works correctly."""

    def test_make_clean_exits_successfully(self):
        """Verify 'make clean' exits with code 0."""
        result = subprocess.run(
            ["make", "clean"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, (
            f"'make clean' failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

    def test_make_clean_removes_csv_files(self):
        """Verify 'make clean' removes *.csv files from output/."""
        # First, create a test csv file to ensure clean works
        test_csv = "/home/user/dataprep/output/test_clean.csv"
        with open(test_csv, 'w') as f:
            f.write("test data")

        # Run make clean
        result = subprocess.run(
            ["make", "clean"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, f"'make clean' failed: {result.stderr}"

        # Check that csv file was removed
        assert not os.path.exists(test_csv), (
            f"'make clean' did not remove {test_csv}"
        )

    def test_make_clean_succeeds_with_no_csv_files(self):
        """Verify 'make clean' exits 0 even when no csv files exist (due to -f flag)."""
        # First clean to remove any existing csv files
        subprocess.run(
            ["make", "clean"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )

        # Run clean again - should still succeed
        result = subprocess.run(
            ["make", "clean"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, (
            f"'make clean' should succeed even with no csv files (use rm -f). "
            f"Exit code: {result.returncode}, stderr: {result.stderr}"
        )

    def test_output_directory_still_exists_after_clean(self):
        """Verify output/ directory still exists after clean (only files removed)."""
        subprocess.run(
            ["make", "clean"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )

        path = "/home/user/dataprep/output"
        assert os.path.isdir(path), (
            f"Directory {path} should still exist after 'make clean' - "
            "only csv files should be removed, not the directory"
        )


class TestMakeProcess:
    """Test that 'make process' works correctly."""

    def test_make_process_exits_successfully(self):
        """Verify 'make process' exits with code 0."""
        result = subprocess.run(
            ["make", "process"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, (
            f"'make process' failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

    def test_make_process_runs_convert_script(self):
        """Verify 'make process' runs python3 scripts/convert.py and prints 'converting...'."""
        result = subprocess.run(
            ["make", "process"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, f"'make process' failed: {result.stderr}"

        # The output should contain "converting..." from the script
        combined_output = result.stdout + result.stderr
        assert "converting..." in combined_output, (
            f"'make process' should run convert.py which prints 'converting...'. "
            f"Got output: {combined_output}"
        )


class TestMakeAll:
    """Test that 'make all' works correctly."""

    def test_make_all_exits_successfully(self):
        """Verify 'make all' exits with code 0."""
        result = subprocess.run(
            ["make", "all"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, (
            f"'make all' failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

    def test_make_all_runs_clean_then_process(self):
        """Verify 'make all' runs clean then process in that order."""
        # Use dry-run to check the order of commands
        result = subprocess.run(
            ["make", "-n", "all"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, f"'make -n all' failed: {result.stderr}"

        output = result.stdout

        # Check that rm command (from clean) appears before python3 command (from process)
        rm_pos = output.find("rm")
        python_pos = output.find("python3")

        assert rm_pos != -1, (
            f"'make -n all' output should contain 'rm' command from clean target. "
            f"Got: {output}"
        )
        assert python_pos != -1, (
            f"'make -n all' output should contain 'python3' command from process target. "
            f"Got: {output}"
        )
        assert rm_pos < python_pos, (
            f"'make all' should run clean (rm) before process (python3). "
            f"rm at position {rm_pos}, python3 at position {python_pos}. "
            f"Output: {output}"
        )


class TestDefaultTarget:
    """Test that the default target is 'all'."""

    def test_make_without_target_runs_all(self):
        """Verify 'make' (no target) runs the all target."""
        # Use dry-run to check what would be executed
        result = subprocess.run(
            ["make", "-n"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert result.returncode == 0, f"'make -n' failed: {result.stderr}"

        output = result.stdout

        # Should show both rm (clean) and python3 (process) commands
        assert "rm" in output, (
            f"Default target should run clean (rm command). Got: {output}"
        )
        assert "python3" in output, (
            f"Default target should run process (python3 command). Got: {output}"
        )

    def test_make_default_same_as_make_all(self):
        """Verify 'make' produces same dry-run output as 'make all'."""
        result_default = subprocess.run(
            ["make", "-n"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        result_all = subprocess.run(
            ["make", "-n", "all"],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )

        assert result_default.returncode == 0, f"'make -n' failed: {result_default.stderr}"
        assert result_all.returncode == 0, f"'make -n all' failed: {result_all.stderr}"

        # The outputs should be essentially the same (both run all target)
        # We check that both contain the same key commands
        default_has_rm = "rm" in result_default.stdout
        all_has_rm = "rm" in result_all.stdout
        default_has_python = "python3" in result_default.stdout
        all_has_python = "python3" in result_all.stdout

        assert default_has_rm == all_has_rm, (
            "'make' and 'make all' should produce same output for rm command"
        )
        assert default_has_python == all_has_python, (
            "'make' and 'make all' should produce same output for python3 command"
        )


class TestInvariants:
    """Test that invariants are preserved."""

    def test_convert_script_unchanged(self):
        """Verify /home/user/dataprep/scripts/convert.py still exists and works."""
        path = "/home/user/dataprep/scripts/convert.py"
        assert os.path.isfile(path), f"File {path} should still exist"

        result = subprocess.run(
            ["python3", path],
            capture_output=True,
            text=True,
            cwd="/home/user/dataprep"
        )
        assert "converting..." in result.stdout, (
            f"convert.py should still print 'converting...' but got: {result.stdout}"
        )

    def test_output_directory_exists(self):
        """Verify /home/user/dataprep/output/ directory still exists."""
        path = "/home/user/dataprep/output"
        assert os.path.isdir(path), f"Directory {path} should still exist"
