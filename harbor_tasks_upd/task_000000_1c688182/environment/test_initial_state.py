# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs
the task of adding a 'downloads' column to the packages table.
"""

import os
import sqlite3
import subprocess
import pytest


DATABASE_PATH = "/home/user/artifacts.db"


class TestDatabaseFileExists:
    """Tests for the database file existence and accessibility."""

    def test_database_file_exists(self):
        """Verify that the artifacts.db file exists."""
        assert os.path.exists(DATABASE_PATH), (
            f"Database file {DATABASE_PATH} does not exist. "
            "The task requires this file to be present."
        )

    def test_database_file_is_file(self):
        """Verify that artifacts.db is a regular file, not a directory."""
        assert os.path.isfile(DATABASE_PATH), (
            f"{DATABASE_PATH} exists but is not a regular file."
        )

    def test_database_file_is_writable(self):
        """Verify that the database file is writable by the current user."""
        assert os.access(DATABASE_PATH, os.W_OK), (
            f"Database file {DATABASE_PATH} is not writable. "
            "The task requires write access to add a column."
        )

    def test_database_file_is_readable(self):
        """Verify that the database file is readable by the current user."""
        assert os.access(DATABASE_PATH, os.R_OK), (
            f"Database file {DATABASE_PATH} is not readable."
        )


class TestDatabaseIsValidSQLite:
    """Tests to verify the database is a valid SQLite3 database."""

    def test_database_is_valid_sqlite3(self):
        """Verify that the file is a valid SQLite3 database."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # Execute a simple query to verify it's a valid database
            cursor.execute("SELECT sqlite_version();")
            result = cursor.fetchone()
            conn.close()
            assert result is not None, "Could not query SQLite version"
        except sqlite3.DatabaseError as e:
            pytest.fail(
                f"{DATABASE_PATH} is not a valid SQLite3 database: {e}"
            )


class TestPackagesTableExists:
    """Tests for the packages table existence and structure."""

    def test_packages_table_exists(self):
        """Verify that the 'packages' table exists in the database."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='packages';"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, (
            "Table 'packages' does not exist in the database. "
            "The task requires this table to be present."
        )

    def test_packages_table_has_id_column(self):
        """Verify that packages table has 'id' column as INTEGER PRIMARY KEY."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        id_column = None
        for col in columns:
            if col[1] == 'id':
                id_column = col
                break

        assert id_column is not None, "Column 'id' not found in packages table"
        assert id_column[2].upper() == 'INTEGER', (
            f"Column 'id' should be INTEGER, got {id_column[2]}"
        )
        assert id_column[5] == 1, "Column 'id' should be PRIMARY KEY"

    def test_packages_table_has_name_column(self):
        """Verify that packages table has 'name' column as TEXT NOT NULL."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        name_column = None
        for col in columns:
            if col[1] == 'name':
                name_column = col
                break

        assert name_column is not None, "Column 'name' not found in packages table"
        assert name_column[2].upper() == 'TEXT', (
            f"Column 'name' should be TEXT, got {name_column[2]}"
        )
        assert name_column[3] == 1, "Column 'name' should be NOT NULL"

    def test_packages_table_has_version_column(self):
        """Verify that packages table has 'version' column as TEXT NOT NULL."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        version_column = None
        for col in columns:
            if col[1] == 'version':
                version_column = col
                break

        assert version_column is not None, "Column 'version' not found in packages table"
        assert version_column[2].upper() == 'TEXT', (
            f"Column 'version' should be TEXT, got {version_column[2]}"
        )
        assert version_column[3] == 1, "Column 'version' should be NOT NULL"

    def test_packages_table_has_checksum_column(self):
        """Verify that packages table has 'checksum' column as TEXT."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        checksum_column = None
        for col in columns:
            if col[1] == 'checksum':
                checksum_column = col
                break

        assert checksum_column is not None, "Column 'checksum' not found in packages table"
        assert checksum_column[2].upper() == 'TEXT', (
            f"Column 'checksum' should be TEXT, got {checksum_column[2]}"
        )

    def test_packages_table_has_created_at_column(self):
        """Verify that packages table has 'created_at' column as TEXT."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        created_at_column = None
        for col in columns:
            if col[1] == 'created_at':
                created_at_column = col
                break

        assert created_at_column is not None, "Column 'created_at' not found in packages table"
        assert created_at_column[2].upper() == 'TEXT', (
            f"Column 'created_at' should be TEXT, got {created_at_column[2]}"
        )

    def test_packages_table_has_exactly_five_columns(self):
        """Verify that packages table has exactly 5 columns initially."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        assert len(columns) == 5, (
            f"Expected 5 columns in packages table, found {len(columns)}. "
            f"Columns: {[col[1] for col in columns]}"
        )

    def test_downloads_column_does_not_exist(self):
        """Verify that 'downloads' column does NOT exist yet (this is what student needs to add)."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert 'downloads' not in column_names, (
            "Column 'downloads' already exists in packages table. "
            "The initial state should not have this column - it's what the student needs to add."
        )


class TestPackagesTableData:
    """Tests for the existing data in the packages table."""

    def test_packages_table_has_five_rows(self):
        """Verify that packages table has exactly 5 existing rows."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM packages;")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 5, (
            f"Expected 5 rows in packages table, found {count}. "
            "The initial state should have 5 existing rows with package data."
        )

    def test_packages_have_valid_data(self):
        """Verify that existing packages have valid name and version data."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, version FROM packages;")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"

        for row in rows:
            id_val, name, version = row
            assert id_val is not None, "Package id should not be NULL"
            assert name is not None and len(name) > 0, (
                f"Package with id {id_val} has invalid name: {name}"
            )
            assert version is not None and len(version) > 0, (
                f"Package with id {id_val} has invalid version: {version}"
            )


class TestSQLite3CLIAvailable:
    """Tests for sqlite3 CLI tool availability."""

    def test_sqlite3_cli_available(self):
        """Verify that sqlite3 CLI tool is available."""
        result = subprocess.run(
            ["which", "sqlite3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "sqlite3 CLI tool is not available in PATH. "
            "The task expects sqlite3 to be installed."
        )

    def test_sqlite3_cli_can_query_database(self):
        """Verify that sqlite3 CLI can query the database."""
        result = subprocess.run(
            ["sqlite3", DATABASE_PATH, "SELECT COUNT(*) FROM packages;"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"sqlite3 CLI failed to query database: {result.stderr}"
        )
        assert result.stdout.strip() == "5", (
            f"Expected 5 rows from sqlite3 CLI, got: {result.stdout.strip()}"
        )
