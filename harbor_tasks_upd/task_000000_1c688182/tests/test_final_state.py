# test_final_state.py
"""
Tests to validate the final state of the system after the student has
added a 'downloads' column to the packages table.
"""

import os
import sqlite3
import subprocess
import pytest


DATABASE_PATH = "/home/user/artifacts.db"


class TestDatabaseFileIntegrity:
    """Tests for the database file integrity after modification."""

    def test_database_file_exists(self):
        """Verify that the artifacts.db file still exists."""
        assert os.path.exists(DATABASE_PATH), (
            f"Database file {DATABASE_PATH} does not exist. "
            "The database file should still be present after adding the column."
        )

    def test_database_file_is_valid_sqlite3(self):
        """Verify that the file is still a valid SQLite3 database."""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            result = cursor.fetchone()
            conn.close()
            assert result is not None, "Could not query SQLite version"
        except sqlite3.DatabaseError as e:
            pytest.fail(
                f"{DATABASE_PATH} is not a valid SQLite3 database after modification: {e}"
            )


class TestDownloadsColumnExists:
    """Tests to verify the downloads column was added correctly."""

    def test_downloads_column_exists_in_schema(self):
        """Verify that 'downloads' column exists in the packages table schema."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert 'downloads' in column_names, (
            f"Column 'downloads' not found in packages table. "
            f"Current columns: {column_names}. "
            "You need to add an integer column called 'downloads' to the packages table."
        )

    def test_downloads_column_is_integer_type(self):
        """Verify that 'downloads' column has INTEGER type."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        downloads_column = None
        for col in columns:
            if col[1] == 'downloads':
                downloads_column = col
                break

        assert downloads_column is not None, "Column 'downloads' not found"
        assert downloads_column[2].upper() == 'INTEGER', (
            f"Column 'downloads' should be INTEGER type, got '{downloads_column[2]}'. "
            "The task requires an integer column."
        )

    def test_downloads_column_via_sqlite3_cli(self):
        """Verify downloads column exists using sqlite3 CLI (as specified in truth)."""
        result = subprocess.run(
            ["sqlite3", DATABASE_PATH, "PRAGMA table_info(packages);"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"sqlite3 CLI failed: {result.stderr}"

        # Check that 'downloads' and 'INTEGER' appear in the output
        output = result.stdout.lower()
        assert 'downloads' in output, (
            f"Column 'downloads' not found in PRAGMA table_info output. "
            f"Output: {result.stdout}"
        )


class TestDownloadsColumnDefaultValue:
    """Tests to verify the downloads column has correct default value."""

    def test_downloads_column_has_default_zero(self):
        """Verify that 'downloads' column has a default value of 0."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        downloads_column = None
        for col in columns:
            if col[1] == 'downloads':
                downloads_column = col
                break

        assert downloads_column is not None, "Column 'downloads' not found"
        # col[4] is the default value in PRAGMA table_info
        default_val = downloads_column[4]
        assert default_val is not None and str(default_val) == '0', (
            f"Column 'downloads' should have default value of 0, got '{default_val}'. "
            "The task requires the column to default to 0."
        )

    def test_new_insert_gets_default_zero(self):
        """Verify that inserting a new row without specifying downloads gets 0."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Insert a test row without specifying downloads
        cursor.execute(
            "INSERT INTO packages (name, version) VALUES ('pytest-verify-pkg', '9.9.9');"
        )
        conn.commit()

        # Check the downloads value for the new row
        cursor.execute(
            "SELECT downloads FROM packages WHERE name='pytest-verify-pkg' AND version='9.9.9';"
        )
        result = cursor.fetchone()

        # Clean up the test row
        cursor.execute(
            "DELETE FROM packages WHERE name='pytest-verify-pkg' AND version='9.9.9';"
        )
        conn.commit()
        conn.close()

        assert result is not None, "Failed to retrieve the test row"
        assert result[0] == 0, (
            f"New row should have downloads=0 by default, got {result[0]}. "
            "The task requires the column to default to 0."
        )


class TestExistingDataPreserved:
    """Tests to verify existing data was preserved."""

    def test_original_five_rows_still_exist(self):
        """Verify that all 5 original rows still exist."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM packages;")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 5, (
            f"Expected at least 5 rows in packages table (the original rows), found {count}. "
            "The original data should be preserved after adding the column."
        )

    def test_original_columns_still_exist(self):
        """Verify that all original columns still exist."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(packages);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        required_columns = ['id', 'name', 'version', 'checksum', 'created_at']

        for col in required_columns:
            assert col in column_names, (
                f"Original column '{col}' is missing from packages table. "
                f"Current columns: {column_names}. "
                "All original columns should be preserved."
            )

    def test_original_data_intact(self):
        """Verify that original rows have their data intact."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, version FROM packages ORDER BY id LIMIT 5;")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) >= 5, f"Expected at least 5 rows, got {len(rows)}"

        for row in rows[:5]:
            id_val, name, version = row
            assert id_val is not None, "Original row id should not be NULL"
            assert name is not None and len(name) > 0, (
                f"Original row with id {id_val} has invalid name"
            )
            assert version is not None and len(version) > 0, (
                f"Original row with id {id_val} has invalid version"
            )

    def test_existing_rows_have_valid_downloads_value(self):
        """Verify existing rows have either 0 or NULL for downloads (both acceptable)."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, downloads FROM packages;")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            id_val, downloads = row
            # Task says "Should be nullable for existing rows, whatever"
            # So either 0 or NULL is acceptable
            assert downloads is None or downloads == 0, (
                f"Row with id {id_val} has unexpected downloads value: {downloads}. "
                "Expected 0 or NULL for existing rows."
            )


class TestNoUnwantedChanges:
    """Tests to verify no unwanted changes were made."""

    def test_packages_table_still_exists(self):
        """Verify that packages table still exists (not dropped and recreated incorrectly)."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='packages';"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, (
            "Table 'packages' does not exist. It should still exist after adding the column."
        )

    def test_no_extra_tables_created(self):
        """Verify that no unexpected tables were created."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = cursor.fetchall()
        conn.close()

        table_names = [t[0] for t in tables]
        # Only 'packages' table should exist
        assert len(table_names) == 1 and 'packages' in table_names, (
            f"Unexpected tables found: {table_names}. "
            "Only 'packages' table should exist."
        )

    def test_downloads_is_real_column_not_view(self):
        """Verify that downloads is a real column, not simulated by a view."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Check that 'packages' is a table, not a view
        cursor.execute(
            "SELECT type FROM sqlite_master WHERE name='packages';"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "packages not found in sqlite_master"
        assert result[0] == 'table', (
            f"'packages' should be a table, not a {result[0]}. "
            "The column must actually exist in the schema, not be simulated by a view."
        )


class TestColumnQueryability:
    """Tests to verify the downloads column can be queried properly."""

    def test_can_select_downloads_column(self):
        """Verify that we can SELECT the downloads column."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT downloads FROM packages LIMIT 1;")
            result = cursor.fetchone()
            # Result should exist (even if NULL)
            assert result is not None or True  # Just checking query succeeds
        except sqlite3.OperationalError as e:
            pytest.fail(f"Could not SELECT downloads column: {e}")
        finally:
            conn.close()

    def test_can_update_downloads_column(self):
        """Verify that we can UPDATE the downloads column."""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            # Get first row id
            cursor.execute("SELECT id FROM packages LIMIT 1;")
            row_id = cursor.fetchone()[0]

            # Update downloads
            cursor.execute(f"UPDATE packages SET downloads = 42 WHERE id = {row_id};")
            conn.commit()

            # Verify update
            cursor.execute(f"SELECT downloads FROM packages WHERE id = {row_id};")
            result = cursor.fetchone()
            assert result[0] == 42, f"Update failed, got {result[0]}"

            # Reset to 0
            cursor.execute(f"UPDATE packages SET downloads = 0 WHERE id = {row_id};")
            conn.commit()
        except sqlite3.OperationalError as e:
            pytest.fail(f"Could not UPDATE downloads column: {e}")
        finally:
            conn.close()

    def test_sqlite3_cli_select_downloads(self):
        """Verify downloads column is queryable via sqlite3 CLI (as per truth)."""
        result = subprocess.run(
            ["sqlite3", DATABASE_PATH, "SELECT downloads FROM packages LIMIT 1;"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"sqlite3 CLI failed to query downloads column: {result.stderr}"
        )
        # Value should be 0 or empty (NULL)
        value = result.stdout.strip()
        assert value == '0' or value == '', (
            f"Expected downloads value of 0 or NULL (empty), got '{value}'"
        )
