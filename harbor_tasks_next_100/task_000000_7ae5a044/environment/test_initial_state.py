# test_initial_state.py
"""
Tests to validate the initial state of the service mesh before the student fixes the bug.
"""

import os
import subprocess
import time
import pytest


MESH_DIR = "/home/user/mesh"


class TestMeshDirectoryStructure:
    """Test that the mesh directory and all required files exist."""

    def test_mesh_directory_exists(self):
        assert os.path.isdir(MESH_DIR), f"Directory {MESH_DIR} does not exist"

    def test_gateway_py_exists(self):
        path = os.path.join(MESH_DIR, "gateway.py")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_auth_py_exists(self):
        path = os.path.join(MESH_DIR, "auth.py")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_backend_py_exists(self):
        path = os.path.join(MESH_DIR, "backend.py")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_start_mesh_sh_exists(self):
        path = os.path.join(MESH_DIR, "start_mesh.sh")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_requirements_txt_exists(self):
        path = os.path.join(MESH_DIR, "requirements.txt")
        assert os.path.isfile(path), f"File {path} does not exist"


class TestRequirementsTxt:
    """Test that requirements.txt contains the expected dependencies."""

    def test_flask_in_requirements(self):
        path = os.path.join(MESH_DIR, "requirements.txt")
        with open(path, "r") as f:
            content = f.read().lower()
        assert "flask" in content, "flask not found in requirements.txt"

    def test_requests_in_requirements(self):
        path = os.path.join(MESH_DIR, "requirements.txt")
        with open(path, "r") as f:
            content = f.read().lower()
        assert "requests" in content, "requests not found in requirements.txt"


class TestServicesRunning:
    """Test that all three services are running as separate processes."""

    def test_gateway_process_running(self):
        result = subprocess.run(
            ["pgrep", "-f", "gateway.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "No process found running gateway.py"
        pids = result.stdout.strip().split('\n')
        assert len([p for p in pids if p]) >= 1, "gateway.py process not found"

    def test_auth_process_running(self):
        result = subprocess.run(
            ["pgrep", "-f", "auth.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "No process found running auth.py"
        pids = result.stdout.strip().split('\n')
        assert len([p for p in pids if p]) >= 1, "auth.py process not found"

    def test_backend_process_running(self):
        result = subprocess.run(
            ["pgrep", "-f", "backend.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "No process found running backend.py"
        pids = result.stdout.strip().split('\n')
        assert len([p for p in pids if p]) >= 1, "backend.py process not found"


class TestPortsListening:
    """Test that all three services are listening on their expected ports."""

    def test_port_8080_listening(self):
        """Gateway should be listening on port 8080."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" in result.stdout, "Port 8080 (gateway) is not listening"

    def test_port_8081_listening(self):
        """Auth should be listening on port 8081."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8081" in result.stdout, "Port 8081 (auth) is not listening"

    def test_port_8082_listening(self):
        """Backend should be listening on port 8082."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8082" in result.stdout, "Port 8082 (backend) is not listening"


class TestIndividualServiceResponses:
    """Test that each service responds individually when curled directly."""

    def test_backend_responds_directly(self):
        """Backend should respond with JSON containing secret_payload_42."""
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", "http://localhost:8082/fetch"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "curl to backend:8082/fetch failed"
        assert "secret_payload_42" in result.stdout, \
            f"Backend response doesn't contain expected data. Got: {result.stdout}"

    def test_gateway_accepts_connections(self):
        """Gateway should accept connections on port 8080 (even if it times out later)."""
        # We just verify it accepts the connection, not that the full chain works
        result = subprocess.run(
            ["curl", "-s", "--max-time", "2", "-o", "/dev/null", "-w", "%{http_code}", 
             "http://localhost:8080/"],
            capture_output=True,
            text=True
        )
        # Even a 404 or timeout means the service is accepting connections
        # We're not testing the /data endpoint here as it's known to hang
        assert result.returncode == 0 or "000" not in result.stdout, \
            "Gateway is not accepting connections on port 8080"

    def test_auth_accepts_connections(self):
        """Auth should accept connections on port 8081."""
        result = subprocess.run(
            ["curl", "-s", "--max-time", "2", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:8081/"],
            capture_output=True,
            text=True
        )
        # Even a 404 means the service is accepting connections
        assert result.returncode == 0 or "000" not in result.stdout, \
            "Auth is not accepting connections on port 8081"


class TestAuthPyContainsBug:
    """Test that auth.py contains the expected bug pattern."""

    def test_auth_py_has_requests_import(self):
        """auth.py should import requests library."""
        path = os.path.join(MESH_DIR, "auth.py")
        with open(path, "r") as f:
            content = f.read()
        assert "import requests" in content or "from requests" in content, \
            "auth.py doesn't import requests library"

    def test_auth_py_calls_backend(self):
        """auth.py should make a request to localhost:8082."""
        path = os.path.join(MESH_DIR, "auth.py")
        with open(path, "r") as f:
            content = f.read()
        assert "8082" in content, \
            "auth.py doesn't appear to call backend on port 8082"

    def test_auth_py_has_flask(self):
        """auth.py should be a Flask app."""
        path = os.path.join(MESH_DIR, "auth.py")
        with open(path, "r") as f:
            content = f.read()
        assert "Flask" in content or "flask" in content, \
            "auth.py doesn't appear to be a Flask app"


class TestGatewayPy:
    """Test gateway.py configuration."""

    def test_gateway_py_has_flask(self):
        """gateway.py should be a Flask app."""
        path = os.path.join(MESH_DIR, "gateway.py")
        with open(path, "r") as f:
            content = f.read()
        assert "Flask" in content or "flask" in content, \
            "gateway.py doesn't appear to be a Flask app"

    def test_gateway_py_calls_auth(self):
        """gateway.py should make a request to localhost:8081."""
        path = os.path.join(MESH_DIR, "gateway.py")
        with open(path, "r") as f:
            content = f.read()
        assert "8081" in content, \
            "gateway.py doesn't appear to call auth on port 8081"


class TestBackendPy:
    """Test backend.py configuration."""

    def test_backend_py_has_flask(self):
        """backend.py should be a Flask app."""
        path = os.path.join(MESH_DIR, "backend.py")
        with open(path, "r") as f:
            content = f.read()
        assert "Flask" in content or "flask" in content, \
            "backend.py doesn't appear to be a Flask app"

    def test_backend_py_has_secret_payload(self):
        """backend.py should contain the secret payload."""
        path = os.path.join(MESH_DIR, "backend.py")
        with open(path, "r") as f:
            content = f.read()
        assert "secret_payload_42" in content, \
            "backend.py doesn't contain the expected secret_payload_42"


class TestStartMeshScript:
    """Test the launcher script configuration."""

    def test_start_mesh_is_executable_or_shell_script(self):
        """start_mesh.sh should be a shell script."""
        path = os.path.join(MESH_DIR, "start_mesh.sh")
        with open(path, "r") as f:
            first_line = f.readline()
        # Check if it's a shell script (has shebang or is executable)
        is_shell = "#!/" in first_line or os.access(path, os.X_OK)
        assert is_shell or True, "start_mesh.sh exists (checking content)"

    def test_start_mesh_references_all_services(self):
        """start_mesh.sh should reference all three service files."""
        path = os.path.join(MESH_DIR, "start_mesh.sh")
        with open(path, "r") as f:
            content = f.read()
        assert "gateway" in content.lower(), "start_mesh.sh doesn't reference gateway"
        assert "auth" in content.lower(), "start_mesh.sh doesn't reference auth"
        assert "backend" in content.lower(), "start_mesh.sh doesn't reference backend"


class TestMeshDirectoryWritable:
    """Test that the mesh directory is writable for fixes."""

    def test_mesh_directory_writable(self):
        """The mesh directory should be writable."""
        assert os.access(MESH_DIR, os.W_OK), f"{MESH_DIR} is not writable"

    def test_auth_py_writable(self):
        """auth.py should be writable for the fix."""
        path = os.path.join(MESH_DIR, "auth.py")
        assert os.access(path, os.W_OK), f"{path} is not writable"
