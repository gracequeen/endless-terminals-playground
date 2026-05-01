# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This validates the environment for a headless scraper debugging task.
"""

import os
import subprocess
import json
import pytest
import socket
import time


class TestScraperDirectoryAndFiles:
    """Test that the scraper directory and files exist."""

    def test_scraper_directory_exists(self):
        """Verify /home/user/scraper directory exists."""
        assert os.path.isdir("/home/user/scraper"), \
            "Directory /home/user/scraper does not exist"

    def test_scrape_py_exists(self):
        """Verify scrape.py script exists."""
        assert os.path.isfile("/home/user/scraper/scrape.py"), \
            "File /home/user/scraper/scrape.py does not exist"

    def test_scraper_directory_is_writable(self):
        """Verify /home/user/scraper is writable."""
        assert os.access("/home/user/scraper", os.W_OK), \
            "Directory /home/user/scraper is not writable"


class TestScriptContent:
    """Test the content of scrape.py to verify it uses pyppeteer."""

    def test_script_uses_pyppeteer(self):
        """Verify scrape.py uses pyppeteer."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        assert "pyppeteer" in content, \
            "scrape.py does not appear to use pyppeteer"

    def test_script_targets_localhost_8080(self):
        """Verify scrape.py targets localhost:8080."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        assert "localhost:8080" in content or "127.0.0.1:8080" in content, \
            "scrape.py does not target localhost:8080"

    def test_script_has_no_sandbox_flag(self):
        """Verify scrape.py has --no-sandbox flag."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        assert "--no-sandbox" in content, \
            "scrape.py does not have --no-sandbox flag"

    def test_script_writes_to_prices_json(self):
        """Verify scrape.py writes to prices.json."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        assert "prices.json" in content, \
            "scrape.py does not reference prices.json"

    def test_script_has_headless_false_problem(self):
        """Verify the script has headless=False (the problem to fix)."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        # The script should have headless=False as part of the problem
        assert "headless=False" in content or "headless = False" in content, \
            "scrape.py does not have headless=False (expected problem state)"


class TestTestSite:
    """Test that the test site directory and files exist."""

    def test_testsite_directory_exists(self):
        """Verify /home/user/testsite directory exists."""
        assert os.path.isdir("/home/user/testsite"), \
            "Directory /home/user/testsite does not exist"

    def test_testsite_directory_is_readable(self):
        """Verify /home/user/testsite is readable."""
        assert os.access("/home/user/testsite", os.R_OK), \
            "Directory /home/user/testsite is not readable"

    def test_products_html_exists(self):
        """Verify products.html exists in testsite."""
        # Check for products.html or similar
        testsite_path = "/home/user/testsite"
        files = os.listdir(testsite_path)
        has_products = any("product" in f.lower() for f in files)
        assert has_products, \
            f"No products file found in /home/user/testsite. Files: {files}"


class TestLocalServer:
    """Test that the local test server is running on port 8080."""

    def test_port_8080_is_listening(self):
        """Verify something is listening on port 8080."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        assert result == 0, \
            "Nothing is listening on localhost:8080 - test server not running"

    def test_server_responds_to_http(self):
        """Verify the server responds to HTTP requests."""
        import urllib.request
        try:
            response = urllib.request.urlopen('http://localhost:8080/', timeout=5)
            assert response.status == 200 or response.status == 404, \
                f"Server returned unexpected status: {response.status}"
        except Exception as e:
            pytest.fail(f"Could not connect to http://localhost:8080/: {e}")

    def test_products_page_accessible(self):
        """Verify /products page is accessible."""
        import urllib.request
        try:
            response = urllib.request.urlopen('http://localhost:8080/products', timeout=5)
            content = response.read().decode('utf-8')
            assert response.status == 200, \
                f"Products page returned status {response.status}"
            assert "product" in content.lower(), \
                "Products page does not contain product data"
        except urllib.error.HTTPError as e:
            # Try products.html as fallback
            try:
                response = urllib.request.urlopen('http://localhost:8080/products.html', timeout=5)
                content = response.read().decode('utf-8')
                assert "product" in content.lower(), \
                    "Products page does not contain product data"
            except Exception as e2:
                pytest.fail(f"Could not access products page: {e} / {e2}")
        except Exception as e:
            pytest.fail(f"Could not access products page: {e}")

    def test_products_page_has_five_products(self):
        """Verify products page has 5 product entries."""
        import urllib.request
        try:
            # Try /products first, then /products.html
            try:
                response = urllib.request.urlopen('http://localhost:8080/products', timeout=5)
            except:
                response = urllib.request.urlopen('http://localhost:8080/products.html', timeout=5)
            content = response.read().decode('utf-8')
            # Count product divs
            product_count = content.lower().count('class="product"') or content.lower().count("class='product'")
            assert product_count == 5, \
                f"Expected 5 products on page, found {product_count}"
        except Exception as e:
            pytest.fail(f"Could not verify product count: {e}")


class TestChromiumInstallation:
    """Test that Chromium is installed via pyppeteer."""

    def test_pyppeteer_chromium_exists(self):
        """Verify pyppeteer's chromium binary exists."""
        chromium_base = os.path.expanduser("~/.local/share/pyppeteer/local-chromium")
        assert os.path.isdir(chromium_base), \
            f"Pyppeteer chromium directory not found at {chromium_base}"

        # Find the chrome binary
        found_chrome = False
        for root, dirs, files in os.walk(chromium_base):
            if "chrome" in files:
                found_chrome = True
                break
        assert found_chrome, \
            f"Chrome binary not found under {chromium_base}"


class TestDevShmProblem:
    """Test that /dev/shm has the problematic small size."""

    def test_dev_shm_exists(self):
        """Verify /dev/shm exists."""
        assert os.path.exists("/dev/shm"), \
            "/dev/shm does not exist"

    def test_dev_shm_is_small(self):
        """Verify /dev/shm has limited size (the problem condition)."""
        result = subprocess.run(
            ["df", "-h", "/dev/shm"],
            capture_output=True,
            text=True
        )
        output = result.stdout
        # Parse the size - looking for small size like 1M or 1.0M
        lines = output.strip().split('\n')
        if len(lines) >= 2:
            # Size is typically in the 2nd column
            parts = lines[1].split()
            if len(parts) >= 2:
                size = parts[1]
                # Check if size is small (1M, 1.0M, etc.)
                is_small = any(x in size.upper() for x in ['1M', '1.0M', '2M', '64M'])
                assert is_small, \
                    f"/dev/shm size is {size}, expected small size (1M) for problem condition"


class TestPyppeteerInstalled:
    """Test that pyppeteer is installed."""

    def test_pyppeteer_importable(self):
        """Verify pyppeteer can be imported."""
        result = subprocess.run(
            ["python3", "-c", "import pyppeteer; print(pyppeteer.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"pyppeteer is not installed or cannot be imported: {result.stderr}"


class TestScriptHangs:
    """Test that the script currently hangs (doesn't complete quickly)."""

    def test_script_does_not_complete_quickly(self):
        """Verify running the script times out (the problem state)."""
        # Run with a short timeout - if it completes, the problem is already fixed
        result = subprocess.run(
            ["timeout", "10", "python3", "/home/user/scraper/scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )
        # Exit code 124 means timeout killed it, which is expected
        # Exit code 0 would mean it completed (problem already fixed)
        assert result.returncode != 0, \
            "Script completed successfully - problem may already be fixed"


class TestNoPricesJsonYet:
    """Test that prices.json does not exist yet or is not valid."""

    def test_prices_json_not_valid_yet(self):
        """Verify prices.json doesn't exist or isn't valid JSON with 5 products."""
        prices_path = "/home/user/scraper/prices.json"
        if os.path.exists(prices_path):
            try:
                with open(prices_path, 'r') as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) == 5:
                    # Check if all have name and price
                    all_valid = all(
                        isinstance(item, dict) and 'name' in item and 'price' in item
                        for item in data
                    )
                    assert not all_valid, \
                        "prices.json already contains valid data - task may already be complete"
            except (json.JSONDecodeError, IOError):
                # File exists but isn't valid JSON - that's fine for initial state
                pass
