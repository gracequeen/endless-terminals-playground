# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the employee database analysis task.
"""

import os
import sqlite3
import pytest


class TestDirectoryStructure:
    """Test that required directories exist and are accessible."""

    def test_home_user_directory_exists(self):
        """Verify /home/user directory exists."""
        assert os.path.isdir("/home/user"), \
            "Directory /home/user does not exist"

    def test_company_directory_exists(self):
        """Verify /home/user/company directory exists."""
        assert os.path.isdir("/home/user/company"), \
            "Directory /home/user/company does not exist"

    def test_company_directory_is_writable(self):
        """Verify /home/user/company directory is writable."""
        assert os.access("/home/user/company", os.W_OK), \
            "Directory /home/user/company is not writable"


class TestDatabaseFile:
    """Test that the SQLite database file exists and has correct structure."""

    def test_database_file_exists(self):
        """Verify employees.db file exists."""
        db_path = "/home/user/company/employees.db"
        assert os.path.isfile(db_path), \
            f"Database file {db_path} does not exist"

    def test_database_is_readable(self):
        """Verify employees.db file is readable."""
        db_path = "/home/user/company/employees.db"
        assert os.access(db_path, os.R_OK), \
            f"Database file {db_path} is not readable"

    def test_database_is_valid_sqlite(self):
        """Verify employees.db is a valid SQLite database."""
        db_path = "/home/user/company/employees.db"
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            conn.close()
        except sqlite3.Error as e:
            pytest.fail(f"File {db_path} is not a valid SQLite database: {e}")

    def test_employees_table_exists(self):
        """Verify employees table exists in the database."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None, \
            "Table 'employees' does not exist in the database"

    def test_employees_table_has_correct_columns(self):
        """Verify employees table has all required columns."""
        db_path = "/home/user/company/employees.db"
        expected_columns = {
            'id', 'name', 'department', 'email', 'salary', 'hire_date', 'manager_id'
        }

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(employees)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        missing_columns = expected_columns - columns
        assert not missing_columns, \
            f"Table 'employees' is missing columns: {missing_columns}"

    def test_employees_table_has_data(self):
        """Verify employees table contains data."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, \
            "Table 'employees' is empty - expected pre-populated data"

    def test_employees_table_has_expected_row_count(self):
        """Verify employees table has the expected number of rows (24)."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 24, \
            f"Table 'employees' has {count} rows, expected 24 rows"


class TestOutputFilesDoNotExist:
    """Test that output files do not exist initially."""

    def test_orphaned_employees_file_does_not_exist(self):
        """Verify orphaned_employees.txt does not exist initially."""
        file_path = "/home/user/company/orphaned_employees.txt"
        assert not os.path.exists(file_path), \
            f"Output file {file_path} already exists - should not exist initially"

    def test_salary_outliers_file_does_not_exist(self):
        """Verify salary_outliers.csv does not exist initially."""
        file_path = "/home/user/company/salary_outliers.csv"
        assert not os.path.exists(file_path), \
            f"Output file {file_path} already exists - should not exist initially"

    def test_duplicate_emails_file_does_not_exist(self):
        """Verify duplicate_emails.txt does not exist initially."""
        file_path = "/home/user/company/duplicate_emails.txt"
        assert not os.path.exists(file_path), \
            f"Output file {file_path} already exists - should not exist initially"

    def test_dept_summary_file_does_not_exist(self):
        """Verify dept_summary.json does not exist initially."""
        file_path = "/home/user/company/dept_summary.json"
        assert not os.path.exists(file_path), \
            f"Output file {file_path} already exists - should not exist initially"


class TestDatabaseContent:
    """Test that the database contains the expected data for the task."""

    def test_database_has_orphaned_manager_references(self):
        """Verify database has employees with non-existent manager_ids (for task 1)."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Find employees whose manager_id doesn't exist as an employee id
        cursor.execute("""
            SELECT COUNT(*) FROM employees e
            WHERE e.manager_id IS NOT NULL
            AND e.manager_id NOT IN (SELECT id FROM employees)
        """)
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, \
            "No orphaned manager references found - expected some for task 1"

    def test_database_has_multiple_departments(self):
        """Verify database has multiple departments (for task 2 and 4)."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT department) FROM employees")
        count = cursor.fetchone()[0]
        conn.close()
        assert count >= 2, \
            f"Only {count} department(s) found - expected multiple departments"

    def test_database_has_duplicate_emails(self):
        """Verify database has duplicate email addresses (for task 3)."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT email FROM employees
                GROUP BY email
                HAVING COUNT(*) > 1
            )
        """)
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, \
            "No duplicate email addresses found - expected some for task 3"

    def test_database_has_salary_data(self):
        """Verify database has salary data (for task 2)."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE salary IS NOT NULL AND salary > 0")
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, \
            "No valid salary data found in employees table"

    def test_database_has_hire_date_data(self):
        """Verify database has hire_date data (for task 4)."""
        db_path = "/home/user/company/employees.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees WHERE hire_date IS NOT NULL")
        count = cursor.fetchone()[0]
        conn.close()
        assert count > 0, \
            "No hire_date data found in employees table"
