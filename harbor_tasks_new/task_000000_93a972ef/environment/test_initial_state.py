# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the monitoring configuration update task.
"""

import os
import pytest
import yaml


class TestDirectoryStructure:
    """Test that required directories exist and have correct permissions."""

    def test_monitoring_directory_exists(self):
        """The /etc/monitoring/ directory must exist."""
        assert os.path.isdir("/etc/monitoring"), (
            "Directory /etc/monitoring/ does not exist. "
            "Please create it before proceeding."
        )

    def test_monitoring_directory_is_writable(self):
        """The /etc/monitoring/ directory must be writable by the current user."""
        assert os.access("/etc/monitoring", os.W_OK), (
            "Directory /etc/monitoring/ is not writable by the current user. "
            "Please ensure write permissions are granted."
        )

    def test_home_user_directory_exists(self):
        """The /home/user directory must exist."""
        assert os.path.isdir("/home/user"), (
            "Directory /home/user does not exist. "
            "Please create the home directory before proceeding."
        )


class TestAlertsYamlFile:
    """Test the initial state of /etc/monitoring/alerts.yaml."""

    ALERTS_FILE = "/etc/monitoring/alerts.yaml"

    def test_alerts_yaml_exists(self):
        """The alerts.yaml file must exist."""
        assert os.path.isfile(self.ALERTS_FILE), (
            f"File {self.ALERTS_FILE} does not exist. "
            "Please create the alerts configuration file before proceeding."
        )

    def test_alerts_yaml_is_readable(self):
        """The alerts.yaml file must be readable."""
        assert os.access(self.ALERTS_FILE, os.R_OK), (
            f"File {self.ALERTS_FILE} is not readable. "
            "Please ensure read permissions are granted."
        )

    def test_alerts_yaml_is_valid_yaml(self):
        """The alerts.yaml file must contain valid YAML."""
        with open(self.ALERTS_FILE, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, (
                    f"File {self.ALERTS_FILE} is empty or contains only null values."
                )
            except yaml.YAMLError as e:
                pytest.fail(f"File {self.ALERTS_FILE} contains invalid YAML: {e}")

    def test_alerts_yaml_has_groups_structure(self):
        """The alerts.yaml must have the expected groups structure."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        assert 'groups' in data, (
            f"File {self.ALERTS_FILE} is missing 'groups' key at root level."
        )
        assert isinstance(data['groups'], list), (
            f"'groups' in {self.ALERTS_FILE} must be a list."
        )
        assert len(data['groups']) > 0, (
            f"'groups' in {self.ALERTS_FILE} must contain at least one group."
        )

    def test_alerts_yaml_has_service_alerts_group(self):
        """The alerts.yaml must have a group named 'service_alerts'."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        group_names = [g.get('name') for g in data['groups']]
        assert 'service_alerts' in group_names, (
            f"File {self.ALERTS_FILE} is missing group named 'service_alerts'. "
            f"Found groups: {group_names}"
        )

    def test_alerts_yaml_has_high_latency_alert(self):
        """The alerts.yaml must have a HighLatency alert rule."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data['groups']:
            if group.get('name') == 'service_alerts':
                rules = group.get('rules', [])
                alert_names = [r.get('alert') for r in rules]
                assert 'HighLatency' in alert_names, (
                    f"Group 'service_alerts' is missing 'HighLatency' alert rule. "
                    f"Found alerts: {alert_names}"
                )
                return
        pytest.fail("Could not find 'service_alerts' group to check for HighLatency alert.")

    def test_alerts_yaml_high_latency_has_for_duration(self):
        """The HighLatency alert must have a 'for' duration field."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data['groups']:
            if group.get('name') == 'service_alerts':
                for rule in group.get('rules', []):
                    if rule.get('alert') == 'HighLatency':
                        assert 'for' in rule, (
                            "HighLatency alert is missing 'for' duration field."
                        )
                        return
        pytest.fail("Could not find HighLatency alert to check 'for' field.")

    def test_alerts_yaml_has_service_down_alert(self):
        """The alerts.yaml must have a ServiceDown alert rule."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data['groups']:
            if group.get('name') == 'service_alerts':
                rules = group.get('rules', [])
                alert_names = [r.get('alert') for r in rules]
                assert 'ServiceDown' in alert_names, (
                    f"Group 'service_alerts' is missing 'ServiceDown' alert rule. "
                    f"Found alerts: {alert_names}"
                )
                return
        pytest.fail("Could not find 'service_alerts' group to check for ServiceDown alert.")

    def test_alerts_yaml_service_down_has_labels(self):
        """The ServiceDown alert must have a labels section."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data['groups']:
            if group.get('name') == 'service_alerts':
                for rule in group.get('rules', []):
                    if rule.get('alert') == 'ServiceDown':
                        assert 'labels' in rule, (
                            "ServiceDown alert is missing 'labels' section."
                        )
                        assert isinstance(rule['labels'], dict), (
                            "ServiceDown alert 'labels' must be a dictionary."
                        )
                        return
        pytest.fail("Could not find ServiceDown alert to check labels.")

    def test_alerts_yaml_has_high_memory_usage_alert(self):
        """The alerts.yaml must have a HighMemoryUsage alert rule."""
        with open(self.ALERTS_FILE, 'r') as f:
            data = yaml.safe_load(f)

        for group in data['groups']:
            if group.get('name') == 'service_alerts':
                rules = group.get('rules', [])
                alert_names = [r.get('alert') for r in rules]
                assert 'HighMemoryUsage' in alert_names, (
                    f"Group 'service_alerts' is missing 'HighMemoryUsage' alert rule. "
                    f"Found alerts: {alert_names}"
                )
                return
        pytest.fail("Could not find 'service_alerts' group to check for HighMemoryUsage alert.")


class TestUptimeTomlFile:
    """Test the initial state of /etc/monitoring/uptime.toml."""

    UPTIME_FILE = "/etc/monitoring/uptime.toml"

    def test_uptime_toml_exists(self):
        """The uptime.toml file must exist."""
        assert os.path.isfile(self.UPTIME_FILE), (
            f"File {self.UPTIME_FILE} does not exist. "
            "Please create the uptime configuration file before proceeding."
        )

    def test_uptime_toml_is_readable(self):
        """The uptime.toml file must be readable."""
        assert os.access(self.UPTIME_FILE, os.R_OK), (
            f"File {self.UPTIME_FILE} is not readable. "
            "Please ensure read permissions are granted."
        )

    def test_uptime_toml_is_valid_toml(self):
        """The uptime.toml file must contain valid TOML."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
                assert data is not None
        except ImportError:
            try:
                import toml
                with open(self.UPTIME_FILE, 'r') as f:
                    data = toml.load(f)
                    assert data is not None
            except ImportError:
                pytest.skip("Neither tomli nor toml package available for TOML parsing.")
            except Exception as e:
                pytest.fail(f"File {self.UPTIME_FILE} contains invalid TOML: {e}")
        except Exception as e:
            pytest.fail(f"File {self.UPTIME_FILE} contains invalid TOML: {e}")

    def test_uptime_toml_has_global_section(self):
        """The uptime.toml must have a [global] section."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            import toml
            with open(self.UPTIME_FILE, 'r') as f:
                data = toml.load(f)

        assert 'global' in data, (
            f"File {self.UPTIME_FILE} is missing [global] section."
        )

    def test_uptime_toml_global_has_check_interval(self):
        """The [global] section must have a check_interval key."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            import toml
            with open(self.UPTIME_FILE, 'r') as f:
                data = toml.load(f)

        assert 'check_interval' in data.get('global', {}), (
            f"[global] section in {self.UPTIME_FILE} is missing 'check_interval' key."
        )

    def test_uptime_toml_has_endpoints_array(self):
        """The uptime.toml must have an [[endpoints]] array."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            import toml
            with open(self.UPTIME_FILE, 'r') as f:
                data = toml.load(f)

        assert 'endpoints' in data, (
            f"File {self.UPTIME_FILE} is missing [[endpoints]] array."
        )
        assert isinstance(data['endpoints'], list), (
            f"'endpoints' in {self.UPTIME_FILE} must be an array."
        )

    def test_uptime_toml_has_api_gateway_endpoint(self):
        """The uptime.toml must have an endpoint named 'api-gateway'."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            import toml
            with open(self.UPTIME_FILE, 'r') as f:
                data = toml.load(f)

        endpoint_names = [ep.get('name') for ep in data.get('endpoints', [])]
        assert 'api-gateway' in endpoint_names, (
            f"File {self.UPTIME_FILE} is missing endpoint named 'api-gateway'. "
            f"Found endpoints: {endpoint_names}"
        )

    def test_uptime_toml_has_auth_service_endpoint(self):
        """The uptime.toml must have an endpoint named 'auth-service'."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            import toml
            with open(self.UPTIME_FILE, 'r') as f:
                data = toml.load(f)

        endpoint_names = [ep.get('name') for ep in data.get('endpoints', [])]
        assert 'auth-service' in endpoint_names, (
            f"File {self.UPTIME_FILE} is missing endpoint named 'auth-service'. "
            f"Found endpoints: {endpoint_names}"
        )

    def test_uptime_toml_has_frontend_endpoint(self):
        """The uptime.toml must have an endpoint named 'frontend'."""
        try:
            import tomli
            with open(self.UPTIME_FILE, 'rb') as f:
                data = tomli.load(f)
        except ImportError:
            import toml
            with open(self.UPTIME_FILE, 'r') as f:
                data = toml.load(f)

        endpoint_names = [ep.get('name') for ep in data.get('endpoints', [])]
        assert 'frontend' in endpoint_names, (
            f"File {self.UPTIME_FILE} is missing endpoint named 'frontend'. "
            f"Found endpoints: {endpoint_names}"
        )


class TestConfigChangesLogDoesNotExist:
    """Test that the output log file does not exist initially."""

    LOG_FILE = "/home/user/config_changes.log"

    def test_config_changes_log_does_not_exist(self):
        """The config_changes.log file must NOT exist initially."""
        assert not os.path.exists(self.LOG_FILE), (
            f"File {self.LOG_FILE} already exists but should not exist initially. "
            "Please remove it before proceeding with the task."
        )


class TestRequiredToolsAvailable:
    """Test that required tools and packages are available."""

    def test_python3_available(self):
        """Python 3 must be available."""
        import sys
        assert sys.version_info.major == 3, (
            f"Python 3 is required but running Python {sys.version_info.major}."
        )

    def test_pyyaml_available(self):
        """PyYAML package must be available."""
        try:
            import yaml
        except ImportError:
            pytest.fail("PyYAML package is not available. Please install it with: pip install pyyaml")

    def test_toml_package_available(self):
        """Either toml or tomli+tomli_w packages must be available."""
        toml_available = False
        try:
            import tomli
            import tomli_w
            toml_available = True
        except ImportError:
            pass

        if not toml_available:
            try:
                import toml
                toml_available = True
            except ImportError:
                pass

        assert toml_available, (
            "Neither toml nor tomli+tomli_w packages are available. "
            "Please install with: pip install toml OR pip install tomli tomli_w"
        )
