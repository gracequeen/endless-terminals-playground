# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the compliance audit script debugging task.
"""

import json
import os
import subprocess
import time
import re
import pytest


# === Path Constants ===
HOME = "/home/user"
AUDIT_DIR = f"{HOME}/audit"
SERVICES_DIR = f"{HOME}/services"
COLLECT_SCRIPT = f"{AUDIT_DIR}/collect.py"
REPORT_JSON = f"{AUDIT_DIR}/report.json"

# Service configuration
SERVICES = {
    "auth": {"port": 9001, "pid_file": f"{SERVICES_DIR}/auth.pid"},
    "billing": {"port": 9002, "pid_file": f"{SERVICES_DIR}/billing.pid"},
    "inventory": {"port": 9003, "pid_file": f"{SERVICES_DIR}/inventory.pid"},
}

AUTH_METRICS_KEYS = ["active_sessions", "failed_logins", "token_refreshes"]
BILLING_METRICS_KEYS = ["transactions_today", "revenue_cents", "refunds"]
INVENTORY_METRICS_KEYS = ["items_in_stock", "pending_orders", "backorders"]


class TestServicesStillRunning:
    """Test that all three services are still running after the fix."""

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_pid_file_exists(self, service, config):
        pid_file = config["pid_file"]
        assert os.path.isfile(pid_file), \
            f"PID file for {service} service no longer exists at {pid_file}. Services must remain running."

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_service_process_is_running(self, service, config):
        pid_file = config["pid_file"]
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            pytest.fail(f"Process for {service} service (PID {pid}) is not running. Services must remain running.")
        except PermissionError:
            pass  # Process exists

    @pytest.mark.parametrize("service,config", SERVICES.items())
    def test_service_responds(self, service, config):
        port = config["port"]
        url = f"http://localhost:{port}/metrics"

        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.stdout == "200", \
            f"Service {service} at {url} is not responding with HTTP 200. Services must remain running."


class TestScriptExecution:
    """Test that the collect script runs successfully and quickly."""

    def test_script_exits_zero(self):
        """Script must exit with code 0."""
        result = subprocess.run(
            ["python3", COLLECT_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"Script exited with code {result.returncode}. Stderr: {result.stderr}"

    def test_script_completes_within_10_seconds(self):
        """Script must complete within 10 seconds."""
        start = time.time()
        result = subprocess.run(
            ["python3", COLLECT_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = time.time() - start

        assert elapsed < 10, \
            f"Script took {elapsed:.2f} seconds to complete, expected < 10 seconds. " \
            f"The timeout bug may not be fully fixed."


class TestScriptRemainsAsync:
    """Anti-shortcut: Script must still use async/aiohttp, not sync requests."""

    def test_no_sync_requests_library(self):
        """Script must not use synchronous requests library."""
        result = subprocess.run(
            ["grep", "-E", r"requests\.(get|post)|urllib\.request|http\.client", COLLECT_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "Script appears to use synchronous requests library (requests.get/post, urllib.request, or http.client). " \
            "The script must remain async using aiohttp."

    def test_script_still_uses_asyncio(self):
        """Script must still use asyncio."""
        with open(COLLECT_SCRIPT, "r") as f:
            content = f.read()
        assert "asyncio" in content, \
            "Script no longer uses asyncio. The async approach must be preserved."

    def test_script_still_uses_aiohttp(self):
        """Script must still use aiohttp."""
        with open(COLLECT_SCRIPT, "r") as f:
            content = f.read()
        assert "aiohttp" in content, \
            "Script no longer uses aiohttp. The async approach must be preserved."


class TestNoHardcodedValues:
    """Anti-shortcut: Values must be dynamically fetched, not hardcoded."""

    def test_no_hardcoded_auth_values(self):
        """active_sessions value must not be hardcoded."""
        result = subprocess.run(
            ["grep", "-E", r'"active_sessions":\s*[0-9]', COLLECT_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "Script appears to have hardcoded active_sessions value. Values must be dynamically fetched."

    def test_no_hardcoded_billing_values(self):
        """transactions_today value must not be hardcoded."""
        result = subprocess.run(
            ["grep", "-E", r'"transactions_today":\s*[0-9]', COLLECT_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "Script appears to have hardcoded transactions_today value. Values must be dynamically fetched."

    def test_no_hardcoded_inventory_values(self):
        """items_in_stock value must not be hardcoded."""
        result = subprocess.run(
            ["grep", "-E", r'"items_in_stock":\s*[0-9]', COLLECT_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "Script appears to have hardcoded items_in_stock value. Values must be dynamically fetched."


class TestReportJsonStructure:
    """Test that report.json has the correct structure."""

    def test_report_json_exists(self):
        assert os.path.isfile(REPORT_JSON), \
            f"Report JSON file does not exist at {REPORT_JSON}"

    def test_report_json_is_valid_json(self):
        with open(REPORT_JSON, "r") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Report JSON is not valid JSON: {e}")

    def test_report_json_has_timestamp(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        assert "timestamp" in data, "Report JSON missing 'timestamp' field"
        assert isinstance(data["timestamp"], str), "timestamp should be a string"
        # Check it looks like an ISO format timestamp
        assert len(data["timestamp"]) >= 10, \
            f"timestamp doesn't look like ISO format: {data['timestamp']}"

    def test_report_json_has_auth_section(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        assert "auth" in data, "Report JSON missing 'auth' section"
        assert data["auth"] is not None, "auth section is null - data not fetched"
        assert isinstance(data["auth"], dict), "auth should be a dictionary"

    def test_report_json_has_billing_section(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        assert "billing" in data, "Report JSON missing 'billing' section"
        assert data["billing"] is not None, "billing section is null - data not fetched"
        assert isinstance(data["billing"], dict), "billing should be a dictionary"

    def test_report_json_has_inventory_section(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        assert "inventory" in data, "Report JSON missing 'inventory' section"
        assert data["inventory"] is not None, "inventory section is null - data not fetched"
        assert isinstance(data["inventory"], dict), "inventory should be a dictionary"


class TestReportAuthData:
    """Test that auth data in report matches actual service data."""

    def _get_service_data(self, port):
        result = subprocess.run(
            ["curl", "-s", f"http://localhost:{port}/metrics"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return json.loads(result.stdout)

    def test_auth_has_active_sessions(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        auth = data.get("auth", {})
        assert "active_sessions" in auth, "auth missing 'active_sessions' field"
        assert auth["active_sessions"] is not None, "active_sessions is null"
        assert isinstance(auth["active_sessions"], (int, float)), \
            f"active_sessions should be numeric, got {type(auth['active_sessions'])}"

    def test_auth_has_failed_logins(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        auth = data.get("auth", {})
        assert "failed_logins" in auth, "auth missing 'failed_logins' field"
        assert auth["failed_logins"] is not None, "failed_logins is null"
        assert isinstance(auth["failed_logins"], (int, float)), \
            f"failed_logins should be numeric, got {type(auth['failed_logins'])}"

    def test_auth_has_token_refreshes(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        auth = data.get("auth", {})
        assert "token_refreshes" in auth, "auth missing 'token_refreshes' field"
        assert auth["token_refreshes"] is not None, "token_refreshes is null"
        assert isinstance(auth["token_refreshes"], (int, float)), \
            f"token_refreshes should be numeric, got {type(auth['token_refreshes'])}"

    def test_auth_values_match_service(self):
        """Report auth values should match what the service returns."""
        with open(REPORT_JSON, "r") as f:
            report_data = json.load(f)

        service_data = self._get_service_data(9001)
        report_auth = report_data.get("auth", {})

        for key in AUTH_METRICS_KEYS:
            assert report_auth.get(key) == service_data.get(key), \
                f"auth.{key} mismatch: report has {report_auth.get(key)}, service returns {service_data.get(key)}"


class TestReportBillingData:
    """Test that billing data in report matches actual service data."""

    def _get_service_data(self, port):
        result = subprocess.run(
            ["curl", "-s", f"http://localhost:{port}/metrics"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return json.loads(result.stdout)

    def test_billing_has_transactions_today(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        billing = data.get("billing", {})
        assert "transactions_today" in billing, "billing missing 'transactions_today' field"
        assert billing["transactions_today"] is not None, "transactions_today is null"
        assert isinstance(billing["transactions_today"], (int, float)), \
            f"transactions_today should be numeric, got {type(billing['transactions_today'])}"

    def test_billing_has_revenue_cents(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        billing = data.get("billing", {})
        assert "revenue_cents" in billing, "billing missing 'revenue_cents' field"
        assert billing["revenue_cents"] is not None, "revenue_cents is null"
        assert isinstance(billing["revenue_cents"], (int, float)), \
            f"revenue_cents should be numeric, got {type(billing['revenue_cents'])}"

    def test_billing_has_refunds(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        billing = data.get("billing", {})
        assert "refunds" in billing, "billing missing 'refunds' field"
        assert billing["refunds"] is not None, "refunds is null"
        assert isinstance(billing["refunds"], (int, float)), \
            f"refunds should be numeric, got {type(billing['refunds'])}"

    def test_billing_values_match_service(self):
        """Report billing values should match what the service returns."""
        with open(REPORT_JSON, "r") as f:
            report_data = json.load(f)

        service_data = self._get_service_data(9002)
        report_billing = report_data.get("billing", {})

        for key in BILLING_METRICS_KEYS:
            assert report_billing.get(key) == service_data.get(key), \
                f"billing.{key} mismatch: report has {report_billing.get(key)}, service returns {service_data.get(key)}"


class TestReportInventoryData:
    """Test that inventory data in report matches actual service data."""

    def _get_service_data(self, port):
        result = subprocess.run(
            ["curl", "-s", f"http://localhost:{port}/metrics"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return json.loads(result.stdout)

    def test_inventory_has_items_in_stock(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        inventory = data.get("inventory", {})
        assert "items_in_stock" in inventory, "inventory missing 'items_in_stock' field"
        assert inventory["items_in_stock"] is not None, "items_in_stock is null"
        assert isinstance(inventory["items_in_stock"], (int, float)), \
            f"items_in_stock should be numeric, got {type(inventory['items_in_stock'])}"

    def test_inventory_has_pending_orders(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        inventory = data.get("inventory", {})
        assert "pending_orders" in inventory, "inventory missing 'pending_orders' field"
        assert inventory["pending_orders"] is not None, "pending_orders is null"
        assert isinstance(inventory["pending_orders"], (int, float)), \
            f"pending_orders should be numeric, got {type(inventory['pending_orders'])}"

    def test_inventory_has_backorders(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        inventory = data.get("inventory", {})
        assert "backorders" in inventory, "inventory missing 'backorders' field"
        assert inventory["backorders"] is not None, "backorders is null"
        assert isinstance(inventory["backorders"], (int, float)), \
            f"backorders should be numeric, got {type(inventory['backorders'])}"

    def test_inventory_values_match_service(self):
        """Report inventory values should match what the service returns."""
        with open(REPORT_JSON, "r") as f:
            report_data = json.load(f)

        service_data = self._get_service_data(9003)
        report_inventory = report_data.get("inventory", {})

        for key in INVENTORY_METRICS_KEYS:
            assert report_inventory.get(key) == service_data.get(key), \
                f"inventory.{key} mismatch: report has {report_inventory.get(key)}, service returns {service_data.get(key)}"


class TestReportNoNulls:
    """Comprehensive check that report has no null values for service data."""

    def test_no_null_values_in_auth(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        auth = data.get("auth")
        assert auth is not None, "auth section is null"

        for key in AUTH_METRICS_KEYS:
            value = auth.get(key)
            assert value is not None, \
                f"auth.{key} is null - the script is still not fetching data correctly"

    def test_no_null_values_in_billing(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        billing = data.get("billing")
        assert billing is not None, "billing section is null"

        for key in BILLING_METRICS_KEYS:
            value = billing.get(key)
            assert value is not None, \
                f"billing.{key} is null - the script is still not fetching data correctly"

    def test_no_null_values_in_inventory(self):
        with open(REPORT_JSON, "r") as f:
            data = json.load(f)

        inventory = data.get("inventory")
        assert inventory is not None, "inventory section is null"

        for key in INVENTORY_METRICS_KEYS:
            value = inventory.get(key)
            assert value is not None, \
                f"inventory.{key} is null - the script is still not fetching data correctly"
