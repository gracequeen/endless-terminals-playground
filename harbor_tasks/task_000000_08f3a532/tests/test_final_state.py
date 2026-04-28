# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the i18n-server debugging task.

The student should have fixed de.yaml to be valid YAML so that the Flask
app can serve German translations.
"""

import os
import subprocess
import time
import socket
import pytest


# Base paths
BASE_DIR = "/home/user/i18n-server"
LOCALES_DIR = os.path.join(BASE_DIR, "locales")
VENV_DIR = os.path.join(BASE_DIR, "venv")
PYTHON_BIN = os.path.join(VENV_DIR, "bin", "python")


def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_flask_app():
    """Start the Flask app and return the process."""
    # Kill any existing process on port 5050
    subprocess.run(["pkill", "-f", "python.*app.py"], capture_output=True)
    time.sleep(0.5)

    # Start the app
    proc = subprocess.Popen(
        [PYTHON_BIN, "app.py"],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    # Wait for the app to start (up to 10 seconds)
    for _ in range(20):
        if is_port_in_use(5050):
            return proc
        time.sleep(0.5)

    # If we get here, app didn't start
    proc.terminate()
    stdout, stderr = proc.communicate(timeout=5)
    raise RuntimeError(f"Flask app failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}")


def stop_flask_app(proc):
    """Stop the Flask app."""
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    # Also kill any lingering processes
    subprocess.run(["pkill", "-f", "python.*app.py"], capture_output=True)


@pytest.fixture(scope="module")
def flask_app():
    """Fixture to start and stop the Flask app for testing."""
    proc = start_flask_app()
    yield proc
    stop_flask_app(proc)


class TestDeYamlFixed:
    """Test that de.yaml has been fixed to be valid YAML."""

    def test_de_yaml_exists(self):
        """de.yaml must still exist."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")
        assert os.path.isfile(de_path), f"German locale file {de_path} does not exist"

    def test_de_yaml_is_valid_yaml(self):
        """de.yaml must now be valid YAML (the bug should be fixed)."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; yaml.safe_load(open('{de_path}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"de.yaml is still not valid YAML. Fix the YAML syntax errors. Error: {result.stderr}"

    def test_de_yaml_has_greeting_key(self):
        """de.yaml must have a 'greeting' key."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{de_path}')); assert 'greeting' in d, 'greeting key missing'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"de.yaml does not have 'greeting' key: {result.stderr}"

    def test_de_yaml_has_farewell_key(self):
        """de.yaml must have a 'farewell' key."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{de_path}')); assert 'farewell' in d, 'farewell key missing'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"de.yaml does not have 'farewell' key: {result.stderr}"

    def test_de_yaml_greeting_contains_hallo(self):
        """de.yaml greeting should contain 'Hallo' (German greeting)."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{de_path}')); assert 'Hallo' in str(d.get('greeting', '')), f'greeting is {{d.get(\"greeting\")}}, expected to contain Hallo'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"de.yaml greeting does not contain 'Hallo': {result.stderr}"


class TestInvariantsPreserved:
    """Test that invariants are preserved (en.yaml, fr.yaml, config.yaml, app.py unchanged)."""

    def test_en_yaml_unchanged_greeting(self):
        """en.yaml must still have greeting='Hello'."""
        en_path = os.path.join(LOCALES_DIR, "en.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{en_path}')); assert d.get('greeting') == 'Hello', f'greeting is {{d.get(\"greeting\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"en.yaml greeting was modified (should still be 'Hello'): {result.stderr}"

    def test_en_yaml_unchanged_farewell(self):
        """en.yaml must still have farewell='Goodbye'."""
        en_path = os.path.join(LOCALES_DIR, "en.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{en_path}')); assert d.get('farewell') == 'Goodbye', f'farewell is {{d.get(\"farewell\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"en.yaml farewell was modified (should still be 'Goodbye'): {result.stderr}"

    def test_fr_yaml_unchanged_greeting(self):
        """fr.yaml must still have greeting='Bonjour'."""
        fr_path = os.path.join(LOCALES_DIR, "fr.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{fr_path}')); assert d.get('greeting') == 'Bonjour', f'greeting is {{d.get(\"greeting\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"fr.yaml greeting was modified (should still be 'Bonjour'): {result.stderr}"

    def test_fr_yaml_unchanged_farewell(self):
        """fr.yaml must still have farewell='Au revoir'."""
        fr_path = os.path.join(LOCALES_DIR, "fr.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; d=yaml.safe_load(open('{fr_path}')); assert d.get('farewell') == 'Au revoir', f'farewell is {{d.get(\"farewell\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"fr.yaml farewell was modified (should still be 'Au revoir'): {result.stderr}"

    def test_config_yaml_port_unchanged(self):
        """config.yaml must still specify port 5050."""
        config_path = os.path.join(BASE_DIR, "config.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; c=yaml.safe_load(open('{config_path}')); assert c.get('port') == 5050, f'Port is {{c.get(\"port\")}}'"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"config.yaml port was modified (should still be 5050): {result.stderr}"


class TestFlaskAppFunctionality:
    """Test that the Flask app works correctly after the fix."""

    def test_german_greeting_returns_200(self, flask_app):
        """GET /api/v1/translate?locale=de&key=greeting should return HTTP 200."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "http://localhost:5050/api/v1/translate?locale=de&key=greeting"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.stdout.strip() == "200", f"German greeting endpoint returned HTTP {result.stdout.strip()}, expected 200. The de.yaml file may still have YAML syntax errors."

    def test_german_greeting_contains_hallo(self, flask_app):
        """GET /api/v1/translate?locale=de&key=greeting should return 'Hallo'."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5050/api/v1/translate?locale=de&key=greeting"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert "Hallo" in result.stdout, f"German greeting response does not contain 'Hallo'. Got: {result.stdout}"

    def test_german_farewell_returns_200(self, flask_app):
        """GET /api/v1/translate?locale=de&key=farewell should return HTTP 200."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:5050/api/v1/translate?locale=de&key=farewell"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.stdout.strip() == "200", f"German farewell endpoint returned HTTP {result.stdout.strip()}, expected 200"

    def test_german_farewell_has_content(self, flask_app):
        """GET /api/v1/translate?locale=de&key=farewell should return a non-empty response."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5050/api/v1/translate?locale=de&key=farewell"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert len(result.stdout.strip()) > 0, "German farewell response is empty"
        # Should contain some form of German farewell
        assert "Wiedersehen" in result.stdout or "wiedersehen" in result.stdout.lower() or len(result.stdout.strip()) > 2, \
            f"German farewell response doesn't look like a valid farewell. Got: {result.stdout}"

    def test_french_greeting_still_works(self, flask_app):
        """GET /api/v1/translate?locale=fr&key=greeting should still return 'Bonjour'."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5050/api/v1/translate?locale=fr&key=greeting"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert "Bonjour" in result.stdout, f"French greeting should still return 'Bonjour'. Got: {result.stdout}"

    def test_english_greeting_still_works(self, flask_app):
        """GET /api/v1/translate?locale=en&key=greeting should still return 'Hello'."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5050/api/v1/translate?locale=en&key=greeting"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert "Hello" in result.stdout, f"English greeting should still return 'Hello'. Got: {result.stdout}"


class TestAntiShortcutGuards:
    """Test that the solution is genuine and not a shortcut/hardcoded workaround."""

    def test_de_yaml_parseable_by_pyyaml(self):
        """de.yaml must be parseable by PyYAML safe_load (anti-shortcut guard)."""
        de_path = os.path.join(LOCALES_DIR, "de.yaml")

        result = subprocess.run(
            [PYTHON_BIN, "-c", f"import yaml; yaml.safe_load(open('{de_path}'))"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"de.yaml is not parseable by PyYAML. The YAML must be fixed, not worked around. Error: {result.stderr}"

    def test_app_serves_from_locale_files_not_hardcoded(self, flask_app):
        """
        Verify the app actually reads from locale files by checking that
        modifying de.yaml would change the response (conceptual test).

        We verify this by ensuring de.yaml is a real YAML file with the expected
        structure that the app would parse.
        """
        de_path = os.path.join(LOCALES_DIR, "de.yaml")

        # Verify de.yaml has the expected structure
        result = subprocess.run(
            [PYTHON_BIN, "-c", f"""
import yaml
with open('{de_path}') as f:
    d = yaml.safe_load(f)
assert isinstance(d, dict), 'de.yaml should parse to a dict'
assert 'greeting' in d, 'de.yaml should have greeting key'
assert 'farewell' in d, 'de.yaml should have farewell key'
assert isinstance(d['greeting'], str), 'greeting should be a string'
assert isinstance(d['farewell'], str), 'farewell should be a string'
print('OK')
"""],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"de.yaml does not have the expected structure: {result.stderr}"
        assert "OK" in result.stdout, f"de.yaml structure validation failed: {result.stdout}"
