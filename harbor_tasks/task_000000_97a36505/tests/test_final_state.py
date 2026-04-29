# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed the task.
This verifies that a static HTTP server is running on port 8080 serving /home/user/www.
"""

import os
import subprocess
import socket
import time
import pytest


class TestServerRunning:
    """Test that a server process is listening on port 8080."""

    def test_port_8080_listening(self):
        """Verify a process is listening on port 8080."""
        # Use ss to check for listening sockets on port 8080
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to run ss command: {result.stderr}"

        # Check if port 8080 appears in the output
        found = False
        lines = result.stdout.split('\n')
        for line in lines:
            if ":8080" in line and "LISTEN" in line:
                found = True
                break

        assert found, (
            "No process is listening on port 8080. "
            "Expected a server to be running on this port.\n"
            f"ss output:\n{result.stdout}"
        )

    def test_port_8080_connectable(self):
        """Verify we can establish a TCP connection to port 8080."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex(('localhost', 8080))
            assert result == 0, (
                f"Cannot connect to localhost:8080. Connection failed with error code {result}. "
                "The server may not be running or not accepting connections."
            )
        finally:
            sock.close()


class TestIndexHtmlServed:
    """Test that index.html is being served correctly."""

    def test_curl_index_returns_content(self):
        """Verify curl to localhost:8080 returns the index.html content."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"curl to http://localhost:8080/ failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )
        assert len(result.stdout) > 0, (
            "curl to http://localhost:8080/ returned empty content. "
            "The server should return the index.html file."
        )

    def test_index_contains_welcome_text(self):
        """Verify the served index.html contains 'Welcome to my site'."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert "Welcome to my site" in result.stdout, (
            "The response from http://localhost:8080/ does not contain 'Welcome to my site'. "
            "The server must serve the actual /home/user/www/index.html file.\n"
            f"Received content: {result.stdout[:500]}..."
        )

    def test_index_matches_file_content(self):
        """Verify the served content matches the actual index.html file."""
        # Get content from server
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        served_content = result.stdout

        # Get content from file
        with open("/home/user/www/index.html", "r") as f:
            file_content = f.read()

        # Check that key content matches (semantic check, not exact byte match due to potential encoding)
        assert "Welcome to my site" in served_content, (
            "Served content does not match /home/user/www/index.html"
        )
        assert "css/style.css" in served_content, (
            "Served content does not contain the CSS link from index.html"
        )


class TestCssServed:
    """Test that the CSS file is being served correctly."""

    def test_css_returns_200(self):
        """Verify curl to css/style.css returns HTTP 200."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "http://localhost:8080/css/style.css"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"curl to css/style.css failed with return code {result.returncode}"
        )
        assert result.stdout == "200", (
            f"Expected HTTP 200 for css/style.css, got HTTP {result.stdout}. "
            "The server should serve the CSS file from /home/user/www/css/style.css"
        )

    def test_css_returns_content(self):
        """Verify css/style.css returns non-empty content."""
        result = subprocess.run(
            ["curl", "-s", "http://localhost:8080/css/style.css"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, (
            f"curl to css/style.css failed: {result.stderr}"
        )
        assert len(result.stdout) > 0, (
            "css/style.css returned empty content. "
            "The server should serve the actual CSS file."
        )


class TestFileIntegrity:
    """Test that the original files have not been modified."""

    def test_index_html_unchanged(self):
        """Verify index.html still contains expected content (not modified)."""
        index_path = "/home/user/www/index.html"
        assert os.path.isfile(index_path), f"File {index_path} no longer exists"

        with open(index_path, "r") as f:
            content = f.read()

        assert "Welcome to my site" in content, (
            "index.html has been modified - no longer contains 'Welcome to my site'"
        )
        assert "css/style.css" in content, (
            "index.html has been modified - no longer contains link to css/style.css"
        )

    def test_style_css_unchanged(self):
        """Verify style.css still exists and is not empty."""
        css_path = "/home/user/www/css/style.css"
        assert os.path.isfile(css_path), f"File {css_path} no longer exists"
        assert os.path.getsize(css_path) > 0, f"File {css_path} is now empty"

    def test_no_extra_files_in_www(self):
        """Verify no additional files were created in /home/user/www."""
        www_path = "/home/user/www"
        expected_items = {"index.html", "css"}

        actual_items = set(os.listdir(www_path))
        extra_items = actual_items - expected_items

        assert len(extra_items) == 0, (
            f"Unexpected files/directories found in {www_path}: {extra_items}. "
            "No additional files should be created in /home/user/www"
        )

    def test_no_extra_files_in_css(self):
        """Verify no additional files were created in /home/user/www/css."""
        css_path = "/home/user/www/css"
        expected_items = {"style.css"}

        actual_items = set(os.listdir(css_path))
        extra_items = actual_items - expected_items

        assert len(extra_items) == 0, (
            f"Unexpected files found in {css_path}: {extra_items}. "
            "No additional files should be created in /home/user/www/css"
        )


class TestServerPersistence:
    """Test that the server remains running (backgrounded/daemonized)."""

    def test_server_still_running_after_delay(self):
        """Verify the server is still running after a brief delay."""
        # Small delay to ensure we're not just catching a dying process
        time.sleep(1)

        # Check if port is still listening
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )

        found = False
        for line in result.stdout.split('\n'):
            if ":8080" in line and "LISTEN" in line:
                found = True
                break

        assert found, (
            "Server is no longer running on port 8080 after delay. "
            "The server process should remain running (backgrounded or daemonized)."
        )

    def test_server_responds_after_delay(self):
        """Verify the server still responds to requests after a delay."""
        time.sleep(1)

        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:8080/"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.stdout == "200", (
            f"Server no longer responding correctly after delay. "
            f"Expected HTTP 200, got {result.stdout}. "
            "The server should remain running and responsive."
        )
