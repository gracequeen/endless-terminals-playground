# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed the task.
This verifies that Alertmanager is running, healthy, and has all required receivers and routes intact.
"""

import json
import os
import socket
import subprocess
import time
import pytest

MONITORING_DIR = "/home/user/monitoring"
ALERTMANAGER_BINARY = os.path.join(MONITORING_DIR, "alertmanager")
ALERTMANAGER_CONFIG = os.path.join(MONITORING_DIR, "alertmanager.yml")
TEMPLATES_DIR = os.path.join(MONITORING_DIR, "templates")
SLACK_TEMPLATE = os.path.join(TEMPLATES_DIR, "slack.tmpl")
PAGERDUTY_TEMPLATE = os.path.join(TEMPLATES_DIR, "pagerduty.tmpl")

ALERTMANAGER_PORT = 9093
ALERTMANAGER_HOST = "localhost"


class TestAlertmanagerRunning:
    """Test that Alertmanager is actually running."""

    def test_alertmanager_process_exists(self):
        """Verify alertmanager process is running."""
        result = subprocess.run(
            ["pgrep", "-f", "alertmanager"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            "Alertmanager process is not running. "
            "The alertmanager binary must be started and stay running."
        )

    def test_port_9093_is_listening(self):
        """Verify something is listening on port 9093."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert ":9093" in result.stdout, (
            "Nothing is listening on port 9093. "
            "Alertmanager must be running and listening on port 9093."
        )

    def test_can_connect_to_port_9093(self):
        """Verify we can establish a TCP connection to port 9093."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex((ALERTMANAGER_HOST, ALERTMANAGER_PORT))
            assert result == 0, (
                f"Cannot connect to {ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}. "
                "Alertmanager must be running and accepting connections."
            )
        finally:
            sock.close()


class TestAlertmanagerHealthy:
    """Test that Alertmanager is healthy and responding."""

    def test_health_endpoint_returns_ok(self):
        """Verify /-/healthy endpoint returns 200 with 'ok'."""
        result = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}", "-o", "/tmp/health_body.txt",
             f"http://{ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}/-/healthy"],
            capture_output=True,
            text=True,
            timeout=10
        )
        http_code = result.stdout.strip()
        assert http_code == "200", (
            f"Health endpoint returned HTTP {http_code}, expected 200. "
            "Alertmanager may not be running or healthy."
        )

        # Check body contains "ok"
        with open("/tmp/health_body.txt", "r") as f:
            body = f.read().lower()
        assert "ok" in body, (
            f"Health endpoint body does not contain 'ok'. Got: {body}"
        )

    def test_ready_endpoint_returns_ok(self):
        """Verify /-/ready endpoint returns 200."""
        result = subprocess.run(
            ["curl", "-s", "-w", "%{http_code}",
             f"http://{ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}/-/ready"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # The output includes the body + http code at the end
        http_code = result.stdout.strip()[-3:]
        assert http_code == "200", (
            f"Ready endpoint returned HTTP {http_code}, expected 200. "
            "Alertmanager may not be fully ready."
        )


class TestAlertmanagerStatus:
    """Test that Alertmanager status API returns valid data."""

    def test_status_endpoint_returns_valid_json(self):
        """Verify /api/v2/status returns valid JSON with cluster field."""
        result = subprocess.run(
            ["curl", "-s", f"http://{ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}/api/v2/status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"Failed to curl status endpoint: {result.stderr}"
        )

        try:
            status_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"Status endpoint did not return valid JSON: {e}. "
                f"Response was: {result.stdout[:500]}"
            )

        assert "cluster" in status_data, (
            f"Status JSON missing 'cluster' field. Got keys: {list(status_data.keys())}"
        )


class TestReceiversIntact:
    """Test that all required receivers are still defined."""

    @pytest.fixture
    def receivers_from_api(self):
        """Fetch receivers from Alertmanager API."""
        result = subprocess.run(
            ["curl", "-s", f"http://{ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}/api/v2/receivers"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Failed to fetch receivers: {result.stderr}"

        try:
            receivers = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Receivers endpoint did not return valid JSON: {e}")

        return receivers

    def test_receivers_endpoint_returns_array(self, receivers_from_api):
        """Verify receivers endpoint returns a JSON array."""
        assert isinstance(receivers_from_api, list), (
            f"Receivers endpoint should return an array, got: {type(receivers_from_api)}"
        )

    def test_at_least_five_receivers(self, receivers_from_api):
        """Verify at least 5 receivers are defined (the 5 custom ones)."""
        assert len(receivers_from_api) >= 5, (
            f"Expected at least 5 receivers, but only found {len(receivers_from_api)}. "
            "All original receivers must remain defined."
        )

    def test_default_receiver_exists(self, receivers_from_api):
        """Verify default-receiver is defined."""
        receiver_names = [r.get("name", "") for r in receivers_from_api]
        assert "default-receiver" in receiver_names, (
            f"'default-receiver' not found in receivers. Found: {receiver_names}"
        )

    def test_pagerduty_critical_receiver_exists(self, receivers_from_api):
        """Verify pagerduty-critical receiver is defined."""
        receiver_names = [r.get("name", "") for r in receivers_from_api]
        assert "pagerduty-critical" in receiver_names, (
            f"'pagerduty-critical' receiver not found. Found: {receiver_names}. "
            "PagerDuty integration must remain intact!"
        )

    def test_slack_warnings_receiver_exists(self, receivers_from_api):
        """Verify slack-warnings receiver is defined."""
        receiver_names = [r.get("name", "") for r in receivers_from_api]
        assert "slack-warnings" in receiver_names, (
            f"'slack-warnings' receiver not found. Found: {receiver_names}. "
            "Slack integration must remain intact!"
        )

    def test_team_backend_receiver_exists(self, receivers_from_api):
        """Verify team-backend receiver is defined."""
        receiver_names = [r.get("name", "") for r in receivers_from_api]
        assert "team-backend" in receiver_names, (
            f"'team-backend' receiver not found. Found: {receiver_names}"
        )

    def test_db_team_receiver_exists(self, receivers_from_api):
        """Verify db-team receiver is defined (cannot be deleted to 'fix' the error)."""
        receiver_names = [r.get("name", "") for r in receivers_from_api]
        assert "db-team" in receiver_names, (
            f"'db-team' receiver not found. Found: {receiver_names}. "
            "The db-team receiver must remain - you cannot delete it to fix the YAML error!"
        )


class TestConfigFileIntegrity:
    """Test that the config file maintains required content."""

    @pytest.fixture
    def config_content(self):
        """Read the alertmanager config file."""
        with open(ALERTMANAGER_CONFIG, 'r') as f:
            return f.read()

    def test_no_tab_characters_in_config(self, config_content):
        """Verify the tab character bug has been fixed."""
        assert "\t" not in config_content, (
            "alertmanager.yml still contains tab characters. "
            "The YAML bug (tab mixed with spaces) must be fixed."
        )

    def test_pagerduty_service_key_unchanged(self, config_content):
        """Verify PagerDuty service key is still present and unchanged."""
        assert "fake-pagerduty-key-12345" in config_content, (
            "PagerDuty service_key 'fake-pagerduty-key-12345' is missing or changed. "
            "PagerDuty integration must remain intact!"
        )

    def test_slack_channels_unchanged(self, config_content):
        """Verify all Slack channels are still configured."""
        expected_channels = [
            "#alerts-general",
            "#alerts-warnings", 
            "#team-backend-alerts",
            "#db-alerts"
        ]
        for channel in expected_channels:
            assert channel in config_content, (
                f"Slack channel '{channel}' is missing from config. "
                "All Slack integrations must remain intact!"
            )

    def test_config_has_multiple_routes(self, config_content):
        """Verify route tree structure is maintained with at least 3 sub-routes."""
        # Count occurrences of route matching patterns
        route_indicators = [
            "severity: critical",
            "severity: warning",
            "match_re:"
        ]
        found_routes = sum(1 for indicator in route_indicators if indicator in config_content)
        assert found_routes >= 3, (
            f"Expected at least 3 route rules, found indicators for {found_routes}. "
            "The route tree structure must remain intact."
        )

    def test_critical_routes_to_pagerduty(self, config_content):
        """Verify critical severity still routes to pagerduty-critical."""
        # Check that both critical severity and pagerduty-critical receiver exist
        assert "severity: critical" in config_content, (
            "Critical severity route is missing"
        )
        assert "pagerduty-critical" in config_content, (
            "pagerduty-critical receiver reference is missing"
        )

    def test_warning_routes_to_slack(self, config_content):
        """Verify warning severity still routes to slack-warnings."""
        assert "severity: warning" in config_content, (
            "Warning severity route is missing"
        )
        assert "slack-warnings" in config_content, (
            "slack-warnings receiver reference is missing"
        )

    def test_service_regex_route_exists(self, config_content):
        """Verify service regex route to team-backend exists."""
        assert "match_re:" in config_content, (
            "Regex matching route is missing"
        )
        assert "team-backend" in config_content, (
            "team-backend receiver reference is missing"
        )


class TestTemplatesUnchanged:
    """Test that template files are unchanged."""

    def test_templates_directory_exists(self):
        """Verify templates directory still exists."""
        assert os.path.isdir(TEMPLATES_DIR), (
            f"Templates directory {TEMPLATES_DIR} is missing"
        )

    def test_slack_template_exists(self):
        """Verify slack.tmpl still exists."""
        assert os.path.isfile(SLACK_TEMPLATE), (
            f"Slack template {SLACK_TEMPLATE} is missing"
        )

    def test_pagerduty_template_exists(self):
        """Verify pagerduty.tmpl still exists."""
        assert os.path.isfile(PAGERDUTY_TEMPLATE), (
            f"PagerDuty template {PAGERDUTY_TEMPLATE} is missing"
        )

    def test_slack_template_has_definitions(self):
        """Verify slack.tmpl still has template definitions."""
        with open(SLACK_TEMPLATE, 'r') as f:
            content = f.read()
        assert "define" in content, (
            "slack.tmpl should contain Go template definitions"
        )

    def test_pagerduty_template_has_definitions(self):
        """Verify pagerduty.tmpl still has template definitions."""
        with open(PAGERDUTY_TEMPLATE, 'r') as f:
            content = f.read()
        assert "define" in content, (
            "pagerduty.tmpl should contain Go template definitions"
        )


class TestAlertmanagerConfigValid:
    """Test that the config is now valid YAML."""

    def test_alertmanager_can_validate_config(self):
        """Verify alertmanager can now parse the config without errors."""
        # Try to check config using amtool if available, or just verify it's running
        # Since alertmanager is running and healthy, config must be valid
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             f"http://{ALERTMANAGER_HOST}:{ALERTMANAGER_PORT}/api/v2/status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.stdout.strip() == "200", (
            "Alertmanager API not responding with 200, config may still be invalid"
        )
