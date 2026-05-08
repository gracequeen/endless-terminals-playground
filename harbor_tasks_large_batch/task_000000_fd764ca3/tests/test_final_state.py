# test_final_state.py
"""
Tests to validate the final state after the student has fixed the data
reconciliation pipeline bug.
"""

import os
import subprocess
import pytest
import csv


HOME = "/home/user"
PIPELINE_DIR = os.path.join(HOME, "pipeline")
INCOMING_DIR = os.path.join(PIPELINE_DIR, "incoming")
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")

RECONCILE_SCRIPT = os.path.join(PIPELINE_DIR, "reconcile.py")
CONFIG_FILE = os.path.join(PIPELINE_DIR, "config.yaml")
MERGED_OUTPUT = os.path.join(OUTPUT_DIR, "merged.csv")

VENDOR_A_CSV = os.path.join(INCOMING_DIR, "vendor_a.csv")
VENDOR_B_CSV = os.path.join(INCOMING_DIR, "vendor_b.csv")
VENDOR_C_CSV = os.path.join(INCOMING_DIR, "vendor_c.csv")


class TestReconcileScriptExecution:
    """Test that the reconcile script runs successfully."""

    def test_reconcile_script_exits_zero(self):
        """The script must exit with code 0."""
        result = subprocess.run(
            ['python3', RECONCILE_SCRIPT],
            capture_output=True,
            text=True,
            cwd=PIPELINE_DIR
        )
        assert result.returncode == 0, \
            f"reconcile.py exited with code {result.returncode}.\nStderr: {result.stderr}\nStdout: {result.stdout}"


class TestMergedOutput:
    """Test the merged output file meets requirements."""

    def test_merged_csv_exists(self):
        """Output file must exist after running the script."""
        # First run the script to ensure output is fresh
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)
        assert os.path.isfile(MERGED_OUTPUT), \
            f"Merged output file {MERGED_OUTPUT} does not exist"

    def test_merged_csv_has_more_than_1400_rows(self):
        """Output must have >1400 rows to verify proper merge."""
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)

        with open(MERGED_OUTPUT, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            row_count = sum(1 for _ in reader)

        assert row_count > 1400, \
            f"Merged output has only {row_count} rows, expected >1400. " \
            "This suggests vendor_c data is not being properly normalized and included."

    def test_merged_csv_has_reasonable_upper_bound(self):
        """Output should not exceed ~1500 rows (sanity check)."""
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)

        with open(MERGED_OUTPUT, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            row_count = sum(1 for _ in reader)

        assert row_count <= 1600, \
            f"Merged output has {row_count} rows, expected <=1600. " \
            "Something may be wrong with the filtering logic."

    def test_merged_csv_has_expected_columns(self):
        """Output should have the standard columns."""
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)

        with open(MERGED_OUTPUT, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

        # Should contain at least id, timestamp, amount, status
        header_lower = [h.lower() for h in header]
        assert 'id' in header_lower, \
            f"Merged output missing 'id' column. Headers: {header}"


class TestVendorCDataIncluded:
    """Test that vendor_c data is properly included in the output."""

    def test_vendor_c_ids_appear_in_output(self):
        """At least 400 distinct IDs from vendor_c must appear in merged output."""
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)

        # Get all IDs from vendor_c
        vendor_c_ids = set()
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor_c_ids.add(row['id'])

        # Get all IDs from merged output
        merged_ids = set()
        with open(MERGED_OUTPUT, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                merged_ids.add(row['id'])

        # Count how many vendor_c IDs appear in merged output
        vendor_c_in_merged = vendor_c_ids.intersection(merged_ids)

        assert len(vendor_c_in_merged) >= 400, \
            f"Only {len(vendor_c_in_merged)} IDs from vendor_c appear in merged output, " \
            f"expected at least 400. This suggests vendor_c data normalization is not working."


class TestSourceFilesUnchanged:
    """Test that source CSV files were not modified (fix should be in processing)."""

    def test_vendor_a_unchanged_row_count(self):
        """vendor_a.csv should still have ~500 rows."""
        with open(VENDOR_A_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            row_count = sum(1 for _ in reader)
        assert 495 <= row_count <= 505, \
            f"vendor_a.csv has {row_count} rows, expected ~500. Source file should not be modified."

    def test_vendor_b_unchanged_row_count(self):
        """vendor_b.csv should still have ~480 rows."""
        with open(VENDOR_B_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            row_count = sum(1 for _ in reader)
        assert 475 <= row_count <= 485, \
            f"vendor_b.csv has {row_count} rows, expected ~480. Source file should not be modified."

    def test_vendor_c_unchanged_row_count(self):
        """vendor_c.csv should still have ~520 rows."""
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.reader(f)
            next(reader)
            row_count = sum(1 for _ in reader)
        assert 515 <= row_count <= 525, \
            f"vendor_c.csv has {row_count} rows, expected ~520. Source file should not be modified."

    def test_vendor_c_still_has_iso_timestamps(self):
        """vendor_c.csv should still have ISO 8601 timestamps (source unchanged)."""
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.DictReader(f)
            iso_count = 0
            for i, row in enumerate(reader):
                if i >= 20:
                    break
                ts = row['timestamp']
                if 'T' in ts or '-' in ts:
                    iso_count += 1
        assert iso_count > 0, \
            "vendor_c.csv timestamps should still be ISO 8601 strings. " \
            "Source file should not be modified; fix should be in reconcile.py."

    def test_vendor_c_still_has_currency_symbols(self):
        """vendor_c.csv should still have currency symbols in amounts (source unchanged)."""
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.DictReader(f)
            currency_count = 0
            for i, row in enumerate(reader):
                if i >= 20:
                    break
                amount = row['amount']
                if '$' in amount:
                    currency_count += 1
        assert currency_count > 0, \
            "vendor_c.csv amounts should still have currency symbols. " \
            "Source file should not be modified; fix should be in reconcile.py."


class TestConfigUnchanged:
    """Test that config.yaml thresholds were not modified."""

    def test_config_timestamp_cutoff_unchanged(self):
        """timestamp_cutoff should still be 1700000000."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
        assert '1700000000' in content, \
            "config.yaml timestamp_cutoff should remain 1700000000. " \
            "Fix should be in data normalization, not changing thresholds."

    def test_config_min_amount_unchanged(self):
        """min_amount should still be 10 (or 10.0)."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()
        # Check for min_amount: 10 or min_amount: 10.0
        assert 'min_amount' in content, \
            "config.yaml should still contain min_amount setting"
        # Parse to verify the value
        import re
        match = re.search(r'min_amount\s*:\s*(\d+(?:\.\d+)?)', content)
        assert match is not None, \
            "Could not find min_amount value in config.yaml"
        value = float(match.group(1))
        assert abs(value - 10.0) < 0.01, \
            f"config.yaml min_amount should be 10.0, found {value}. " \
            "Fix should be in data normalization, not changing thresholds."


class TestScriptStillReadsConfig:
    """Test that reconcile.py still reads from config.yaml (not hardcoded)."""

    def test_script_references_config_or_yaml(self):
        """Script should still use config.yaml for thresholds."""
        with open(RECONCILE_SCRIPT, 'r') as f:
            content = f.read()

        has_config_reference = ('config' in content.lower() or 
                                'yaml' in content.lower() or
                                '.yaml' in content or
                                '.yml' in content)

        assert has_config_reference, \
            "reconcile.py should read thresholds from config.yaml, not hardcode them. " \
            "No reference to 'config' or 'yaml' found in script."


class TestOutputDataQuality:
    """Test the quality of the merged output data."""

    def test_output_amounts_are_numeric(self):
        """All amounts in output should be valid numbers (no currency symbols)."""
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)

        with open(MERGED_OUTPUT, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 100:  # Check first 100 rows
                    break
                amount = row.get('amount', '')
                assert '$' not in amount, \
                    f"Row {i+1} has currency symbol in amount: {amount}"
                try:
                    float(amount)
                except ValueError:
                    pytest.fail(f"Row {i+1} amount is not a valid number: {amount}")

    def test_output_has_data_from_all_vendors(self):
        """Output should contain data originating from all three vendors."""
        subprocess.run(['python3', RECONCILE_SCRIPT], cwd=PIPELINE_DIR, capture_output=True)

        # Get IDs from each vendor
        vendor_a_ids = set()
        with open(VENDOR_A_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor_a_ids.add(row['id'])

        vendor_b_ids = set()
        with open(VENDOR_B_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor_b_ids.add(row['id'])

        vendor_c_ids = set()
        with open(VENDOR_C_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor_c_ids.add(row['id'])

        # Get IDs from merged output
        merged_ids = set()
        with open(MERGED_OUTPUT, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                merged_ids.add(row['id'])

        # Check each vendor contributes
        a_in_merged = len(vendor_a_ids.intersection(merged_ids))
        b_in_merged = len(vendor_b_ids.intersection(merged_ids))
        c_in_merged = len(vendor_c_ids.intersection(merged_ids))

        assert a_in_merged > 100, \
            f"Only {a_in_merged} IDs from vendor_a in output, expected >100"
        assert b_in_merged > 100, \
            f"Only {b_in_merged} IDs from vendor_b in output, expected >100"
        assert c_in_merged > 100, \
            f"Only {c_in_merged} IDs from vendor_c in output, expected >100"
