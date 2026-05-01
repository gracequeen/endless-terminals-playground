# test_initial_state.py
"""
Pre-condition tests to validate the operating system / filesystem state
before the student performs the task of extracting the 20 largest artifacts
from the SQLite database.
"""

import os
import sqlite3
import subprocess
import pytest

HOME_DIR = "/home/user"
BUILDS_DIR = "/home/user/builds"
DB_PATH = "/home/user/builds/artifacts.db"
OUTPUT_FILE = "/home/user/builds/large_artifacts.txt"


class TestDirectoryStructure:
    """Test that required directories exist and are accessible."""

    def test_home_directory_exists(self):
        """Verify /home/user directory exists."""
        assert os.path.isdir(HOME_DIR), f"Home directory {HOME_DIR} does not exist"

    def test_builds_directory_exists(self):
        """Verify /home/user/builds directory exists."""
        assert os.path.isdir(BUILDS_DIR), f"Builds directory {BUILDS_DIR} does not exist"

    def test_builds_directory_is_writable(self):
        """Verify /home/user/builds directory is writable."""
        assert os.access(BUILDS_DIR, os.W_OK), f"Builds directory {BUILDS_DIR} is not writable"


class TestDatabaseFile:
    """Test that the SQLite database file exists and is valid."""

    def test_database_file_exists(self):
        """Verify artifacts.db file exists."""
        assert os.path.isfile(DB_PATH), f"Database file {DB_PATH} does not exist"

    def test_database_file_is_readable(self):
        """Verify artifacts.db file is readable."""
        assert os.access(DB_PATH, os.R_OK), f"Database file {DB_PATH} is not readable"

    def test_database_is_valid_sqlite3(self):
        """Verify artifacts.db is a valid SQLite3 database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
        except sqlite3.DatabaseError as e:
            pytest.fail(f"Database file {DB_PATH} is not a valid SQLite3 database: {e}")


class TestDatabaseSchema:
    """Test that the database has the correct schema."""

    @pytest.fixture
    def db_connection(self):
        """Provide a database connection for tests."""
        conn = sqlite3.connect(DB_PATH)
        yield conn
        conn.close()

    def test_build_artifacts_table_exists(self, db_connection):
        """Verify build_artifacts table exists."""
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='build_artifacts'"
        )
        result = cursor.fetchone()
        assert result is not None, "Table 'build_artifacts' does not exist in the database"

    def test_table_has_id_column(self, db_connection):
        """Verify build_artifacts table has 'id' column."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(build_artifacts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "id" in columns, "Column 'id' is missing from build_artifacts table"
        assert "INT" in columns["id"].upper(), f"Column 'id' should be INTEGER, got {columns['id']}"

    def test_table_has_build_id_column(self, db_connection):
        """Verify build_artifacts table has 'build_id' column."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(build_artifacts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "build_id" in columns, "Column 'build_id' is missing from build_artifacts table"
        assert "TEXT" in columns["build_id"].upper(), f"Column 'build_id' should be TEXT, got {columns['build_id']}"

    def test_table_has_path_column(self, db_connection):
        """Verify build_artifacts table has 'path' column."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(build_artifacts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "path" in columns, "Column 'path' is missing from build_artifacts table"
        assert "TEXT" in columns["path"].upper(), f"Column 'path' should be TEXT, got {columns['path']}"

    def test_table_has_size_bytes_column(self, db_connection):
        """Verify build_artifacts table has 'size_bytes' column."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(build_artifacts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "size_bytes" in columns, "Column 'size_bytes' is missing from build_artifacts table"
        assert "INT" in columns["size_bytes"].upper(), f"Column 'size_bytes' should be INTEGER, got {columns['size_bytes']}"

    def test_table_has_created_at_column(self, db_connection):
        """Verify build_artifacts table has 'created_at' column."""
        cursor = db_connection.cursor()
        cursor.execute("PRAGMA table_info(build_artifacts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "created_at" in columns, "Column 'created_at' is missing from build_artifacts table"
        assert "TEXT" in columns["created_at"].upper(), f"Column 'created_at' should be TEXT, got {columns['created_at']}"


class TestDatabaseContent:
    """Test that the database has the expected content."""

    @pytest.fixture
    def db_connection(self):
        """Provide a database connection for tests."""
        conn = sqlite3.connect(DB_PATH)
        yield conn
        conn.close()

    def test_table_has_150_rows(self, db_connection):
        """Verify build_artifacts table contains 150 rows."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM build_artifacts")
        count = cursor.fetchone()[0]
        assert count == 150, f"Table 'build_artifacts' should have 150 rows, but has {count}"

    def test_size_bytes_has_varying_values(self, db_connection):
        """Verify size_bytes column has varying values in expected range."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT MIN(size_bytes), MAX(size_bytes) FROM build_artifacts")
        min_size, max_size = cursor.fetchone()

        # Range should be roughly 1KB to 500MB
        assert min_size is not None, "size_bytes column has no values"
        assert max_size is not None, "size_bytes column has no values"
        assert min_size >= 0, f"Minimum size_bytes should be non-negative, got {min_size}"
        assert max_size > min_size, "size_bytes values should vary (max should be greater than min)"

    def test_at_least_20_distinct_sizes(self, db_connection):
        """Verify there are at least 20 distinct size_bytes values for meaningful sorting."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT size_bytes) FROM build_artifacts")
        distinct_count = cursor.fetchone()[0]
        assert distinct_count >= 20, f"Should have at least 20 distinct size_bytes values, got {distinct_count}"


class TestSqlite3CLI:
    """Test that sqlite3 CLI is available."""

    def test_sqlite3_cli_installed(self):
        """Verify sqlite3 CLI is installed and available."""
        result = subprocess.run(
            ["which", "sqlite3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "sqlite3 CLI is not installed or not in PATH"

    def test_sqlite3_cli_works(self):
        """Verify sqlite3 CLI can execute basic commands."""
        result = subprocess.run(
            ["sqlite3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"sqlite3 CLI failed to run: {result.stderr}"


class TestOutputFileNotExists:
    """Test that the output file does not exist initially."""

    def test_large_artifacts_file_does_not_exist(self):
        """Verify large_artifacts.txt does not exist initially."""
        assert not os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} already exists - it should not exist before the task is performed"
        )
