# test_final_state.py
"""
Post-condition tests to validate the operating system / filesystem state
after the student has completed the task of extracting the 20 largest artifacts
from the SQLite database into /home/user/builds/large_artifacts.txt.
"""

import os
import sqlite3
import pytest

BUILDS_DIR = "/home/user/builds"
DB_PATH = "/home/user/builds/artifacts.db"
OUTPUT_FILE = "/home/user/builds/large_artifacts.txt"


class TestOutputFileExists:
    """Test that the output file exists and is properly created."""

    def test_output_file_exists(self):
        """Verify large_artifacts.txt exists."""
        assert os.path.isfile(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist. "
            "The task requires creating this file with the 20 largest artifacts."
        )

    def test_output_file_is_readable(self):
        """Verify large_artifacts.txt is readable."""
        assert os.access(OUTPUT_FILE, os.R_OK), (
            f"Output file {OUTPUT_FILE} exists but is not readable."
        )


class TestOutputFileContent:
    """Test that the output file has the correct content."""

    @pytest.fixture
    def output_lines(self):
        """Read and return the lines from the output file."""
        with open(OUTPUT_FILE, 'r') as f:
            lines = f.read().strip().split('\n')
        # Filter out empty lines
        return [line for line in lines if line.strip()]

    @pytest.fixture
    def expected_data(self):
        """Query the database for the expected 20 largest artifacts."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT build_id, size_bytes FROM build_artifacts "
            "ORDER BY size_bytes DESC LIMIT 20"
        )
        results = cursor.fetchall()
        conn.close()
        return results

    def test_output_has_exactly_20_lines(self, output_lines):
        """Verify the output file contains exactly 20 lines."""
        assert len(output_lines) == 20, (
            f"Output file should contain exactly 20 lines, but has {len(output_lines)} lines. "
            "The task requires listing the 20 largest artifacts."
        )

    def test_each_line_is_tab_separated(self, output_lines):
        """Verify each line is tab-separated with two fields."""
        for i, line in enumerate(output_lines, 1):
            parts = line.split('\t')
            assert len(parts) == 2, (
                f"Line {i} should have exactly 2 tab-separated fields, "
                f"but has {len(parts)} fields. Line content: '{line}'"
            )

    def test_size_bytes_are_integers(self, output_lines):
        """Verify the second field (size_bytes) is a valid integer."""
        for i, line in enumerate(output_lines, 1):
            parts = line.split('\t')
            try:
                int(parts[1])
            except ValueError:
                pytest.fail(
                    f"Line {i}: size_bytes field '{parts[1]}' is not a valid integer. "
                    f"Line content: '{line}'"
                )

    def test_output_matches_database_query(self, output_lines, expected_data):
        """Verify the output matches the actual query results from the database."""
        for i, (line, (expected_build_id, expected_size)) in enumerate(
            zip(output_lines, expected_data), 1
        ):
            parts = line.split('\t')
            actual_build_id = parts[0]
            actual_size = int(parts[1])

            assert actual_build_id == expected_build_id, (
                f"Line {i}: build_id mismatch. "
                f"Expected '{expected_build_id}', got '{actual_build_id}'"
            )
            assert actual_size == expected_size, (
                f"Line {i}: size_bytes mismatch. "
                f"Expected {expected_size}, got {actual_size}"
            )

    def test_output_is_sorted_descending(self, output_lines):
        """Verify the output is sorted by size_bytes in descending order."""
        sizes = []
        for line in output_lines:
            parts = line.split('\t')
            sizes.append(int(parts[1]))

        for i in range(len(sizes) - 1):
            assert sizes[i] >= sizes[i + 1], (
                f"Output is not sorted in descending order by size_bytes. "
                f"Line {i + 1} has size {sizes[i]}, but line {i + 2} has size {sizes[i + 1]}."
            )


class TestDatabaseUnchanged:
    """Test that the database has not been modified."""

    @pytest.fixture
    def db_connection(self):
        """Provide a database connection for tests."""
        conn = sqlite3.connect(DB_PATH)
        yield conn
        conn.close()

    def test_database_still_exists(self):
        """Verify the database file still exists."""
        assert os.path.isfile(DB_PATH), (
            f"Database file {DB_PATH} no longer exists. "
            "The database should not be deleted or moved."
        )

    def test_table_still_has_150_rows(self, db_connection):
        """Verify build_artifacts table still contains 150 rows (no deletions)."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM build_artifacts")
        count = cursor.fetchone()[0]
        assert count == 150, (
            f"Table 'build_artifacts' should still have 150 rows, but has {count}. "
            "The database should not be modified."
        )

    def test_schema_unchanged(self, db_connection):
        """Verify the table schema has not been changed."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(build_artifacts)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {"id", "build_id", "path", "size_bytes", "created_at"}
        assert columns == expected_columns, (
            f"Table schema has been modified. "
            f"Expected columns: {expected_columns}, got: {columns}"
        )


class TestNoExtraFilesCreated:
    """Test that no extra files were created in the builds directory."""

    def test_only_expected_files_in_builds_dir(self):
        """Verify only artifacts.db and large_artifacts.txt exist in builds directory."""
        expected_files = {"artifacts.db", "large_artifacts.txt"}
        actual_files = set(os.listdir(BUILDS_DIR))

        # Check for unexpected files
        unexpected = actual_files - expected_files
        assert not unexpected, (
            f"Unexpected files found in {BUILDS_DIR}: {unexpected}. "
            "Only artifacts.db and large_artifacts.txt should exist."
        )

        # Verify expected files exist
        assert "artifacts.db" in actual_files, (
            f"artifacts.db is missing from {BUILDS_DIR}"
        )
        assert "large_artifacts.txt" in actual_files, (
            f"large_artifacts.txt is missing from {BUILDS_DIR}"
        )
