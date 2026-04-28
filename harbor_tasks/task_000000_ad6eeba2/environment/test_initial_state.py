# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the CSV to JSON migration task.
"""

import os
import re
import subprocess
import pytest


class TestInventoryDirectoryExists:
    """Test that the inventory directory exists and is writable."""

    def test_inventory_directory_exists(self):
        """The /home/user/inventory/ directory must exist."""
        path = "/home/user/inventory"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_inventory_directory_is_writable(self):
        """The /home/user/inventory/ directory must be writable."""
        path = "/home/user/inventory"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestAssetsCSVExists:
    """Test that the source CSV file exists with expected structure."""

    def test_assets_csv_exists(self):
        """The /home/user/inventory/assets.csv file must exist."""
        path = "/home/user/inventory/assets.csv"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_assets_csv_is_readable(self):
        """The /home/user/inventory/assets.csv file must be readable."""
        path = "/home/user/inventory/assets.csv"
        assert os.access(path, os.R_OK), f"File {path} is not readable"

    def test_assets_csv_has_847_rows(self):
        """The assets.csv file must have exactly 847 rows (including header)."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            # Count lines, handling potential malformed CSV
            lines = f.readlines()
            line_count = len(lines)
        assert line_count == 847, f"Expected 847 rows in {path}, found {line_count}"

    def test_assets_csv_has_correct_header(self):
        """The assets.csv file must have the correct header line."""
        path = "/home/user/inventory/assets.csv"
        expected_header = "id,name,serial,purchase_date,price,location"
        with open(path, 'r', encoding='utf-8') as f:
            header = f.readline().strip()
        assert header == expected_header, (
            f"Expected header '{expected_header}' in {path}, found '{header}'"
        )


class TestCSVDataQuality:
    """Test that the CSV has the expected data quality issues."""

    @pytest.fixture
    def csv_content(self):
        """Load the CSV content for analysis."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    @pytest.fixture
    def csv_lines(self, csv_content):
        """Get CSV lines excluding header."""
        lines = csv_content.split('\n')
        return [l for l in lines[1:] if l.strip()]  # Skip header, ignore empty

    def test_has_mm_dd_yyyy_dates(self, csv_content):
        """CSV should contain MM/DD/YYYY format dates."""
        # Pattern for MM/DD/YYYY (e.g., 03/15/2019)
        pattern = r'\d{2}/\d{2}/\d{4}'
        matches = re.findall(pattern, csv_content)
        assert len(matches) > 0, "Expected MM/DD/YYYY format dates in CSV, found none"

    def test_has_yyyy_mm_dd_dates(self, csv_content):
        """CSV should contain YYYY-MM-DD format dates."""
        # Pattern for YYYY-MM-DD (e.g., 2019-03-15)
        pattern = r'\d{4}-\d{2}-\d{2}'
        matches = re.findall(pattern, csv_content)
        assert len(matches) > 0, "Expected YYYY-MM-DD format dates in CSV, found none"

    def test_has_dd_mm_yyyy_dates(self, csv_content):
        """CSV should contain DD.MM.YYYY format dates (European)."""
        # Pattern for DD.MM.YYYY (e.g., 15.03.2019)
        pattern = r'\d{2}\.\d{2}\.\d{4}'
        matches = re.findall(pattern, csv_content)
        assert len(matches) > 0, "Expected DD.MM.YYYY format dates in CSV, found none"

    def test_has_dollar_sign_prices(self, csv_content):
        """CSV should contain prices with dollar signs."""
        # Pattern for prices like $1,234.56
        pattern = r'\$[\d,]+\.?\d*'
        matches = re.findall(pattern, csv_content)
        assert len(matches) > 0, "Expected prices with dollar signs in CSV, found none"

    def test_has_serial_number_pattern(self, csv_content):
        """CSV should contain serial numbers matching SN-[A-Z]{3}-[0-9]{5} pattern."""
        # Pattern for serial numbers
        pattern = r'SN-[A-Z]{3}-\d{5}'
        matches = re.findall(pattern, csv_content)
        assert len(matches) > 0, "Expected serial numbers matching SN-XXX-##### pattern, found none"

    def test_has_asset_ids(self, csv_content):
        """CSV should contain asset IDs."""
        # Pattern for asset IDs like AST-00142
        pattern = r'AST-\d{5}'
        matches = re.findall(pattern, csv_content)
        assert len(matches) > 0, "Expected asset IDs matching AST-##### pattern, found none"


class TestPythonAvailable:
    """Test that Python 3.11 is available."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ['python3', '--version'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"

    def test_python3_version_is_3_11(self):
        """Python version should be 3.11.x."""
        result = subprocess.run(
            ['python3', '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Could not determine Python version"
        version = result.stdout.strip()
        assert version.startswith("3."), f"Expected Python 3.x, got {version}"

    def test_python_json_module_available(self):
        """Python json module must be available (stdlib)."""
        result = subprocess.run(
            ['python3', '-c', 'import json'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python json module is not available"

    def test_python_csv_module_available(self):
        """Python csv module must be available (stdlib)."""
        result = subprocess.run(
            ['python3', '-c', 'import csv'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python csv module is not available"

    def test_python_re_module_available(self):
        """Python re module must be available (stdlib)."""
        result = subprocess.run(
            ['python3', '-c', 'import re'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python re module is not available"

    def test_python_datetime_module_available(self):
        """Python datetime module must be available (stdlib)."""
        result = subprocess.run(
            ['python3', '-c', 'from datetime import datetime'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python datetime module is not available"


class TestExternalToolsNotAvailable:
    """Test that certain external tools are NOT pre-installed."""

    def test_jq_not_installed(self):
        """jq should NOT be pre-installed."""
        result = subprocess.run(
            ['which', 'jq'],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "jq is pre-installed but should not be"

    def test_csvtool_not_installed(self):
        """csvtool should NOT be pre-installed."""
        result = subprocess.run(
            ['which', 'csvtool'],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "csvtool is pre-installed but should not be"


class TestOutputFilesDoNotExist:
    """Test that output files do not exist yet (clean initial state)."""

    def test_assets_json_does_not_exist(self):
        """The output file /home/user/inventory/assets.json should NOT exist yet."""
        path = "/home/user/inventory/assets.json"
        assert not os.path.exists(path), f"Output file {path} already exists but should not"

    def test_rejected_json_does_not_exist(self):
        """The output file /home/user/inventory/rejected.json should NOT exist yet."""
        path = "/home/user/inventory/rejected.json"
        assert not os.path.exists(path), f"Output file {path} already exists but should not"


class TestSpecificRecordsExist:
    """Test that specific records mentioned in the truth value exist in the CSV."""

    def test_ast_00142_exists(self):
        """Asset AST-00142 should exist in the CSV."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        assert 'AST-00142' in content, "Asset AST-00142 not found in CSV"

    def test_ast_00847_exists(self):
        """Asset AST-00847 should exist in the CSV."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        assert 'AST-00847' in content, "Asset AST-00847 not found in CSV"

    def test_ast_00333_exists(self):
        """Asset AST-00333 (duplicate case) should exist in the CSV."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        assert 'AST-00333' in content, "Asset AST-00333 not found in CSV"

    def test_sn_kvm_00142_exists(self):
        """Serial number SN-KVM-00142 should exist in the CSV."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        assert 'SN-KVM-00142' in content, "Serial number SN-KVM-00142 not found in CSV"

    def test_standing_desk_pro_exists(self):
        """Product name 'Standing Desk Pro' should exist in the CSV."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        assert 'Standing Desk Pro' in content, "Product 'Standing Desk Pro' not found in CSV"


class TestDuplicateIDsExist:
    """Test that duplicate asset IDs exist in the CSV as expected."""

    def test_duplicate_ids_present(self):
        """There should be duplicate asset IDs in the CSV (19 duplicate pairs = 38 rows)."""
        path = "/home/user/inventory/assets.csv"
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Find all AST-##### patterns
        pattern = r'AST-\d{5}'
        matches = re.findall(pattern, content)

        # Count occurrences
        from collections import Counter
        counts = Counter(matches)

        # Find IDs that appear more than once
        duplicates = {k: v for k, v in counts.items() if v > 1}

        assert len(duplicates) > 0, "Expected duplicate asset IDs in CSV, found none"
        assert len(duplicates) >= 19, f"Expected at least 19 duplicate asset IDs, found {len(duplicates)}"
