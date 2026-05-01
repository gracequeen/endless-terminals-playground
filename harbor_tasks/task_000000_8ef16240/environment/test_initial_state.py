# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the batch job checkpoint/resume bug.
"""

import os
import json
import subprocess
import pytest


# Constants
PIPELINE_DIR = "/home/user/pipeline"
RUN_SCRIPT = os.path.join(PIPELINE_DIR, "run.sh")
PROCESS_SCRIPT = os.path.join(PIPELINE_DIR, "process.py")
DATA_DIR = os.path.join(PIPELINE_DIR, "data")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
CHECKPOINT_FILE = os.path.join(PIPELINE_DIR, ".checkpoint")


class TestPipelineDirectoryStructure:
    """Test that the pipeline directory structure exists correctly."""

    def test_pipeline_directory_exists(self):
        """The /home/user/pipeline directory must exist."""
        assert os.path.isdir(PIPELINE_DIR), \
            f"Pipeline directory {PIPELINE_DIR} does not exist"

    def test_pipeline_directory_is_writable(self):
        """The /home/user/pipeline directory must be writable."""
        assert os.access(PIPELINE_DIR, os.W_OK), \
            f"Pipeline directory {PIPELINE_DIR} is not writable"

    def test_data_directory_exists(self):
        """The /home/user/pipeline/data directory must exist."""
        assert os.path.isdir(DATA_DIR), \
            f"Data directory {DATA_DIR} does not exist"

    def test_output_directory_exists(self):
        """The /home/user/pipeline/output directory must exist."""
        assert os.path.isdir(OUTPUT_DIR), \
            f"Output directory {OUTPUT_DIR} does not exist"

    def test_output_directory_is_empty(self):
        """The /home/user/pipeline/output directory should be empty initially."""
        contents = os.listdir(OUTPUT_DIR)
        assert len(contents) == 0, \
            f"Output directory {OUTPUT_DIR} should be empty but contains: {contents}"


class TestRequiredScripts:
    """Test that required scripts exist and are properly configured."""

    def test_run_script_exists(self):
        """The run.sh script must exist."""
        assert os.path.isfile(RUN_SCRIPT), \
            f"Run script {RUN_SCRIPT} does not exist"

    def test_run_script_is_executable(self):
        """The run.sh script must be executable."""
        assert os.access(RUN_SCRIPT, os.X_OK), \
            f"Run script {RUN_SCRIPT} is not executable"

    def test_run_script_invokes_python_process(self):
        """The run.sh script should invoke process.py."""
        with open(RUN_SCRIPT, 'r') as f:
            content = f.read()
        assert 'process.py' in content or 'python' in content, \
            f"Run script {RUN_SCRIPT} does not appear to invoke process.py"

    def test_process_script_exists(self):
        """The process.py script must exist."""
        assert os.path.isfile(PROCESS_SCRIPT), \
            f"Process script {PROCESS_SCRIPT} does not exist"

    def test_process_script_is_readable(self):
        """The process.py script must be readable."""
        assert os.access(PROCESS_SCRIPT, os.R_OK), \
            f"Process script {PROCESS_SCRIPT} is not readable"

    def test_process_script_is_valid_python(self):
        """The process.py script must be valid Python syntax."""
        result = subprocess.run(
            ['python3', '-m', 'py_compile', PROCESS_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Process script {PROCESS_SCRIPT} has syntax errors: {result.stderr}"


class TestEventsDataFile:
    """Test that the events.json data file exists and has correct format."""

    def test_events_file_exists(self):
        """The events.json file must exist."""
        assert os.path.isfile(EVENTS_FILE), \
            f"Events file {EVENTS_FILE} does not exist"

    def test_events_file_is_readable(self):
        """The events.json file must be readable."""
        assert os.access(EVENTS_FILE, os.R_OK), \
            f"Events file {EVENTS_FILE} is not readable"

    def test_events_file_has_50000_records(self):
        """The events.json file should contain 50,000 JSONL records."""
        with open(EVENTS_FILE, 'r') as f:
            line_count = sum(1 for line in f if line.strip())
        assert line_count == 50000, \
            f"Events file should have 50,000 records but has {line_count}"

    def test_events_file_is_valid_jsonl(self):
        """Each line in events.json should be valid JSON."""
        errors = []
        with open(EVENTS_FILE, 'r') as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {i+1}: {e}")
                if len(errors) >= 5:  # Stop after 5 errors
                    break
        assert len(errors) == 0, \
            f"Events file has invalid JSON lines: {errors}"

    def test_events_file_records_have_required_fields(self):
        """Each record should have id, timestamp, category, and value fields."""
        required_fields = {'id', 'timestamp', 'category', 'value'}
        errors = []
        with open(EVENTS_FILE, 'r') as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                record = json.loads(line)
                missing = required_fields - set(record.keys())
                if missing:
                    errors.append(f"Line {i+1} missing fields: {missing}")
                if len(errors) >= 5:
                    break
        assert len(errors) == 0, \
            f"Events file records missing required fields: {errors}"

    def test_events_file_field_types(self):
        """Verify field types: id (int), timestamp (str), category (str), value (float/int)."""
        errors = []
        with open(EVENTS_FILE, 'r') as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record.get('id'), int):
                    errors.append(f"Line {i+1}: 'id' should be int")
                if not isinstance(record.get('timestamp'), str):
                    errors.append(f"Line {i+1}: 'timestamp' should be str")
                if not isinstance(record.get('category'), str):
                    errors.append(f"Line {i+1}: 'category' should be str")
                if not isinstance(record.get('value'), (int, float)):
                    errors.append(f"Line {i+1}: 'value' should be numeric")
                if len(errors) >= 5:
                    break
        assert len(errors) == 0, \
            f"Events file records have incorrect field types: {errors}"


class TestCheckpointState:
    """Test the initial checkpoint state."""

    def test_checkpoint_file_does_not_exist(self):
        """The .checkpoint file should not exist initially."""
        assert not os.path.exists(CHECKPOINT_FILE), \
            f"Checkpoint file {CHECKPOINT_FILE} should not exist initially"


class TestSystemDependencies:
    """Test that required system dependencies are available."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ['python3', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Python 3 is not available"

    def test_python3_version_is_3_11_or_higher(self):
        """Python version should be 3.11 or higher."""
        result = subprocess.run(
            ['python3', '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],
            capture_output=True,
            text=True
        )
        version = result.stdout.strip()
        major, minor = map(int, version.split('.'))
        assert (major, minor) >= (3, 11), \
            f"Python version should be 3.11+, got {version}"

    def test_sqlite3_module_available(self):
        """The sqlite3 Python module must be available."""
        result = subprocess.run(
            ['python3', '-c', 'import sqlite3; print(sqlite3.version)'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"sqlite3 module is not available: {result.stderr}"

    def test_jq_installed(self):
        """jq must be installed."""
        result = subprocess.run(
            ['which', 'jq'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "jq is not installed"

    def test_jq_works(self):
        """jq must be functional."""
        result = subprocess.run(
            ['jq', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"jq is not working properly: {result.stderr}"

    def test_bash_available(self):
        """Bash must be available."""
        result = subprocess.run(
            ['bash', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Bash is not available"


class TestProcessScriptStructure:
    """Test that process.py has the expected structure with the bugs."""

    def test_process_script_uses_checkpoint(self):
        """The process.py script should have checkpoint functionality."""
        with open(PROCESS_SCRIPT, 'r') as f:
            content = f.read()
        assert 'checkpoint' in content.lower(), \
            "Process script should contain checkpoint-related code"

    def test_process_script_uses_sqlite(self):
        """The process.py script should use sqlite3."""
        with open(PROCESS_SCRIPT, 'r') as f:
            content = f.read()
        assert 'sqlite3' in content, \
            "Process script should import/use sqlite3"

    def test_process_script_reads_events_json(self):
        """The process.py script should read from events.json."""
        with open(PROCESS_SCRIPT, 'r') as f:
            content = f.read()
        assert 'events.json' in content or 'data/' in content, \
            "Process script should reference events.json data file"

    def test_process_script_uses_batching(self):
        """The process.py script should process in batches."""
        with open(PROCESS_SCRIPT, 'r') as f:
            content = f.read()
        assert 'batch' in content.lower() or 'BATCH' in content, \
            "Process script should use batch processing"
