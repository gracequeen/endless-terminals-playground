# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the API key rotation task.
"""

import os
import csv
import pytest
import subprocess
import re


# Constants
CONFIG_FILE = "/home/user/services/config.yaml"
CSV_FILE = "/home/user/rotation/new_keys.csv"

OLD_KEYS = [
    "sk_live_a1b2c3d4e5f6",
    "sk_live_g7h8i9j0k1l2",
    "sk_live_m3n4o5p6q7r8",
    "sk_live_s9t0u1v2w3x4",
    "sk_live_y5z6a7b8c9d0",
    "sk_live_e1f2g3h4i5j6",
    "sk_live_k7l8m9n0o1p2",
    "sk_live_q3r4s5t6u7v8",
    "sk_live_w9x0y1z2a3b4",
    "sk_live_c5d6e7f8g9h0",
    "sk_live_i1j2k3l4m5n6",
    "sk_live_o7p8q9r0s1t2",
]

NEW_KEYS = [
    "sk_live_NEW_001_xyz",
    "sk_live_NEW_002_xyz",
    "sk_live_NEW_003_xyz",
    "sk_live_NEW_004_xyz",
    "sk_live_NEW_005_xyz",
    "sk_live_NEW_006_xyz",
    "sk_live_NEW_007_xyz",
    "sk_live_NEW_008_xyz",
    "sk_live_NEW_009_xyz",
    "sk_live_NEW_010_xyz",
    "sk_live_NEW_011_xyz",
    "sk_live_NEW_012_xyz",
]

EXPECTED_CSV_MAPPINGS = [
    ("sk_live_a1b2c3d4e5f6", "sk_live_NEW_001_xyz"),
    ("sk_live_g7h8i9j0k1l2", "sk_live_NEW_002_xyz"),
    ("sk_live_m3n4o5p6q7r8", "sk_live_NEW_003_xyz"),
    ("sk_live_s9t0u1v2w3x4", "sk_live_NEW_004_xyz"),
    ("sk_live_y5z6a7b8c9d0", "sk_live_NEW_005_xyz"),
    ("sk_live_e1f2g3h4i5j6", "sk_live_NEW_006_xyz"),
    ("sk_live_k7l8m9n0o1p2", "sk_live_NEW_007_xyz"),
    ("sk_live_q3r4s5t6u7v8", "sk_live_NEW_008_xyz"),
    ("sk_live_w9x0y1z2a3b4", "sk_live_NEW_009_xyz"),
    ("sk_live_c5d6e7f8g9h0", "sk_live_NEW_010_xyz"),
    ("sk_live_i1j2k3l4m5n6", "sk_live_NEW_011_xyz"),
    ("sk_live_o7p8q9r0s1t2", "sk_live_NEW_012_xyz"),
]


class TestConfigFileExists:
    """Tests for the config.yaml file existence after task completion."""

    def test_config_file_exists(self):
        """Verify that /home/user/services/config.yaml still exists."""
        assert os.path.exists(CONFIG_FILE), (
            f"Config file {CONFIG_FILE} does not exist. "
            "The file should still be present after key rotation."
        )

    def test_config_file_is_file(self):
        """Verify that config.yaml is a regular file."""
        assert os.path.isfile(CONFIG_FILE), (
            f"{CONFIG_FILE} exists but is not a regular file."
        )


class TestAllNewKeysPresent:
    """Tests to verify all new keys are present in the config file."""

    def test_config_contains_all_new_keys(self):
        """Verify that all 12 new keys are present in config.yaml."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        missing_keys = []
        for new_key in NEW_KEYS:
            if new_key not in content:
                missing_keys.append(new_key)

        assert not missing_keys, (
            f"The following new API keys are missing from {CONFIG_FILE}: {missing_keys}. "
            "All 12 new keys should be present after rotation."
        )

    def test_exactly_12_new_keys_present(self):
        """Verify that exactly 12 new-format keys are in config.yaml."""
        result = subprocess.run(
            ["grep", "-c", "sk_live_NEW_", CONFIG_FILE],
            capture_output=True,
            text=True
        )

        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 12, (
            f"Expected exactly 12 new-format keys (sk_live_NEW_) in {CONFIG_FILE}, "
            f"but found {count}."
        )


class TestNoOldKeysRemain:
    """Tests to verify no old keys remain in the config file."""

    def test_no_old_keys_in_config(self):
        """Verify that none of the 12 old keys remain in config.yaml."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        remaining_old_keys = []
        for old_key in OLD_KEYS:
            if old_key in content:
                remaining_old_keys.append(old_key)

        assert not remaining_old_keys, (
            f"The following old API keys still remain in {CONFIG_FILE}: {remaining_old_keys}. "
            "All old keys should have been replaced with new ones."
        )

    def test_no_old_format_keys_remain(self):
        """Verify that no old-format keys (12 lowercase alphanumeric chars) remain."""
        # Pattern for old keys: sk_live_ followed by exactly 12 lowercase alphanumeric chars
        # This matches the old format but not the new format (which has NEW_ and _xyz)
        result = subprocess.run(
            ["grep", "-cE", r"sk_live_[a-z0-9]{12}[^_]|sk_live_[a-z0-9]{12}$", CONFIG_FILE],
            capture_output=True,
            text=True
        )

        # Alternative approach: check each old key pattern directly
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        # Check for old-style keys that are exactly 12 chars after sk_live_
        old_pattern = re.compile(r'sk_live_[a-z][0-9][a-z][0-9][a-z][0-9][a-z][0-9][a-z][0-9][a-z][0-9]')
        matches = old_pattern.findall(content)

        # Filter out any that might be new keys (contain NEW)
        old_matches = [m for m in matches if 'NEW' not in m]

        assert len(old_matches) == 0, (
            f"Found {len(old_matches)} old-format keys still in {CONFIG_FILE}: {old_matches}. "
            "All old keys should have been replaced."
        )


class TestYamlValidity:
    """Tests to verify the config file remains valid YAML."""

    def test_config_is_valid_yaml(self):
        """Verify that config.yaml is still valid YAML after modifications."""
        result = subprocess.run(
            ["python3", "-c", f"import yaml; yaml.safe_load(open('{CONFIG_FILE}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"{CONFIG_FILE} is not valid YAML after key rotation. "
            f"Error: {result.stderr}. "
            "The file structure should remain intact after replacing keys."
        )


class TestCsvFileUnchanged:
    """Tests to verify the CSV file was not modified."""

    def test_csv_file_exists(self):
        """Verify that new_keys.csv still exists."""
        assert os.path.exists(CSV_FILE), (
            f"CSV file {CSV_FILE} no longer exists. "
            "The mapping file should not be deleted."
        )

    def test_csv_has_correct_header(self):
        """Verify that new_keys.csv still has the correct header."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)

        assert header == ["old_key", "new_key"], (
            f"CSV header was modified. Expected ['old_key', 'new_key'], got {header}. "
            "The CSV file should remain unchanged."
        )

    def test_csv_has_12_mappings(self):
        """Verify that new_keys.csv still contains exactly 12 mappings."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

        assert len(rows) == 12, (
            f"CSV file was modified. Expected 12 mappings, found {len(rows)}. "
            "The CSV file should remain unchanged."
        )

    def test_csv_contains_original_mappings(self):
        """Verify that new_keys.csv contains all original mappings unchanged."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = [(row[0], row[1]) for row in reader if len(row) >= 2]

        for expected_old, expected_new in EXPECTED_CSV_MAPPINGS:
            found = (expected_old, expected_new) in rows
            assert found, (
                f"CSV mapping ({expected_old} -> {expected_new}) was modified or removed. "
                "The CSV file should remain unchanged."
            )


class TestApiKeyPattern:
    """Tests to verify the api_key pattern is maintained."""

    def test_api_key_pattern_preserved(self):
        """Verify that keys still follow the api_key: \"sk_live_...\" pattern."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        # Check that new keys appear in the expected pattern
        pattern = r'api_key:\s*"sk_live_NEW_\d{3}_xyz"'
        matches = re.findall(pattern, content)

        assert len(matches) == 12, (
            f"Expected 12 api_key entries with new key pattern, but found {len(matches)}. "
            "Keys should be in the format: api_key: \"sk_live_NEW_XXX_xyz\""
        )


class TestKeyCountConsistency:
    """Tests for overall key count consistency."""

    def test_total_sk_live_keys_is_12(self):
        """Verify that there are exactly 12 sk_live_ keys total."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        # Count all sk_live_ occurrences in quoted strings
        pattern = r'"sk_live_[^"]*"'
        matches = re.findall(pattern, content)

        assert len(matches) == 12, (
            f"Expected exactly 12 sk_live_ keys in {CONFIG_FILE}, but found {len(matches)}. "
            f"Keys found: {matches}"
        )

    def test_each_new_key_appears_exactly_once(self):
        """Verify that each new key appears exactly once."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        for new_key in NEW_KEYS:
            count = content.count(new_key)
            assert count == 1, (
                f"New key {new_key} appears {count} times in {CONFIG_FILE}. "
                "Each new key should appear exactly once."
            )
