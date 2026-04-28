# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the CSV to JSON migration task.
"""

import json
import os
import re
import subprocess
import pytest


class TestOutputFilesExist:
    """Test that the required output files exist."""

    def test_assets_json_exists(self):
        """The /home/user/inventory/assets.json file must exist."""
        path = "/home/user/inventory/assets.json"
        assert os.path.isfile(path), f"Output file {path} does not exist"

    def test_rejected_json_exists(self):
        """The /home/user/inventory/rejected.json file must exist."""
        path = "/home/user/inventory/rejected.json"
        assert os.path.isfile(path), f"Output file {path} does not exist"

    def test_original_csv_unchanged(self):
        """The original /home/user/inventory/assets.csv must still exist with 847 rows."""
        path = "/home/user/inventory/assets.csv"
        assert os.path.isfile(path), f"Original file {path} was deleted or moved"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        assert len(lines) == 847, f"Original CSV should have 847 rows, found {len(lines)}"


class TestAssetsJsonValidity:
    """Test that assets.json is valid JSON with correct structure."""

    @pytest.fixture
    def assets_data(self):
        """Load the assets.json file."""
        path = "/home/user/inventory/assets.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_assets_json_is_valid_json(self):
        """The assets.json file must be valid JSON."""
        path = "/home/user/inventory/assets.json"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"assets.json is not valid JSON: {e}")

    def test_assets_json_is_array(self, assets_data):
        """The assets.json must contain an array at the top level."""
        assert isinstance(assets_data, list), "assets.json must be a JSON array"

    def test_assets_json_has_813_records(self, assets_data):
        """The assets.json must contain exactly 813 records."""
        count = len(assets_data)
        assert count == 813, f"Expected 813 records in assets.json, found {count}"

    def test_each_record_has_required_keys(self, assets_data):
        """Each record must have exactly the required keys."""
        required_keys = {'id', 'name', 'serial', 'purchase_date', 'price_cents', 'location'}
        for i, record in enumerate(assets_data):
            record_keys = set(record.keys())
            assert record_keys == required_keys, (
                f"Record {i} has keys {record_keys}, expected {required_keys}"
            )


class TestAssetsJsonDataQuality:
    """Test that assets.json data meets quality requirements."""

    @pytest.fixture
    def assets_data(self):
        """Load the assets.json file."""
        path = "/home/user/inventory/assets.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_all_purchase_dates_are_iso8601(self, assets_data):
        """All purchase_date values must be valid ISO 8601 dates (YYYY-MM-DD)."""
        iso_pattern = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
        invalid_dates = []
        for i, record in enumerate(assets_data):
            date_val = record.get('purchase_date', '')
            if not iso_pattern.match(str(date_val)):
                invalid_dates.append((i, record.get('id'), date_val))

        assert len(invalid_dates) == 0, (
            f"Found {len(invalid_dates)} records with invalid ISO 8601 dates: "
            f"{invalid_dates[:5]}{'...' if len(invalid_dates) > 5 else ''}"
        )

    def test_all_price_cents_are_positive_integers(self, assets_data):
        """All price_cents values must be positive integers."""
        invalid_prices = []
        for i, record in enumerate(assets_data):
            price = record.get('price_cents')
            if not isinstance(price, int) or price <= 0:
                invalid_prices.append((i, record.get('id'), price))

        assert len(invalid_prices) == 0, (
            f"Found {len(invalid_prices)} records with invalid price_cents: "
            f"{invalid_prices[:5]}{'...' if len(invalid_prices) > 5 else ''}"
        )

    def test_no_duplicate_ids(self, assets_data):
        """There must be no duplicate id values in assets.json."""
        ids = [record.get('id') for record in assets_data]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), (
            f"Found duplicate IDs: {len(ids)} total, {len(unique_ids)} unique"
        )


class TestSpecificRecords:
    """Test specific records mentioned in the truth value."""

    @pytest.fixture
    def assets_data(self):
        """Load the assets.json file."""
        path = "/home/user/inventory/assets.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @pytest.fixture
    def assets_by_id(self, assets_data):
        """Create a lookup dict by id."""
        return {record['id']: record for record in assets_data}

    def test_ast_00142_record(self, assets_by_id):
        """AST-00142 should have correct purchase_date, price_cents, and serial."""
        record = assets_by_id.get('AST-00142')
        assert record is not None, "AST-00142 not found in assets.json"
        assert record['purchase_date'] == '2019-03-15', (
            f"AST-00142 purchase_date should be '2019-03-15', got '{record['purchase_date']}'"
        )
        assert record['price_cents'] == 234599, (
            f"AST-00142 price_cents should be 234599, got {record['price_cents']}"
        )
        assert record['serial'] == 'SN-KVM-00142', (
            f"AST-00142 serial should be 'SN-KVM-00142', got '{record['serial']}'"
        )

    def test_ast_00847_record(self, assets_by_id):
        """AST-00847 should have correct purchase_date, price_cents, and name."""
        record = assets_by_id.get('AST-00847')
        assert record is not None, "AST-00847 not found in assets.json"
        assert record['purchase_date'] == '2023-11-28', (
            f"AST-00847 purchase_date should be '2023-11-28', got '{record['purchase_date']}'"
        )
        assert record['price_cents'] == 89900, (
            f"AST-00847 price_cents should be 89900, got {record['price_cents']}"
        )
        assert record['name'] == 'Standing Desk Pro', (
            f"AST-00847 name should be 'Standing Desk Pro', got '{record['name']}'"
        )

    def test_ast_00333_duplicate_resolution(self, assets_by_id):
        """AST-00333 (duplicate case) should have only one record with later date."""
        record = assets_by_id.get('AST-00333')
        assert record is not None, "AST-00333 not found in assets.json"
        assert record['purchase_date'] == '2022-06-15', (
            f"AST-00333 should have the later date '2022-06-15', got '{record['purchase_date']}'"
        )


class TestRejectedJson:
    """Test the rejected.json file."""

    @pytest.fixture
    def rejected_data(self):
        """Load the rejected.json file."""
        path = "/home/user/inventory/rejected.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_rejected_json_is_valid_json(self):
        """The rejected.json file must be valid JSON."""
        path = "/home/user/inventory/rejected.json"
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"rejected.json is not valid JSON: {e}")

    def test_rejected_json_is_array(self, rejected_data):
        """The rejected.json must contain an array at the top level."""
        assert isinstance(rejected_data, list), "rejected.json must be a JSON array"

    def test_rejected_json_has_14_records(self, rejected_data):
        """The rejected.json must contain exactly 14 records."""
        count = len(rejected_data)
        assert count == 14, f"Expected 14 records in rejected.json, found {count}"

    def test_rejected_records_have_required_keys(self, rejected_data):
        """Each rejected record must have original_row and reason keys."""
        for i, record in enumerate(rejected_data):
            assert 'original_row' in record, f"Rejected record {i} missing 'original_row' key"
            assert 'reason' in record, f"Rejected record {i} missing 'reason' key"

    def test_rejected_original_row_is_string(self, rejected_data):
        """Each original_row must be a string."""
        for i, record in enumerate(rejected_data):
            assert isinstance(record.get('original_row'), str), (
                f"Rejected record {i} original_row is not a string"
            )

    def test_rejected_reason_is_string(self, rejected_data):
        """Each reason must be a string."""
        for i, record in enumerate(rejected_data):
            assert isinstance(record.get('reason'), str), (
                f"Rejected record {i} reason is not a string"
            )


class TestAntiShortcutGuards:
    """Run the anti-shortcut validation commands from the truth value."""

    def test_price_cents_validation(self):
        """All price_cents must be positive integers."""
        cmd = [
            'python3', '-c',
            "import json; d=json.load(open('/home/user/inventory/assets.json')); "
            "assert all(isinstance(r['price_cents'], int) and r['price_cents'] > 0 for r in d)"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"price_cents validation failed: {result.stderr}"
        )

    def test_purchase_date_iso8601_validation(self):
        """All purchase_date values must match ISO 8601 format."""
        cmd = [
            'python3', '-c',
            "import json,re; d=json.load(open('/home/user/inventory/assets.json')); "
            "assert all(re.match(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$', r['purchase_date']) for r in d)"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"purchase_date ISO 8601 validation failed: {result.stderr}"
        )

    def test_no_duplicate_ids_validation(self):
        """No duplicate IDs in assets.json."""
        cmd = [
            'python3', '-c',
            "import json; d=json.load(open('/home/user/inventory/assets.json')); "
            "ids=[r['id'] for r in d]; assert len(ids)==len(set(ids))"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Duplicate ID validation failed: {result.stderr}"
        )

    def test_assets_count_validation(self):
        """assets.json must have exactly 813 records."""
        cmd = [
            'python3', '-c',
            "import json; d=json.load(open('/home/user/inventory/assets.json')); "
            "assert len(d)==813"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Assets count validation failed (expected 813): {result.stderr}"
        )

    def test_rejected_validation(self):
        """rejected.json must have 14 records with required keys."""
        cmd = [
            'python3', '-c',
            "import json; d=json.load(open('/home/user/inventory/rejected.json')); "
            "assert len(d)==14 and all('original_row' in r and 'reason' in r for r in d)"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Rejected validation failed: {result.stderr}"
        )


class TestSwappedColumnsFixed:
    """Test that rows with swapped serial/name columns were corrected."""

    @pytest.fixture
    def assets_data(self):
        """Load the assets.json file."""
        path = "/home/user/inventory/assets.json"
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_serial_fields_match_pattern(self, assets_data):
        """All serial fields should match the SN-XXX-##### pattern."""
        serial_pattern = re.compile(r'^SN-[A-Z]{3}-\d{5}$')
        invalid_serials = []
        for record in assets_data:
            serial = record.get('serial', '')
            if not serial_pattern.match(serial):
                invalid_serials.append((record.get('id'), serial))

        assert len(invalid_serials) == 0, (
            f"Found {len(invalid_serials)} records with invalid serial format: "
            f"{invalid_serials[:5]}{'...' if len(invalid_serials) > 5 else ''}"
        )

    def test_name_fields_do_not_match_serial_pattern(self, assets_data):
        """No name field should match the serial number pattern (swapped columns fixed)."""
        serial_pattern = re.compile(r'^SN-[A-Z]{3}-\d{5}$')
        swapped_names = []
        for record in assets_data:
            name = record.get('name', '')
            if serial_pattern.match(name):
                swapped_names.append((record.get('id'), name))

        assert len(swapped_names) == 0, (
            f"Found {len(swapped_names)} records where name looks like a serial (columns still swapped): "
            f"{swapped_names[:5]}{'...' if len(swapped_names) > 5 else ''}"
        )


class TestRecordAccounting:
    """Test that all records are properly accounted for."""

    def test_total_records_accounted(self):
        """Total records in assets.json + rejected.json + duplicates = 846 (all non-header rows)."""
        assets_path = "/home/user/inventory/assets.json"
        rejected_path = "/home/user/inventory/rejected.json"

        with open(assets_path, 'r', encoding='utf-8') as f:
            assets_data = json.load(f)
        with open(rejected_path, 'r', encoding='utf-8') as f:
            rejected_data = json.load(f)

        assets_count = len(assets_data)  # 813
        rejected_count = len(rejected_data)  # 14
        duplicates_removed = 19  # As per truth value

        total = assets_count + rejected_count + duplicates_removed
        expected_total = 846  # 847 rows - 1 header

        assert total == expected_total, (
            f"Record accounting mismatch: {assets_count} assets + {rejected_count} rejected + "
            f"{duplicates_removed} duplicates = {total}, expected {expected_total}"
        )
