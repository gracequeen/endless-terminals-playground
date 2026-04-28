# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the i18n-server debugging task.
"""

import os
import subprocess
import pytest


# Base paths
BASE_DIR = "/home/user/i18n-server"
LOCALES_DIR = os.path.join(BASE_DIR, "locales")
VENV_DIR = os.path.join(BASE_DIR, "venv")


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_i18n_server_directory_exists(self):
        """The i18n-server directory must exist."""
        assert os.path.isdir(BASE_DIR), f"Directory {BASE_DIR} does not exist"

    def test_locales_directory_exists(self):
        """The locales directory must exist."""
        assert os.path.isdir(LOCALES_DIR), f"Directory {LOCALES_DIR} does not exist"

    def test_venv_directory_exists(self):
        """The virtual environment directory must exist."""
        assert os.path.isdir(VENV_DIR), f"Virtual environment {VENV_DIR} does not exist"


class TestRequiredFiles:
    """Test that required files exist."""

    def test_app_py_exists(self):
        """app.py must exist in the i18n-server directory."""
        app_path = os.path.join(BASE_DIR, "app.py")
        assert os.path.isfile(app_path), f"Flask application {app_path} does not exist"

    def test_config_yaml_exists(self):
        """config.yaml must exist in the i18n-server directory."""
        config_path = os.path.join(BASE_DIR, "config.yaml")
        assert os.path.isfile(config_path), f"Config file {config_path} does not exist"

    def test_en_yaml_exists(self):
        """en.yaml locale file must exist."""
        en_path = os.path.join(LOCALES_DIR, "en.yaml")
        assert os.path.isfile(en_path), f"English locale file {en_path} does not exist"

    def test_fr_yaml_exists(self):
        """fr.yaml locale file must exist."""
        fr_path = os.path.join(LOCALES_DIR, "fr.yaml")
        assert os.path.isfile(fr_path), f"French locale file {fr_path} does not exist"

    def test_de_yaml_exists(self):
        """de.yaml locale file must exist."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        assert os.path.isfile(de_path), f"German locale file {de_path} does not exist"


class TestConfigYaml:
    """Test that config.yaml has the expected configuration."""

    def test_config_yaml_is_valid_yaml(self):
        """config.yaml must be valid YAML."""
        config_path = os.path.join(BASE_DIR, "config.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; yaml.safe_load(open('{config_path}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"config.yaml is not valid YAML: {result.stderr}"

    def test_config_specifies_port_5050(self):
        """config.yaml must specify port 5050."""
        config_path = os.path.join(BASE_DIR, "config.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; c=yaml.safe_load(open('{config_path}')); assert c.get('port') == 5050, f'Port is {{c.get(\"port\")}}, expected 5050'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"config.yaml does not specify port 5050: {result.stderr}"

    def test_config_specifies_locales_dir(self):
        """config.yaml must specify locale_dir as 'locales'."""
        config_path = os.path.join(BASE_DIR, "config.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; c=yaml.safe_load(open('{config_path}')); assert c.get('locale_dir') == 'locales', f'locale_dir is {{c.get(\"locale_dir\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"config.yaml does not specify locale_dir as 'locales': {result.stderr}"

    def test_config_includes_de_in_supported_locales(self):
        """config.yaml must include 'de' in supported_locales."""
        config_path = os.path.join(BASE_DIR, "config.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; c=yaml.safe_load(open('{config_path}')); assert 'de' in c.get('supported_locales', []), 'de not in supported_locales'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"config.yaml does not include 'de' in supported_locales: {result.stderr}"


class TestLocaleFiles:
    """Test the state of locale files."""

    def test_en_yaml_is_valid(self):
        """en.yaml must be valid YAML."""
        en_path = os.path.join(LOCALES_DIR, "en.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; yaml.safe_load(open('{en_path}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"en.yaml is not valid YAML: {result.stderr}"

    def test_en_yaml_has_greeting(self):
        """en.yaml must have a 'greeting' key with value 'Hello'."""
        en_path = os.path.join(LOCALES_DIR, "en.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; d=yaml.safe_load(open('{en_path}')); assert d.get('greeting') == 'Hello', f'greeting is {{d.get(\"greeting\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"en.yaml does not have greeting='Hello': {result.stderr}"

    def test_fr_yaml_is_valid(self):
        """fr.yaml must be valid YAML."""
        fr_path = os.path.join(LOCALES_DIR, "fr.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; yaml.safe_load(open('{fr_path}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"fr.yaml is not valid YAML: {result.stderr}"

    def test_fr_yaml_has_greeting_bonjour(self):
        """fr.yaml must have a 'greeting' key with value 'Bonjour'."""
        fr_path = os.path.join(LOCALES_DIR, "fr.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; d=yaml.safe_load(open('{fr_path}')); assert d.get('greeting') == 'Bonjour', f'greeting is {{d.get(\"greeting\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"fr.yaml does not have greeting='Bonjour': {result.stderr}"

    def test_de_yaml_is_invalid(self):
        """de.yaml must be INVALID YAML (this is the bug to fix)."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", f"import yaml; yaml.safe_load(open('{de_path}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, f"de.yaml should be INVALID YAML (this is the bug), but it parsed successfully"

    def test_de_yaml_contains_hallo(self):
        """de.yaml must contain 'Hallo' somewhere (the German greeting)."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        with open(de_path, 'r') as f:
            content = f.read()
        assert 'Hallo' in content, f"de.yaml does not contain 'Hallo'"

    def test_de_yaml_contains_greeting_key(self):
        """de.yaml must contain 'greeting' key somewhere."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        with open(de_path, 'r') as f:
            content = f.read()
        assert 'greeting' in content, f"de.yaml does not contain 'greeting' key"

    def test_de_yaml_contains_farewell_key(self):
        """de.yaml must contain 'farewell' key somewhere."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        with open(de_path, 'r') as f:
            content = f.read()
        assert 'farewell' in content, f"de.yaml does not contain 'farewell' key"


class TestVirtualEnvironment:
    """Test that the virtual environment is properly set up."""

    def test_venv_python_exists(self):
        """Python binary must exist in venv."""
        python_bin = os.path.join(VENV_DIR, "bin", "python")
        assert os.path.isfile(python_bin), f"Python binary {python_bin} does not exist"

    def test_flask_is_installed(self):
        """Flask must be installed in the venv."""
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", "import flask"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Flask is not installed in venv: {result.stderr}"

    def test_pyyaml_is_installed(self):
        """PyYAML must be installed in the venv."""
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", "import yaml"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"PyYAML is not installed in venv: {result.stderr}"


class TestAppNotRunning:
    """Test that the Flask app is NOT currently running."""

    def test_port_5050_not_in_use(self):
        """Port 5050 should not be in use (app not running)."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check that nothing is listening on port 5050
        assert ":5050" not in result.stdout, "Port 5050 is already in use - the app should NOT be running initially"

    def test_no_flask_process_for_app(self):
        """No Flask process should be running for this app."""
        result = subprocess.run(
            ["pgrep", "-f", "python.*app.py"],
            capture_output=True,
            text=True
        )
        # pgrep returns 1 if no processes found, which is what we want
        assert result.returncode != 0 or result.stdout.strip() == "", "Flask app.py process is already running - it should NOT be running initially"


class TestFilePermissions:
    """Test that files are writable."""

    def test_i18n_server_dir_writable(self):
        """The i18n-server directory must be writable."""
        assert os.access(BASE_DIR, os.W_OK), f"{BASE_DIR} is not writable"

    def test_locales_dir_writable(self):
        """The locales directory must be writable."""
        assert os.access(LOCALES_DIR, os.W_OK), f"{LOCALES_DIR} is not writable"

    def test_de_yaml_writable(self):
        """de.yaml must be writable (so it can be fixed)."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        assert os.access(de_path, os.W_OK), f"{de_path} is not writable"


class TestSystemTools:
    """Test that required system tools are available."""

    def test_curl_available(self):
        """curl must be available."""
        result = subprocess.run(
            ["which", "curl"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "curl is not available"

    def test_python_version(self):
        """Python 3.10+ must be available in venv."""
        python_bin = os.path.join(VENV_DIR, "bin", "python")

        result = subprocess.run(
            [python_bin, "-c", "import sys; assert sys.version_info >= (3, 10), f'Python {sys.version_info} is too old'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Python version is not 3.10+: {result.stderr}"
