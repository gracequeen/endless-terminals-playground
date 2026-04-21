# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the employee database analysis task.
"""

import os
import sqlite3
import json
import csv
import hashlib
import pytest


class TestOutputFilesExist:
    """Test that all required output files have been created."""

    def test_orphaned_employees_file_exists(self):
        """Verify orphaned_employees.txt was created."""
        file_path = "/home/user/company/orphaned_employees.txt"
        assert os.path.isfile(file_path), \
            f"Output file {file_path} was not created"

    def test_salary_outliers_file_exists(self):
        """Verify salary_outliers.csv was created."""
        file_path = "/home/user/company/salary_outliers.csv"
        assert os.path.isfile(file_path), \
            f"Output file {file_path} was not created"

    def test_duplicate_emails_file_exists(self):
        """Verify duplicate_emails.txt was created."""
        file_path = "/home/user/company/duplicate_emails.txt"
        assert os.path.isfile(file_path), \
            f"Output file {file_path} was not created"

    def test_dept_summary_file_exists(self):
        """Verify dept_summary.json was created."""
        file_path = "/home/user/company/dept_summary.json"
        assert os.path.isfile(file_path), \
            f"Output file {file_path} was not created"


class TestOrphanedEmployeesFile:
    """Test the contents of orphaned_employees.txt."""

    def test_orphaned_employees_content(self):
        """Verify orphaned_employees.txt contains correct names."""
        file_path = "/home/user/company/orphaned_employees.txt"

        with open(file_path, 'r') as f:
            content = f.read()

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        expected_names = ["Frank Miller", "Quinn Harris", "Rachel Clark"]

        assert lines == expected_names, \
            f"orphaned_employees.txt contains {lines}, expected {expected_names}. " \
            f"These should be employees with manager_id values that don't exist as employee ids, sorted alphabetically."

    def test_orphaned_employees_sorted_alphabetically(self):
        """Verify orphaned_employees.txt is sorted alphabetically."""
        file_path = "/home/user/company/orphaned_employees.txt"

        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        sorted_lines = sorted(lines)
        assert lines == sorted_lines, \
            f"orphaned_employees.txt is not sorted alphabetically. Got {lines}, expected {sorted_lines}"

    def test_orphaned_employees_count(self):
        """Verify orphaned_employees.txt has exactly 3 entries."""
        file_path = "/home/user/company/orphaned_employees.txt"

        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) == 3, \
            f"orphaned_employees.txt has {len(lines)} entries, expected 3"


class TestSalaryOutliersFile:
    """Test the contents of salary_outliers.csv."""

    def test_salary_outliers_has_header(self):
        """Verify salary_outliers.csv has correct header row."""
        file_path = "/home/user/company/salary_outliers.csv"

        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

        expected_header = ['id', 'name', 'department', 'salary', 'dept_average']
        assert header == expected_header, \
            f"salary_outliers.csv header is {header}, expected {expected_header}"

    def test_salary_outliers_content(self):
        """Verify salary_outliers.csv contains correct data."""
        file_path = "/home/user/company/salary_outliers.csv"

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Expected outliers (sorted by department, then salary descending)
        expected_data = [
            {'id': '3', 'name': 'Carol White', 'department': 'Engineering', 'salary': '145000.0', 'dept_average': '99833.33'},
            {'id': '15', 'name': 'Olivia Thomas', 'department': 'Finance', 'salary': '125000.0', 'dept_average': '86600.0'},
            {'id': '19', 'name': 'Sam Lewis', 'department': 'Marketing', 'salary': '98000.0', 'dept_average': '71750.0'},
            {'id': '6', 'name': 'Frank Miller', 'department': 'Sales', 'salary': '115000.0', 'dept_average': '81400.0'},
        ]

        assert len(rows) == 4, \
            f"salary_outliers.csv has {len(rows)} data rows, expected 4"

        for i, (actual, expected) in enumerate(zip(rows, expected_data)):
            assert actual['id'] == expected['id'], \
                f"Row {i+1}: id is {actual['id']}, expected {expected['id']}"
            assert actual['name'] == expected['name'], \
                f"Row {i+1}: name is {actual['name']}, expected {expected['name']}"
            assert actual['department'] == expected['department'], \
                f"Row {i+1}: department is {actual['department']}, expected {expected['department']}"

            # Handle salary comparison with float tolerance
            actual_salary = float(actual['salary'])
            expected_salary = float(expected['salary'])
            assert abs(actual_salary - expected_salary) < 0.01, \
                f"Row {i+1}: salary is {actual_salary}, expected {expected_salary}"

            # Handle dept_average comparison with float tolerance
            actual_avg = float(actual['dept_average'])
            expected_avg = float(expected['dept_average'])
            assert abs(actual_avg - expected_avg) < 0.01, \
                f"Row {i+1}: dept_average is {actual_avg}, expected {expected_avg}"

    def test_salary_outliers_sorted_correctly(self):
        """Verify salary_outliers.csv is sorted by department then salary descending."""
        file_path = "/home/user/company/salary_outliers.csv"

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        departments = [row['department'] for row in rows]
        expected_dept_order = ['Engineering', 'Finance', 'Marketing', 'Sales']

        assert departments == expected_dept_order, \
            f"Departments are in order {departments}, expected {expected_dept_order}"


class TestDuplicateEmailsFile:
    """Test the contents of duplicate_emails.txt."""

    def test_duplicate_emails_content(self):
        """Verify duplicate_emails.txt contains correct emails."""
        file_path = "/home/user/company/duplicate_emails.txt"

        with open(file_path, 'r') as f:
            content = f.read()

        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        expected_emails = ["bob@company.com", "grace@company.com"]

        assert lines == expected_emails, \
            f"duplicate_emails.txt contains {lines}, expected {expected_emails}"

    def test_duplicate_emails_sorted_alphabetically(self):
        """Verify duplicate_emails.txt is sorted alphabetically."""
        file_path = "/home/user/company/duplicate_emails.txt"

        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        sorted_lines = sorted(lines)
        assert lines == sorted_lines, \
            f"duplicate_emails.txt is not sorted alphabetically. Got {lines}, expected {sorted_lines}"

    def test_duplicate_emails_count(self):
        """Verify duplicate_emails.txt has exactly 2 entries."""
        file_path = "/home/user/company/duplicate_emails.txt"

        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) == 2, \
            f"duplicate_emails.txt has {len(lines)} entries, expected 2"


class TestDeptSummaryFile:
    """Test the contents of dept_summary.json."""

    def test_dept_summary_is_valid_json(self):
        """Verify dept_summary.json is valid JSON."""
        file_path = "/home/user/company/dept_summary.json"

        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"dept_summary.json is not valid JSON: {e}")

    def test_dept_summary_has_all_departments(self):
        """Verify dept_summary.json contains all 5 departments."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        expected_departments = {'Engineering', 'Finance', 'HR', 'Marketing', 'Sales'}
        actual_departments = set(data.keys())

        assert actual_departments == expected_departments, \
            f"dept_summary.json has departments {actual_departments}, expected {expected_departments}"

    def test_dept_summary_engineering(self):
        """Verify Engineering department data is correct."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        eng = data.get('Engineering', {})

        assert eng.get('count') == 6, \
            f"Engineering count is {eng.get('count')}, expected 6"
        assert abs(eng.get('avg_salary', 0) - 99833.33) < 0.01, \
            f"Engineering avg_salary is {eng.get('avg_salary')}, expected 99833.33"
        assert eng.get('oldest_hire') == '2018-01-10', \
            f"Engineering oldest_hire is {eng.get('oldest_hire')}, expected 2018-01-10"
        assert eng.get('newest_hire') == '2023-04-10', \
            f"Engineering newest_hire is {eng.get('newest_hire')}, expected 2023-04-10"

    def test_dept_summary_finance(self):
        """Verify Finance department data is correct."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        fin = data.get('Finance', {})

        assert fin.get('count') == 5, \
            f"Finance count is {fin.get('count')}, expected 5"
        assert abs(fin.get('avg_salary', 0) - 86600.0) < 0.01, \
            f"Finance avg_salary is {fin.get('avg_salary')}, expected 86600.0"
        assert fin.get('oldest_hire') == '2015-12-01', \
            f"Finance oldest_hire is {fin.get('oldest_hire')}, expected 2015-12-01"
        assert fin.get('newest_hire') == '2022-11-28', \
            f"Finance newest_hire is {fin.get('newest_hire')}, expected 2022-11-28"

    def test_dept_summary_hr(self):
        """Verify HR department data is correct."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        hr = data.get('HR', {})

        assert hr.get('count') == 4, \
            f"HR count is {hr.get('count')}, expected 4"
        assert abs(hr.get('avg_salary', 0) - 64500.0) < 0.01, \
            f"HR avg_salary is {hr.get('avg_salary')}, expected 64500.0"
        assert hr.get('oldest_hire') == '2016-04-22', \
            f"HR oldest_hire is {hr.get('oldest_hire')}, expected 2016-04-22"
        assert hr.get('newest_hire') == '2023-03-08', \
            f"HR newest_hire is {hr.get('newest_hire')}, expected 2023-03-08"

    def test_dept_summary_marketing(self):
        """Verify Marketing department data is correct."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        mkt = data.get('Marketing', {})

        assert mkt.get('count') == 4, \
            f"Marketing count is {mkt.get('count')}, expected 4"
        assert abs(mkt.get('avg_salary', 0) - 71750.0) < 0.01, \
            f"Marketing avg_salary is {mkt.get('avg_salary')}, expected 71750.0"
        assert mkt.get('oldest_hire') == '2019-06-20', \
            f"Marketing oldest_hire is {mkt.get('oldest_hire')}, expected 2019-06-20"
        assert mkt.get('newest_hire') == '2023-07-01', \
            f"Marketing newest_hire is {mkt.get('newest_hire')}, expected 2023-07-01"

    def test_dept_summary_sales(self):
        """Verify Sales department data is correct."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            data = json.load(f)

        sales = data.get('Sales', {})

        assert sales.get('count') == 5, \
            f"Sales count is {sales.get('count')}, expected 5"
        assert abs(sales.get('avg_salary', 0) - 81400.0) < 0.01, \
            f"Sales avg_salary is {sales.get('avg_salary')}, expected 81400.0"
        assert sales.get('oldest_hire') == '2017-11-05', \
            f"Sales oldest_hire is {sales.get('oldest_hire')}, expected 2017-11-05"
        assert sales.get('newest_hire') == '2022-07-12', \
            f"Sales newest_hire is {sales.get('newest_hire')}, expected 2022-07-12"

    def test_dept_summary_departments_alphabetical_order(self):
        """Verify departments appear in alphabetical order in the JSON file."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            content = f.read()

        # Find positions of department names in the file
        departments = ['Engineering', 'Finance', 'HR', 'Marketing', 'Sales']
        positions = []
        for dept in departments:
            pos = content.find(f'"{dept}"')
            if pos == -1:
                pytest.fail(f"Department '{dept}' not found in dept_summary.json")
            positions.append((pos, dept))

        # Sort by position and check if departments are in alphabetical order
        sorted_by_pos = [dept for pos, dept in sorted(positions)]
        assert sorted_by_pos == departments, \
            f"Departments in file appear in order {sorted_by_pos}, expected alphabetical order {departments}"

    def test_dept_summary_pretty_printed(self):
        """Verify dept_summary.json is pretty-printed with 2-space indentation."""
        file_path = "/home/user/company/dept_summary.json"

        with open(file_path, 'r') as f:
            content = f.read()

        # Check for 2-space indentation pattern
        assert '  "' in content, \
            "dept_summary.json does not appear to be pretty-printed with 2-space indentation"

        # Verify it's not all on one line
        lines = content.strip().split('\n')
        assert len(lines) > 1, \
            "dept_summary.json appears to be on a single line - expected pretty-printed format"


class TestDatabaseUnmodified:
    """Test that the original database was not modified."""

    def test_database_still_exists(self):
        """Verify the database file still exists."""
        db_path = "/home/user/company/employees.db"
        assert os.path.isfile(db_path), \
            f"Database file {db_path} no longer exists"

    def test_database_has_same_row_count(self):
        """Verify the database still has 24 rows."""
        db_path = "/home/user/company/employees.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 24, \
            f"Database has {count} rows, expected 24 - database may have been modified"

    def test_database_has_original_employees(self):
        """Verify the database contains the original employees."""
        db_path = "/home/user/company/employees.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check for a few specific employees that should exist
        expected_employees = [
            (1, 'Alice Johnson', 'Engineering'),
            (9, 'Ivy Chen', 'HR'),
            (14, 'Noah Anderson', 'Finance'),
            (19, 'Sam Lewis', 'Marketing'),
            (24, 'Xavier King', 'Marketing'),
        ]

        for emp_id, name, dept in expected_employees:
            cursor.execute(
                "SELECT name, department FROM employees WHERE id = ?",
                (emp_id,)
            )
            result = cursor.fetchone()
            assert result is not None, \
                f"Employee with id {emp_id} not found - database may have been modified"
            assert result[0] == name and result[1] == dept, \
                f"Employee {emp_id} has name='{result[0]}', dept='{result[1]}', " \
                f"expected name='{name}', dept='{dept}' - database may have been modified"

        conn.close()

    def test_database_table_structure_unchanged(self):
        """Verify the employees table structure is unchanged."""
        db_path = "/home/user/company/employees.db"

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(employees)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected_columns = {'id', 'name', 'department', 'email', 'salary', 'hire_date', 'manager_id'}
        assert columns == expected_columns, \
            f"Table columns are {columns}, expected {expected_columns} - table structure may have been modified"
