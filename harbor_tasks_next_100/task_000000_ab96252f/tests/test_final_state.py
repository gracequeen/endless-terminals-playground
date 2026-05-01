# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the rsync task to sync only CSV files from /home/user/reports/
to /home/user/backup/reports/.
"""

import os
import subprocess
import filecmp
import pytest


class TestBackupDirectoryStructure:
    """Test that the backup directory structure was created correctly."""

    def test_backup_reports_directory_exists(self):
        """Verify /home/user/backup/reports/ directory was created."""
        path = "/home/user/backup/reports"
        assert os.path.isdir(path), f"Directory {path} does not exist - rsync should have created it"

    def test_backup_q1_subdirectory_exists(self):
        """Verify /home/user/backup/reports/q1/ subdirectory was created."""
        path = "/home/user/backup/reports/q1"
        assert os.path.isdir(path), f"Directory {path} does not exist - subdirectories should be synced"

    def test_backup_q2_subdirectory_exists(self):
        """Verify /home/user/backup/reports/q2/ subdirectory was created."""
        path = "/home/user/backup/reports/q2"
        assert os.path.isdir(path), f"Directory {path} does not exist - subdirectories should be synced"


class TestBackupCSVFilesExist:
    """Test that all required CSV files were synced to the backup directory."""

    def test_backup_summary_csv_exists(self):
        """Verify /home/user/backup/reports/summary.csv was synced."""
        path = "/home/user/backup/reports/summary.csv"
        assert os.path.isfile(path), f"File {path} does not exist - CSV files should be synced"

    def test_backup_q1_sales_csv_exists(self):
        """Verify /home/user/backup/reports/q1/sales.csv was synced."""
        path = "/home/user/backup/reports/q1/sales.csv"
        assert os.path.isfile(path), f"File {path} does not exist - CSV files should be synced"

    def test_backup_q1_inventory_csv_exists(self):
        """Verify /home/user/backup/reports/q1/inventory.csv was synced."""
        path = "/home/user/backup/reports/q1/inventory.csv"
        assert os.path.isfile(path), f"File {path} does not exist - CSV files should be synced"

    def test_backup_q2_sales_csv_exists(self):
        """Verify /home/user/backup/reports/q2/sales.csv was synced."""
        path = "/home/user/backup/reports/q2/sales.csv"
        assert os.path.isfile(path), f"File {path} does not exist - CSV files should be synced"


class TestNoXLSXFilesInBackup:
    """Test that no xlsx files were synced to the backup directory."""

    def test_no_xlsx_in_backup_root(self):
        """Verify no xlsx files in /home/user/backup/reports/."""
        path = "/home/user/backup/reports/scratch.xlsx"
        assert not os.path.exists(path), f"File {path} should NOT exist - xlsx files should be excluded"

    def test_no_xlsx_in_backup_q1(self):
        """Verify no xlsx files in /home/user/backup/reports/q1/."""
        path = "/home/user/backup/reports/q1/sales_draft.xlsx"
        assert not os.path.exists(path), f"File {path} should NOT exist - xlsx files should be excluded"

    def test_no_xlsx_in_backup_q2(self):
        """Verify no xlsx files in /home/user/backup/reports/q2/."""
        path = "/home/user/backup/reports/q2/notes.xlsx"
        assert not os.path.exists(path), f"File {path} should NOT exist - xlsx files should be excluded"

    def test_find_no_xlsx_files_in_backup(self):
        """Verify find command returns 0 xlsx files in backup."""
        result = subprocess.run(
            ["find", "/home/user/backup/reports", "-name", "*.xlsx"],
            capture_output=True,
            text=True
        )
        xlsx_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(xlsx_files) == 0, f"Expected 0 xlsx files in backup, found {len(xlsx_files)}: {xlsx_files}"


class TestCSVFileCount:
    """Test that exactly 4 CSV files were synced."""

    def test_backup_has_exactly_four_csv_files(self):
        """Verify there are exactly 4 CSV files in /home/user/backup/reports/."""
        result = subprocess.run(
            ["find", "/home/user/backup/reports", "-name", "*.csv"],
            capture_output=True,
            text=True
        )
        csv_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(csv_files) == 4, f"Expected 4 CSV files in backup, found {len(csv_files)}: {csv_files}"


class TestCSVFilesAreIdentical:
    """Test that synced CSV files are byte-identical to source files."""

    def test_summary_csv_is_identical(self):
        """Verify summary.csv in backup is identical to source."""
        source = "/home/user/reports/summary.csv"
        backup = "/home/user/backup/reports/summary.csv"
        assert filecmp.cmp(source, backup, shallow=False), \
            f"File {backup} is not identical to {source}"

    def test_q1_sales_csv_is_identical(self):
        """Verify q1/sales.csv in backup is identical to source."""
        source = "/home/user/reports/q1/sales.csv"
        backup = "/home/user/backup/reports/q1/sales.csv"
        assert filecmp.cmp(source, backup, shallow=False), \
            f"File {backup} is not identical to {source}"

    def test_q1_inventory_csv_is_identical(self):
        """Verify q1/inventory.csv in backup is identical to source."""
        source = "/home/user/reports/q1/inventory.csv"
        backup = "/home/user/backup/reports/q1/inventory.csv"
        assert filecmp.cmp(source, backup, shallow=False), \
            f"File {backup} is not identical to {source}"

    def test_q2_sales_csv_is_identical(self):
        """Verify q2/sales.csv in backup is identical to source."""
        source = "/home/user/reports/q2/sales.csv"
        backup = "/home/user/backup/reports/q2/sales.csv"
        assert filecmp.cmp(source, backup, shallow=False), \
            f"File {backup} is not identical to {source}"


class TestSourceDirectoryUnchanged:
    """Test that the source directory remains unchanged (invariant)."""

    def test_source_reports_still_exists(self):
        """Verify /home/user/reports/ still exists."""
        path = "/home/user/reports"
        assert os.path.isdir(path), f"Directory {path} should still exist"

    def test_source_still_has_four_csv_files(self):
        """Verify source still has exactly 4 CSV files."""
        result = subprocess.run(
            ["find", "/home/user/reports", "-name", "*.csv"],
            capture_output=True,
            text=True
        )
        csv_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(csv_files) == 4, f"Source should still have 4 CSV files, found {len(csv_files)}"

    def test_source_still_has_three_xlsx_files(self):
        """Verify source still has exactly 3 XLSX files."""
        result = subprocess.run(
            ["find", "/home/user/reports", "-name", "*.xlsx"],
            capture_output=True,
            text=True
        )
        xlsx_files = [f for f in result.stdout.strip().split('\n') if f]
        assert len(xlsx_files) == 3, f"Source should still have 3 XLSX files, found {len(xlsx_files)}"

    def test_source_summary_csv_exists(self):
        """Verify /home/user/reports/summary.csv still exists."""
        path = "/home/user/reports/summary.csv"
        assert os.path.isfile(path), f"File {path} should still exist in source"

    def test_source_scratch_xlsx_exists(self):
        """Verify /home/user/reports/scratch.xlsx still exists."""
        path = "/home/user/reports/scratch.xlsx"
        assert os.path.isfile(path), f"File {path} should still exist in source"


class TestAntiShortcutGuards:
    """Anti-shortcut tests as specified in the task."""

    def test_xlsx_count_is_zero(self):
        """Verify `find /home/user/backup/reports -name '*.xlsx' | wc -l` returns 0."""
        result = subprocess.run(
            "find /home/user/backup/reports -name '*.xlsx' | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        assert count == 0, f"Expected 0 xlsx files in backup, found {count}"

    def test_csv_count_is_four(self):
        """Verify `find /home/user/backup/reports -name '*.csv' | wc -l` returns 4."""
        result = subprocess.run(
            "find /home/user/backup/reports -name '*.csv' | wc -l",
            shell=True,
            capture_output=True,
            text=True
        )
        count = int(result.stdout.strip())
        assert count == 4, f"Expected 4 csv files in backup, found {count}"
