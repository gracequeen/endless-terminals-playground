# test_final_state.py
"""
Tests to validate the final state of the system after the student has completed the task.
This verifies the Flask inventory API is running correctly with proper authentication.
"""

import json
import os
import socket
import sqlite3
import subprocess
import time
import pytest


class TestAppRunning:
    """Test that the Flask application is running and listening."""

    def test_port_8080_is_listening(self):
        """Port 8080 must be listening."""
        # Try to connect to the port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            result = sock.connect_ex(('localhost', 8080))
            assert result == 0, f"Port 8080 is not listening (connect returned {result})"
        finally:
            sock.close()

    def test_flask_process_running(self):
        """A Python process serving the app should be running."""
        # Check if something is listening on port 8080
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )
        assert ":8080" in result.stdout, \
            f"No process is listening on port 8080. ss output: {result.stdout}"


class TestAuthentication:
    """Test that authentication is properly enforced."""

    def test_request_without_api_key_returns_401(self):
        """Requests without X-Api-Key header must return 401."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"curl failed: {result.stderr}"
        http_code = result.stdout.strip()
        assert http_code == "401", \
            f"Request without API key should return 401, got {http_code}"

    def test_request_with_wrong_api_key_returns_401(self):
        """Requests with wrong X-Api-Key must return 401."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-H", "X-Api-Key: wrong-key-12345",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"curl failed: {result.stderr}"
        http_code = result.stdout.strip()
        assert http_code == "401", \
            f"Request with wrong API key should return 401, got {http_code}"

    def test_request_with_correct_api_key_returns_200(self):
        """Requests with correct X-Api-Key must return 200."""
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"curl failed: {result.stderr}"
        http_code = result.stdout.strip()
        assert http_code == "200", \
            f"Request with correct API key should return 200, got {http_code}"


class TestGetItems:
    """Test the GET /api/items endpoint."""

    def test_get_items_returns_json(self):
        """GET /api/items must return valid JSON."""
        result = subprocess.run(
            ["curl", "-s",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"curl failed: {result.stderr}"

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Response is not valid JSON: {e}. Response: {result.stdout[:500]}")

    def test_get_items_returns_array(self):
        """GET /api/items must return a JSON array."""
        result = subprocess.run(
            ["curl", "-s",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list), \
            f"Response should be a JSON array, got {type(data).__name__}"

    def test_get_items_returns_at_least_15_items(self):
        """GET /api/items must return at least 15 items."""
        result = subprocess.run(
            ["curl", "-s",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        data = json.loads(result.stdout)
        assert len(data) >= 15, \
            f"Response should contain at least 15 items, got {len(data)}"

    def test_items_have_required_keys(self):
        """Each item must have id, sku, name, quantity keys."""
        result = subprocess.run(
            ["curl", "-s",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        data = json.loads(result.stdout)

        required_keys = {"id", "sku", "name", "quantity"}
        for i, item in enumerate(data):
            assert isinstance(item, dict), f"Item {i} is not an object: {item}"
            missing = required_keys - set(item.keys())
            assert not missing, \
                f"Item {i} is missing keys: {missing}. Item: {item}"


class TestPostItems:
    """Test the POST /api/items endpoint."""

    def test_post_new_item_returns_201(self):
        """POST /api/items with new item must return 201."""
        payload = json.dumps({
            "sku": "TEST-RESTORE-001",
            "name": "Restore Verification",
            "quantity": 1
        })

        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-X", "POST",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "-H", "Content-Type: application/json",
             "-d", payload,
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"curl failed: {result.stderr}"
        http_code = result.stdout.strip()
        # Accept 201 (created) or 200 (if item already exists from previous test run)
        # Also accept 409 (conflict) if item already exists
        assert http_code in ["201", "200", "409"], \
            f"POST should return 201 (or 200/409 if exists), got {http_code}"

    def test_posted_item_appears_in_get(self):
        """After POST, the new item must appear in GET /api/items."""
        # First, try to POST the item (might already exist)
        payload = json.dumps({
            "sku": "TEST-RESTORE-001",
            "name": "Restore Verification",
            "quantity": 1
        })

        subprocess.run(
            ["curl", "-s",
             "-X", "POST",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "-H", "Content-Type: application/json",
             "-d", payload,
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Now GET and verify the item exists
        result = subprocess.run(
            ["curl", "-s",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )

        data = json.loads(result.stdout)
        skus = [item.get("sku") for item in data]
        assert "TEST-RESTORE-001" in skus, \
            f"TEST-RESTORE-001 not found in items. SKUs found: {skus}"


class TestDatabaseIntegrity:
    """Test that the database maintains integrity."""

    def test_database_file_exists(self):
        """The database file must still exist at the expected path."""
        path = "/home/user/inventory/data.db"
        assert os.path.isfile(path), f"Database file {path} does not exist"

    def test_database_has_original_items_preserved(self):
        """The original 18 items must be preserved (or more if new items added)."""
        path = "/home/user/inventory/data.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        conn.close()
        # Should have at least 18 (original) items, possibly more if TEST-RESTORE-001 was added
        assert count >= 18, \
            f"Database has {count} items, expected at least 18 (original items may have been deleted)"

    def test_database_contains_test_restore_item(self):
        """The TEST-RESTORE-001 item must exist in the database after POST."""
        # First ensure the item was posted
        payload = json.dumps({
            "sku": "TEST-RESTORE-001",
            "name": "Restore Verification",
            "quantity": 1
        })

        subprocess.run(
            ["curl", "-s",
             "-X", "POST",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "-H", "Content-Type: application/json",
             "-d", payload,
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check database directly
        path = "/home/user/inventory/data.db"
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT sku, name, quantity FROM items WHERE sku = 'TEST-RESTORE-001'")
        row = cursor.fetchone()
        conn.close()

        assert row is not None, \
            "TEST-RESTORE-001 not found in database - POST did not persist to database"
        assert row[0] == "TEST-RESTORE-001", f"SKU mismatch: {row[0]}"


class TestEnvFilePreserved:
    """Test that the .env file is preserved."""

    def test_env_file_exists(self):
        """The .env file must still exist."""
        path = "/home/user/inventory/.env"
        assert os.path.isfile(path), f"Environment file {path} does not exist"

    def test_env_contains_api_key(self):
        """The .env file must still contain the correct API_KEY."""
        path = "/home/user/inventory/.env"
        with open(path, "r") as f:
            content = f.read()
        assert "API_KEY=inv-7f3a2b9c4d5e6f1a" in content, \
            f".env file does not contain expected API_KEY. Content: {content}"


class TestConsistentResponses:
    """Test that the API returns consistent data across multiple calls."""

    def test_multiple_get_requests_return_consistent_data(self):
        """Multiple GET requests should return consistent item counts."""
        counts = []
        for _ in range(3):
            result = subprocess.run(
                ["curl", "-s",
                 "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
                 "http://localhost:8080/api/items"],
                capture_output=True,
                text=True,
                timeout=10
            )
            data = json.loads(result.stdout)
            counts.append(len(data))

        # All counts should be the same
        assert len(set(counts)) == 1, \
            f"Inconsistent item counts across requests: {counts}"

    def test_api_returns_real_data_not_mocked(self):
        """Verify the API is returning real database data by checking specific fields."""
        result = subprocess.run(
            ["curl", "-s",
             "-H", "X-Api-Key: inv-7f3a2b9c4d5e6f1a",
             "http://localhost:8080/api/items"],
            capture_output=True,
            text=True,
            timeout=10
        )
        data = json.loads(result.stdout)

        # Verify items have realistic data (not empty strings, valid quantities)
        for item in data:
            assert item.get("id") is not None, f"Item missing id: {item}"
            assert item.get("sku"), f"Item has empty sku: {item}"
            assert item.get("name"), f"Item has empty name: {item}"
            assert isinstance(item.get("quantity"), int), \
                f"Item quantity is not an integer: {item}"
