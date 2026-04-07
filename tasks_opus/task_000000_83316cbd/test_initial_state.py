# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the web scraping task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Tests to verify the system is ready for the web scraping task."""

    def test_home_directory_exists(self):
        """Verify that /home/user directory exists."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), f"Home directory {home_dir} does not exist"

    def test_home_directory_is_writable(self):
        """Verify that /home/user directory is writable."""
        home_dir = "/home/user"
        assert os.path.isdir(home_dir), f"Home directory {home_dir} is not writable"

    def test_output_file_does_not_exist(self):
        """Verify that the output file /home/user/hn_titles.txt does not already exist."""
        output_file = "/home/user/hn_titles.txt"
        assert not os.path.exists(output_file), (
            f"Output file {output_file} already exists. "
            "It should not exist before the task is performed."
        )

    def test_log_file_does_not_exist(self):
        """Verify that the log file /home/user/scrape_log.txt does not already exist."""
        log_file = "/home/user/scrape_log.txt"
        assert not os.path.exists(log_file), (
            f"Log file {log_file} already exists. "
            "It should not exist before the task is performed."
        )

    def test_nodejs_is_installed(self):
        """Verify that Node.js is installed and accessible."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, (
                f"Node.js is not working properly. "
                f"Exit code: {result.returncode}, stderr: {result.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("Node.js is not installed. 'node' command not found.")
        except subprocess.TimeoutExpired:
            pytest.fail("Node.js version check timed out.")

    def test_npm_is_installed(self):
        """Verify that npm is installed and accessible."""
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, (
                f"npm is not working properly. "
                f"Exit code: {result.returncode}, stderr: {result.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("npm is not installed. 'npm' command not found.")
        except subprocess.TimeoutExpired:
            pytest.fail("npm version check timed out.")

    def test_python3_is_installed(self):
        """Verify that Python 3 is installed (alternative tool for the task)."""
        try:
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, (
                f"Python 3 is not working properly. "
                f"Exit code: {result.returncode}, stderr: {result.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("Python 3 is not installed. 'python3' command not found.")
        except subprocess.TimeoutExpired:
            pytest.fail("Python 3 version check timed out.")

    def test_pip_is_installed(self):
        """Verify that pip is installed (for installing Python packages)."""
        try:
            result = subprocess.run(
                ["pip3", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Also try 'pip' if 'pip3' fails
            if result.returncode != 0:
                result = subprocess.run(
                    ["pip", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            assert result.returncode == 0, (
                f"pip is not working properly. "
                f"Exit code: {result.returncode}, stderr: {result.stderr}"
            )
        except FileNotFoundError:
            pytest.fail("pip is not installed. Neither 'pip3' nor 'pip' command found.")
        except subprocess.TimeoutExpired:
            pytest.fail("pip version check timed out.")

    def test_network_connectivity(self):
        """Verify basic network connectivity to reach external websites."""
        try:
            # Try to resolve a DNS name to verify network is available
            import socket
            socket.setdefaulttimeout(10)
            socket.gethostbyname("news.ycombinator.com")
        except socket.gaierror:
            pytest.fail(
                "Cannot resolve news.ycombinator.com. "
                "Network connectivity or DNS resolution is not working."
            )
        except socket.timeout:
            pytest.fail("DNS resolution timed out. Network may be slow or unavailable.")