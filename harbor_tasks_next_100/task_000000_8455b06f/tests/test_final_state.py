# test_final_state.py
"""
Post-condition tests to validate the final state after the student has
added a 'discontinued' column to the products table.
"""

import os
import sqlite3
import subprocess
import pytest


# Constants
DB_PATH = "/home/user/data/inventory.db"
DATA_DIR = "/home/user/data"


class TestDatabaseFileValid:
    """Test that the database file is still valid after modification."""

    def test_database_file_exists(self):
        """Verify inventory.db file still exists."""
        assert os.path.isfile(DB_PATH), (
            f"Database file {DB_PATH} does not exist. "
            "The database file should still exist after the modification."
        )

    def test_database_is_valid_sqlite3(self):
        """Verify the file is still a valid SQLite3 database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            result = cursor.fetchone()
            conn.close()
            assert result is not None, "Could not query SQLite version"
        except sqlite3.DatabaseError as e:
            pytest.fail(
                f"File {DB_PATH} is not a valid SQLite3 database after modification. Error: {e}"
            )


class TestDiscontinuedColumnExists:
    """Test that the discontinued column was added correctly."""

    def test_discontinued_column_exists_in_schema(self):
        """Verify 'discontinued' column exists in the products table schema."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert 'discontinued' in column_names, (
            f"Column 'discontinued' not found in products table. "
            f"Current columns: {column_names}. "
            "The task requires adding a 'discontinued' column to the products table."
        )

    def test_discontinued_column_type_is_integer(self):
        """Verify 'discontinued' column has INTEGER type."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        discontinued_col = None
        for col in columns:
            if col[1] == 'discontinued':
                discontinued_col = col
                break

        assert discontinued_col is not None, (
            "Column 'discontinued' not found in products table."
        )
        # col[2] is the type
        assert discontinued_col[2].upper() == 'INTEGER', (
            f"Column 'discontinued' has type '{discontinued_col[2]}', expected 'INTEGER'."
        )

    def test_discontinued_column_has_default_zero(self):
        """Verify 'discontinued' column has DEFAULT 0."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        discontinued_col = None
        for col in columns:
            if col[1] == 'discontinued':
                discontinued_col = col
                break

        assert discontinued_col is not None, (
            "Column 'discontinued' not found in products table."
        )
        # col[4] is the default value
        default_val = discontinued_col[4]
        # Default can be '0', 0, or similar representation
        assert default_val is not None and str(default_val) == '0', (
            f"Column 'discontinued' has default value '{default_val}', expected '0'. "
            "The column must have DEFAULT 0."
        )

    def test_discontinued_column_via_cli_schema(self):
        """Verify 'discontinued' column appears in schema via sqlite3 CLI."""
        result = subprocess.run(
            ["sqlite3", DB_PATH, ".schema products"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"sqlite3 CLI failed to get schema. Error: {result.stderr}"
        )

        schema_output = result.stdout.lower()
        assert 'discontinued' in schema_output, (
            f"Column 'discontinued' not found in schema output from sqlite3 CLI. "
            f"Schema: {result.stdout}"
        )
        assert 'integer' in schema_output, (
            f"INTEGER type not found in schema output. Schema: {result.stdout}"
        )

    def test_discontinued_column_returns_zero(self):
        """Verify selecting discontinued column returns 0 for existing rows."""
        result = subprocess.run(
            ["sqlite3", DB_PATH, "SELECT discontinued FROM products LIMIT 1;"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"sqlite3 CLI failed to select discontinued column. Error: {result.stderr}"
        )

        output = result.stdout.strip()
        assert output == '0', (
            f"SELECT discontinued FROM products LIMIT 1 returned '{output}', expected '0'. "
            "The discontinued column should have default value 0 for all existing rows."
        )


class TestOriginalColumnsPreserved:
    """Test that original columns are still present and unchanged."""

    def test_id_column_still_exists(self):
        """Verify 'id' column still exists with correct type."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        id_col = None
        for col in columns:
            if col[1] == 'id':
                id_col = col
                break

        assert id_col is not None, "Column 'id' no longer exists in products table."
        assert id_col[2].upper() == 'INTEGER', (
            f"Column 'id' type changed to '{id_col[2]}', expected 'INTEGER'."
        )

    def test_name_column_still_exists(self):
        """Verify 'name' column still exists with correct type."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        name_col = None
        for col in columns:
            if col[1] == 'name':
                name_col = col
                break

        assert name_col is not None, "Column 'name' no longer exists in products table."
        assert name_col[2].upper() == 'TEXT', (
            f"Column 'name' type changed to '{name_col[2]}', expected 'TEXT'."
        )

    def test_price_column_still_exists(self):
        """Verify 'price' column still exists with correct type."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        price_col = None
        for col in columns:
            if col[1] == 'price':
                price_col = col
                break

        assert price_col is not None, "Column 'price' no longer exists in products table."
        assert price_col[2].upper() == 'REAL', (
            f"Column 'price' type changed to '{price_col[2]}', expected 'REAL'."
        )

    def test_quantity_column_still_exists(self):
        """Verify 'quantity' column still exists with correct type."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        quantity_col = None
        for col in columns:
            if col[1] == 'quantity':
                quantity_col = col
                break

        assert quantity_col is not None, "Column 'quantity' no longer exists in products table."
        assert quantity_col[2].upper() == 'INTEGER', (
            f"Column 'quantity' type changed to '{quantity_col[2]}', expected 'INTEGER'."
        )

    def test_products_table_has_five_columns(self):
        """Verify products table now has exactly 5 columns."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert len(columns) == 5, (
            f"Products table has {len(columns)} columns ({column_names}), expected 5. "
            "Expected: id, name, price, quantity, discontinued"
        )


class TestOriginalDataPreserved:
    """Test that original data rows are preserved."""

    def test_products_table_still_has_five_rows(self):
        """Verify products table still has exactly 5 rows."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products;")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 5, (
            f"Products table has {count} rows, expected 5. "
            "Original data rows should be preserved after adding the column."
        )

    def test_all_rows_have_valid_original_data(self):
        """Verify all rows still have non-null values for original columns."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, quantity FROM products;")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 5, f"Expected 5 rows, got {len(rows)}"

        for row in rows:
            assert row[0] is not None, "Found row with NULL id"
            assert row[1] is not None, f"Row id={row[0]} has NULL name"
            assert row[2] is not None, f"Row id={row[0]} has NULL price"
            assert row[3] is not None, f"Row id={row[0]} has NULL quantity"

    def test_all_discontinued_values_are_zero(self):
        """Verify all existing rows have discontinued = 0."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, discontinued FROM products;")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            assert row[1] == 0, (
                f"Row id={row[0]} has discontinued={row[1]}, expected 0. "
                "All existing rows should have discontinued = 0 (the default value)."
            )


class TestTableStructure:
    """Test that table structure is correct."""

    def test_products_table_still_exists(self):
        """Verify products table still exists."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products';"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, (
            "Table 'products' no longer exists. "
            "The table should be altered, not dropped and recreated incorrectly."
        )

    def test_only_products_table_exists(self):
        """Verify no additional tables were created."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = cursor.fetchall()
        conn.close()

        table_names = [t[0] for t in tables]
        assert table_names == ['products'], (
            f"Found tables: {table_names}. Expected only 'products' table. "
            "No additional tables should be created."
        )

    def test_discontinued_is_real_column_not_view(self):
        """Verify discontinued is a real column, not accessed via a view."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check no views exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='view';"
        )
        views = cursor.fetchall()

        # Also verify column is in PRAGMA table_info
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        view_names = [v[0] for v in views]
        assert len(views) == 0, (
            f"Found views: {view_names}. "
            "The discontinued column must be a real column, not accessed via a view."
        )

        column_names = [col[1] for col in columns]
        assert 'discontinued' in column_names, (
            "Column 'discontinued' must exist as a real column in the table schema."
        )
