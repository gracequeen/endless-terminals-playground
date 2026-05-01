# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the CVE data pipeline bug.
"""

import os
import csv
import subprocess
import re
import pytest


HOME = "/home/user"
PIPELINE_DIR = os.path.join(HOME, "pipeline")
STAGES_DIR = os.path.join(PIPELINE_DIR, "stages")
INTAKE_DIR = os.path.join(PIPELINE_DIR, "intake")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
LOGS_DIR = os.path.join(PIPELINE_DIR, "logs")


class TestPipelineDirectoryStructure:
    """Test that the pipeline directory structure exists."""

    def test_pipeline_directory_exists(self):
        assert os.path.isdir(PIPELINE_DIR), \
            f"Pipeline directory {PIPELINE_DIR} does not exist"

    def test_stages_directory_exists(self):
        assert os.path.isdir(STAGES_DIR), \
            f"Stages directory {STAGES_DIR} does not exist"

    def test_intake_directory_exists(self):
        assert os.path.isdir(INTAKE_DIR), \
            f"Intake directory {INTAKE_DIR} does not exist"

    def test_output_directory_exists(self):
        assert os.path.isdir(OUTPUT_DIR), \
            f"Output directory {OUTPUT_DIR} does not exist"


class TestPipelineFiles:
    """Test that required pipeline Python files exist."""

    def test_run_py_exists(self):
        run_py = os.path.join(PIPELINE_DIR, "run.py")
        assert os.path.isfile(run_py), \
            f"Orchestrator script {run_py} does not exist"

    def test_ingest_py_exists(self):
        ingest_py = os.path.join(STAGES_DIR, "ingest.py")
        assert os.path.isfile(ingest_py), \
            f"Ingest stage {ingest_py} does not exist"

    def test_normalize_py_exists(self):
        normalize_py = os.path.join(STAGES_DIR, "normalize.py")
        assert os.path.isfile(normalize_py), \
            f"Normalize stage {normalize_py} does not exist"

    def test_enrich_py_exists(self):
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        assert os.path.isfile(enrich_py), \
            f"Enrich stage {enrich_py} does not exist"


class TestIntakeCSVFiles:
    """Test that the intake CSV files exist and have correct structure."""

    def test_servers_csv_exists(self):
        servers_csv = os.path.join(INTAKE_DIR, "servers.csv")
        assert os.path.isfile(servers_csv), \
            f"Source CSV {servers_csv} does not exist"

    def test_workstations_csv_exists(self):
        workstations_csv = os.path.join(INTAKE_DIR, "workstations.csv")
        assert os.path.isfile(workstations_csv), \
            f"Source CSV {workstations_csv} does not exist"

    def test_network_devices_csv_exists(self):
        network_devices_csv = os.path.join(INTAKE_DIR, "network_devices.csv")
        assert os.path.isfile(network_devices_csv), \
            f"Source CSV {network_devices_csv} does not exist"

    def test_csv_files_have_cve_list_column(self):
        """Verify all CSVs have the cve_list column."""
        csv_files = ["servers.csv", "workstations.csv", "network_devices.csv"]
        for csv_file in csv_files:
            csv_path = os.path.join(INTAKE_DIR, csv_file)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                assert headers is not None, f"{csv_file} appears to be empty"
                assert "cve_list" in headers, \
                    f"{csv_file} is missing 'cve_list' column. Found columns: {headers}"

    def test_csv_files_have_required_columns(self):
        """Verify all CSVs have the expected columns."""
        required_columns = {"hostname", "ip", "os", "cve_list"}
        csv_files = ["servers.csv", "workstations.csv", "network_devices.csv"]
        for csv_file in csv_files:
            csv_path = os.path.join(INTAKE_DIR, csv_file)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                headers = set(reader.fieldnames) if reader.fieldnames else set()
                missing = required_columns - headers
                assert not missing, \
                    f"{csv_file} is missing columns: {missing}. Found: {headers}"

    def test_total_host_records_is_47(self):
        """Verify there are exactly 47 host records across all CSVs."""
        csv_files = ["servers.csv", "workstations.csv", "network_devices.csv"]
        total_records = 0
        for csv_file in csv_files:
            csv_path = os.path.join(INTAKE_DIR, csv_file)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
                total_records += len(records)
        assert total_records == 47, \
            f"Expected 47 total host records, found {total_records}"

    def test_all_records_have_nonempty_cve_list(self):
        """Verify all 47 records have non-empty cve_list values."""
        csv_files = ["servers.csv", "workstations.csv", "network_devices.csv"]
        empty_cve_hosts = []
        for csv_file in csv_files:
            csv_path = os.path.join(INTAKE_DIR, csv_file)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cve_list = row.get("cve_list", "").strip()
                    if not cve_list:
                        empty_cve_hosts.append(row.get("hostname", "unknown"))
        assert not empty_cve_hosts, \
            f"The following hosts have empty cve_list: {empty_cve_hosts}"

    def test_cve_list_format_is_pipe_delimited(self):
        """Verify cve_list values contain pipe-delimited CVE IDs."""
        csv_files = ["servers.csv", "workstations.csv", "network_devices.csv"]
        cve_pattern = re.compile(r'^CVE-\d{4}-\d+$')
        invalid_entries = []
        for csv_file in csv_files:
            csv_path = os.path.join(INTAKE_DIR, csv_file)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cve_list = row.get("cve_list", "").strip()
                    if cve_list:
                        cves = cve_list.split("|")
                        for cve in cves:
                            if not cve_pattern.match(cve.strip()):
                                invalid_entries.append(
                                    f"{row.get('hostname', 'unknown')}: '{cve}'"
                                )
        assert not invalid_entries, \
            f"Invalid CVE format found in: {invalid_entries[:5]}..."  # Show first 5


class TestNormalizePyHasBug:
    """Test that normalize.py contains the expected bug (typo in field mapping)."""

    def test_normalize_maps_to_cve_references_with_s(self):
        """Verify the bug: normalize.py maps to 'cve_references' (with 's')."""
        normalize_py = os.path.join(STAGES_DIR, "normalize.py")
        with open(normalize_py, 'r') as f:
            content = f.read()
        # The bug is that it maps to 'cve_references' (with 's')
        assert "cve_references" in content, \
            "normalize.py should contain 'cve_references' (the buggy mapping)"


class TestEnrichPyExpectsDifferentFieldName:
    """Test that enrich.py expects a different field name than what normalize provides."""

    def test_enrich_expects_cve_reference_without_s(self):
        """Verify enrich.py looks for 'cve_reference' (without 's')."""
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        with open(enrich_py, 'r') as f:
            content = f.read()
        # enrich.py expects 'cve_reference' (without 's')
        assert "cve_reference" in content, \
            "enrich.py should contain 'cve_reference' field check"

    def test_enrich_has_try_except_for_keyerror(self):
        """Verify enrich.py has try/except handling for KeyError."""
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        with open(enrich_py, 'r') as f:
            content = f.read()
        assert "KeyError" in content or "except" in content, \
            "enrich.py should have exception handling"

    def test_enrich_creates_cve_refs_field(self):
        """Verify enrich.py has logic to create 'cve_refs' field."""
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        with open(enrich_py, 'r') as f:
            content = f.read()
        assert "cve_refs" in content, \
            "enrich.py should contain logic to create 'cve_refs' field"


class TestPythonAvailable:
    """Test that Python 3 is available."""

    def test_python3_available(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"python3 not available: {result.stderr}"

    def test_python3_version_is_3_11_or_higher(self):
        result = subprocess.run(
            ["python3", "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        version = result.stdout.strip()
        major, minor = map(int, version.split('.'))
        assert (major, minor) >= (3, 11), \
            f"Expected Python 3.11+, got {version}"


class TestPipelineRunsWithoutError:
    """Test that the pipeline runs without crashing (exits 0)."""

    def test_run_py_exits_zero(self):
        """Verify run.py exits with code 0 (even though output is buggy)."""
        result = subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        assert result.returncode == 0, \
            f"run.py should exit 0 but exited {result.returncode}. stderr: {result.stderr}"


class TestFilesAreWritable:
    """Test that pipeline files are writable for fixing."""

    def test_normalize_py_is_writable(self):
        normalize_py = os.path.join(STAGES_DIR, "normalize.py")
        assert os.access(normalize_py, os.W_OK), \
            f"{normalize_py} is not writable"

    def test_enrich_py_is_writable(self):
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        assert os.access(enrich_py, os.W_OK), \
            f"{enrich_py} is not writable"

    def test_run_py_is_writable(self):
        run_py = os.path.join(PIPELINE_DIR, "run.py")
        assert os.access(run_py, os.W_OK), \
            f"{run_py} is not writable"
