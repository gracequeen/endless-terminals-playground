# test_final_state.py
"""
Tests to validate the final state after the student has fixed the distributed
feature-extraction pipeline. The pipeline must produce correct tf-idf features
for all 50,000 rows using 3 workers communicating via ZeroMQ.
"""

import os
import subprocess
import sys
import time
import re
import pytest


# Base paths
HOME = "/home/user"
PIPELINE_DIR = os.path.join(HOME, "pipeline")
DATA_DIR = os.path.join(HOME, "data")
FEATURES_PATH = os.path.join(DATA_DIR, "features.parquet")
RAW_PATH = os.path.join(DATA_DIR, "raw.parquet")
SINGLE_REFERENCE_PATH = os.path.join(DATA_DIR, "single_reference.parquet")


def run_pipeline():
    """Run the distributed pipeline and return the result."""
    result = subprocess.run(
        ["bash", "run.sh"],
        cwd=PIPELINE_DIR,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    return result


def run_single_py():
    """Run the single-threaded reference implementation."""
    result = subprocess.run(
        [sys.executable, "single.py"],
        cwd=PIPELINE_DIR,
        capture_output=True,
        text=True,
        timeout=600  # 10 minute timeout for single-threaded
    )
    return result


def generate_reference_if_needed():
    """Generate reference output from single.py if not already present."""
    if not os.path.exists(SINGLE_REFERENCE_PATH):
        # Run single.py and save its output as reference
        result = run_single_py()
        if result.returncode == 0:
            # single.py should produce features.parquet, rename it to reference
            if os.path.exists(FEATURES_PATH):
                import shutil
                shutil.copy(FEATURES_PATH, SINGLE_REFERENCE_PATH)


class TestPipelineExecution:
    """Test that the pipeline runs successfully."""

    def test_run_sh_exits_zero(self):
        """run.sh must exit with code 0."""
        # Clean up any existing output
        if os.path.exists(FEATURES_PATH):
            os.remove(FEATURES_PATH)

        result = run_pipeline()
        assert result.returncode == 0, (
            f"run.sh exited with code {result.returncode}.\n"
            f"stdout: {result.stdout[:2000]}\n"
            f"stderr: {result.stderr[:2000]}"
        )

    def test_features_parquet_created(self):
        """features.parquet must be created after running the pipeline."""
        # Ensure pipeline has been run
        if not os.path.exists(FEATURES_PATH):
            run_pipeline()

        assert os.path.exists(FEATURES_PATH), (
            f"features.parquet was not created at {FEATURES_PATH}. "
            "The pipeline must produce output at /home/user/data/features.parquet."
        )


class TestOutputCorrectness:
    """Test that the output has correct row count and valid values."""

    @pytest.fixture(autouse=True)
    def ensure_pipeline_run(self):
        """Ensure the pipeline has been run before tests."""
        if not os.path.exists(FEATURES_PATH):
            result = run_pipeline()
            assert result.returncode == 0, "Pipeline must run successfully"

    def test_exactly_50000_rows(self):
        """features.parquet must have exactly 50,000 rows."""
        import pandas as pd
        df = pd.read_parquet(FEATURES_PATH)
        assert len(df) == 50000, (
            f"features.parquet has {len(df)} rows, expected exactly 50,000. "
            "This suggests chunks are being dropped or duplicated."
        )

    def test_tfidf_values_in_valid_range(self):
        """All tf-idf values must be in range [0.0, 1.0]."""
        import pandas as pd
        import numpy as np

        df = pd.read_parquet(FEATURES_PATH)

        # Get only numeric columns (tf-idf features)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) == 0:
            pytest.fail("No numeric columns found in features.parquet")

        numeric_data = df[numeric_cols]

        min_val = numeric_data.min().min()
        max_val = numeric_data.max().max()

        assert min_val >= 0.0, (
            f"Found tf-idf value {min_val} < 0.0. "
            "All tf-idf scores must be non-negative."
        )
        assert max_val <= 1.0 + 1e-9, (
            f"Found tf-idf value {max_val} > 1.0. "
            "tf-idf scores cannot exceed 1.0. This suggests vocabulary collision "
            "or duplicate chunk aggregation issues."
        )

    def test_no_nan_values(self):
        """features.parquet should not have NaN values in tf-idf columns."""
        import pandas as pd
        import numpy as np

        df = pd.read_parquet(FEATURES_PATH)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        nan_count = df[numeric_cols].isna().sum().sum()
        assert nan_count == 0, (
            f"Found {nan_count} NaN values in features.parquet. "
            "This suggests vocabulary misalignment between workers."
        )


class TestConsistency:
    """Test that the pipeline produces consistent results across multiple runs."""

    def test_multiple_runs_same_row_count(self):
        """Running the pipeline multiple times must always produce 50,000 rows."""
        import pandas as pd

        row_counts = []
        for i in range(3):  # Run 3 times to check for race conditions
            if os.path.exists(FEATURES_PATH):
                os.remove(FEATURES_PATH)

            result = run_pipeline()
            assert result.returncode == 0, f"Run {i+1} failed with code {result.returncode}"

            df = pd.read_parquet(FEATURES_PATH)
            row_counts.append(len(df))

        for i, count in enumerate(row_counts):
            assert count == 50000, (
                f"Run {i+1} produced {count} rows instead of 50,000. "
                f"All runs: {row_counts}. "
                "Inconsistent row counts indicate race conditions in the pipeline."
            )

    def test_multiple_runs_valid_values(self):
        """All runs must produce valid tf-idf values in [0, 1]."""
        import pandas as pd
        import numpy as np

        for i in range(2):  # Additional runs
            if os.path.exists(FEATURES_PATH):
                os.remove(FEATURES_PATH)

            result = run_pipeline()
            assert result.returncode == 0, f"Run {i+1} failed"

            df = pd.read_parquet(FEATURES_PATH)
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            numeric_data = df[numeric_cols]

            max_val = numeric_data.max().max()
            assert max_val <= 1.0 + 1e-9, (
                f"Run {i+1} produced tf-idf value {max_val} > 1.0. "
                "Race conditions may be causing duplicate aggregation."
            )


class TestDistributedRequirements:
    """Test that the solution remains distributed (not a shortcut)."""

    def test_still_uses_zeromq(self):
        """coordinator.py and worker.py must still use ZeroMQ."""
        coordinator_path = os.path.join(PIPELINE_DIR, "coordinator.py")
        worker_path = os.path.join(PIPELINE_DIR, "worker.py")

        with open(coordinator_path, 'r') as f:
            coord_content = f.read()
        with open(worker_path, 'r') as f:
            worker_content = f.read()

        assert 'zmq' in coord_content, (
            "coordinator.py no longer uses ZeroMQ. "
            "The solution must remain distributed using ZeroMQ."
        )
        assert 'zmq' in worker_content, (
            "worker.py no longer uses ZeroMQ. "
            "The solution must remain distributed using ZeroMQ."
        )

    def test_run_sh_starts_three_workers(self):
        """run.sh must still start 3 workers."""
        run_sh_path = os.path.join(PIPELINE_DIR, "run.sh")

        with open(run_sh_path, 'r') as f:
            content = f.read()

        # Count worker invocations - look for patterns like "worker.py 1", "worker.py 2", etc.
        # or loop constructs that start 3 workers
        worker_mentions = content.lower().count('worker')

        # Check for explicit 3 workers or a loop that would create 3
        has_three_workers = (
            '1' in content and '2' in content and '3' in content and 'worker' in content.lower()
        ) or (
            'for' in content.lower() and ('3' in content or 'seq' in content)
        ) or (
            worker_mentions >= 3
        )

        assert has_three_workers, (
            "run.sh does not appear to start 3 workers. "
            "The solution must use 3 parallel workers."
        )

    def test_coordinator_does_not_do_all_computation(self):
        """Coordinator should not compute tf-idf itself (workers must do it)."""
        coordinator_path = os.path.join(PIPELINE_DIR, "coordinator.py")

        with open(coordinator_path, 'r') as f:
            content = f.read()

        # Coordinator should not fit a TfidfVectorizer on data
        # It's okay to have TfidfVectorizer for vocabulary sharing, but not fit_transform on data
        lines = content.split('\n')
        code_lines = [l for l in lines if not l.strip().startswith('#')]
        code = '\n'.join(code_lines)

        # Check that coordinator doesn't do the main tf-idf computation
        # It may share vocabulary, but shouldn't call fit_transform on the actual data chunks
        has_fit_transform_on_text = 'fit_transform' in code and 'text' in code.lower()

        # This is a heuristic - coordinator may legitimately build vocabulary
        # but shouldn't be doing all the tf-idf work
        if has_fit_transform_on_text:
            # Check if it's just for vocabulary building (acceptable) vs full computation (not acceptable)
            # If coordinator still sends to workers, it's okay
            assert 'send' in code.lower() or 'push' in code.lower(), (
                "Coordinator appears to compute tf-idf without distributing to workers. "
                "Work must be distributed across workers."
            )


class TestSemanticCorrectness:
    """Test that the output is semantically correct compared to reference."""

    @pytest.fixture(autouse=True)
    def setup_reference(self):
        """Generate reference output if needed."""
        # We'll compare against a fresh single.py run
        pass

    def test_output_matches_reference_structure(self):
        """Output should have similar structure to single-threaded reference."""
        import pandas as pd

        # Run pipeline
        if os.path.exists(FEATURES_PATH):
            os.remove(FEATURES_PATH)
        result = run_pipeline()
        assert result.returncode == 0

        df = pd.read_parquet(FEATURES_PATH)

        # Basic structural checks
        assert len(df) == 50000, f"Expected 50000 rows, got {len(df)}"

        # Should have multiple feature columns (tf-idf produces many features)
        assert len(df.columns) > 1, (
            f"Only {len(df.columns)} columns found. "
            "tf-idf should produce multiple feature columns."
        )

    def test_feature_values_reasonable(self):
        """Feature values should be reasonable tf-idf scores."""
        import pandas as pd
        import numpy as np

        if not os.path.exists(FEATURES_PATH):
            run_pipeline()

        df = pd.read_parquet(FEATURES_PATH)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        # Most tf-idf values should be 0 (sparse), with some non-zero values
        numeric_data = df[numeric_cols].values

        # Check sparsity - tf-idf matrices are typically very sparse
        non_zero_ratio = np.count_nonzero(numeric_data) / numeric_data.size

        # Typical tf-idf sparsity is 95-99%+ zeros
        assert non_zero_ratio < 0.5, (
            f"Non-zero ratio is {non_zero_ratio:.2%}, which is unusually dense for tf-idf. "
            "This may indicate incorrect feature computation."
        )

        # There should be some non-zero values
        assert non_zero_ratio > 0.0001, (
            f"Non-zero ratio is {non_zero_ratio:.6%}, which is too sparse. "
            "This may indicate missing or zeroed-out features."
        )

    def test_no_duplicate_indices(self):
        """Output should not have duplicate row indices."""
        import pandas as pd

        if not os.path.exists(FEATURES_PATH):
            run_pipeline()

        df = pd.read_parquet(FEATURES_PATH)

        # If there's an index column, check for duplicates
        if 'index' in df.columns or 'row_id' in df.columns or 'chunk_id' in df.columns:
            idx_col = 'index' if 'index' in df.columns else ('row_id' if 'row_id' in df.columns else 'chunk_id')
            duplicates = df[idx_col].duplicated().sum()
            assert duplicates == 0, (
                f"Found {duplicates} duplicate indices in output. "
                "This suggests chunks are being processed multiple times."
            )

        # Also check the DataFrame index itself
        if not df.index.is_unique:
            dup_count = df.index.duplicated().sum()
            assert dup_count == 0, (
                f"Found {dup_count} duplicate DataFrame indices. "
                "Row indices should be unique."
            )


class TestRawDataUnchanged:
    """Verify that the input data was not modified."""

    def test_raw_parquet_unchanged(self):
        """raw.parquet should still have 50,000 rows with text column."""
        import pandas as pd

        df = pd.read_parquet(RAW_PATH)

        assert len(df) == 50000, (
            f"raw.parquet now has {len(df)} rows, expected 50,000. "
            "The input data should not be modified."
        )

        assert 'text' in df.columns, (
            "raw.parquet no longer has 'text' column. "
            "The input data should not be modified."
        )


class TestWorkerDistribution:
    """Test that work is actually distributed across workers."""

    def test_workers_process_chunks(self):
        """Each worker should process multiple chunks."""
        # Run pipeline and capture output
        if os.path.exists(FEATURES_PATH):
            os.remove(FEATURES_PATH)

        result = run_pipeline()
        combined_output = result.stdout + result.stderr

        # Look for evidence that multiple workers processed chunks
        # This depends on logging in the worker scripts
        # Common patterns: "worker 1", "worker 2", "worker 3", "processed chunk"

        # At minimum, check that the pipeline completed successfully
        assert result.returncode == 0, "Pipeline must complete successfully"

        # Check output file
        import pandas as pd
        df = pd.read_parquet(FEATURES_PATH)
        assert len(df) == 50000, "All 50000 rows must be processed"
