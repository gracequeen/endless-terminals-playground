# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the tar extraction task for database dumps.
"""

import os
import tarfile
import subprocess
import pytest


HOME_DIR = "/home/user"
ARCHIVE_PATH = "/home/user/backup-2024-03-15.tar.gz"
RESTORED_DB_PATH = "/home/user/restored_db"


class TestRestoredDbDirectoryExists:
    """Test that the output directory was created."""

    def test_restored_db_exists(self):
        """The restored_db directory must exist after extraction."""
        assert os.path.exists(RESTORED_DB_PATH), (
            f"{RESTORED_DB_PATH} does not exist. "
            "You need to create this directory and extract the db files into it."
        )

    def test_restored_db_is_directory(self):
        """The restored_db path must be a directory."""
        assert os.path.isdir(RESTORED_DB_PATH), (
            f"{RESTORED_DB_PATH} exists but is not a directory."
        )


class TestSqlFilesExtracted:
    """Test that all required SQL files were extracted."""

    def _find_file_recursive(self, directory, filename):
        """Find a file recursively in a directory."""
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def test_users_sql_exists(self):
        """users.sql must be extracted to restored_db."""
        filepath = self._find_file_recursive(RESTORED_DB_PATH, "users.sql")
        assert filepath is not None, (
            f"users.sql was not found anywhere under {RESTORED_DB_PATH}. "
            "You need to extract the db/users.sql file from the archive."
        )

    def test_orders_sql_exists(self):
        """orders.sql must be extracted to restored_db."""
        filepath = self._find_file_recursive(RESTORED_DB_PATH, "orders.sql")
        assert filepath is not None, (
            f"orders.sql was not found anywhere under {RESTORED_DB_PATH}. "
            "You need to extract the db/orders.sql file from the archive."
        )

    def test_products_sql_exists(self):
        """products.sql must be extracted to restored_db."""
        filepath = self._find_file_recursive(RESTORED_DB_PATH, "products.sql")
        assert filepath is not None, (
            f"products.sql was not found anywhere under {RESTORED_DB_PATH}. "
            "You need to extract the db/products.sql file from the archive."
        )


class TestSqlFileContents:
    """Test that the extracted SQL files have correct content."""

    def _find_file_recursive(self, directory, filename):
        """Find a file recursively in a directory."""
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def test_users_sql_content(self):
        """users.sql must contain the expected dump marker."""
        filepath = self._find_file_recursive(RESTORED_DB_PATH, "users.sql")
        if filepath is None:
            pytest.skip("users.sql not found - tested in TestSqlFilesExtracted")

        with open(filepath, "r") as f:
            content = f.read()

        assert "-- users table dump" in content, (
            f"users.sql does not contain expected content '-- users table dump'. "
            f"File may be corrupted or incorrect. Content starts with: {content[:100]}"
        )

    def test_orders_sql_content(self):
        """orders.sql must contain the expected dump marker."""
        filepath = self._find_file_recursive(RESTORED_DB_PATH, "orders.sql")
        if filepath is None:
            pytest.skip("orders.sql not found - tested in TestSqlFilesExtracted")

        with open(filepath, "r") as f:
            content = f.read()

        assert "-- orders table dump" in content, (
            f"orders.sql does not contain expected content '-- orders table dump'. "
            f"File may be corrupted or incorrect. Content starts with: {content[:100]}"
        )

    def test_products_sql_content(self):
        """products.sql must contain the expected dump marker."""
        filepath = self._find_file_recursive(RESTORED_DB_PATH, "products.sql")
        if filepath is None:
            pytest.skip("products.sql not found - tested in TestSqlFilesExtracted")

        with open(filepath, "r") as f:
            content = f.read()

        assert "-- products table dump" in content, (
            f"products.sql does not contain expected content '-- products table dump'. "
            f"File may be corrupted or incorrect. Content starts with: {content[:100]}"
        )


class TestNoUnwantedFiles:
    """Test that logs and uploads were NOT extracted."""

    def test_no_log_files(self):
        """No .log files should be present under restored_db."""
        result = subprocess.run(
            ["find", RESTORED_DB_PATH, "-name", "*.log"],
            capture_output=True,
            text=True
        )
        log_files = [f for f in result.stdout.strip().split("\n") if f]
        assert len(log_files) == 0, (
            f"Found .log files under {RESTORED_DB_PATH}: {log_files}. "
            "You should only extract the db/ folder contents, not logs/."
        )

    def test_no_jpg_files(self):
        """No .jpg files should be present under restored_db."""
        result = subprocess.run(
            ["find", RESTORED_DB_PATH, "-name", "*.jpg"],
            capture_output=True,
            text=True
        )
        jpg_files = [f for f in result.stdout.strip().split("\n") if f]
        assert len(jpg_files) == 0, (
            f"Found .jpg files under {RESTORED_DB_PATH}: {jpg_files}. "
            "You should only extract the db/ folder contents, not uploads/."
        )

    def test_no_access_log(self):
        """access.log should not be present."""
        for root, dirs, files in os.walk(RESTORED_DB_PATH):
            assert "access.log" not in files, (
                f"Found access.log under {RESTORED_DB_PATH}. "
                "You should only extract the db/ folder contents."
            )

    def test_no_error_log(self):
        """error.log should not be present."""
        for root, dirs, files in os.walk(RESTORED_DB_PATH):
            assert "error.log" not in files, (
                f"Found error.log under {RESTORED_DB_PATH}. "
                "You should only extract the db/ folder contents."
            )

    def test_no_img001_jpg(self):
        """img001.jpg should not be present."""
        for root, dirs, files in os.walk(RESTORED_DB_PATH):
            assert "img001.jpg" not in files, (
                f"Found img001.jpg under {RESTORED_DB_PATH}. "
                "You should only extract the db/ folder contents."
            )

    def test_no_img002_jpg(self):
        """img002.jpg should not be present."""
        for root, dirs, files in os.walk(RESTORED_DB_PATH):
            assert "img002.jpg" not in files, (
                f"Found img002.jpg under {RESTORED_DB_PATH}. "
                "You should only extract the db/ folder contents."
            )


class TestArchiveUnchanged:
    """Test that the original archive is still intact."""

    def test_archive_still_exists(self):
        """The original archive must still exist."""
        assert os.path.exists(ARCHIVE_PATH), (
            f"Archive {ARCHIVE_PATH} no longer exists. "
            "The original archive should not be deleted."
        )

    def test_archive_still_valid(self):
        """The original archive must still be a valid tarball."""
        assert tarfile.is_tarfile(ARCHIVE_PATH), (
            f"{ARCHIVE_PATH} is no longer a valid tar file. "
            "The original archive should not be modified."
        )

    def test_archive_still_contains_all_files(self):
        """The original archive must still contain all expected files."""
        expected_suffixes = [
            "db/users.sql",
            "db/orders.sql", 
            "db/products.sql",
            "logs/access.log",
            "logs/error.log",
            "uploads/img001.jpg",
            "uploads/img002.jpg"
        ]

        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()

            for suffix in expected_suffixes:
                found = any(m.endswith(suffix) for m in members)
                assert found, (
                    f"Archive no longer contains {suffix}. "
                    f"The original archive should not be modified. Members: {members}"
                )


class TestOnlySqlFilesPresent:
    """Additional check that only SQL files are in the restored directory."""

    def test_only_expected_file_types(self):
        """Only .sql files should be present under restored_db."""
        non_sql_files = []
        for root, dirs, files in os.walk(RESTORED_DB_PATH):
            for f in files:
                if not f.endswith(".sql"):
                    non_sql_files.append(os.path.join(root, f))

        assert len(non_sql_files) == 0, (
            f"Found non-.sql files under {RESTORED_DB_PATH}: {non_sql_files}. "
            "Only database dump files (.sql) should be extracted."
        )

    def test_exactly_three_sql_files(self):
        """Exactly three SQL files should be present."""
        sql_files = []
        for root, dirs, files in os.walk(RESTORED_DB_PATH):
            for f in files:
                if f.endswith(".sql"):
                    sql_files.append(os.path.join(root, f))

        assert len(sql_files) == 3, (
            f"Expected exactly 3 SQL files, found {len(sql_files)}: {sql_files}. "
            "You should extract users.sql, orders.sql, and products.sql."
        )
