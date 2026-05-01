# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the distributed feature-extraction debugging task.
"""

import os
import subprocess
import sys
import pytest


# Base paths
HOME = "/home/user"
PIPELINE_DIR = os.path.join(HOME, "pipeline")
DATA_DIR = os.path.join(HOME, "data")


class TestPipelineDirectoryStructure:
    """Test that the pipeline directory and required files exist."""

    def test_pipeline_directory_exists(self):
        """Pipeline directory must exist."""
        assert os.path.isdir(PIPELINE_DIR), (
            f"Pipeline directory {PIPELINE_DIR} does not exist. "
            "The task requires /home/user/pipeline/ with coordinator and worker scripts."
        )

    def test_coordinator_py_exists(self):
        """coordinator.py must exist in pipeline directory."""
        coordinator_path = os.path.join(PIPELINE_DIR, "coordinator.py")
        assert os.path.isfile(coordinator_path), (
            f"coordinator.py not found at {coordinator_path}. "
            "The coordinator script is required for the distributed pipeline."
        )

    def test_worker_py_exists(self):
        """worker.py must exist in pipeline directory."""
        worker_path = os.path.join(PIPELINE_DIR, "worker.py")
        assert os.path.isfile(worker_path), (
            f"worker.py not found at {worker_path}. "
            "The worker script is required for the distributed pipeline."
        )

    def test_run_sh_exists(self):
        """run.sh must exist in pipeline directory."""
        run_sh_path = os.path.join(PIPELINE_DIR, "run.sh")
        assert os.path.isfile(run_sh_path), (
            f"run.sh not found at {run_sh_path}. "
            "The run script is required to start the distributed pipeline."
        )

    def test_single_py_exists(self):
        """single.py must exist in pipeline directory."""
        single_path = os.path.join(PIPELINE_DIR, "single.py")
        assert os.path.isfile(single_path), (
            f"single.py not found at {single_path}. "
            "The single-threaded reference implementation is required."
        )

    def test_run_sh_is_executable_or_readable(self):
        """run.sh should be readable (and ideally executable)."""
        run_sh_path = os.path.join(PIPELINE_DIR, "run.sh")
        assert os.access(run_sh_path, os.R_OK), (
            f"run.sh at {run_sh_path} is not readable."
        )


class TestDataDirectory:
    """Test that the data directory and input file exist."""

    def test_data_directory_exists(self):
        """Data directory must exist."""
        assert os.path.isdir(DATA_DIR), (
            f"Data directory {DATA_DIR} does not exist. "
            "The task requires /home/user/data/ with raw.parquet."
        )

    def test_raw_parquet_exists(self):
        """raw.parquet must exist in data directory."""
        raw_parquet_path = os.path.join(DATA_DIR, "raw.parquet")
        assert os.path.isfile(raw_parquet_path), (
            f"raw.parquet not found at {raw_parquet_path}. "
            "The input data file is required for the feature extraction task."
        )

    def test_raw_parquet_has_correct_row_count(self):
        """raw.parquet should have 50,000 rows."""
        raw_parquet_path = os.path.join(DATA_DIR, "raw.parquet")
        try:
            import pandas as pd
            df = pd.read_parquet(raw_parquet_path)
            assert len(df) == 50000, (
                f"raw.parquet has {len(df)} rows, expected 50,000 rows. "
                "The input data must have exactly 50k rows for this task."
            )
        except ImportError:
            pytest.skip("pandas not available to verify row count")

    def test_raw_parquet_has_text_column(self):
        """raw.parquet should have a 'text' column."""
        raw_parquet_path = os.path.join(DATA_DIR, "raw.parquet")
        try:
            import pandas as pd
            df = pd.read_parquet(raw_parquet_path)
            assert "text" in df.columns, (
                f"raw.parquet does not have a 'text' column. "
                f"Found columns: {list(df.columns)}. "
                "The input data must have a 'text' column for tf-idf extraction."
            )
        except ImportError:
            pytest.skip("pandas not available to verify columns")


class TestDirectoryPermissions:
    """Test that required directories are writable."""

    def test_pipeline_directory_writable(self):
        """Pipeline directory must be writable."""
        assert os.access(PIPELINE_DIR, os.W_OK), (
            f"Pipeline directory {PIPELINE_DIR} is not writable. "
            "The student may need to modify files in this directory."
        )

    def test_data_directory_writable(self):
        """Data directory must be writable."""
        assert os.access(DATA_DIR, os.W_OK), (
            f"Data directory {DATA_DIR} is not writable. "
            "The pipeline needs to write features.parquet to this directory."
        )


class TestPythonEnvironment:
    """Test that required Python packages are installed."""

    def test_python_version(self):
        """Python 3.11+ should be available."""
        assert sys.version_info >= (3, 11), (
            f"Python version is {sys.version_info.major}.{sys.version_info.minor}, "
            "but Python 3.11+ is required for this task."
        )

    def test_pyzmq_installed(self):
        """pyzmq must be installed."""
        try:
            import zmq
            assert zmq is not None
        except ImportError:
            pytest.fail(
                "pyzmq is not installed. "
                "The distributed pipeline requires ZeroMQ for communication."
            )

    def test_pandas_installed(self):
        """pandas must be installed."""
        try:
            import pandas
            assert pandas is not None
        except ImportError:
            pytest.fail(
                "pandas is not installed. "
                "The pipeline requires pandas for data handling."
            )

    def test_sklearn_installed(self):
        """scikit-learn must be installed."""
        try:
            import sklearn
            assert sklearn is not None
        except ImportError:
            pytest.fail(
                "scikit-learn is not installed. "
                "The pipeline requires scikit-learn for tf-idf computation."
            )

    def test_pyarrow_or_fastparquet_installed(self):
        """A parquet engine (pyarrow or fastparquet) must be installed."""
        try:
            import pyarrow
            return
        except ImportError:
            pass

        try:
            import fastparquet
            return
        except ImportError:
            pass

        pytest.fail(
            "Neither pyarrow nor fastparquet is installed. "
            "A parquet engine is required to read/write .parquet files."
        )


class TestCoordinatorScript:
    """Test that coordinator.py has expected structure."""

    def test_coordinator_uses_zmq(self):
        """coordinator.py should import/use zmq."""
        coordinator_path = os.path.join(PIPELINE_DIR, "coordinator.py")
        with open(coordinator_path, 'r') as f:
            content = f.read()
        assert 'zmq' in content, (
            "coordinator.py does not appear to use ZeroMQ. "
            "The distributed pipeline must use ZeroMQ for communication."
        )

    def test_coordinator_uses_expected_ports(self):
        """coordinator.py should use ports 5557 and 5558."""
        coordinator_path = os.path.join(PIPELINE_DIR, "coordinator.py")
        with open(coordinator_path, 'r') as f:
            content = f.read()
        assert '5557' in content, (
            "coordinator.py does not reference port 5557. "
            "Expected PUSH socket on tcp://127.0.0.1:5557."
        )
        assert '5558' in content, (
            "coordinator.py does not reference port 5558. "
            "Expected PULL socket on tcp://127.0.0.1:5558."
        )


class TestWorkerScript:
    """Test that worker.py has expected structure."""

    def test_worker_uses_zmq(self):
        """worker.py should import/use zmq."""
        worker_path = os.path.join(PIPELINE_DIR, "worker.py")
        with open(worker_path, 'r') as f:
            content = f.read()
        assert 'zmq' in content, (
            "worker.py does not appear to use ZeroMQ. "
            "The distributed pipeline must use ZeroMQ for communication."
        )

    def test_worker_uses_tfidf(self):
        """worker.py should use TfidfVectorizer."""
        worker_path = os.path.join(PIPELINE_DIR, "worker.py")
        with open(worker_path, 'r') as f:
            content = f.read()
        assert 'tfidf' in content.lower() or 'TfidfVectorizer' in content, (
            "worker.py does not appear to use tf-idf. "
            "Workers should compute tf-idf vectors."
        )


class TestRunScript:
    """Test that run.sh has expected structure."""

    def test_run_sh_starts_workers(self):
        """run.sh should start multiple workers."""
        run_sh_path = os.path.join(PIPELINE_DIR, "run.sh")
        with open(run_sh_path, 'r') as f:
            content = f.read()
        # Should reference worker.py multiple times or use a loop
        assert 'worker' in content.lower(), (
            "run.sh does not appear to start workers. "
            "The script should start 3 worker processes."
        )

    def test_run_sh_starts_coordinator(self):
        """run.sh should start the coordinator."""
        run_sh_path = os.path.join(PIPELINE_DIR, "run.sh")
        with open(run_sh_path, 'r') as f:
            content = f.read()
        assert 'coordinator' in content.lower(), (
            "run.sh does not appear to start the coordinator. "
            "The script should start the coordinator process."
        )


class TestSingleScript:
    """Test that single.py exists and has expected structure."""

    def test_single_uses_tfidf(self):
        """single.py should use TfidfVectorizer."""
        single_path = os.path.join(PIPELINE_DIR, "single.py")
        with open(single_path, 'r') as f:
            content = f.read()
        assert 'tfidf' in content.lower() or 'TfidfVectorizer' in content, (
            "single.py does not appear to use tf-idf. "
            "The reference implementation should compute tf-idf vectors."
        )

    def test_single_does_not_use_zmq(self):
        """single.py should not use ZeroMQ (it's single-threaded)."""
        single_path = os.path.join(PIPELINE_DIR, "single.py")
        with open(single_path, 'r') as f:
            content = f.read()
        # It's okay if zmq is mentioned in comments, but shouldn't be imported
        lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
        code_content = '\n'.join(lines)
        assert 'import zmq' not in code_content, (
            "single.py appears to import ZeroMQ. "
            "The single-threaded reference should not use distributed communication."
        )


class TestNoOutputFilesYet:
    """Verify that output files don't exist yet (clean initial state)."""

    def test_features_parquet_does_not_exist(self):
        """features.parquet should not exist before running the pipeline."""
        features_path = os.path.join(DATA_DIR, "features.parquet")
        # This is a soft check - it's okay if it exists from a previous run
        # but we note it for awareness
        if os.path.exists(features_path):
            pytest.skip(
                f"features.parquet already exists at {features_path}. "
                "This may be from a previous run. Consider cleaning up for a fresh test."
            )
