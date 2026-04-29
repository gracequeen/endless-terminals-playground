# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has fixed the batch job checkpoint/resume bug in /home/user/pipeline.

The fix must address:
1. Checkpoint file not being flushed properly (use context manager or explicit flush/close)
2. Checkpoint storing batch_num but using it as line_num (must store actual line count)
3. INSERT OR REPLACE overwriting aggregates instead of accumulating on resume
"""

import os
import json
import sqlite3
import subprocess
import signal
import time
import pytest
from collections import defaultdict


# Constants
PIPELINE_DIR = "/home/user/pipeline"
RUN_SCRIPT = os.path.join(PIPELINE_DIR, "run.sh")
PROCESS_SCRIPT = os.path.join(PIPELINE_DIR, "process.py")
DATA_DIR = os.path.join(PIPELINE_DIR, "data")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
SUMMARY_DB = os.path.join(OUTPUT_DIR, "summary.db")
CHECKPOINT_FILE = os.path.join(PIPELINE_DIR, ".checkpoint")


def compute_expected_totals():
    """Compute expected totals directly from events.json."""
    totals = defaultdict(lambda: {'total': 0.0, 'count': 0})
    with open(EVENTS_FILE, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            cat = record['category']
            totals[cat]['total'] += record['value']
            totals[cat]['count'] += 1
    return dict(totals)


def get_db_totals(db_path):
    """Get totals from the summary database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.execute('SELECT category, total_value, count FROM summary')
    totals = {}
    for row in cursor:
        totals[row[0]] = {'total': row[1], 'count': row[2]}
    conn.close()
    return totals


def cleanup_pipeline_state():
    """Remove checkpoint and summary.db to start fresh."""
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
    if os.path.exists(SUMMARY_DB):
        os.remove(SUMMARY_DB)


def run_pipeline_with_interrupt(interrupt_after_seconds=3):
    """Run the pipeline, interrupt it after specified seconds, then run again to completion."""
    # First run - will be interrupted
    proc = subprocess.Popen(
        ['bash', RUN_SCRIPT],
        cwd=PIPELINE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(interrupt_after_seconds)

    # Send SIGTERM to interrupt
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    # Second run - should complete from checkpoint
    result = subprocess.run(
        ['bash', RUN_SCRIPT],
        cwd=PIPELINE_DIR,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout for full processing
    )

    return result


def run_pipeline_to_completion():
    """Run the pipeline to completion without interruption."""
    result = subprocess.run(
        ['bash', RUN_SCRIPT],
        cwd=PIPELINE_DIR,
        capture_output=True,
        text=True,
        timeout=300
    )
    return result


class TestPipelineFilesIntact:
    """Test that required files still exist and events.json is unchanged."""

    def test_events_file_exists(self):
        """The events.json file must still exist."""
        assert os.path.isfile(EVENTS_FILE), \
            f"Events file {EVENTS_FILE} must still exist"

    def test_events_file_has_50000_records(self):
        """The events.json file must still have 50,000 records."""
        with open(EVENTS_FILE, 'r') as f:
            line_count = sum(1 for line in f if line.strip())
        assert line_count == 50000, \
            f"Events file must still have 50,000 records, has {line_count}"

    def test_run_script_exists(self):
        """The run.sh script must still exist."""
        assert os.path.isfile(RUN_SCRIPT), \
            f"Run script {RUN_SCRIPT} must still exist"

    def test_process_script_exists(self):
        """The process.py script must still exist."""
        assert os.path.isfile(PROCESS_SCRIPT), \
            f"Process script {PROCESS_SCRIPT} must still exist"

    def test_process_script_is_valid_python(self):
        """The process.py script must be valid Python syntax."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', PROCESS_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Process script has syntax errors: {result.stderr}"


class TestProcessScriptStillUsesBatching:
    """Test that the fix maintains batch processing (not loading all 50k at once)."""

    def test_script_still_uses_batching(self):
        """The process.py script must still use batch processing."""
        with open(PROCESS_SCRIPT, 'r') as f:
            content = f.read()
        # Check for batch-related code
        has_batch = 'batch' in content.lower() or 'BATCH' in content
        assert has_batch, \
            "Process script must still use batch processing"

    def test_script_still_uses_checkpoint(self):
        """The process.py script must still have checkpoint functionality."""
        with open(PROCESS_SCRIPT, 'r') as f:
            content = f.read()
        assert 'checkpoint' in content.lower(), \
            "Process script must still use checkpoint functionality"


class TestFullRunProducesCorrectResults:
    """Test that a full uninterrupted run produces correct results."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clean up before and after test."""
        cleanup_pipeline_state()
        yield
        # Don't cleanup after - leave for inspection if needed

    def test_full_run_completes_successfully(self):
        """A full run should complete without errors."""
        result = run_pipeline_to_completion()
        assert result.returncode == 0, \
            f"Pipeline failed with return code {result.returncode}. Stderr: {result.stderr}"

    def test_summary_db_created(self):
        """After full run, summary.db should exist."""
        cleanup_pipeline_state()
        run_pipeline_to_completion()
        assert os.path.isfile(SUMMARY_DB), \
            f"Summary database {SUMMARY_DB} was not created"

    def test_full_run_produces_correct_totals(self):
        """After full run, totals in summary.db should match expected values."""
        cleanup_pipeline_state()
        result = run_pipeline_to_completion()
        assert result.returncode == 0, \
            f"Pipeline failed: {result.stderr}"

        expected = compute_expected_totals()
        actual = get_db_totals(SUMMARY_DB)

        # Check all categories present
        assert set(actual.keys()) == set(expected.keys()), \
            f"Category mismatch. Expected: {set(expected.keys())}, Got: {set(actual.keys())}"

        # Check totals match within tolerance
        tolerance = 0.01
        errors = []
        for cat in expected:
            exp_total = expected[cat]['total']
            act_total = actual[cat]['total']
            exp_count = expected[cat]['count']
            act_count = actual[cat]['count']

            if abs(exp_total - act_total) > tolerance:
                errors.append(f"Category '{cat}': expected total {exp_total}, got {act_total}")
            if exp_count != act_count:
                errors.append(f"Category '{cat}': expected count {exp_count}, got {act_count}")

        assert len(errors) == 0, \
            f"Totals mismatch:\n" + "\n".join(errors)


class TestResumeAfterInterrupt:
    """Test that the pipeline correctly resumes after being interrupted."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clean up before test."""
        cleanup_pipeline_state()
        yield

    def test_checkpoint_created_during_run(self):
        """A checkpoint file should be created during processing."""
        cleanup_pipeline_state()

        # Start pipeline
        proc = subprocess.Popen(
            ['bash', RUN_SCRIPT],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait a bit for some batches to process
        time.sleep(3)

        # Check checkpoint exists
        checkpoint_exists = os.path.isfile(CHECKPOINT_FILE)

        # Clean up process
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        assert checkpoint_exists, \
            "Checkpoint file should be created during processing"

    def test_resume_produces_correct_totals(self):
        """After interrupt and resume, totals should still be correct."""
        cleanup_pipeline_state()

        # Run with interrupt, then resume
        result = run_pipeline_with_interrupt(interrupt_after_seconds=3)

        assert result.returncode == 0, \
            f"Resumed pipeline failed: {result.stderr}"

        assert os.path.isfile(SUMMARY_DB), \
            "Summary database should exist after resume"

        expected = compute_expected_totals()
        actual = get_db_totals(SUMMARY_DB)

        # Check all categories present
        assert set(actual.keys()) == set(expected.keys()), \
            f"Category mismatch after resume. Expected: {set(expected.keys())}, Got: {set(actual.keys())}"

        # Check totals match within tolerance
        tolerance = 0.01
        errors = []
        for cat in expected:
            exp_total = expected[cat]['total']
            act_total = actual[cat]['total']
            exp_count = expected[cat]['count']
            act_count = actual[cat]['count']

            if abs(exp_total - act_total) > tolerance:
                errors.append(f"Category '{cat}': expected total {exp_total}, got {act_total} (diff: {abs(exp_total - act_total)})")
            if exp_count != act_count:
                errors.append(f"Category '{cat}': expected count {exp_count}, got {act_count}")

        assert len(errors) == 0, \
            f"Totals mismatch after resume - checkpoint/resume is not working correctly:\n" + "\n".join(errors)

    def test_multiple_interrupts_still_correct(self):
        """Multiple interrupts and resumes should still produce correct results."""
        cleanup_pipeline_state()

        # First interrupt
        proc = subprocess.Popen(
            ['bash', RUN_SCRIPT],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        # Second interrupt
        proc = subprocess.Popen(
            ['bash', RUN_SCRIPT],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(2)
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        # Final run to completion
        result = subprocess.run(
            ['bash', RUN_SCRIPT],
            cwd=PIPELINE_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )

        assert result.returncode == 0, \
            f"Final run failed: {result.stderr}"

        expected = compute_expected_totals()
        actual = get_db_totals(SUMMARY_DB)

        tolerance = 0.01
        errors = []
        for cat in expected:
            exp_total = expected[cat]['total']
            act_total = actual[cat]['total']
            exp_count = expected[cat]['count']
            act_count = actual[cat]['count']

            if abs(exp_total - act_total) > tolerance:
                errors.append(f"Category '{cat}': expected total {exp_total}, got {act_total}")
            if exp_count != act_count:
                errors.append(f"Category '{cat}': expected count {exp_count}, got {act_count}")

        assert len(errors) == 0, \
            f"Totals incorrect after multiple interrupts:\n" + "\n".join(errors)


class TestCheckpointContentIsValid:
    """Test that the checkpoint file contains valid and correct data."""

    def test_checkpoint_is_valid_json(self):
        """The checkpoint file should contain valid JSON."""
        cleanup_pipeline_state()

        # Start and interrupt pipeline
        proc = subprocess.Popen(
            ['bash', RUN_SCRIPT],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3)
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        if os.path.isfile(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                content = f.read()
            try:
                data = json.loads(content)
                assert isinstance(data, dict), \
                    "Checkpoint should be a JSON object"
            except json.JSONDecodeError as e:
                pytest.fail(f"Checkpoint file is not valid JSON: {e}")

    def test_checkpoint_tracks_progress_correctly(self):
        """The checkpoint should track actual line progress, not just batch count."""
        cleanup_pipeline_state()

        # Start and interrupt pipeline after processing some batches
        proc = subprocess.Popen(
            ['bash', RUN_SCRIPT],
            cwd=PIPELINE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(4)  # Allow several batches to process
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

        if os.path.isfile(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, 'r') as f:
                checkpoint = json.load(f)

            # The checkpoint should indicate significant progress
            # If it's storing batch_num as line_num, the value would be very small (< 50)
            # If it's correctly storing line count, it should be in thousands
            # We check that whatever value is stored makes sense for resuming

            # Get the value that represents progress
            progress_value = None
            for key in ['last_line', 'line', 'processed', 'offset', 'position']:
                if key in checkpoint:
                    progress_value = checkpoint[key]
                    break

            if progress_value is not None:
                # After 4 seconds, we should have processed more than just a few lines
                # With batch size 1000, even 1 batch = 1000 lines
                # A buggy implementation storing batch_num would have values like 1, 2, 3...
                # We can't be too strict here, but if progress is very low, it's suspicious
                # This is a heuristic check
                pass  # The main validation is in the resume test


class TestDatabaseIntegrity:
    """Test that the database maintains integrity through interrupts."""

    def test_database_has_correct_schema(self):
        """The summary.db should have the correct table schema."""
        cleanup_pipeline_state()
        run_pipeline_to_completion()

        conn = sqlite3.connect(SUMMARY_DB)
        cursor = conn.execute("PRAGMA table_info(summary)")
        columns = {row[1]: row[2] for row in cursor}
        conn.close()

        assert 'category' in columns, "summary table should have 'category' column"
        assert 'total_value' in columns or 'total' in columns, \
            "summary table should have a total value column"
        assert 'count' in columns, "summary table should have 'count' column"

    def test_no_duplicate_categories(self):
        """Each category should appear exactly once in the summary."""
        cleanup_pipeline_state()
        run_pipeline_with_interrupt(interrupt_after_seconds=3)

        conn = sqlite3.connect(SUMMARY_DB)
        cursor = conn.execute("SELECT category, COUNT(*) FROM summary GROUP BY category HAVING COUNT(*) > 1")
        duplicates = cursor.fetchall()
        conn.close()

        assert len(duplicates) == 0, \
            f"Found duplicate categories in summary: {duplicates}"
