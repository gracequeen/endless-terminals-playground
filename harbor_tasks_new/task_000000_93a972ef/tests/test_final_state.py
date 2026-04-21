# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the monitoring configuration update task.
"""

import os
import pytest
import yaml


def load_toml(filepath):
    """Load a TOML file using available library."""
    try:
        import tomli
        with open(filepath, 'rb') as f:
            return tomli.load(f)
    except ImportError:
        import toml
        with open(filepath, 'r') as f:
            return toml.load(f)


class TestAlertsYamlFinalState:
    """Test the final state of /etc/monitoring/alerts.yaml."""

    ALERTS_FILE = "/etc/monitoring/alerts.yaml"

    def test_alerts_yaml_exists(self):
        """The alerts.yaml file must still exist."""
        assert os.path.isfile(self.ALERTS_FILE), (
            f"File {self.ALERTS_FILE} does not exist. "
            "The alerts configuration file is missing."
        )

    def test_alerts_yaml_is_valid_yaml(self):
        """The alerts.yaml file must contain valid YAML after modifications."""
        with open(self.ALERTS_FILE, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, (
                    f"File {self.ALERTS_FILE} is empty or contains only null values."
                )
            except yaml.YAMLError as e:
                pytest.fail(
                    f"File {self.ALERTS_FILE} contains invalid YAML after modifications: {e}"
                )

    def test_alerts_yaml_has_groups_structure(self):
        """The alerts.yaml must maintain the groups structure."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        assert 'groups' in data, (
            f"File {self.ALERTS_FILE} is missing 'groups' key at root level."
        )
        assert isinstance(data['groups'], list), (
            f"'groups' in {self.ALERTS_FILE} must be a list."
        )

    def test_high_latency_for_duration_updated(self):
        """The HighLatency alert must have 'for: 3m'."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'HighLatency':
                    for_value = rule.get('for')
                    assert for_value == '3m', (
                        f"HighLatency alert 'for' duration should be '3m' but is '{for_value}'. "
                        "The duration was not updated correctly."
                    )
                    return
        pytest.fail("HighLatency alert rule not found in alerts.yaml.")

    def test_service_down_has_escalation_level(self):
        """The ServiceDown alert must have 'escalation_level: critical' in labels."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'ServiceDown':
                    labels = rule.get('labels', {})
                    assert 'escalation_level' in labels, (
                        "ServiceDown alert is missing 'escalation_level' label. "
                        "The label was not added."
                    )
                    assert labels['escalation_level'] == 'critical', (
                        f"ServiceDown alert 'escalation_level' should be 'critical' "
                        f"but is '{labels['escalation_level']}'."
                    )
                    return
        pytest.fail("ServiceDown alert rule not found in alerts.yaml.")

    def test_service_down_preserves_existing_labels(self):
        """The ServiceDown alert must still have its original labels."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'ServiceDown':
                    labels = rule.get('labels', {})
                    assert 'severity' in labels, (
                        "ServiceDown alert lost its 'severity' label. "
                        "Existing labels must be preserved."
                    )
                    assert labels['severity'] == 'critical', (
                        f"ServiceDown alert 'severity' should still be 'critical' "
                        f"but is '{labels['severity']}'."
                    )
                    assert 'team' in labels, (
                        "ServiceDown alert lost its 'team' label. "
                        "Existing labels must be preserved."
                    )
                    assert labels['team'] == 'platform', (
                        f"ServiceDown alert 'team' should still be 'platform' "
                        f"but is '{labels['team']}'."
                    )
                    return
        pytest.fail("ServiceDown alert rule not found in alerts.yaml.")

    def test_disk_space_low_alert_exists(self):
        """A new DiskSpaceLow alert must exist."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'DiskSpaceLow':
                    return
        pytest.fail(
            "DiskSpaceLow alert rule not found in alerts.yaml. "
            "The new alert was not added."
        )

    def test_disk_space_low_expr(self):
        """The DiskSpaceLow alert must have the correct expr."""
        expected_expr = 'node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1'
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'DiskSpaceLow':
                    expr = rule.get('expr')
                    assert expr == expected_expr, (
                        f"DiskSpaceLow alert 'expr' is incorrect.\n"
                        f"Expected: {expected_expr}\n"
                        f"Got: {expr}"
                    )
                    return
        pytest.fail("DiskSpaceLow alert rule not found.")

    def test_disk_space_low_for_duration(self):
        """The DiskSpaceLow alert must have 'for: 10m'."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'DiskSpaceLow':
                    for_value = rule.get('for')
                    assert for_value == '10m', (
                        f"DiskSpaceLow alert 'for' duration should be '10m' but is '{for_value}'."
                    )
                    return
        pytest.fail("DiskSpaceLow alert rule not found.")

    def test_disk_space_low_labels(self):
        """The DiskSpaceLow alert must have correct labels."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'DiskSpaceLow':
                    labels = rule.get('labels', {})
                    assert labels.get('severity') == 'warning', (
                        f"DiskSpaceLow alert 'severity' label should be 'warning' "
                        f"but is '{labels.get('severity')}'."
                    )
                    assert labels.get('team') == 'infrastructure', (
                        f"DiskSpaceLow alert 'team' label should be 'infrastructure' "
                        f"but is '{labels.get('team')}'."
                    )
                    return
        pytest.fail("DiskSpaceLow alert rule not found.")

    def test_disk_space_low_annotations(self):
        """The DiskSpaceLow alert must have correct annotations."""
        expected_summary = 'Disk space below 10% on {{ $labels.instance }}'
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'DiskSpaceLow':
                    annotations = rule.get('annotations', {})
                    assert 'summary' in annotations, (
                        "DiskSpaceLow alert is missing 'summary' annotation."
                    )
                    assert annotations['summary'] == expected_summary, (
                        f"DiskSpaceLow alert 'summary' annotation is incorrect.\n"
                        f"Expected: {expected_summary}\n"
                        f"Got: {annotations['summary']}"
                    )
                    return
        pytest.fail("DiskSpaceLow alert rule not found.")

    def test_high_memory_usage_alert_unchanged(self):
        """The HighMemoryUsage alert must still exist and be unchanged."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data.get('groups', []):
            for rule in group.get('rules', []):
                if rule.get('alert') == 'HighMemoryUsage':
                    assert rule.get('for') == '5m', (
                        f"HighMemoryUsage alert 'for' should still be '5m' but is '{rule.get('for')}'."
                    )
                    labels = rule.get('labels', {})
                    assert labels.get('severity') == 'warning', (
                        "HighMemoryUsage alert 'severity' label was modified but should be unchanged."
                    )
                    return
        pytest.fail(
            "HighMemoryUsage alert rule not found in alerts.yaml. "
            "This existing alert should not have been removed."
        )


class TestUptimeTomlFinalState:
    """Test the final state of /etc/monitoring/uptime.toml."""

    UPTIME_FILE = "/etc/monitoring/uptime.toml"

    def test_uptime_toml_exists(self):
        """The uptime.toml file must still exist."""
        assert os.path.isfile(self.UPTIME_FILE), (
            f"File {self.UPTIME_FILE} does not exist. "
            "The uptime configuration file is missing."
        )

    def test_uptime_toml_is_valid_toml(self):
        """The uptime.toml file must contain valid TOML after modifications."""
        try:
            data = load_toml(self.UPTIME_FILE)
            assert data is not None
        except Exception as e:
            pytest.fail(
                f"File {self.UPTIME_FILE} contains invalid TOML after modifications: {e}"
            )

    def test_global_check_interval_updated(self):
        """The [global] section must have check_interval = 30."""
        data = load_toml(self.UPTIME_FILE)
        global_section = data.get('global', {})
        check_interval = global_section.get('check_interval')
        assert check_interval == 30, (
            f"[global] check_interval should be 30 but is {check_interval}. "
            "The value was not updated correctly."
        )

    def test_global_timeout_added(self):
        """The [global] section must have timeout = 10."""
        data = load_toml(self.UPTIME_FILE)
        global_section = data.get('global', {})
        timeout = global_section.get('timeout')
        assert timeout == 10, (
            f"[global] timeout should be 10 but is {timeout}. "
            "The timeout key was not added correctly."
        )

    def test_global_retry_count_preserved(self):
        """The [global] section must still have retry_count = 3."""
        data = load_toml(self.UPTIME_FILE)
        global_section = data.get('global', {})
        retry_count = global_section.get('retry_count')
        assert retry_count == 3, (
            f"[global] retry_count should still be 3 but is {retry_count}. "
            "Existing configuration was not preserved."
        )

    def test_global_log_level_preserved(self):
        """The [global] section must still have log_level = 'info'."""
        data = load_toml(self.UPTIME_FILE)
        global_section = data.get('global', {})
        log_level = global_section.get('log_level')
        assert log_level == 'info', (
            f"[global] log_level should still be 'info' but is '{log_level}'. "
            "Existing configuration was not preserved."
        )

    def test_api_gateway_expected_status_updated(self):
        """The api-gateway endpoint must have expected_status = 200."""
        data = load_toml(self.UPTIME_FILE)
        for endpoint in data.get('endpoints', []):
            if endpoint.get('name') == 'api-gateway':
                expected_status = endpoint.get('expected_status')
                assert expected_status == 200, (
                    f"api-gateway endpoint expected_status should be 200 but is {expected_status}."
                )
                return
        pytest.fail("api-gateway endpoint not found in uptime.toml.")

    def test_api_gateway_critical_added(self):
        """The api-gateway endpoint must have critical = true."""
        data = load_toml(self.UPTIME_FILE)
        for endpoint in data.get('endpoints', []):
            if endpoint.get('name') == 'api-gateway':
                critical = endpoint.get('critical')
                assert critical is True, (
                    f"api-gateway endpoint 'critical' should be true but is {critical}."
                )
                return
        pytest.fail("api-gateway endpoint not found in uptime.toml.")

    def test_payment_service_endpoint_exists(self):
        """A new payment-service endpoint must exist."""
        data = load_toml(self.UPTIME_FILE)
        endpoint_names = [ep.get('name') for ep in data.get('endpoints', [])]
        assert 'payment-service' in endpoint_names, (
            f"payment-service endpoint not found in uptime.toml. "
            f"Found endpoints: {endpoint_names}"
        )

    def test_payment_service_url(self):
        """The payment-service endpoint must have the correct URL."""
        expected_url = "https://payments.internal.example.com/health"
        data = load_toml(self.UPTIME_FILE)
        for endpoint in data.get('endpoints', []):
            if endpoint.get('name') == 'payment-service':
                url = endpoint.get('url')
                assert url == expected_url, (
                    f"payment-service endpoint URL should be '{expected_url}' but is '{url}'."
                )
                return
        pytest.fail("payment-service endpoint not found.")

    def test_payment_service_expected_status(self):
        """The payment-service endpoint must have expected_status = 200."""
        data = load_toml(self.UPTIME_FILE)
        for endpoint in data.get('endpoints', []):
            if endpoint.get('name') == 'payment-service':
                expected_status = endpoint.get('expected_status')
                assert expected_status == 200, (
                    f"payment-service endpoint expected_status should be 200 but is {expected_status}."
                )
                return
        pytest.fail("payment-service endpoint not found.")

    def test_payment_service_critical(self):
        """The payment-service endpoint must have critical = true."""
        data = load_toml(self.UPTIME_FILE)
        for endpoint in data.get('endpoints', []):
            if endpoint.get('name') == 'payment-service':
                critical = endpoint.get('critical')
                assert critical is True, (
                    f"payment-service endpoint 'critical' should be true but is {critical}."
                )
                return
        pytest.fail("payment-service endpoint not found.")

    def test_payment_service_headers(self):
        """The payment-service endpoint must have correct headers."""
        expected_auth = "Bearer ${PAYMENTS_TOKEN}"
        data = load_toml(self.UPTIME_FILE)
        for endpoint in data.get('endpoints', []):
            if endpoint.get('name') == 'payment-service':
                headers = endpoint.get('headers', {})
                assert 'Authorization' in headers, (
                    "payment-service endpoint is missing 'Authorization' header."
                )
                assert headers['Authorization'] == expected_auth, (
                    f"payment-service endpoint Authorization header should be "
                    f"'{expected_auth}' but is '{headers['Authorization']}'."
                )
                return
        pytest.fail("payment-service endpoint not found.")

    def test_auth_service_endpoint_preserved(self):
        """The auth-service endpoint must still exist."""
        data = load_toml(self.UPTIME_FILE)
        endpoint_names = [ep.get('name') for ep in data.get('endpoints', [])]
        assert 'auth-service' in endpoint_names, (
            "auth-service endpoint was removed but should be preserved."
        )

    def test_frontend_endpoint_preserved(self):
        """The frontend endpoint must still exist."""
        data = load_toml(self.UPTIME_FILE)
        endpoint_names = [ep.get('name') for ep in data.get('endpoints', [])]
        assert 'frontend' in endpoint_names, (
            "frontend endpoint was removed but should be preserved."
        )


class TestConfigChangesLog:
    """Test the final state of /home/user/config_changes.log."""

    LOG_FILE = "/home/user/config_changes.log"

    EXPECTED_CONTENT = """YAML_CHANGES:
- alerts.yaml: HighLatency for duration updated
- alerts.yaml: ServiceDown escalation_level added
- alerts.yaml: DiskSpaceLow alert added
TOML_CHANGES:
- uptime.toml: global.check_interval updated to 30
- uptime.toml: global.timeout added
- uptime.toml: api-gateway endpoint modified
- uptime.toml: payment-service endpoint added
VALIDATION: COMPLETE
"""

    def test_config_changes_log_exists(self):
        """The config_changes.log file must exist."""
        assert os.path.isfile(self.LOG_FILE), (
            f"File {self.LOG_FILE} does not exist. "
            "The validation log was not created."
        )

    def test_config_changes_log_content(self):
        """The config_changes.log must have the exact expected content."""
        with open(self.LOG_FILE, 'r') as f:
            content = f.read()

        assert content == self.EXPECTED_CONTENT, (
            f"File {self.LOG_FILE} content does not match expected format.\n"
            f"Expected:\n{repr(self.EXPECTED_CONTENT)}\n"
            f"Got:\n{repr(content)}"
        )

    def test_config_changes_log_has_yaml_changes_section(self):
        """The log must contain YAML_CHANGES section."""
        with open(self.LOG_FILE, 'r') as f:
            content = f.read()

        assert 'YAML_CHANGES:' in content, (
            f"File {self.LOG_FILE} is missing 'YAML_CHANGES:' section."
        )

    def test_config_changes_log_has_toml_changes_section(self):
        """The log must contain TOML_CHANGES section."""
        with open(self.LOG_FILE, 'r') as f:
            content = f.read()

        assert 'TOML_CHANGES:' in content, (
            f"File {self.LOG_FILE} is missing 'TOML_CHANGES:' section."
        )

    def test_config_changes_log_has_validation_complete(self):
        """The log must end with VALIDATION: COMPLETE."""
        with open(self.LOG_FILE, 'r') as f:
            content = f.read()

        assert 'VALIDATION: COMPLETE' in content, (
            f"File {self.LOG_FILE} is missing 'VALIDATION: COMPLETE' line."
        )

    def test_config_changes_log_has_trailing_newline(self):
        """The log must end with a trailing newline."""
        with open(self.LOG_FILE, 'r') as f:
            content = f.read()

        assert content.endswith('\n'), (
            f"File {self.LOG_FILE} must end with a trailing newline."
        )
