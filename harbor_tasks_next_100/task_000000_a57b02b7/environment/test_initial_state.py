# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the API key rotation task.
"""

import os
import csv
import pytest
import subprocess


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
    """Tests for the config.yaml file existence and properties."""

    def test_config_file_exists(self):
        """Verify that /home/user/services/config.yaml exists."""
        assert os.path.exists(CONFIG_FILE), (
            f"Config file {CONFIG_FILE} does not exist. "
            "The task requires this file to be present."
        )

    def test_config_file_is_file(self):
        """Verify that config.yaml is a regular file, not a directory."""
        assert os.path.isfile(CONFIG_FILE), (
            f"{CONFIG_FILE} exists but is not a regular file."
        )

    def test_config_file_is_readable(self):
        """Verify that config.yaml is readable."""
        assert os.access(CONFIG_FILE, os.R_OK), (
            f"{CONFIG_FILE} is not readable."
        )

    def test_config_file_is_writable(self):
        """Verify that config.yaml is writable."""
        assert os.access(CONFIG_FILE, os.W_OK), (
            f"{CONFIG_FILE} is not writable. The task requires write access."
        )


class TestConfigFileContent:
    """Tests for the content of config.yaml."""

    def test_config_file_is_valid_yaml(self):
        """Verify that config.yaml is valid YAML."""
        result = subprocess.run(
            ["python3", "-c", f"import yaml; yaml.safe_load(open('{CONFIG_FILE}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"{CONFIG_FILE} is not valid YAML. "
            f"Error: {result.stderr}"
        )

    def test_config_file_contains_12_api_keys(self):
        """Verify that config.yaml contains exactly 12 API keys."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        key_count = 0
        for old_key in OLD_KEYS:
            if old_key in content:
                key_count += 1

        assert key_count == 12, (
            f"Expected 12 old API keys in {CONFIG_FILE}, but found {key_count}. "
            f"Missing keys: {[k for k in OLD_KEYS if k not in content]}"
        )

    def test_config_file_contains_all_old_keys(self):
        """Verify that all 12 specific old keys are present."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        missing_keys = []
        for old_key in OLD_KEYS:
            if old_key not in content:
                missing_keys.append(old_key)

        assert not missing_keys, (
            f"The following old API keys are missing from {CONFIG_FILE}: {missing_keys}"
        )

    def test_config_file_has_api_key_pattern(self):
        """Verify that keys follow the api_key: \"sk_live_...\" pattern."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        import re
        pattern = r'api_key:\s*"sk_live_[^"]*"'
        matches = re.findall(pattern, content)

        assert len(matches) >= 12, (
            f"Expected at least 12 api_key entries with sk_live_ pattern, "
            f"but found {len(matches)}."
        )

    def test_config_file_approximately_80_lines(self):
        """Verify that config.yaml is approximately 80 lines."""
        with open(CONFIG_FILE, 'r') as f:
            lines = f.readlines()

        line_count = len(lines)
        # Allow some flexibility (60-100 lines)
        assert 60 <= line_count <= 100, (
            f"Expected config.yaml to be ~80 lines, but found {line_count} lines."
        )


class TestCsvFileExists:
    """Tests for the new_keys.csv file existence and properties."""

    def test_csv_directory_exists(self):
        """Verify that /home/user/rotation directory exists."""
        rotation_dir = "/home/user/rotation"
        assert os.path.exists(rotation_dir), (
            f"Directory {rotation_dir} does not exist."
        )

    def test_csv_file_exists(self):
        """Verify that /home/user/rotation/new_keys.csv exists."""
        assert os.path.exists(CSV_FILE), (
            f"CSV file {CSV_FILE} does not exist. "
            "The task requires this file for key mappings."
        )

    def test_csv_file_is_file(self):
        """Verify that new_keys.csv is a regular file."""
        assert os.path.isfile(CSV_FILE), (
            f"{CSV_FILE} exists but is not a regular file."
        )

    def test_csv_file_is_readable(self):
        """Verify that new_keys.csv is readable."""
        assert os.access(CSV_FILE, os.R_OK), (
            f"{CSV_FILE} is not readable."
        )


class TestCsvFileContent:
    """Tests for the content of new_keys.csv."""

    def test_csv_has_header(self):
        """Verify that new_keys.csv has the correct header."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            header = next(reader, None)

        assert header is not None, f"{CSV_FILE} is empty."
        assert header == ["old_key", "new_key"], (
            f"Expected header ['old_key', 'new_key'], but got {header}"
        )

    def test_csv_has_12_mappings(self):
        """Verify that new_keys.csv contains exactly 12 key mappings."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = list(reader)

        assert len(rows) == 12, (
            f"Expected 12 key mappings in {CSV_FILE}, but found {len(rows)}."
        )

    def test_csv_contains_correct_mappings(self):
        """Verify that new_keys.csv contains all expected mappings."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            rows = [(row[0], row[1]) for row in reader]

        for expected_old, expected_new in EXPECTED_CSV_MAPPINGS:
            found = False
            for old, new in rows:
                if old == expected_old and new == expected_new:
                    found = True
                    break
            assert found, (
                f"Expected mapping ({expected_old} -> {expected_new}) "
                f"not found in {CSV_FILE}"
            )

    def test_csv_old_keys_match_config_keys(self):
        """Verify that old_key values in CSV match keys in config.yaml."""
        with open(CSV_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            csv_old_keys = [row[0] for row in reader]

        assert set(csv_old_keys) == set(OLD_KEYS), (
            f"Old keys in CSV don't match expected old keys. "
            f"CSV keys: {sorted(csv_old_keys)}, "
            f"Expected: {sorted(OLD_KEYS)}"
        )


class TestRequiredTools:
    """Tests for required tools availability."""

    def test_sed_available(self):
        """Verify that sed is available."""
        result = subprocess.run(["which", "sed"], capture_output=True)
        assert result.returncode == 0, "sed is not available on this system."

    def test_awk_available(self):
        """Verify that awk is available."""
        result = subprocess.run(["which", "awk"], capture_output=True)
        assert result.returncode == 0, "awk is not available on this system."

    def test_python3_available(self):
        """Verify that python3 is available."""
        result = subprocess.run(["which", "python3"], capture_output=True)
        assert result.returncode == 0, "python3 is not available on this system."

    def test_perl_available(self):
        """Verify that perl is available."""
        result = subprocess.run(["which", "perl"], capture_output=True)
        assert result.returncode == 0, "perl is not available on this system."


class TestNoNewKeysYet:
    """Tests to verify new keys are NOT yet in the config file."""

    def test_no_new_keys_in_config(self):
        """Verify that none of the new keys are in config.yaml yet."""
        with open(CONFIG_FILE, 'r') as f:
            content = f.read()

        new_keys_found = []
        for _, new_key in EXPECTED_CSV_MAPPINGS:
            if new_key in content:
                new_keys_found.append(new_key)

        assert not new_keys_found, (
            f"New keys should not be in {CONFIG_FILE} yet (initial state). "
            f"Found: {new_keys_found}"
        )

    def test_no_new_pattern_keys_in_config(self):
        """Verify that no sk_live_NEW_ pattern keys exist in config yet."""
        result = subprocess.run(
            ["grep", "-c", "sk_live_NEW_", CONFIG_FILE],
            capture_output=True,
            text=True
        )
        # grep returns 1 if no matches found, which is what we want
        count = int(result.stdout.strip()) if result.returncode == 0 else 0
        assert count == 0, (
            f"Expected 0 new-format keys (sk_live_NEW_) in {CONFIG_FILE}, "
            f"but found {count}. Initial state should have only old keys."
        )
