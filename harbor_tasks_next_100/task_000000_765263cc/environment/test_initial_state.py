# test_initial_state.py
"""
Validates the initial state of the OS/filesystem before the student performs the action.
This tests the scenario where pytest fails with ModuleNotFoundError for requests
due to a PATH/venv mismatch issue.
"""

import os
import subprocess
import pytest


class TestProjectStructure:
    """Test that the project directory structure exists."""

    def test_project_root_exists(self):
        """Project root /home/user/qa/ must exist."""
        assert os.path.isdir("/home/user/qa"), \
            "Project root /home/user/qa/ does not exist"

    def test_tests_directory_exists(self):
        """Tests directory must exist."""
        assert os.path.isdir("/home/user/qa/tests"), \
            "Tests directory /home/user/qa/tests/ does not exist"

    def test_test_api_file_exists(self):
        """Test file test_api.py must exist."""
        assert os.path.isfile("/home/user/qa/tests/test_api.py"), \
            "Test file /home/user/qa/tests/test_api.py does not exist"

    def test_requirements_file_exists(self):
        """requirements.txt must exist."""
        assert os.path.isfile("/home/user/qa/requirements.txt"), \
            "Requirements file /home/user/qa/requirements.txt does not exist"

    def test_requirements_content(self):
        """requirements.txt must contain requests and pytest."""
        with open("/home/user/qa/requirements.txt", "r") as f:
            content = f.read()
        assert "requests" in content, \
            "requirements.txt does not contain 'requests'"
        assert "pytest" in content, \
            "requirements.txt does not contain 'pytest'"


class TestQaEnvVenv:
    """Test the qa-env virtual environment state."""

    def test_qa_env_exists(self):
        """qa-env venv directory must exist."""
        assert os.path.isdir("/home/user/qa/qa-env"), \
            "qa-env venv /home/user/qa/qa-env/ does not exist"

    def test_qa_env_bin_exists(self):
        """qa-env bin directory must exist."""
        assert os.path.isdir("/home/user/qa/qa-env/bin"), \
            "qa-env bin directory /home/user/qa/qa-env/bin/ does not exist"

    def test_qa_env_python_exists(self):
        """qa-env python executable must exist."""
        assert os.path.isfile("/home/user/qa/qa-env/bin/python"), \
            "qa-env python /home/user/qa/qa-env/bin/python does not exist"

    def test_qa_env_pip_exists(self):
        """qa-env pip executable must exist."""
        assert os.path.isfile("/home/user/qa/qa-env/bin/pip"), \
            "qa-env pip /home/user/qa/qa-env/bin/pip does not exist"

    def test_qa_env_python_works(self):
        """qa-env python must be functional."""
        result = subprocess.run(
            ["/home/user/qa/qa-env/bin/python", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"qa-env python is not functional: {result.stderr}"

    def test_qa_env_has_requests(self):
        """qa-env must have requests installed."""
        result = subprocess.run(
            ["/home/user/qa/qa-env/bin/python", "-c", "import requests; print(requests.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"qa-env does not have requests installed: {result.stderr}"

    def test_qa_env_does_not_have_pytest(self):
        """qa-env must NOT have pytest installed (this is the bug)."""
        pytest_path = "/home/user/qa/qa-env/bin/pytest"
        assert not os.path.exists(pytest_path), \
            f"qa-env has pytest installed at {pytest_path} - this should NOT exist for the initial bug state"


class TestToxVenv:
    """Test the old tox venv state."""

    def test_tox_venv_exists(self):
        """Tox venv directory must exist."""
        assert os.path.isdir("/home/user/qa/.tox/py311"), \
            "Tox venv /home/user/qa/.tox/py311/ does not exist"

    def test_tox_pytest_exists(self):
        """Tox venv must have pytest installed."""
        assert os.path.isfile("/home/user/qa/.tox/py311/bin/pytest"), \
            "Tox pytest /home/user/qa/.tox/py311/bin/pytest does not exist"

    def test_tox_pytest_executable(self):
        """Tox pytest must be executable."""
        assert os.access("/home/user/qa/.tox/py311/bin/pytest", os.X_OK), \
            "Tox pytest /home/user/qa/.tox/py311/bin/pytest is not executable"

    def test_tox_venv_does_not_have_requests(self):
        """Tox venv must NOT have requests installed (this causes the import error)."""
        result = subprocess.run(
            ["/home/user/qa/.tox/py311/bin/python", "-c", "import requests"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "Tox venv has requests installed - it should NOT have requests for the bug to manifest"


class TestPathConfiguration:
    """Test the PATH configuration that causes the bug."""

    def test_which_pytest_resolves_to_tox(self):
        """which pytest should resolve to tox venv (the bug)."""
        # Simulate the PATH as described
        env = os.environ.copy()
        env["PATH"] = "/home/user/qa/qa-env/bin:/home/user/qa/.tox/py311/bin:/usr/local/bin:/usr/bin:/bin"

        result = subprocess.run(
            ["which", "pytest"],
            capture_output=True,
            text=True,
            env=env
        )

        assert result.returncode == 0, \
            "pytest not found in PATH"
        pytest_path = result.stdout.strip()
        assert pytest_path == "/home/user/qa/.tox/py311/bin/pytest", \
            f"Expected pytest to resolve to /home/user/qa/.tox/py311/bin/pytest but got {pytest_path}"

    def test_which_python_resolves_to_qa_env(self):
        """which python should resolve to qa-env (works fine)."""
        env = os.environ.copy()
        env["PATH"] = "/home/user/qa/qa-env/bin:/home/user/qa/.tox/py311/bin:/usr/local/bin:/usr/bin:/bin"

        result = subprocess.run(
            ["which", "python"],
            capture_output=True,
            text=True,
            env=env
        )

        assert result.returncode == 0, \
            "python not found in PATH"
        python_path = result.stdout.strip()
        assert python_path == "/home/user/qa/qa-env/bin/python", \
            f"Expected python to resolve to /home/user/qa/qa-env/bin/python but got {python_path}"


class TestBugReproduction:
    """Test that the bug can be reproduced."""

    def test_python_import_requests_works(self):
        """Running python -c 'import requests' with qa-env python should work."""
        result = subprocess.run(
            ["/home/user/qa/qa-env/bin/python", "-c", "import requests"],
            capture_output=True,
            text=True,
            cwd="/home/user/qa"
        )
        assert result.returncode == 0, \
            f"python -c 'import requests' failed when it should work: {result.stderr}"

    def test_tox_pytest_fails_with_import_error(self):
        """Running pytest from tox venv should fail with ModuleNotFoundError."""
        result = subprocess.run(
            ["/home/user/qa/.tox/py311/bin/pytest", "tests/", "-v"],
            capture_output=True,
            text=True,
            cwd="/home/user/qa"
        )
        assert result.returncode != 0, \
            "Tox pytest should fail but it succeeded"
        # Check for the import error
        combined_output = result.stdout + result.stderr
        assert "ModuleNotFoundError" in combined_output or "No module named" in combined_output, \
            f"Expected ModuleNotFoundError but got different error: {combined_output}"


class TestTestFileContent:
    """Test that the test file has the expected content."""

    def test_test_api_imports_requests(self):
        """test_api.py must import requests."""
        with open("/home/user/qa/tests/test_api.py", "r") as f:
            content = f.read()
        assert "import requests" in content, \
            "test_api.py does not import requests"

    def test_test_api_has_test_function(self):
        """test_api.py must have a test function."""
        with open("/home/user/qa/tests/test_api.py", "r") as f:
            content = f.read()
        assert "def test_" in content, \
            "test_api.py does not have a test function"


class TestDirectoryWritable:
    """Test that directories are writable."""

    def test_qa_dir_writable(self):
        """Project directory must be writable."""
        assert os.access("/home/user/qa", os.W_OK), \
            "/home/user/qa is not writable"

    def test_qa_env_bin_writable(self):
        """qa-env bin directory must be writable."""
        assert os.access("/home/user/qa/qa-env/bin", os.W_OK), \
            "/home/user/qa/qa-env/bin is not writable"
