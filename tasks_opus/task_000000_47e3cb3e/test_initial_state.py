# test_initial_state.py
"""
Tests to validate the initial state of the operating system before the student
performs the disk I/O benchmark task.
"""

import pytest
import os
from pathlib import Path


HOME_DIR = "/home/user"
ARTIFACT_STORAGE_DIR = "/home/user/artifact_storage"
BENCHMARK_FILE = "/home/user/artifact_storage/benchmark_test.dat"
BENCHMARK_LOG = "/home/user/artifact_storage/benchmark_results.log"


class TestInitialState:
    """Test the initial state before the benchmark task is performed."""

    def test_home_directory_exists(self):
        """Verify that the home directory /home/user exists."""
        assert os.path.isdir(HOME_DIR), (
            f"Home directory {HOME_DIR} does not exist. "
            "The user's home directory must be present."
        )

    def test_artifact_storage_directory_does_not_exist(self):
        """
        Verify that /home/user/artifact_storage does NOT exist initially.
        The task requires the student to create this directory.
        """
        assert not os.path.exists(ARTIFACT_STORAGE_DIR), (
            f"Directory {ARTIFACT_STORAGE_DIR} already exists but should not. "
            "The task requires the student to create this directory if it doesn't exist."
        )

    def test_benchmark_test_file_does_not_exist(self):
        """
        Verify that the benchmark test file does NOT exist initially.
        This is an output file that should be created by the student.
        """
        assert not os.path.exists(BENCHMARK_FILE), (
            f"File {BENCHMARK_FILE} already exists but should not. "
            "This output file should be created by the student during the benchmark."
        )

    def test_benchmark_log_file_does_not_exist(self):
        """
        Verify that the benchmark results log does NOT exist initially.
        This is an output file that should be created by the student.
        """
        assert not os.path.exists(BENCHMARK_LOG), (
            f"File {BENCHMARK_LOG} already exists but should not. "
            "This output file should be created by the student after the benchmark."
        )

    def test_dev_zero_exists(self):
        """
        Verify that /dev/zero exists and is accessible.
        This is required as the source for the dd command.
        """
        assert os.path.exists("/dev/zero"), (
            "/dev/zero does not exist. "
            "This special file is required as the source for the dd benchmark command."
        )

    def test_dd_command_available(self):
        """
        Verify that the dd command is available on the system.
        """
        import shutil
        dd_path = shutil.which("dd")
        assert dd_path is not None, (
            "The 'dd' command is not available on this system. "
            "The dd command is required to perform the disk write benchmark."
        )

    def test_home_directory_is_writable(self):
        """
        Verify that the home directory is writable so the student can create
        the artifact_storage directory.
        """
        assert os.access(HOME_DIR, os.W_OK), (
            f"Home directory {HOME_DIR} is not writable. "
            "The student needs write permission to create the artifact_storage directory."
        )