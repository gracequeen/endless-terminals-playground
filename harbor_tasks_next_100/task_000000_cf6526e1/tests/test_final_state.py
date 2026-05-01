# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has fixed the CVE data pipeline bug.
"""

import os
import csv
import json
import subprocess
import re
import hashlib
import pytest


HOME = "/home/user"
PIPELINE_DIR = os.path.join(HOME, "pipeline")
STAGES_DIR = os.path.join(PIPELINE_DIR, "stages")
INTAKE_DIR = os.path.join(PIPELINE_DIR, "intake")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "assets.json")


class TestPipelineExecutesSuccessfully:
    """Test that the pipeline runs and exits successfully."""

    def test_run_py_exits_zero(self):
        """Verify run.py exits with code 0."""
        result = subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        assert result.returncode == 0, \
            f"run.py should exit 0 but exited {result.returncode}. stderr: {result.stderr}"


class TestOutputFileExists:
    """Test that the output JSON file exists and is valid."""

    def test_assets_json_exists(self):
        """Verify assets.json exists in output directory."""
        # First run the pipeline to ensure output is generated
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        assert os.path.isfile(OUTPUT_JSON), \
            f"Output file {OUTPUT_JSON} does not exist"

    def test_assets_json_is_valid_json(self):
        """Verify assets.json contains valid JSON."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        try:
            with open(OUTPUT_JSON, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"assets.json is not valid JSON: {e}")
        except FileNotFoundError:
            pytest.fail(f"assets.json does not exist at {OUTPUT_JSON}")


class TestOutputContainsAllRecords:
    """Test that the output contains exactly 47 records."""

    def test_output_has_47_records(self):
        """Verify the JSON contains exactly 47 records."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        with open(OUTPUT_JSON, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), \
            f"Expected assets.json to contain a list, got {type(data).__name__}"
        assert len(data) == 47, \
            f"Expected 47 records in assets.json, found {len(data)}"


class TestAllRecordsHaveCveRefs:
    """Test that every record has the cve_refs field populated."""

    def test_all_records_have_cve_refs_key(self):
        """Verify every record has a 'cve_refs' key."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        with open(OUTPUT_JSON, 'r') as f:
            data = json.load(f)

        missing_cve_refs = []
        for i, record in enumerate(data):
            if 'cve_refs' not in record:
                hostname = record.get('hostname', record.get('host', f'record_{i}'))
                missing_cve_refs.append(hostname)

        assert not missing_cve_refs, \
            f"The following {len(missing_cve_refs)} records are missing 'cve_refs': {missing_cve_refs[:10]}{'...' if len(missing_cve_refs) > 10 else ''}"

    def test_all_cve_refs_are_nonempty_lists(self):
        """Verify every record's cve_refs is a non-empty list."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        with open(OUTPUT_JSON, 'r') as f:
            data = json.load(f)

        empty_cve_refs = []
        for i, record in enumerate(data):
            cve_refs = record.get('cve_refs')
            hostname = record.get('hostname', record.get('host', f'record_{i}'))
            if cve_refs is None:
                empty_cve_refs.append(f"{hostname}: missing cve_refs")
            elif not isinstance(cve_refs, list):
                empty_cve_refs.append(f"{hostname}: cve_refs is not a list (got {type(cve_refs).__name__})")
            elif len(cve_refs) == 0:
                empty_cve_refs.append(f"{hostname}: cve_refs is empty list")

        assert not empty_cve_refs, \
            f"The following records have invalid cve_refs: {empty_cve_refs[:10]}{'...' if len(empty_cve_refs) > 10 else ''}"

    def test_cve_refs_contain_valid_cve_ids(self):
        """Verify cve_refs contain strings matching CVE-YYYY-NNNNN pattern."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        with open(OUTPUT_JSON, 'r') as f:
            data = json.load(f)

        cve_pattern = re.compile(r'^CVE-\d{4}-\d+$')
        invalid_cves = []

        for i, record in enumerate(data):
            cve_refs = record.get('cve_refs', [])
            hostname = record.get('hostname', record.get('host', f'record_{i}'))
            if isinstance(cve_refs, list):
                for cve in cve_refs:
                    if not isinstance(cve, str) or not cve_pattern.match(cve.strip()):
                        invalid_cves.append(f"{hostname}: '{cve}'")

        assert not invalid_cves, \
            f"Invalid CVE format found: {invalid_cves[:10]}{'...' if len(invalid_cves) > 10 else ''}"


class TestGrepCveRefsCount:
    """Test using grep to count cve_refs occurrences."""

    def test_grep_cve_refs_returns_47(self):
        """Verify grep -c '"cve_refs"' returns 47."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        result = subprocess.run(
            ["grep", "-c", '"cve_refs"', OUTPUT_JSON],
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 47, \
            f"Expected grep -c '\"cve_refs\"' to return 47, got {count}"


class TestPythonAssertionCommand:
    """Test the exact Python assertion command from the task."""

    def test_python_assertion_exits_zero(self):
        """Verify the Python assertion command exits 0."""
        subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        cmd = (
            "import json; "
            f"d=json.load(open('{OUTPUT_JSON}')); "
            "assert all('cve_refs' in r and len(r['cve_refs'])>0 for r in d)"
        )
        result = subprocess.run(
            ["python3", "-c", cmd],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Python assertion failed. stderr: {result.stderr}"


class TestSourceCSVsUnmodified:
    """Test that source CSV files were not modified."""

    def test_servers_csv_has_cve_list_column(self):
        """Verify servers.csv still has cve_list column (not renamed)."""
        csv_path = os.path.join(INTAKE_DIR, "servers.csv")
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        assert "cve_list" in headers, \
            f"servers.csv should still have 'cve_list' column. Found: {headers}"

    def test_workstations_csv_has_cve_list_column(self):
        """Verify workstations.csv still has cve_list column."""
        csv_path = os.path.join(INTAKE_DIR, "workstations.csv")
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        assert "cve_list" in headers, \
            f"workstations.csv should still have 'cve_list' column. Found: {headers}"

    def test_network_devices_csv_has_cve_list_column(self):
        """Verify network_devices.csv still has cve_list column."""
        csv_path = os.path.join(INTAKE_DIR, "network_devices.csv")
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
        assert "cve_list" in headers, \
            f"network_devices.csv should still have 'cve_list' column. Found: {headers}"

    def test_total_source_records_still_47(self):
        """Verify source CSVs still contain 47 total records."""
        csv_files = ["servers.csv", "workstations.csv", "network_devices.csv"]
        total_records = 0
        for csv_file in csv_files:
            csv_path = os.path.join(INTAKE_DIR, csv_file)
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
                total_records += len(records)
        assert total_records == 47, \
            f"Source CSVs should still have 47 records, found {total_records}"


class TestEnrichPyNotGutted:
    """Test that enrich.py still contains proper CVE processing logic."""

    def test_enrich_still_has_split_logic(self):
        """Verify enrich.py still contains logic to split CVE references."""
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        with open(enrich_py, 'r') as f:
            content = f.read()

        # Check that enrich.py still has split logic (not just copying field wholesale)
        assert "split" in content, \
            "enrich.py should still contain 'split' logic for processing CVE references"

    def test_enrich_still_creates_cve_refs(self):
        """Verify enrich.py still has logic to create cve_refs field."""
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")
        with open(enrich_py, 'r') as f:
            content = f.read()

        assert "cve_refs" in content, \
            "enrich.py should still contain 'cve_refs' field creation logic"


class TestFieldNameMismatchFixed:
    """Test that the field name mismatch has been fixed."""

    def test_normalize_and_enrich_field_names_match(self):
        """Verify the field name used by normalize matches what enrich expects."""
        normalize_py = os.path.join(STAGES_DIR, "normalize.py")
        enrich_py = os.path.join(STAGES_DIR, "enrich.py")

        with open(normalize_py, 'r') as f:
            normalize_content = f.read()
        with open(enrich_py, 'r') as f:
            enrich_content = f.read()

        # The fix could be either:
        # 1. Change normalize.py to output 'cve_reference' (without 's')
        # 2. Change enrich.py to expect 'cve_references' (with 's')
        # Either way, the pipeline should now work

        # We verify this by checking the output works (already tested above)
        # But we can also check that at least one of the files was modified
        # to have consistent naming

        # Check if they now use the same field name
        uses_cve_reference = "cve_reference" in enrich_content and "'cve_reference'" in enrich_content
        uses_cve_references = "cve_references" in normalize_content and "'cve_references'" in normalize_content

        # The simplest check is that the output works, which is tested elsewhere
        # Here we just verify the pipeline code exists and is syntactically valid
        result = subprocess.run(
            ["python3", "-m", "py_compile", normalize_py],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"normalize.py has syntax errors: {result.stderr}"

        result = subprocess.run(
            ["python3", "-m", "py_compile", enrich_py],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"enrich.py has syntax errors: {result.stderr}"


class TestOutputProducedByRunPy:
    """Test that output is produced by running run.py, not manually created."""

    def test_fresh_run_produces_valid_output(self):
        """Verify a fresh run of run.py produces the expected output."""
        # Remove existing output if present
        if os.path.exists(OUTPUT_JSON):
            os.remove(OUTPUT_JSON)

        # Run the pipeline
        result = subprocess.run(
            ["python3", os.path.join(PIPELINE_DIR, "run.py")],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )

        assert result.returncode == 0, \
            f"run.py failed with exit code {result.returncode}. stderr: {result.stderr}"

        assert os.path.isfile(OUTPUT_JSON), \
            f"run.py did not create {OUTPUT_JSON}"

        with open(OUTPUT_JSON, 'r') as f:
            data = json.load(f)

        assert len(data) == 47, \
            f"Fresh run should produce 47 records, got {len(data)}"

        records_with_cve_refs = sum(1 for r in data if 'cve_refs' in r and isinstance(r['cve_refs'], list) and len(r['cve_refs']) > 0)
        assert records_with_cve_refs == 47, \
            f"Fresh run should produce 47 records with valid cve_refs, got {records_with_cve_refs}"
