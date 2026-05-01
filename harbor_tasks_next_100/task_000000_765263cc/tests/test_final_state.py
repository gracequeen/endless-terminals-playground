# test_final_state.py
"""
Validates the final state of the OS/filesystem after the student has fixed
the pytest/venv mismatch issue. The fix should ensure that running pytest
from the qa-env virtual environment works correctly.
"""

import os
import subprocess
import pytest


class TestInvariantsPreserved:
    """Test that invariants are preserved - files that shouldn't change."""

    def test_test_api_file_exists(self):
        """Test file test_api.py must still exist."""
        assert os.path.isfile("/home/user/qa/tests/test_api.py"), \
            "Test file /home/user/qa/tests/test_api.py does not exist"

    def test_test_api_content_unchanged(self):
        """test_api.py must have the expected content (byte-identical to initial)."""
        expected_content = '''import requests

def test_api_reachable():
    # Just verifies imports work; doesn't hit network
    assert hasattr(requests, 'get')
    assert callable(requests.get)
'''
        with open("/home/user/qa/tests/test_api.py", "r") as f:
            actual_content = f.read()

        # Normalize line endings for comparison
        expected_normalized = expected_content.strip()
        actual_normalized = actual_content.strip()

        assert actual_normalized == expected_normalized, \
            f"test_api.py content has been modified. Expected:\n{expected_content}\nGot:\n{actual_content}"

    def test_requirements_file_exists(self):
        """requirements.txt must still exist."""
        assert os.path.isfile("/home/user/qa/requirements.txt"), \
            "Requirements file /home/user/qa/requirements.txt does not exist"

    def test_requirements_content_unchanged(self):
        """requirements.txt must contain requests and pytest."""
        with open("/home/user/qa/requirements.txt", "r") as f:
            content = f.read()
        assert "requests" in content, \
            "requirements.txt does not contain 'requests'"
        assert "pytest" in content, \
            "requirements.txt does not contain 'pytest'"


class TestQaEnvStillFunctional:
    """Test that qa-env remains a functional venv with requests installed."""

    def test_qa_env_exists(self):
        """qa-env venv directory must still exist."""
        assert os.path.isdir("/home/user/qa/qa-env"), \
            "qa-env venv /home/user/qa/qa-env/ does not exist"

    def test_qa_env_python_exists(self):
        """qa-env python executable must exist."""
        assert os.path.isfile("/home/user/qa/qa-env/bin/python"), \
            "qa-env python /home/user/qa/qa-env/bin/python does not exist"

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
        """qa-env must still have requests installed."""
        result = subprocess.run(
            ["/home/user/qa/qa-env/bin/python", "-c", "import requests; print(requests.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"qa-env does not have requests installed: {result.stderr}"


class TestAntiShortcutGuards:
    """Test that the solution doesn't take shortcuts."""

    def test_requests_not_installed_in_tox_if_tox_exists(self):
        """If .tox/py311 still exists, requests should NOT be installed there."""
        tox_python = "/home/user/qa/.tox/py311/bin/python"
        if os.path.exists(tox_python):
            result = subprocess.run(
                [tox_python, "-c", "import requests"],
                capture_output=True,
                text=True
            )
            # It's acceptable if tox is deleted, but if it exists, requests shouldn't be there
            assert result.returncode != 0, \
                "Shortcut detected: requests was installed into .tox/py311 instead of fixing the venv issue"


class TestMainFix:
    """Test that the main fix works - pytest runs successfully from qa-env."""

    def test_pytest_runs_successfully_from_qa_env(self):
        """
        The grader command: source qa-env/bin/activate && cd /home/user/qa && pytest tests/ -v
        Must exit 0 and show '1 passed'.
        """
        # We simulate the activated environment by using the qa-env python/pytest directly
        # First, check if pytest is available in qa-env
        qa_env_pytest = "/home/user/qa/qa-env/bin/pytest"
        qa_env_python = "/home/user/qa/qa-env/bin/python"

        # Try running pytest directly from qa-env if it exists
        if os.path.exists(qa_env_pytest):
            result = subprocess.run(
                [qa_env_pytest, "tests/", "-v"],
                capture_output=True,
                text=True,
                cwd="/home/user/qa"
            )
        else:
            # Otherwise, use python -m pytest from qa-env
            result = subprocess.run(
                [qa_env_python, "-m", "pytest", "tests/", "-v"],
                capture_output=True,
                text=True,
                cwd="/home/user/qa"
            )

        combined_output = result.stdout + result.stderr

        assert result.returncode == 0, \
            f"pytest did not exit with code 0. Exit code: {result.returncode}\nOutput:\n{combined_output}"

        assert "1 passed" in combined_output, \
            f"Expected '1 passed' in output but got:\n{combined_output}"

    def test_pytest_available_via_qa_env(self):
        """
        pytest must be invokable from qa-env - either as qa-env/bin/pytest 
        or via python -m pytest with qa-env's python.
        """
        qa_env_pytest = "/home/user/qa/qa-env/bin/pytest"
        qa_env_python = "/home/user/qa/qa-env/bin/python"

        # Check if pytest binary exists in qa-env
        pytest_binary_exists = os.path.exists(qa_env_pytest)

        # Check if python -m pytest works
        result = subprocess.run(
            [qa_env_python, "-m", "pytest", "--version"],
            capture_output=True,
            text=True
        )
        python_m_pytest_works = result.returncode == 0

        assert pytest_binary_exists or python_m_pytest_works, \
            "pytest is not available from qa-env. Either install pytest into qa-env " \
            "or ensure 'python -m pytest' works with qa-env's python"

    def test_no_import_error_when_running_tests(self):
        """Running tests should not produce ModuleNotFoundError."""
        qa_env_pytest = "/home/user/qa/qa-env/bin/pytest"
        qa_env_python = "/home/user/qa/qa-env/bin/python"

        if os.path.exists(qa_env_pytest):
            result = subprocess.run(
                [qa_env_pytest, "tests/", "-v"],
                capture_output=True,
                text=True,
                cwd="/home/user/qa"
            )
        else:
            result = subprocess.run(
                [qa_env_python, "-m", "pytest", "tests/", "-v"],
                capture_output=True,
                text=True,
                cwd="/home/user/qa"
            )

        combined_output = result.stdout + result.stderr

        assert "ModuleNotFoundError" not in combined_output, \
            f"ModuleNotFoundError still occurs:\n{combined_output}"
        assert "No module named" not in combined_output, \
            f"Import error still occurs:\n{combined_output}"


class TestActivatedEnvironmentBehavior:
    """Test behavior when simulating an activated qa-env environment."""

    def test_activated_env_pytest_works(self):
        """
        Simulate running with qa-env activated by setting PATH appropriately.
        This tests that `pytest tests/` works in an activated qa-env.
        """
        # Set up environment as if qa-env is activated
        env = os.environ.copy()
        env["PATH"] = f"/home/user/qa/qa-env/bin:{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = "/home/user/qa/qa-env"

        # Run pytest (should find the one in qa-env now if installed)
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v"],
            capture_output=True,
            text=True,
            cwd="/home/user/qa",
            env=env
        )

        combined_output = result.stdout + result.stderr

        assert result.returncode == 0, \
            f"pytest failed in activated qa-env. Exit code: {result.returncode}\nOutput:\n{combined_output}"

        assert "1 passed" in combined_output, \
            f"Expected '1 passed' in output but got:\n{combined_output}"

    def test_which_python_in_activated_env(self):
        """In activated qa-env, which python should point to qa-env."""
        env = os.environ.copy()
        env["PATH"] = f"/home/user/qa/qa-env/bin:{env.get('PATH', '')}"

        result = subprocess.run(
            ["which", "python"],
            capture_output=True,
            text=True,
            env=env
        )

        python_path = result.stdout.strip()
        assert python_path == "/home/user/qa/qa-env/bin/python", \
            f"Expected python to be /home/user/qa/qa-env/bin/python but got {python_path}"
