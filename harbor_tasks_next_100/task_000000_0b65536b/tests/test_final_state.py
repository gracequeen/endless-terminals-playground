# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the vulnerability scanner config update task.

The task was to change the network subnet from 10.0.1.0/24 to 10.0.2.0/24
in /home/user/scanner/scan.yaml while keeping all other configuration intact.
"""

import os
import subprocess
import pytest
import yaml


class TestFinalState:
    """Test suite to verify the final state after the task is performed."""

    SCANNER_DIR = "/home/user/scanner"
    CONFIG_FILE = "/home/user/scanner/scan.yaml"

    def test_config_file_still_exists(self):
        """Verify that the scan.yaml config file still exists at the same location."""
        assert os.path.isfile(self.CONFIG_FILE), (
            f"Config file '{self.CONFIG_FILE}' does not exist. "
            "The file should remain at the same location after the edit."
        )

    def test_config_file_is_valid_yaml(self):
        """Verify that the config file still contains valid YAML after editing."""
        with open(self.CONFIG_FILE, 'r') as f:
            try:
                content = yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(
                    f"Config file '{self.CONFIG_FILE}' is not valid YAML after editing: {e}"
                )
        assert content is not None, (
            f"Config file '{self.CONFIG_FILE}' is empty or contains only null."
        )

    def test_config_has_correct_subnet(self):
        """Verify that the config now has the correct subnet (10.0.2.0/24)."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        network = content.get('targets', {}).get('network')
        assert network == '10.0.2.0/24', (
            f"Config file '{self.CONFIG_FILE}' should have network '10.0.2.0/24' "
            f"after the task is completed, but found '{network}'. "
            "The subnet was not correctly updated."
        )

    def test_raw_content_contains_correct_subnet(self):
        """Verify that the raw file content contains the correct subnet string."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = f.read()

        assert '10.0.2.0/24' in content, (
            f"Config file '{self.CONFIG_FILE}' does not contain '10.0.2.0/24' "
            "in its raw content. The subnet replacement was not performed."
        )

    def test_raw_content_does_not_contain_old_subnet(self):
        """Verify that the raw file content no longer contains the old subnet."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = f.read()

        assert '10.0.1.0/24' not in content, (
            f"Config file '{self.CONFIG_FILE}' still contains '10.0.1.0/24'. "
            "The old subnet should have been replaced with '10.0.2.0/24'."
        )

    def test_grep_finds_new_subnet(self):
        """Verify using grep that the new subnet is present."""
        result = subprocess.run(
            ['grep', '-E', r'10\.0\.2\.0/24', self.CONFIG_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"grep for '10.0.2.0/24' in '{self.CONFIG_FILE}' did not find a match. "
            "The new subnet should be present in the config file."
        )

    def test_grep_does_not_find_old_subnet(self):
        """Verify using grep that the old subnet is no longer present."""
        result = subprocess.run(
            ['grep', '-E', r'10\.0\.1\.0/24', self.CONFIG_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, (
            f"grep for '10.0.1.0/24' in '{self.CONFIG_FILE}' found a match. "
            "The old subnet should have been removed from the config file."
        )

    def test_scanner_name_unchanged(self):
        """Verify that the scanner name remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        name = content.get('scanner', {}).get('name')
        assert name == 'edge-node-scan', (
            f"Scanner name should remain 'edge-node-scan', but found '{name}'. "
            "Only the network subnet should have been changed."
        )

    def test_scanner_version_unchanged(self):
        """Verify that the scanner version remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        version = content.get('scanner', {}).get('version')
        assert version == 2.1, (
            f"Scanner version should remain 2.1, but found '{version}'. "
            "Only the network subnet should have been changed."
        )

    def test_ports_unchanged(self):
        """Verify that the ports configuration remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        ports = content.get('targets', {}).get('ports')
        assert ports == [22, 443, 8883], (
            f"Ports should remain [22, 443, 8883], but found {ports}. "
            "Only the network subnet should have been changed."
        )

    def test_protocol_unchanged(self):
        """Verify that the protocol configuration remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        protocol = content.get('targets', {}).get('protocol')
        assert protocol == 'tcp', (
            f"Protocol should remain 'tcp', but found '{protocol}'. "
            "Only the network subnet should have been changed."
        )

    def test_timeout_unchanged(self):
        """Verify that the timeout option remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        timeout = content.get('options', {}).get('timeout')
        assert timeout == 30, (
            f"Timeout should remain 30, but found {timeout}. "
            "Only the network subnet should have been changed."
        )

    def test_retries_unchanged(self):
        """Verify that the retries option remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        retries = content.get('options', {}).get('retries')
        assert retries == 3, (
            f"Retries should remain 3, but found {retries}. "
            "Only the network subnet should have been changed."
        )

    def test_verbose_unchanged(self):
        """Verify that the verbose option remains unchanged."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        verbose = content.get('options', {}).get('verbose')
        assert verbose is False, (
            f"Verbose should remain False, but found {verbose}. "
            "Only the network subnet should have been changed."
        )

    def test_all_sections_present(self):
        """Verify that all original sections are still present."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        required_sections = ['scanner', 'targets', 'options']
        for section in required_sections:
            assert section in content, (
                f"Section '{section}' is missing from the config file. "
                "All original sections should be preserved."
            )

    def test_targets_section_complete(self):
        """Verify that the targets section has all required fields."""
        with open(self.CONFIG_FILE, 'r') as f:
            content = yaml.safe_load(f)

        targets = content.get('targets', {})
        required_fields = ['network', 'ports', 'protocol']
        for field in required_fields:
            assert field in targets, (
                f"Field '{field}' is missing from the targets section. "
                "All original fields should be preserved."
            )
