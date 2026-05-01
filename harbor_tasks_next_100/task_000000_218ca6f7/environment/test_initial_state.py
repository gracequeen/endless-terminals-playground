# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the task of creating a markdown doc from routes.json.
"""

import json
import os
import shutil
import subprocess
import pytest


class TestInitialState:
    """Test suite to verify the initial state before task execution."""

    def test_api_directory_exists(self):
        """Verify /home/user/api/ directory exists."""
        api_dir = "/home/user/api"
        assert os.path.isdir(api_dir), f"Directory {api_dir} does not exist"

    def test_docs_directory_exists(self):
        """Verify /home/user/docs/ directory exists."""
        docs_dir = "/home/user/docs"
        assert os.path.isdir(docs_dir), f"Directory {docs_dir} does not exist"

    def test_docs_directory_is_empty(self):
        """Verify /home/user/docs/ directory is empty."""
        docs_dir = "/home/user/docs"
        contents = os.listdir(docs_dir)
        assert len(contents) == 0, f"Directory {docs_dir} should be empty but contains: {contents}"

    def test_routes_json_exists(self):
        """Verify /home/user/api/routes.json file exists."""
        routes_file = "/home/user/api/routes.json"
        assert os.path.isfile(routes_file), f"File {routes_file} does not exist"

    def test_routes_json_is_valid_json(self):
        """Verify /home/user/api/routes.json contains valid JSON."""
        routes_file = "/home/user/api/routes.json"
        with open(routes_file, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"File {routes_file} does not contain valid JSON: {e}")

    def test_routes_json_is_array(self):
        """Verify /home/user/api/routes.json contains a JSON array."""
        routes_file = "/home/user/api/routes.json"
        with open(routes_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list), f"routes.json should contain a JSON array, got {type(data).__name__}"

    def test_routes_json_has_three_endpoints(self):
        """Verify /home/user/api/routes.json contains exactly 3 endpoints."""
        routes_file = "/home/user/api/routes.json"
        with open(routes_file, 'r') as f:
            data = json.load(f)
        assert len(data) == 3, f"routes.json should contain 3 endpoints, found {len(data)}"

    def test_routes_json_endpoints_have_required_fields(self):
        """Verify each endpoint in routes.json has method, path, and description fields."""
        routes_file = "/home/user/api/routes.json"
        with open(routes_file, 'r') as f:
            data = json.load(f)

        required_fields = {"method", "path", "description"}
        for i, endpoint in enumerate(data):
            missing = required_fields - set(endpoint.keys())
            assert not missing, f"Endpoint {i} is missing required fields: {missing}"

    def test_routes_json_contains_expected_endpoints(self):
        """Verify routes.json contains the expected three endpoints."""
        routes_file = "/home/user/api/routes.json"
        with open(routes_file, 'r') as f:
            data = json.load(f)

        expected_endpoints = [
            {"method": "GET", "path": "/users", "description": "List all users"},
            {"method": "POST", "path": "/users", "description": "Create a new user"},
            {"method": "GET", "path": "/users/{id}", "description": "Get user by ID"}
        ]

        # Check each expected endpoint exists in the data
        for expected in expected_endpoints:
            found = any(
                ep.get("method") == expected["method"] and
                ep.get("path") == expected["path"] and
                ep.get("description") == expected["description"]
                for ep in data
            )
            assert found, f"Expected endpoint not found in routes.json: {expected}"

    def test_api_directory_is_writable(self):
        """Verify /home/user/api/ directory is writable."""
        api_dir = "/home/user/api"
        assert os.access(api_dir, os.W_OK), f"Directory {api_dir} is not writable"

    def test_docs_directory_is_writable(self):
        """Verify /home/user/docs/ directory is writable."""
        docs_dir = "/home/user/docs"
        assert os.access(docs_dir, os.W_OK), f"Directory {docs_dir} is not writable"

    def test_jq_is_available(self):
        """Verify jq command is available."""
        jq_path = shutil.which("jq")
        assert jq_path is not None, "jq is not available in PATH"

    def test_python3_is_available(self):
        """Verify python3 command is available."""
        python3_path = shutil.which("python3")
        assert python3_path is not None, "python3 is not available in PATH"

    def test_endpoints_md_does_not_exist(self):
        """Verify /home/user/docs/endpoints.md does not exist yet (output file)."""
        endpoints_file = "/home/user/docs/endpoints.md"
        assert not os.path.exists(endpoints_file), f"Output file {endpoints_file} should not exist in initial state"
