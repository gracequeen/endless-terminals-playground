# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the vulnerability scanner config update task.
"""

import os
import pytest
import yaml


class TestInitialState:
    """Test suite to verify the initial state before the task is performed."""

    SCANNER_DIR = "/home/user/scanner"
    CONFIG_FILE = "/home/user/scanner/scan.yaml"

    def test_scanner_directory_exists(self):
        """Verify that the scanner directory exists."""
        assert os.path.isdir(self.SCANNER_DIR), (
            f"Scanner directory '{self.SCANNER_DIR}' does not exist. "
            "The directory must be present before performing the task."
        )

    def test_scanner_directory_is_writable(self):
        """Verify that the scanner directory is writable."""
        assert os.access(self.SCANNER_DIR, os.W_OK), (
            f"Scanner directory '{self.SCANNER_DIR}' is not writable. "
            "The agent needs write access to modify the config file."
        )

    def test_config_file_exists(self):
        """Verify that the scan.yaml config file exists."""
        assert os.path.isfile(self.CONFIG_FILE), (
            f"Config file '{self.CONFIG_FILE}' does not exist. "
            "The scan.yaml file must be present before performing the task."
        )

    def test_config_file_is_readable(self):
        """Verify that the config file is readable."""
        assert os.access(self.CONFIG_FILE, os.R_OK), (
            f"Config file '{self.CONFIG_FILE}' is not readable. "
            "The agent needs read access to view the current configuration."
        )

    def test_config_file_is_writable(self):
        """Verify that the config file is writable."""
        assert os.access(self.CONFIG_FILE, os.W_OK), (
            f"Config file '{self.CONFIG_FILE}' is not writable. "
            "The agent needs write access to modify the configuration."
        )

    def test_config_file_is_valid_yaml(self):
        """Verify that the config file contains valid YAML."""
        with open(self.CONFIG_FILE, 'r') as f:
            try:
                content = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(
                    f"Config file '{self.CONFIG_FILE}' is not valid YAML: {e}"
                )
        assert content is not None, (
            f"Config file '{self.CONFIG_FILE}' is empty or contains only null."
        )

    def test_config_has_scanner_section(self):
        """Verify that the config has the scanner section."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        assert 'scanner' in content, (
            f"Config file '{self.CONFIG_FILE}' is missing the 'scanner' section."
        )
        assert content['scanner'].get('name') == 'edge-node-scan', (
            f"Config file '{self.CONFIG_FILE}' has unexpected scanner name. "
            f"Expected 'edge-node-scan', got '{content['scanner'].get('name')}'."
        )
        assert content['scanner'].get('version') == 2.1, (
            f"Config file '{self.CONFIG_FILE}' has unexpected scanner version. "
            f"Expected 2.1, got '{content['scanner'].get('version')}'."
        )

    def test_config_has_targets_section(self):
        """Verify that the config has the targets section."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        assert 'targets' in content, (
            f"Config file '{self.CONFIG_FILE}' is missing the 'targets' section."
        )

    def test_config_has_wrong_subnet(self):
        """Verify that the config currently has the wrong subnet (10.0.1.0/24)."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        network = content.get('targets', {}).get('network')
        assert network == '10.0.1.0/24', (
            f"Config file '{self.CONFIG_FILE}' should have network '10.0.1.0/24' "
            f"in initial state, but found '{network}'. "
            "This is the value that needs to be changed to '10.0.2.0/24'."
        )

    def test_config_has_expected_ports(self):
        """Verify that the config has the expected ports configuration."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        ports = content.get('targets', {}).get('ports')
        assert ports == [22, 443, 8883], (
            f"Config file '{self.CONFIG_FILE}' has unexpected ports. "
            f"Expected [22, 443, 8883], got {ports}."
        )

    def test_config_has_expected_protocol(self):
        """Verify that the config has the expected protocol configuration."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        protocol = content.get('targets', {}).get('protocol')
        assert protocol == 'tcp', (
            f"Config file '{self.CONFIG_FILE}' has unexpected protocol. "
            f"Expected 'tcp', got '{protocol}'."
        )

    def test_config_has_options_section(self):
        """Verify that the config has the options section with expected values."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        assert 'options' in content, (
            f"Config file '{self.CONFIG_FILE}' is missing the 'options' section."
        )

        options = content['options']
        assert options.get('timeout') == 30, (
            f"Config file '{self.CONFIG_FILE}' has unexpected timeout. "
            f"Expected 30, got {options.get('timeout')}."
        )
        assert options.get('retries') == 3, (
            f"Config file '{self.CONFIG_FILE}' has unexpected retries. "
            f"Expected 3, got {options.get('retries')}."
        )
        assert options.get('verbose') is False, (
            f"Config file '{self.CONFIG_FILE}' has unexpected verbose setting. "
            f"Expected false, got {options.get('verbose')}."
        )

    def test_raw_content_contains_wrong_subnet(self):
        """Verify that the raw file content contains the wrong subnet string."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = f.read()

        assert '10.0.1.0/24' in content, (
            f"Config file '{self.CONFIG_FILE}' does not contain '10.0.1.0/24' "
            "in its raw content. This is the subnet that needs to be replaced."
        )

    def test_raw_content_does_not_contain_correct_subnet(self):
        """Verify that the raw file content does NOT yet contain the correct subnet."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = f.read()

        assert '10.0.2.0/24' not in content, (
            f"Config file '{self.CONFIG_FILE}' already contains '10.0.2.0/24'. "
            "The task has not been completed yet, so this should not be present."
        )
