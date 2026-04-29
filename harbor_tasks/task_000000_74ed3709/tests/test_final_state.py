# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed the task.
This validates that the headless scraper debugging task has been successfully completed.
"""

import os
import subprocess
import json
import pytest
import socket
import time
import re


class TestScriptCompletesSuccessfully:
    """Test that the scraper script now completes successfully."""

    def test_script_completes_within_timeout(self):
        """Verify running the script completes within 60 seconds."""
        # Clean up any existing prices.json first to ensure fresh run
        prices_path = "/home/user/scraper/prices.json"
        if os.path.exists(prices_path):
            os.remove(prices_path)

        result = subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )
        assert result.returncode == 0, \
            f"Script did not complete successfully. Exit code: {result.returncode}\nStderr: {result.stderr}\nStdout: {result.stdout}"

    def test_no_chromium_process_remains(self):
        """Verify no chromium process remains running after script completes."""
        # First run the script to completion
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        # Give a moment for cleanup
        time.sleep(2)

        # Check for lingering chromium processes
        result = subprocess.run(
            ["pgrep", "-f", "chrome|chromium"],
            capture_output=True,
            text=True
        )
        # pgrep returns 0 if processes found, 1 if none found
        # We want no chromium processes, so returncode should be 1
        # However, there might be legitimate chrome processes, so we check more specifically
        if result.returncode == 0:
            # Check if these are related to our scraper
            ps_result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True
            )
            chrome_lines = [line for line in ps_result.stdout.split('\n') 
                          if 'chrome' in line.lower() or 'chromium' in line.lower()]
            # Filter out grep itself
            chrome_lines = [line for line in chrome_lines if 'grep' not in line]
            # If there are zombie/leftover processes, fail
            assert len(chrome_lines) == 0, \
                f"Chromium processes still running after script completion:\n" + "\n".join(chrome_lines)


class TestPricesJsonOutput:
    """Test that prices.json is created with valid content."""

    def test_prices_json_exists(self):
        """Verify prices.json file exists."""
        # Run the script first to ensure prices.json is created
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        prices_path = "/home/user/scraper/prices.json"
        assert os.path.isfile(prices_path), \
            f"prices.json does not exist at {prices_path}"

    def test_prices_json_is_valid_json(self):
        """Verify prices.json contains valid JSON."""
        # Run the script first
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        prices_path = "/home/user/scraper/prices.json"
        with open(prices_path, 'r') as f:
            content = f.read()

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"prices.json is not valid JSON: {e}\nContent: {content[:500]}")

    def test_prices_json_contains_array_of_five_objects(self):
        """Verify prices.json contains an array of 5 objects."""
        # Run the script first
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        prices_path = "/home/user/scraper/prices.json"
        with open(prices_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), \
            f"prices.json should contain a list/array, got {type(data).__name__}"
        assert len(data) == 5, \
            f"prices.json should contain 5 items, got {len(data)}"

    def test_prices_json_objects_have_required_keys(self):
        """Verify each object in prices.json has 'name' and 'price' keys."""
        # Run the script first
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        prices_path = "/home/user/scraper/prices.json"
        with open(prices_path, 'r') as f:
            data = json.load(f)

        for i, item in enumerate(data):
            assert isinstance(item, dict), \
                f"Item {i} should be an object/dict, got {type(item).__name__}"
            assert 'name' in item, \
                f"Item {i} is missing 'name' key. Keys present: {list(item.keys())}"
            assert 'price' in item, \
                f"Item {i} is missing 'price' key. Keys present: {list(item.keys())}"

    def test_prices_json_values_are_strings(self):
        """Verify name and price values are strings."""
        # Run the script first
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        prices_path = "/home/user/scraper/prices.json"
        with open(prices_path, 'r') as f:
            data = json.load(f)

        for i, item in enumerate(data):
            assert isinstance(item.get('name'), str), \
                f"Item {i} 'name' should be a string, got {type(item.get('name')).__name__}"
            assert isinstance(item.get('price'), str), \
                f"Item {i} 'price' should be a string, got {type(item.get('price')).__name__}"

    def test_prices_have_dollar_format(self):
        """Verify price values look like currency (e.g., '$19.99')."""
        # Run the script first
        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        prices_path = "/home/user/scraper/prices.json"
        with open(prices_path, 'r') as f:
            data = json.load(f)

        price_pattern = re.compile(r'^\$\d+\.\d{2}$')
        for i, item in enumerate(data):
            price = item.get('price', '')
            assert price_pattern.match(price), \
                f"Item {i} price '{price}' doesn't match expected format like '$19.99'"


class TestScriptStillUsesPyppeteer:
    """Test that the script still uses pyppeteer (not switched to another method)."""

    def test_script_uses_pyppeteer(self):
        """Verify scrape.py still uses pyppeteer."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        assert "pyppeteer" in content, \
            "scrape.py no longer uses pyppeteer - must use pyppeteer for this task"

    def test_script_does_not_use_requests(self):
        """Verify scrape.py doesn't bypass browser with requests library."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        # Check for common bypass methods
        assert "requests.get" not in content, \
            "scrape.py uses requests.get - must use pyppeteer browser, not HTTP library"

    def test_script_does_not_use_urllib(self):
        """Verify scrape.py doesn't bypass browser with urllib."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        # Check for urllib usage (but allow urllib imports that might be unrelated)
        assert "urllib.request.urlopen" not in content and "urlopen(" not in content, \
            "scrape.py uses urllib - must use pyppeteer browser, not HTTP library"

    def test_script_does_not_use_curl(self):
        """Verify scrape.py doesn't bypass browser with curl subprocess."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        # Check for curl subprocess calls
        curl_patterns = ["subprocess.run.*curl", "subprocess.call.*curl", "'curl'", '"curl"']
        for pattern in curl_patterns:
            if re.search(pattern, content):
                pytest.fail("scrape.py uses curl - must use pyppeteer browser, not curl")


class TestTestServerStillRunning:
    """Test that the test server is still running and serving content."""

    def test_port_8080_is_listening(self):
        """Verify something is still listening on port 8080."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 8080))
        sock.close()
        assert result == 0, \
            "Nothing is listening on localhost:8080 - test server not running"

    def test_products_page_still_accessible(self):
        """Verify /products page is still accessible."""
        import urllib.request
        try:
            response = urllib.request.urlopen('http://localhost:8080/products', timeout=5)
            content = response.read().decode('utf-8')
            assert response.status == 200, \
                f"Products page returned status {response.status}"
        except urllib.error.HTTPError:
            # Try products.html as fallback
            try:
                response = urllib.request.urlopen('http://localhost:8080/products.html', timeout=5)
                assert response.status == 200
            except Exception as e:
                pytest.fail(f"Could not access products page: {e}")
        except Exception as e:
            pytest.fail(f"Could not access products page: {e}")


class TestTestSiteUnchanged:
    """Test that the test site directory is unchanged."""

    def test_testsite_directory_exists(self):
        """Verify /home/user/testsite directory still exists."""
        assert os.path.isdir("/home/user/testsite"), \
            "Directory /home/user/testsite does not exist"

    def test_testsite_has_products_file(self):
        """Verify products file still exists in testsite."""
        testsite_path = "/home/user/testsite"
        files = os.listdir(testsite_path)
        has_products = any("product" in f.lower() for f in files)
        assert has_products, \
            f"No products file found in /home/user/testsite. Files: {files}"


class TestAntiShortcutDynamicScraping:
    """Test that prices.json was dynamically scraped, not hardcoded."""

    def test_access_log_shows_recent_request(self):
        """Verify the test server access log shows a recent GET /products request."""
        access_log_path = "/home/user/testsite/access.log"

        # First, run the script to ensure it makes a request
        # Record time before running
        before_run = time.time()

        subprocess.run(
            ["timeout", "60", "python3", "scrape.py"],
            capture_output=True,
            text=True,
            cwd="/home/user/scraper"
        )

        # Check if access log exists
        if os.path.exists(access_log_path):
            with open(access_log_path, 'r') as f:
                log_content = f.read()

            # Look for GET /products request
            assert "/products" in log_content or "/products.html" in log_content, \
                f"Access log does not show any request to /products. Log content:\n{log_content[-1000:]}"
        else:
            # If no access log, we can't verify this way
            # Check that prices.json matches what the server serves
            import urllib.request
            try:
                response = urllib.request.urlopen('http://localhost:8080/products', timeout=5)
            except:
                response = urllib.request.urlopen('http://localhost:8080/products.html', timeout=5)
            html_content = response.read().decode('utf-8')

            # Extract prices from HTML
            price_pattern = re.compile(r'\$\d+\.\d{2}')
            html_prices = set(price_pattern.findall(html_content))

            # Get prices from JSON
            with open("/home/user/scraper/prices.json", 'r') as f:
                data = json.load(f)
            json_prices = set(item.get('price', '') for item in data)

            # Prices should match (indicating dynamic scraping)
            assert html_prices == json_prices, \
                f"Prices in JSON ({json_prices}) don't match prices on page ({html_prices}) - possible hardcoding"


class TestChromiumLaunchArgsFix:
    """Test that the chromium launch arguments have been properly fixed."""

    def test_script_has_disable_dev_shm_usage(self):
        """Verify scrape.py has --disable-dev-shm-usage flag."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()
        assert "--disable-dev-shm-usage" in content, \
            "scrape.py should have --disable-dev-shm-usage flag to work with limited /dev/shm"

    def test_script_has_headless_enabled(self):
        """Verify scrape.py has headless mode enabled (not False)."""
        with open("/home/user/scraper/scrape.py", "r") as f:
            content = f.read()

        # Should NOT have headless=False anymore
        has_headless_false = "headless=False" in content or "headless = False" in content
        assert not has_headless_false, \
            "scrape.py still has headless=False - should be headless=True or headless='new'"

        # Should have headless=True or headless='new' or just headless (defaults to True)
        has_headless_true = ("headless=True" in content or 
                           "headless = True" in content or
                           "headless='new'" in content or
                           'headless="new"' in content)
        # If headless parameter is removed entirely, pyppeteer defaults to headless=True
        # So we just need to ensure headless=False is gone
        assert has_headless_true or "headless" not in content.replace("--headless", ""), \
            "scrape.py should have headless=True or headless='new' (or omit for default True)"
