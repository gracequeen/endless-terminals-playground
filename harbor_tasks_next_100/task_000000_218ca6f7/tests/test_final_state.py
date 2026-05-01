# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has created a markdown doc from routes.json.
"""

import json
import os
import re
import pytest


class TestFinalState:
    """Test suite to verify the final state after task execution."""

    def test_endpoints_md_exists(self):
        """Verify /home/user/docs/endpoints.md file exists."""
        endpoints_file = "/home/user/docs/endpoints.md"
        assert os.path.isfile(endpoints_file), f"File {endpoints_file} does not exist"

    def test_endpoints_md_is_not_empty(self):
        """Verify /home/user/docs/endpoints.md is not empty."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read()
        assert len(content.strip()) > 0, f"File {endpoints_file} is empty"

    def test_endpoints_md_contains_pipe_separators(self):
        """Verify the markdown file uses | separators for table formatting."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read()
        assert '|' in content, "Markdown table should use | separators"

    def test_endpoints_md_has_header_separator_row(self):
        """Verify the markdown table has a header separator row with dashes."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read()

        # Look for a line that contains dashes between pipes (header separator)
        # Pattern matches lines like |---|---|---| or | --- | --- | --- |
        separator_pattern = r'\|[\s\-:]+\|[\s\-:]+\|'
        assert re.search(separator_pattern, content), \
            "Markdown table should have a header separator row with dashes (e.g., |---|---|---|)"

    def test_endpoints_md_has_method_column(self):
        """Verify the table has a Method column header (or similar)."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read().lower()

        assert 'method' in content, "Table should have a 'Method' column header"

    def test_endpoints_md_has_path_column(self):
        """Verify the table has a Path column header (or similar)."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read().lower()

        assert 'path' in content, "Table should have a 'Path' column header"

    def test_endpoints_md_has_description_column(self):
        """Verify the table has a Description column header (or similar)."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read().lower()

        assert 'description' in content, "Table should have a 'Description' column header"

    def test_endpoints_md_contains_get_users_endpoint(self):
        """Verify the table contains GET /users endpoint with description."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read()

        # Check for GET method
        assert 'GET' in content, "Table should contain GET method"
        # Check for /users path
        assert '/users' in content, "Table should contain /users path"
        # Check for description
        assert 'List all users' in content, "Table should contain 'List all users' description"

    def test_endpoints_md_contains_post_users_endpoint(self):
        """Verify the table contains POST /users endpoint with description."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read()

        # Check for POST method
        assert 'POST' in content, "Table should contain POST method"
        # Check for description
        assert 'Create a new user' in content, "Table should contain 'Create a new user' description"

    def test_endpoints_md_contains_get_user_by_id_endpoint(self):
        """Verify the table contains GET /users/{id} endpoint with description."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            content = f.read()

        # Check for /users/{id} path (may have various escaping)
        assert '/users/{id}' in content or '/users/\\{id\\}' in content or '/users/{id}' in content, \
            "Table should contain /users/{id} path"
        # Check for description
        assert 'Get user by ID' in content, "Table should contain 'Get user by ID' description"

    def test_endpoints_md_has_exactly_three_data_rows(self):
        """Verify the table has exactly 3 data rows (one per endpoint)."""
        endpoints_file = "/home/user/docs/endpoints.md"
        with open(endpoints_file, 'r') as f:
            lines = f.readlines()

        # Count lines that look like table data rows (contain | and are not header separator)
        # A data row should have | and contain actual content (not just dashes)
        data_rows = []
        for line in lines:
            line = line.strip()
            if '|' in line:
                # Skip separator rows (lines with only |, -, :, and spaces)
                if re.match(r'^[\|\s\-:]+$', line):
                    continue
                # This is likely a content row (header or data)
                data_rows.append(line)

        # Should have 1 header row + 3 data rows = 4 content rows with |
        # Or we can check that we have at least 3 rows with endpoint data
        endpoint_count = 0
        for row in data_rows:
            if '/users' in row:
                endpoint_count += 1

        assert endpoint_count == 3, \
            f"Table should have exactly 3 data rows with endpoints, found {endpoint_count}"

    def test_routes_json_unchanged(self):
        """Verify /home/user/api/routes.json is unchanged (invariant)."""
        routes_file = "/home/user/api/routes.json"

        with open(routes_file, 'r') as f:
            data = json.load(f)

        expected_endpoints = [
            {"method": "GET", "path": "/users", "description": "List all users"},
            {"method": "POST", "path": "/users", "description": "Create a new user"},
            {"method": "GET", "path": "/users/{id}", "description": "Get user by ID"}
        ]

        assert len(data) == 3, f"routes.json should still have 3 endpoints, found {len(data)}"

        for expected in expected_endpoints:
            found = any(
                ep.get("method") == expected["method"] and
                ep.get("path") == expected["path"] and
                ep.get("description") == expected["description"]
                for ep in data
            )
            assert found, f"routes.json should be unchanged, missing endpoint: {expected}"

    def test_all_endpoints_from_json_in_markdown(self):
        """Verify all endpoints from routes.json appear in the markdown (anti-shortcut guard)."""
        routes_file = "/home/user/api/routes.json"
        endpoints_file = "/home/user/docs/endpoints.md"

        with open(routes_file, 'r') as f:
            routes_data = json.load(f)

        with open(endpoints_file, 'r') as f:
            md_content = f.read()

        for endpoint in routes_data:
            method = endpoint.get("method")
            path = endpoint.get("path")
            description = endpoint.get("description")

            assert method in md_content, \
                f"Method '{method}' from routes.json not found in endpoints.md"
            assert path in md_content or path.replace('{', '\\{').replace('}', '\\}') in md_content, \
                f"Path '{path}' from routes.json not found in endpoints.md"
            assert description in md_content, \
                f"Description '{description}' from routes.json not found in endpoints.md"
