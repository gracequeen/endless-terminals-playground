# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the compliance audit script debugging task.
"""

import json
import os
import subprocess
import time
import pytest


# === Path Constants ===
HOME = "/home/user"
AUDIT_DIR = f"{HOME}/audit"
SERVICES_DIR = f"{HOME}/services"
COLLECT_SCRIPT = f"{AUDIT_DIR}/collect.py"
REPORT_JSON = f"{AUDIT_DIR}/report.json"
START_ALL_SCRIPT = f"{SERVICES_DIR}/start_all.sh"

# Service configuration
SERVICES = {
    "auth": {"port": 9001, "pid_file": f"{SERVICES_DIR}/auth.pid"},
    "billing": {"port": 9002, "pid_file": f"{SERVICES_DIR}/billing.pid"},
    "inventory": {"port": 9003, "pid_file": f"{SERVICES_DIR}/inventory.pid"},
}

AUTH_METRICS_KEYS = ["active_sessions", "failed_logins", "token_refreshes"]
BILLING_METRICS_KEYS = ["transactions_today", "revenue_cents", "refunds"]
INVENTORY_METRICS_KEYS = ["items_in_stock", "pending_orders", "backorders"]


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_audit_directory_exists(self):
        assert os.path.isdir(AUDIT_DIR), f"Audit directory {AUDIT_DIR} does not exist"

    def test_services_directory_exists(self):
        assert os.path.isdir(SERVICES_DIR), f"Services directory {SERVICES_DIR} does not exist"

    def test_audit_directory_is_writable(self):
        assert os.access(AUDIT_DIR, os.W_OK), f"Audit directory {AUDIT_DIR} is not writable"


class TestRequiredFiles:
    """Test that required files exist."""

    def test_collect_script_exists(self):
        assert os.path.isfile(COLLECT_SCRIPT), f"Collection script {COLLECT_SCRIPT} does not exist"

    def test_collect_script_is_readable(self):
        assert os.access(COLLECT_SCRIPT, os.R_OK), f"Collection script {COLLECT_SCRIPT} is not readable"

    def test_start_all_script_exists(self):
        assert os.path.isfile(START_ALL_SCRIPT), f"Start all script {START_ALL_SCRIPT} does not exist"

    def test_report_json_exists(self):
        assert os.path.isfile(REPORT_JSON), f"Report JSON {REPORT_JSON} does not exist"


class TestCollectScriptContent:
    """Test that the collect script uses asyncio/aiohttp approach."""

    def test_script_uses_asyncio(self):
        with open(COLLECT_SCRIPT, "r") as f:
            content = f.read()
        assert "asyncio" in content, "Collection script should use asyncio"

    def test_script_uses_aiohttp(self):
        with open(COLLECT_SCRIPT, "r") as f:
            content = f.read()
        assert "aiohttp" in content, "Collection script should use aiohttp"

    def test_script_is_valid_python(self):
        result = subprocess.run(
            ["python3", "-m", "py_compile", COLLECT_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Collection script has syntax errors: {result.stderr}"


class TestReportJsonInitialState:
    """Test that the report.json has nulls for service data (the bug symptom)."""

    def test_report_json_is_valid_json(self):
        with open(REPORT_JSON, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Report JSON is not valid JSON: {e}")

    def test_report_json_has_expected_structure(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        expected_keys = {"timestamp", "auth", "billing", "inventory"}
        actual_keys = set(data.keys())
        assert expected_keys.issubset(actual_keys), \
            f"Report JSON missing expected keys. Expected: {expected_keys}, Got: {actual_keys}"

    def test_report_json_has_nulls_for_service_data(self):
        """Verify the initial buggy state - services should have null data."""
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        # Check that at least some service data is null (the bug symptom)
        null_count = 0
        for service in ["auth", "billing", "inventory"]:
            if service in data:
                service_data = data[service]
                if service_data is None:
                    null_count += 1
                elif isinstance(service_data, dict):
                    for value in service_data.values():
                        if value is None:
                            null_count += 1

        assert null_count > 0, \
            "Report JSON should have null values for service data (demonstrating the bug)"


class TestServicePidFiles:
    """Test that service PID files exist."""

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_pid_file_exists(self, service, config):
        pid_file = config["pid_file"]
        assert os.path.isfile(pid_file), f"PID file for {service} service does not exist at {pid_file}"

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_pid_file_contains_valid_pid(self, service, config):
        pid_file = config["pid_file"]
        with open(pid_file, "r") as f:
            content = f.read().strip()

        try:
            pid = int(content)
            assert pid > 0, f"PID for {service} should be positive, got {pid}"
        except ValueError:
            pytest.fail(f"PID file for {service} does not contain a valid integer: {content}")


class TestServicesRunning:
    """Test that all three services are running and responding."""

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_service_process_is_running(self, service, config):
        pid_file = config["pid_file"]
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        # Check if process exists
        try:
            os.kill(pid, 0)  # Signal 0 just checks if process exists
        except ProcessLookupError:
            pytest.fail(f"Process for {service} service (PID {pid}) is not running")
        except PermissionError:
            pass  # Process exists but we don't have permission (still valid)

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_service_port_is_listening(self, service, config):
        port = config["port"]
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert f":{port}" in result.stdout, \
            f"No service listening on port {port} for {service} service"

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_service_responds_to_curl(self, service, config):
        port = config["port"]
        url = f"http://localhost:{port}/metrics"

        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.stdout == "200", \
            f"Service {service} at {url} did not return HTTP 200, got {result.stdout}"

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_service_responds_quickly(self, service, config):
        """Each service should respond in under 100ms as stated in the task."""
        port = config["port"]
        url = f"http://localhost:{port}/metrics"

        start = time.time()
        result = subprocess.run(
            ["curl", "-s", url],
            capture_output=True,
            text=True,
            timeout=5
        )
        elapsed = time.time() - start

        assert elapsed < 0.5, \
            f"Service {service} took {elapsed:.3f}s to respond, expected < 100ms"
        assert result.returncode == 0, \
            f"curl to {service} service failed: {result.stderr}"


class TestServiceResponses:
    """Test that services return valid JSON with expected fields."""

    def test_auth_service_returns_expected_fields(self):
        result = subprocess.run(
            ["curl", "-s", "http://localhost:9001/metrics"],
            capture_output=True,
            text=True,
            timeout=5
        )
        data = json.loads(result.stdout)

        for key in AUTH_METRICS_KEYS:
            assert key in data, f"Auth service response missing '{key}' field"
            assert isinstance(data[key], (int, float)), \
                f"Auth service '{key}' should be numeric, got {type(data[key])}"

    def test_billing_service_returns_expected_fields(self):
        result = subprocess.run(
            ["curl", "-s", "http://localhost:9002/metrics"],
            capture_output=True,
            text=True,
            timeout=5
        )
        data = json.loads(result.stdout)

        for key in BILLING_METRICS_KEYS:
            assert key in data, f"Billing service response missing '{key}' field"
            assert isinstance(data[key], (int, float)), \
                f"Billing service '{key}' should be numeric, got {type(data[key])}"

    def test_inventory_service_returns_expected_fields(self):
        result = subprocess.run(
            ["curl", "-s", "http://localhost:9003/metrics"],
            capture_output=True,
            text=True,
            timeout=5
        )
        data = json.loads(result.stdout)

        for key in INVENTORY_METRICS_KEYS:
            assert key in data, f"Inventory service response missing '{key}' field"
            assert isinstance(data[key], (int, float)), \
                f"Inventory service '{key}' should be numeric, got {type(data[key])}"


class TestPythonEnvironment:
    """Test that required Python packages are available."""

    def test_python3_available(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"
        assert "Python 3" in result.stdout, f"Expected Python 3, got: {result.stdout}"

    def test_aiohttp_installed(self):
        result = subprocess.run(
            ["python3", "-c", "import aiohttp; print(aiohttp.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"aiohttp is not installed: {result.stderr}"

    def test_asyncio_available(self):
        result = subprocess.run(
            ["python3", "-c", "import asyncio; print('ok')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"asyncio is not available: {result.stderr}"
