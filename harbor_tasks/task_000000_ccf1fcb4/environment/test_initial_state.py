# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies the buggy state exists as described in the task.
"""

import os
import subprocess
import pytest


BASE_DIR = "/home/user/labeler"


class TestDirectoryStructure:
    """Verify the labeler directory and required files exist."""

    def test_labeler_directory_exists(self):
        """The /home/user/labeler directory must exist."""
        assert os.path.isdir(BASE_DIR), f"Directory {BASE_DIR} does not exist"

    def test_app_directory_exists(self):
        """The app/ subdirectory must exist."""
        app_dir = os.path.join(BASE_DIR, "app")
        assert os.path.isdir(app_dir), f"Directory {app_dir} does not exist"

    def test_config_directory_exists(self):
        """The config/ subdirectory must exist."""
        config_dir = os.path.join(BASE_DIR, "config")
        assert os.path.isdir(config_dir), f"Directory {config_dir} does not exist"

    def test_venv_directory_exists(self):
        """The venv/ subdirectory must exist."""
        venv_dir = os.path.join(BASE_DIR, "venv")
        assert os.path.isdir(venv_dir), f"Virtual environment {venv_dir} does not exist"


class TestRequiredFiles:
    """Verify all required files exist."""

    def test_app_init_exists(self):
        """app/__init__.py must exist."""
        filepath = os.path.join(BASE_DIR, "app", "__init__.py")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_app_routes_exists(self):
        """app/routes.py must exist."""
        filepath = os.path.join(BASE_DIR, "app", "routes.py")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_settings_ini_exists(self):
        """config/settings.ini must exist."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_gunicorn_conf_exists(self):
        """config/gunicorn.conf.py must exist."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_start_sh_exists(self):
        """start.sh must exist."""
        filepath = os.path.join(BASE_DIR, "start.sh")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"

    def test_requirements_txt_exists(self):
        """requirements.txt must exist."""
        filepath = os.path.join(BASE_DIR, "requirements.txt")
        assert os.path.isfile(filepath), f"File {filepath} does not exist"


class TestStartShScript:
    """Verify start.sh is executable and has correct content."""

    def test_start_sh_is_executable(self):
        """start.sh must be executable."""
        filepath = os.path.join(BASE_DIR, "start.sh")
        assert os.access(filepath, os.X_OK), f"{filepath} is not executable"

    def test_start_sh_uses_gunicorn(self):
        """start.sh must use gunicorn."""
        filepath = os.path.join(BASE_DIR, "start.sh")
        with open(filepath, "r") as f:
            content = f.read()
        assert "gunicorn" in content, "start.sh does not reference gunicorn"

    def test_start_sh_activates_venv(self):
        """start.sh must activate the virtual environment."""
        filepath = os.path.join(BASE_DIR, "start.sh")
        with open(filepath, "r") as f:
            content = f.read()
        assert "venv" in content, "start.sh does not reference venv"


class TestSettingsIniBug:
    """Verify the bug exists in settings.ini - the typo [sevrer] instead of [server]."""

    def test_settings_ini_has_typo(self):
        """settings.ini must have the typo [sevrer] instead of [server]."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        with open(filepath, "r") as f:
            content = f.read()
        assert "[sevrer]" in content, (
            "settings.ini does not contain the expected typo [sevrer]. "
            "The bug should be present in the initial state."
        )

    def test_settings_ini_missing_correct_server_section(self):
        """settings.ini must NOT have the correct [server] section (that's the bug)."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        result = subprocess.run(
            ["grep", "-q", r"^\[server\]", filepath],
            capture_output=True
        )
        assert result.returncode != 0, (
            "settings.ini already has [server] section. "
            "The bug (typo [sevrer]) should be present in the initial state."
        )

    def test_settings_ini_has_port_5000(self):
        """settings.ini must have port=5000 configured (under the typo'd section)."""
        filepath = os.path.join(BASE_DIR, "config", "settings.ini")
        with open(filepath, "r") as f:
            content = f.read()
        assert "port=5000" in content or "port = 5000" in content, (
            "settings.ini does not have port=5000 configured"
        )


class TestGunicornConfig:
    """Verify gunicorn.conf.py reads from settings.ini and uses fallback."""

    def test_gunicorn_conf_reads_settings_ini(self):
        """gunicorn.conf.py must read from settings.ini."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "settings.ini" in content, (
            "gunicorn.conf.py does not reference settings.ini"
        )

    def test_gunicorn_conf_uses_configparser(self):
        """gunicorn.conf.py must use configparser."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "configparser" in content or "ConfigParser" in content, (
            "gunicorn.conf.py does not use configparser"
        )

    def test_gunicorn_conf_has_fallback(self):
        """gunicorn.conf.py must have fallback logic."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "fallback" in content, (
            "gunicorn.conf.py does not have fallback logic"
        )

    def test_gunicorn_conf_no_hardcoded_5000(self):
        """gunicorn.conf.py must NOT have port 5000 hardcoded in bind."""
        filepath = os.path.join(BASE_DIR, "config", "gunicorn.conf.py")
        result = subprocess.run(
            ["grep", "-q", r"bind.*5000", filepath],
            capture_output=True
        )
        assert result.returncode != 0, (
            "gunicorn.conf.py has port 5000 hardcoded in bind. "
            "Port should come from config file, not be hardcoded."
        )


class TestFlaskApp:
    """Verify the Flask app structure is correct."""

    def test_app_init_has_create_app(self):
        """app/__init__.py must have create_app factory function."""
        filepath = os.path.join(BASE_DIR, "app", "__init__.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "create_app" in content, (
            "app/__init__.py does not have create_app function"
        )

    def test_app_routes_has_index(self):
        """app/routes.py must have a route returning the expected message."""
        filepath = os.path.join(BASE_DIR, "app", "routes.py")
        with open(filepath, "r") as f:
            content = f.read()
        assert "Labeler v2.1 running" in content, (
            "app/routes.py does not have the expected 'Labeler v2.1 running' response"
        )


class TestVirtualEnvironment:
    """Verify the virtual environment is properly set up."""

    def test_venv_python_exists(self):
        """venv/bin/python must exist."""
        python_path = os.path.join(BASE_DIR, "venv", "bin", "python")
        assert os.path.isfile(python_path), f"Python executable {python_path} does not exist"

    def test_venv_gunicorn_exists(self):
        """venv/bin/gunicorn must exist."""
        gunicorn_path = os.path.join(BASE_DIR, "venv", "bin", "gunicorn")
        assert os.path.isfile(gunicorn_path), f"Gunicorn executable {gunicorn_path} does not exist"


class TestSystemTools:
    """Verify required system tools are available."""

    def test_curl_available(self):
        """curl must be available."""
        result = subprocess.run(["which", "curl"], capture_output=True)
        assert result.returncode == 0, "curl is not available"

    def test_netstat_or_ss_available(self):
        """netstat or ss must be available."""
        netstat_result = subprocess.run(["which", "netstat"], capture_output=True)
        ss_result = subprocess.run(["which", "ss"], capture_output=True)
        assert netstat_result.returncode == 0 or ss_result.returncode == 0, (
            "Neither netstat nor ss is available"
        )

    def test_ps_available(self):
        """ps must be available."""
        result = subprocess.run(["which", "ps"], capture_output=True)
        assert result.returncode == 0, "ps is not available"

    def test_pgrep_available(self):
        """pgrep must be available."""
        result = subprocess.run(["which", "pgrep"], capture_output=True)
        assert result.returncode == 0, "pgrep is not available"


class TestDirectoryWritable:
    """Verify the labeler directory is writable."""

    def test_labeler_directory_writable(self):
        """The /home/user/labeler directory must be writable."""
        assert os.access(BASE_DIR, os.W_OK), f"Directory {BASE_DIR} is not writable"

    def test_config_directory_writable(self):
        """The config/ directory must be writable."""
        config_dir = os.path.join(BASE_DIR, "config")
        assert os.access(config_dir, os.W_OK), f"Directory {config_dir} is not writable"


class TestPort5000NotInUse:
    """Verify port 5000 is not currently in use (as described in the task)."""

    def test_port_5000_not_listening(self):
        """Port 5000 should not have anything listening (per task description)."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if anything is listening on port 5000
        lines = result.stdout.split('\n')
        port_5000_in_use = any(':5000' in line for line in lines)
        assert not port_5000_in_use, (
            "Port 5000 is already in use. According to the task, "
            "nothing should be listening on port 5000 initially."
        )
