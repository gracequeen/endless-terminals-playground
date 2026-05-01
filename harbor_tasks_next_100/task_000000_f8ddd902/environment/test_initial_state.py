# test_initial_state.py
"""
Tests to validate the initial state of the edge-gateway environment
before the student attempts to fix the async event loop bug.
"""

import os
import subprocess
import pytest


class TestDirectoryStructure:
    """Verify the edge-gateway directory and files exist."""

    def test_edge_gateway_directory_exists(self):
        """The /home/user/edge-gateway directory must exist."""
        path = "/home/user/edge-gateway"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_gateway_py_exists(self):
        """The main gateway.py file must exist."""
        path = "/home/user/edge-gateway/gateway.py"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_start_sh_exists(self):
        """The start.sh script must exist."""
        path = "/home/user/edge-gateway/start.sh"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_start_sh_is_executable(self):
        """The start.sh script must be executable."""
        path = "/home/user/edge-gateway/start.sh"
        assert os.access(path, os.X_OK), f"File {path} is not executable"

    def test_logs_directory_exists(self):
        """The logs directory must exist."""
        path = "/home/user/edge-gateway/logs"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_edge_gateway_directory_is_writable(self):
        """The edge-gateway directory must be writable."""
        path = "/home/user/edge-gateway"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestGatewayPyContent:
    """Verify gateway.py contains the expected buggy code."""

    def test_gateway_py_contains_aiohttp_import(self):
        """gateway.py must use aiohttp."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "from aiohttp import web" in content or "import aiohttp" in content, \
            "gateway.py must import aiohttp"

    def test_gateway_py_contains_aiomqtt_import(self):
        """gateway.py must use aiomqtt."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "aiomqtt" in content, "gateway.py must import aiomqtt"

    def test_gateway_py_contains_health_handler(self):
        """gateway.py must have a health_handler function."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "health_handler" in content, "gateway.py must contain health_handler"

    def test_gateway_py_contains_sensor_handler(self):
        """gateway.py must have a sensor_handler function."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "sensor_handler" in content, "gateway.py must contain sensor_handler"

    def test_gateway_py_contains_health_endpoint(self):
        """gateway.py must define /health endpoint."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "/health" in content, "gateway.py must define /health endpoint"

    def test_gateway_py_contains_sensor_endpoint(self):
        """gateway.py must define /sensor endpoint."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "/sensor" in content, "gateway.py must define /sensor endpoint"

    def test_gateway_py_uses_port_8080(self):
        """gateway.py must use port 8080."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "8080" in content, "gateway.py must use port 8080"

    def test_gateway_py_uses_mqtt_port_1883(self):
        """gateway.py must connect to MQTT on port 1883."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "1883" in content, "gateway.py must use MQTT port 1883"

    def test_gateway_py_contains_web_run_app(self):
        """gateway.py must contain web.run_app (the buggy pattern)."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "web.run_app" in content, \
            "gateway.py must contain web.run_app() - this is part of the bug to fix"

    def test_gateway_py_contains_mqtt_loop(self):
        """gateway.py must have an mqtt_loop function."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "mqtt_loop" in content, "gateway.py must contain mqtt_loop function"


class TestStartShContent:
    """Verify start.sh has expected content."""

    def test_start_sh_launches_mosquitto(self):
        """start.sh must launch mosquitto."""
        path = "/home/user/edge-gateway/start.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "mosquitto" in content, "start.sh must launch mosquitto"

    def test_start_sh_runs_gateway_py(self):
        """start.sh must run gateway.py."""
        path = "/home/user/edge-gateway/start.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "gateway.py" in content or "python" in content, \
            "start.sh must run gateway.py"


class TestSystemDependencies:
    """Verify required system dependencies are available."""

    def test_python3_available(self):
        """Python 3 must be available."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not available"

    def test_mosquitto_installed(self):
        """mosquitto broker must be installed."""
        result = subprocess.run(
            ["which", "mosquitto"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "mosquitto is not installed"

    def test_mosquitto_pub_installed(self):
        """mosquitto_pub client must be installed."""
        result = subprocess.run(
            ["which", "mosquitto_pub"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "mosquitto_pub is not installed"

    def test_mosquitto_sub_installed(self):
        """mosquitto_sub client must be installed."""
        result = subprocess.run(
            ["which", "mosquitto_sub"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "mosquitto_sub is not installed"

    def test_curl_available(self):
        """curl must be available for testing."""
        result = subprocess.run(
            ["which", "curl"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "curl is not available"


class TestPythonPackages:
    """Verify required Python packages are installed."""

    def test_aiohttp_installed(self):
        """aiohttp package must be installed."""
        result = subprocess.run(
            ["python3", "-c", "import aiohttp; print(aiohttp.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"aiohttp is not installed: {result.stderr}"

    def test_aiomqtt_installed(self):
        """aiomqtt package must be installed."""
        result = subprocess.run(
            ["python3", "-c", "import aiomqtt; print('ok')"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"aiomqtt is not installed: {result.stderr}"


class TestInitialPortState:
    """Verify ports are not already in use before starting."""

    def test_port_8080_not_in_use(self):
        """Port 8080 should not be in use initially."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if anything is listening on 8080
        lines = result.stdout.split('\n')
        for line in lines:
            if ':8080' in line and 'LISTEN' in line:
                pytest.fail("Port 8080 is already in use - please stop any existing services")

    def test_port_1883_not_in_use(self):
        """Port 1883 should not be in use initially (mosquitto not yet started)."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if anything is listening on 1883
        lines = result.stdout.split('\n')
        for line in lines:
            if ':1883' in line and 'LISTEN' in line:
                pytest.fail("Port 1883 is already in use - please stop any existing mosquitto")


class TestNoExistingProcesses:
    """Verify no gateway or mosquitto processes are running."""

    def test_no_gateway_process_running(self):
        """No gateway.py process should be running initially."""
        result = subprocess.run(
            ["pgrep", "-f", "gateway.py"],
            capture_output=True,
            text=True
        )
        # pgrep returns 0 if processes found, 1 if none found
        if result.returncode == 0:
            pytest.fail("gateway.py is already running - please stop it first")

    def test_no_mosquitto_process_running(self):
        """No mosquitto process should be running initially."""
        result = subprocess.run(
            ["pgrep", "-x", "mosquitto"],
            capture_output=True,
            text=True
        )
        # pgrep returns 0 if processes found, 1 if none found
        if result.returncode == 0:
            pytest.fail("mosquitto is already running - please stop it first")
