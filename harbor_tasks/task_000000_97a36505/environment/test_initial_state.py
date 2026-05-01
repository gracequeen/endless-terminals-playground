# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies that the environment is correctly set up for the static site serving task.
"""

import os
import subprocess
import pytest


class TestDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_www_directory_exists(self):
        """Verify /home/user/www directory exists."""
        www_path = "/home/user/www"
        assert os.path.isdir(www_path), f"Directory {www_path} does not exist"

    def test_www_directory_readable(self):
        """Verify /home/user/www is readable."""
        www_path = "/home/user/www"
        assert os.access(www_path, os.R_OK), f"Directory {www_path} is not readable"

    def test_css_subdirectory_exists(self):
        """Verify /home/user/www/css subdirectory exists."""
        css_path = "/home/user/www/css"
        assert os.path.isdir(css_path), f"Directory {css_path} does not exist"


class TestIndexHtml:
    """Test that index.html exists and has correct content."""

    def test_index_html_exists(self):
        """Verify index.html exists in /home/user/www."""
        index_path = "/home/user/www/index.html"
        assert os.path.isfile(index_path), f"File {index_path} does not exist"

    def test_index_html_readable(self):
        """Verify index.html is readable."""
        index_path = "/home/user/www/index.html"
        assert os.access(index_path, os.R_OK), f"File {index_path} is not readable"

    def test_index_html_contains_welcome_text(self):
        """Verify index.html contains 'Welcome to my site' text."""
        index_path = "/home/user/www/index.html"
        with open(index_path, "r") as f:
            content = f.read()
        assert "Welcome to my site" in content, \
            f"index.html does not contain expected text 'Welcome to my site'"

    def test_index_html_links_to_css(self):
        """Verify index.html contains a link to css/style.css."""
        index_path = "/home/user/www/index.html"
        with open(index_path, "r") as f:
            content = f.read()
        assert "css/style.css" in content, \
            f"index.html does not contain a link to css/style.css"

    def test_index_html_is_valid_html(self):
        """Verify index.html appears to be valid HTML (has basic structure)."""
        index_path = "/home/user/www/index.html"
        with open(index_path, "r") as f:
            content = f.read().lower()
        # Check for basic HTML structure
        assert "<html" in content or "<!doctype" in content, \
            "index.html does not appear to be a valid HTML file"


class TestStyleCss:
    """Test that style.css exists and is valid."""

    def test_style_css_exists(self):
        """Verify style.css exists in /home/user/www/css."""
        css_path = "/home/user/www/css/style.css"
        assert os.path.isfile(css_path), f"File {css_path} does not exist"

    def test_style_css_readable(self):
        """Verify style.css is readable."""
        css_path = "/home/user/www/css/style.css"
        assert os.access(css_path, os.R_OK), f"File {css_path} is not readable"

    def test_style_css_not_empty(self):
        """Verify style.css is not empty."""
        css_path = "/home/user/www/css/style.css"
        assert os.path.getsize(css_path) > 0, f"File {css_path} is empty"


class TestPythonInstallation:
    """Test that Python 3 and http.server module are available."""

    def test_python3_installed(self):
        """Verify Python 3 is installed and accessible."""
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Python 3 is not installed or not accessible"
        assert "Python 3" in result.stdout, f"Expected Python 3, got: {result.stdout}"

    def test_http_server_module_available(self):
        """Verify http.server module is available."""
        result = subprocess.run(
            ["python3", "-c", "import http.server"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"http.server module is not available: {result.stderr}"


class TestPort8080NotInUse:
    """Test that port 8080 is not currently in use."""

    def test_port_8080_not_listening(self):
        """Verify no process is currently listening on port 8080."""
        # Use ss to check for listening sockets on port 8080
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        # Check if port 8080 appears in the output
        lines = result.stdout.split('\n')
        for line in lines:
            if ":8080" in line and "LISTEN" in line:
                pytest.fail(f"Port 8080 is already in use: {line}")


class TestCurlInstalled:
    """Test that curl is installed for verification."""

    def test_curl_installed(self):
        """Verify curl is installed and accessible."""
        result = subprocess.run(
            ["curl", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "curl is not installed or not accessible"
        assert "curl" in result.stdout.lower(), f"Unexpected curl output: {result.stdout}"
