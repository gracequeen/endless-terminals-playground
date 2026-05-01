# test_final_state.py
"""
Tests to validate the final state of the edge-gateway environment
after the student has fixed the async event loop bug.

The gateway should:
1. Respond to HTTP requests on port 8080 while MQTT is connected
2. Return healthy status with MQTT connected on /health
3. Accept sensor data on /sensor and publish to MQTT
4. Use aiohttp for HTTP and aiomqtt for MQTT (no library changes)
5. Not use threading to sidestep the async issue
"""

import json
import os
import signal
import socket
import subprocess
import time
import pytest


def cleanup_processes():
    """Kill any running gateway or mosquitto processes."""
    subprocess.run(["pkill", "-f", "gateway.py"], capture_output=True)
    subprocess.run(["pkill", "-x", "mosquitto"], capture_output=True)
    time.sleep(1)


def wait_for_port(port, timeout=10):
    """Wait for a port to become available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def running_gateway():
    """Start the gateway stack and yield, then cleanup."""
    cleanup_processes()

    # Start the gateway stack
    proc = subprocess.Popen(
        ["./start.sh"],
        cwd="/home/user/edge-gateway",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    # Wait for services to start
    time.sleep(3)

    # Verify ports are listening
    mqtt_ready = wait_for_port(1883, timeout=5)
    http_ready = wait_for_port(8080, timeout=5)

    yield {
        "process": proc,
        "mqtt_ready": mqtt_ready,
        "http_ready": http_ready
    }

    # Cleanup
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except:
        pass
    cleanup_processes()


class TestServicesRunning:
    """Verify both services are running and accessible."""

    def test_mosquitto_running(self, running_gateway):
        """Mosquitto broker must be running on port 1883."""
        assert running_gateway["mqtt_ready"], \
            "Mosquitto is not listening on port 1883 after startup"

    def test_http_server_running(self, running_gateway):
        """HTTP server must be running on port 8080."""
        assert running_gateway["http_ready"], \
            "HTTP server is not listening on port 8080 after startup"

    def test_mosquitto_process_exists(self, running_gateway):
        """Mosquitto process must be running."""
        result = subprocess.run(
            ["pgrep", "-x", "mosquitto"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Mosquitto process is not running"


class TestHealthEndpoint:
    """Test the /health endpoint responds correctly."""

    def test_health_endpoint_responds(self, running_gateway):
        """Health endpoint must respond within timeout (not hang)."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "http://localhost:8080/health"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Health endpoint timed out or failed: {result.stderr}"

    def test_health_returns_json(self, running_gateway):
        """Health endpoint must return valid JSON."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "http://localhost:8080/health"],
            capture_output=True,
            text=True
        )
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"Health endpoint did not return valid JSON: {result.stdout}")

    def test_health_returns_200(self, running_gateway):
        """Health endpoint must return HTTP 200."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:8080/health"],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "200", \
            f"Health endpoint returned status {result.stdout.strip()}, expected 200"

    def test_health_status_healthy(self, running_gateway):
        """Health endpoint must report status as healthy."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "http://localhost:8080/health"],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        assert data.get("status") == "healthy", \
            f"Health status is '{data.get('status')}', expected 'healthy'"

    def test_health_mqtt_connected(self, running_gateway):
        """Health endpoint must report MQTT as connected."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "http://localhost:8080/health"],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        assert data.get("mqtt") == "connected", \
            f"MQTT status is '{data.get('mqtt')}', expected 'connected'"


class TestSensorEndpoint:
    """Test the /sensor endpoint responds correctly."""

    def test_sensor_endpoint_responds(self, running_gateway):
        """Sensor endpoint must respond within timeout."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", '{"temp": 22.5}',
             "http://localhost:8080/sensor"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Sensor endpoint timed out or failed: {result.stderr}"

    def test_sensor_returns_200(self, running_gateway):
        """Sensor endpoint must return HTTP 200."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",
             "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", '{"temp": 22.5}',
             "http://localhost:8080/sensor"],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == "200", \
            f"Sensor endpoint returned status {result.stdout.strip()}, expected 200"

    def test_sensor_returns_accepted(self, running_gateway):
        """Sensor endpoint must return accepted: true."""
        result = subprocess.run(
            ["curl", "-s", "-m", "5", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", '{"temp": 22.5}',
             "http://localhost:8080/sensor"],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        assert data.get("accepted") == True, \
            f"Sensor response 'accepted' is {data.get('accepted')}, expected True"


class TestMqttIntegration:
    """Test that MQTT actually works end-to-end."""

    def test_sensor_publishes_to_mqtt(self, running_gateway):
        """Data posted to /sensor must be published to MQTT topic."""
        # Start mosquitto_sub to listen for one message
        sub_proc = subprocess.Popen(
            ["mosquitto_sub", "-t", "sensors/data", "-C", "1", "-W", "5"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give subscriber time to connect
        time.sleep(0.5)

        # Post data to sensor endpoint
        test_data = {"test_value": 42, "source": "pytest"}
        curl_result = subprocess.run(
            ["curl", "-s", "-m", "5", "-X", "POST",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(test_data),
             "http://localhost:8080/sensor"],
            capture_output=True,
            text=True
        )

        # Wait for subscriber to receive message
        try:
            stdout, stderr = sub_proc.communicate(timeout=6)
        except subprocess.TimeoutExpired:
            sub_proc.kill()
            pytest.fail("mosquitto_sub timed out waiting for message - MQTT publish not working")

        assert sub_proc.returncode == 0, \
            f"mosquitto_sub failed: {stderr}"
        assert "test_value" in stdout or "42" in stdout, \
            f"MQTT message did not contain expected data. Received: {stdout}"


class TestCodeRequirements:
    """Verify the code still meets requirements (no shortcuts)."""

    def test_gateway_py_still_uses_aiohttp(self):
        """gateway.py must still use aiohttp."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "aiohttp" in content, \
            "gateway.py must still use aiohttp - cannot switch to Flask or other sync frameworks"

    def test_gateway_py_still_uses_aiomqtt(self):
        """gateway.py must still use aiomqtt."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "aiomqtt" in content, \
            "gateway.py must still use aiomqtt - cannot remove MQTT functionality"

    def test_gateway_py_no_threading_import(self):
        """gateway.py must not use threading module to sidestep async issue."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        # Check for threading imports that would indicate a threading-based workaround
        import_patterns = [
            "import threading",
            "from threading import",
            "import concurrent.futures",
            "from concurrent.futures import ThreadPoolExecutor",
        ]
        for pattern in import_patterns:
            if pattern in content:
                # Allow if it's in a comment
                lines = content.split('\n')
                for line in lines:
                    stripped = line.strip()
                    if pattern in stripped and not stripped.startswith('#'):
                        pytest.fail(
                            f"gateway.py uses '{pattern}' - solution must properly integrate "
                            "both HTTP and MQTT in one event loop, not use threading"
                        )

    def test_gateway_py_has_health_endpoint(self):
        """gateway.py must still have /health endpoint."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "/health" in content, "gateway.py must still define /health endpoint"

    def test_gateway_py_has_sensor_endpoint(self):
        """gateway.py must still have /sensor endpoint."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "/sensor" in content, "gateway.py must still define /sensor endpoint"

    def test_gateway_py_uses_port_8080(self):
        """gateway.py must still use port 8080."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "8080" in content, "gateway.py must still use port 8080"

    def test_gateway_py_uses_mqtt_port_1883(self):
        """gateway.py must still connect to MQTT on port 1883."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        assert "1883" in content, "gateway.py must still use MQTT port 1883"

    def test_health_actually_checks_mqtt(self):
        """Health endpoint must actually check MQTT connectivity, not return hardcoded response."""
        path = "/home/user/edge-gateway/gateway.py"
        with open(path, 'r') as f:
            content = f.read()
        # The health handler should reference mqtt_client or similar
        # and check connection status
        assert "mqtt" in content.lower() and ("is_connected" in content or "client" in content), \
            "Health endpoint must actually check MQTT connectivity status"


class TestConcurrentRequests:
    """Test that HTTP server handles requests while MQTT is active."""

    def test_multiple_health_requests(self, running_gateway):
        """Multiple rapid health requests should all succeed."""
        for i in range(5):
            result = subprocess.run(
                ["curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",
                 "http://localhost:8080/health"],
                capture_output=True,
                text=True
            )
            assert result.stdout.strip() == "200", \
                f"Health request {i+1} failed with status {result.stdout.strip()}"

    def test_interleaved_health_and_sensor(self, running_gateway):
        """Interleaved health and sensor requests should all succeed."""
        for i in range(3):
            # Health request
            health_result = subprocess.run(
                ["curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",
                 "http://localhost:8080/health"],
                capture_output=True,
                text=True
            )
            assert health_result.stdout.strip() == "200", \
                f"Health request {i+1} failed"

            # Sensor request
            sensor_result = subprocess.run(
                ["curl", "-s", "-m", "5", "-o", "/dev/null", "-w", "%{http_code}",
                 "-X", "POST",
                 "-H", "Content-Type: application/json",
                 "-d", f'{{"iteration": {i}}}',
                 "http://localhost:8080/sensor"],
                capture_output=True,
                text=True
            )
            assert sensor_result.stdout.strip() == "200", \
                f"Sensor request {i+1} failed"
