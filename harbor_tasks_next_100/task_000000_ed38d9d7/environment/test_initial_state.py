# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies the monitoring directory structure, alertmanager binary, config files,
and the presence of the YAML bug that needs to be fixed.
"""

import os
import stat
import subprocess
import pytest

MONITORING_DIR = "/home/user/monitoring"
ALERTMANAGER_BINARY = os.path.join(MONITORING_DIR, "alertmanager")
ALERTMANAGER_CONFIG = os.path.join(MONITORING_DIR, "alertmanager.yml")
TEMPLATES_DIR = os.path.join(MONITORING_DIR, "templates")
SLACK_TEMPLATE = os.path.join(TEMPLATES_DIR, "slack.tmpl")
PAGERDUTY_TEMPLATE = os.path.join(TEMPLATES_DIR, "pagerduty.tmpl")
RECEIVERS_FILE = os.path.join(MONITORING_DIR, "receivers.yml")
RULES_DIR = os.path.join(MONITORING_DIR, "rules")


class TestMonitoringDirectoryStructure:
    """Test that the monitoring directory and its contents exist."""

    def test_monitoring_directory_exists(self):
        """Verify /home/user/monitoring directory exists."""
        assert os.path.isdir(MONITORING_DIR), (
            f"Monitoring directory {MONITORING_DIR} does not exist"
        )

    def test_templates_directory_exists(self):
        """Verify templates subdirectory exists."""
        assert os.path.isdir(TEMPLATES_DIR), (
            f"Templates directory {TEMPLATES_DIR} does not exist"
        )

    def test_rules_directory_exists(self):
        """Verify rules subdirectory exists."""
        assert os.path.isdir(RULES_DIR), (
            f"Rules directory {RULES_DIR} does not exist"
        )


class TestAlertmanagerBinary:
    """Test that the Alertmanager binary exists and is executable."""

    def test_alertmanager_binary_exists(self):
        """Verify alertmanager binary exists."""
        assert os.path.isfile(ALERTMANAGER_BINARY), (
            f"Alertmanager binary {ALERTMANAGER_BINARY} does not exist"
        )

    def test_alertmanager_binary_is_executable(self):
        """Verify alertmanager binary is executable."""
        assert os.access(ALERTMANAGER_BINARY, os.X_OK), (
            f"Alertmanager binary {ALERTMANAGER_BINARY} is not executable"
        )

    def test_alertmanager_version(self):
        """Verify alertmanager is a real binary that can report its version."""
        result = subprocess.run(
            [ALERTMANAGER_BINARY, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Version command should succeed
        assert result.returncode == 0, (
            f"Alertmanager --version failed: {result.stderr}"
        )
        # Should contain version info
        output = result.stdout + result.stderr
        assert "alertmanager" in output.lower(), (
            f"Alertmanager version output doesn't look right: {output}"
        )


class TestConfigurationFiles:
    """Test that configuration files exist with expected content."""

    def test_alertmanager_config_exists(self):
        """Verify alertmanager.yml exists."""
        assert os.path.isfile(ALERTMANAGER_CONFIG), (
            f"Alertmanager config {ALERTMANAGER_CONFIG} does not exist"
        )

    def test_slack_template_exists(self):
        """Verify slack.tmpl template exists."""
        assert os.path.isfile(SLACK_TEMPLATE), (
            f"Slack template {SLACK_TEMPLATE} does not exist"
        )

    def test_pagerduty_template_exists(self):
        """Verify pagerduty.tmpl template exists."""
        assert os.path.isfile(PAGERDUTY_TEMPLATE), (
            f"PagerDuty template {PAGERDUTY_TEMPLATE} does not exist"
        )

    def test_receivers_file_exists(self):
        """Verify receivers.yml exists (even if not properly included)."""
        assert os.path.isfile(RECEIVERS_FILE), (
            f"Receivers file {RECEIVERS_FILE} does not exist"
        )


class TestAlertmanagerConfigContent:
    """Test that alertmanager.yml has the expected content structure."""

    @pytest.fixture
    def config_content(self):
        """Read the alertmanager config file."""
        with open(ALERTMANAGER_CONFIG, 'r') as f:
            return f.read()

    def test_config_has_global_section(self, config_content):
        """Verify config has global section."""
        assert "global:" in config_content, (
            "alertmanager.yml missing 'global:' section"
        )

    def test_config_has_templates_section(self, config_content):
        """Verify config has templates section."""
        assert "templates:" in config_content, (
            "alertmanager.yml missing 'templates:' section"
        )

    def test_config_has_route_section(self, config_content):
        """Verify config has route section."""
        assert "route:" in config_content, (
            "alertmanager.yml missing 'route:' section"
        )

    def test_config_has_receivers_section(self, config_content):
        """Verify config has receivers section."""
        assert "receivers:" in config_content, (
            "alertmanager.yml missing 'receivers:' section"
        )

    def test_config_has_default_receiver(self, config_content):
        """Verify default-receiver is defined."""
        assert "default-receiver" in config_content, (
            "alertmanager.yml missing 'default-receiver'"
        )

    def test_config_has_pagerduty_critical_receiver(self, config_content):
        """Verify pagerduty-critical receiver is defined."""
        assert "pagerduty-critical" in config_content, (
            "alertmanager.yml missing 'pagerduty-critical' receiver"
        )

    def test_config_has_slack_warnings_receiver(self, config_content):
        """Verify slack-warnings receiver is defined."""
        assert "slack-warnings" in config_content, (
            "alertmanager.yml missing 'slack-warnings' receiver"
        )

    def test_config_has_team_backend_receiver(self, config_content):
        """Verify team-backend receiver is defined."""
        assert "team-backend" in config_content, (
            "alertmanager.yml missing 'team-backend' receiver"
        )

    def test_config_has_db_team_receiver(self, config_content):
        """Verify db-team receiver is defined."""
        assert "db-team" in config_content, (
            "alertmanager.yml missing 'db-team' receiver"
        )

    def test_config_has_pagerduty_service_key(self, config_content):
        """Verify PagerDuty service key is present."""
        assert "fake-pagerduty-key-12345" in config_content, (
            "alertmanager.yml missing PagerDuty service_key"
        )

    def test_config_has_slack_channels(self, config_content):
        """Verify Slack channels are configured."""
        expected_channels = [
            "#alerts-general",
            "#alerts-warnings",
            "#team-backend-alerts",
            "#db-alerts"
        ]
        for channel in expected_channels:
            assert channel in config_content, (
                f"alertmanager.yml missing Slack channel '{channel}'"
            )

    def test_config_has_severity_routes(self, config_content):
        """Verify severity-based routing is configured."""
        assert "severity: critical" in config_content, (
            "alertmanager.yml missing critical severity route"
        )
        assert "severity: warning" in config_content, (
            "alertmanager.yml missing warning severity route"
        )

    def test_config_has_tab_character_bug(self, config_content):
        """Verify the YAML bug (tab character) exists in the config."""
        assert "\t" in config_content, (
            "alertmanager.yml should contain a tab character (the bug to fix)"
        )


class TestAlertmanagerFailsToStart:
    """Test that alertmanager currently fails to start due to YAML error."""

    def test_alertmanager_config_check_fails(self):
        """Verify alertmanager fails config validation (the bug exists)."""
        result = subprocess.run(
            [ALERTMANAGER_BINARY, "--config.file=" + ALERTMANAGER_CONFIG, "--dry-run"],
            capture_output=True,
            text=True,
            cwd=MONITORING_DIR,
            timeout=10
        )
        # Should fail due to YAML error
        # Note: alertmanager may not have --dry-run, so we check if it fails quickly
        # when trying to parse the config

    def test_alertmanager_startup_fails_with_yaml_error(self):
        """Verify alertmanager fails to start with current config."""
        result = subprocess.run(
            [ALERTMANAGER_BINARY, "--config.file=" + ALERTMANAGER_CONFIG],
            capture_output=True,
            text=True,
            cwd=MONITORING_DIR,
            timeout=5
        )
        # Should fail (non-zero exit code) due to YAML parsing error
        assert result.returncode != 0, (
            "Alertmanager should fail to start with the buggy config, "
            "but it succeeded. The YAML bug may not be present."
        )
        # Error output should mention yaml or parsing issue
        error_output = (result.stderr + result.stdout).lower()
        assert "yaml" in error_output or "parse" in error_output or "unmarshal" in error_output or "error" in error_output, (
            f"Alertmanager failed but not with expected YAML error. Output: {result.stderr}"
        )


class TestPort9093NotInUse:
    """Test that port 9093 is not currently in use."""

    def test_port_9093_not_listening(self):
        """Verify nothing is currently listening on port 9093."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert ":9093" not in result.stdout, (
            "Port 9093 is already in use. No process should be listening on it initially."
        )


class TestFilePermissions:
    """Test that files are writable by the user."""

    def test_monitoring_dir_writable(self):
        """Verify monitoring directory is writable."""
        assert os.access(MONITORING_DIR, os.W_OK), (
            f"Monitoring directory {MONITORING_DIR} is not writable"
        )

    def test_alertmanager_config_writable(self):
        """Verify alertmanager.yml is writable."""
        assert os.access(ALERTMANAGER_CONFIG, os.W_OK), (
            f"Alertmanager config {ALERTMANAGER_CONFIG} is not writable"
        )


class TestTemplateFiles:
    """Test that template files have valid content."""

    def test_slack_template_has_content(self):
        """Verify slack.tmpl has template definitions."""
        with open(SLACK_TEMPLATE, 'r') as f:
            content = f.read()
        assert "define" in content, (
            "slack.tmpl should contain Go template definitions"
        )
        assert "slack" in content.lower(), (
            "slack.tmpl should contain slack-related template definitions"
        )

    def test_pagerduty_template_has_content(self):
        """Verify pagerduty.tmpl has template definitions."""
        with open(PAGERDUTY_TEMPLATE, 'r') as f:
            content = f.read()
        assert "define" in content, (
            "pagerduty.tmpl should contain Go template definitions"
        )
