# test_initial_state.py
"""
Pre-condition tests to validate the initial state before the student performs
the task of adding a 'discontinued' column to the products table.
"""

import os
import sqlite3
import subprocess
import pytest


# Constants
DB_PATH = "/home/user/data/inventory.db"
DATA_DIR = "/home/user/data"


class TestDirectoryExists:
    """Test that the data directory exists and is writable."""

    def test_data_directory_exists(self):
        """Verify /home/user/data/ directory exists."""
        assert os.path.isdir(DATA_DIR), (
            f"Data directory {DATA_DIR} does not exist. "
            "The directory must exist before the task can be performed."
        )

    def test_data_directory_is_writable(self):
        """Verify /home/user/data/ directory is writable."""
        assert os.access(DATA_DIR, os.W_OK), (
            f"Data directory {DATA_DIR} is not writable. "
            "Write permissions are required to modify the database."
        )


class TestDatabaseFileExists:
    """Test that the database file exists and is valid."""

    def test_database_file_exists(self):
        """Verify inventory.db file exists."""
        assert os.path.isfile(DB_PATH), (
            f"Database file {DB_PATH} does not exist. "
            "The SQLite database file must exist before the task can be performed."
        )

    def test_database_file_is_readable(self):
        """Verify database file is readable."""
        assert os.access(DB_PATH, os.R_OK), (
            f"Database file {DB_PATH} is not readable. "
            "Read permissions are required to access the database."
        )

    def test_database_file_is_writable(self):
        """Verify database file is writable."""
        assert os.access(DB_PATH, os.W_OK), (
            f"Database file {DB_PATH} is not writable. "
            "Write permissions are required to modify the database schema."
        )

    def test_database_is_valid_sqlite3(self):
        """Verify the file is a valid SQLite3 database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Simple query to verify database is valid
            cursor.execute("SELECT sqlite_version();")
            result = cursor.fetchone()
            conn.close()
            assert result is not None, "Could not query SQLite version"
        except sqlite3.DatabaseError as e:
            pytest.fail(
                f"File {DB_PATH} is not a valid SQLite3 database. Error: {e}"
            )


class TestSqlite3CliAvailable:
    """Test that sqlite3 CLI tool is available."""

    def test_sqlite3_cli_exists(self):
        """Verify sqlite3 command-line tool is available."""
        result = subprocess.run(
            ["which", "sqlite3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "sqlite3 CLI tool is not available in PATH. "
            "The sqlite3 command-line tool must be installed."
        )

    def test_sqlite3_cli_works(self):
        """Verify sqlite3 CLI can execute commands."""
        result = subprocess.run(
            ["sqlite3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "sqlite3 CLI tool is not working properly. "
            f"Error: {result.stderr}"
        )


class TestProductsTableExists:
    """Test that the products table exists with correct schema."""

    def test_products_table_exists(self):
        """Verify products table exists in the database."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='products';"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, (
            "Table 'products' does not exist in the database. "
            "The products table must exist before adding the discontinued column."
        )

    def test_products_table_has_id_column(self):
        """Verify products table has 'id' column as INTEGER PRIMARY KEY."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        id_column = None
        for col in columns:
            if col[1] == 'id':
                id_column = col
                break

        assert id_column is not None, (
            "Column 'id' not found in products table. "
            "Expected schema: id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER"
        )
        assert id_column[2].upper() == 'INTEGER', (
            f"Column 'id' has type '{id_column[2]}', expected 'INTEGER'."
        )
        assert id_column[5] == 1, (
            "Column 'id' is not a PRIMARY KEY as expected."
        )

    def test_products_table_has_name_column(self):
        """Verify products table has 'name' column as TEXT."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        name_column = None
        for col in columns:
            if col[1] == 'name':
                name_column = col
                break

        assert name_column is not None, (
            "Column 'name' not found in products table. "
            "Expected schema: id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER"
        )
        assert name_column[2].upper() == 'TEXT', (
            f"Column 'name' has type '{name_column[2]}', expected 'TEXT'."
        )

    def test_products_table_has_price_column(self):
        """Verify products table has 'price' column as REAL."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        price_column = None
        for col in columns:
            if col[1] == 'price':
                price_column = col
                break

        assert price_column is not None, (
            "Column 'price' not found in products table. "
            "Expected schema: id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER"
        )
        assert price_column[2].upper() == 'REAL', (
            f"Column 'price' has type '{price_column[2]}', expected 'REAL'."
        )

    def test_products_table_has_quantity_column(self):
        """Verify products table has 'quantity' column as INTEGER."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        quantity_column = None
        for col in columns:
            if col[1] == 'quantity':
                quantity_column = col
                break

        assert quantity_column is not None, (
            "Column 'quantity' not found in products table. "
            "Expected schema: id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER"
        )
        assert quantity_column[2].upper() == 'INTEGER', (
            f"Column 'quantity' has type '{quantity_column[2]}', expected 'INTEGER'."
        )

    def test_products_table_has_exactly_four_columns(self):
        """Verify products table has exactly 4 columns (no discontinued column yet)."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert len(columns) == 4, (
            f"Products table has {len(columns)} columns ({column_names}), expected 4. "
            "Expected schema: id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER"
        )

    def test_discontinued_column_does_not_exist(self):
        """Verify 'discontinued' column does not exist yet."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(products);")
        columns = cursor.fetchall()
        conn.close()

        column_names = [col[1] for col in columns]
        assert 'discontinued' not in column_names, (
            "Column 'discontinued' already exists in products table. "
            "The task is to add this column, but it already exists."
        )


class TestSampleDataExists:
    """Test that the products table has the expected sample data."""

    def test_products_table_has_five_rows(self):
        """Verify products table has exactly 5 rows of sample data."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products;")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 5, (
            f"Products table has {count} rows, expected 5 rows of sample data."
        )

    def test_all_rows_have_valid_data(self):
        """Verify all rows have non-null values for required columns."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, price, quantity FROM products;")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            assert row[0] is not None, "Found row with NULL id"
            assert row[1] is not None, f"Row id={row[0]} has NULL name"
            assert row[2] is not None, f"Row id={row[0]} has NULL price"
            assert row[3] is not None, f"Row id={row[0]} has NULL quantity"


class TestNoOtherTables:
    """Test that only the products table exists."""

    def test_only_products_table_exists(self):
        """Verify only the products table exists (no other user tables)."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = cursor.fetchall()
        conn.close()

        table_names = [t[0] for t in tables]
        assert table_names == ['products'], (
            f"Found tables: {table_names}. Expected only 'products' table."
        )
