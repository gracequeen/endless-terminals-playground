# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the tar extraction task.
"""

import os
import tarfile
import subprocess
import pytest


HOME_DIR = "/home/user"
ARCHIVE_PATH = "/home/user/backup-2024-03-15.tar.gz"
RESTORED_DB_PATH = "/home/user/restored_db"


class TestArchiveExists:
    """Test that the source archive exists and is readable."""

    def test_archive_file_exists(self):
        """The backup archive must exist."""
        assert os.path.exists(ARCHIVE_PATH), (
            f"Archive file {ARCHIVE_PATH} does not exist. "
            "The task requires this file to be present."
        )

    def test_archive_is_file(self):
        """The backup archive must be a regular file."""
        assert os.path.isfile(ARCHIVE_PATH), (
            f"{ARCHIVE_PATH} exists but is not a regular file."
        )

    def test_archive_is_readable(self):
        """The backup archive must be readable."""
        assert os.access(ARCHIVE_PATH, os.R_OK), (
            f"Archive file {ARCHIVE_PATH} is not readable. "
            "Check file permissions."
        )


class TestArchiveStructure:
    """Test that the archive has the expected internal structure."""

    def test_archive_is_valid_tarball(self):
        """The archive must be a valid gzipped tar file."""
        assert tarfile.is_tarfile(ARCHIVE_PATH), (
            f"{ARCHIVE_PATH} is not a valid tar file."
        )

    def test_archive_contains_db_directory(self):
        """The archive must contain a db/ directory."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            db_entries = [m for m in members if "/db/" in m or m.endswith("/db")]
            assert len(db_entries) > 0, (
                f"Archive {ARCHIVE_PATH} does not contain a db/ directory. "
                f"Found members: {members}"
            )

    def test_archive_contains_users_sql(self):
        """The archive must contain users.sql in the db/ folder."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            users_sql = [m for m in members if m.endswith("db/users.sql")]
            assert len(users_sql) > 0, (
                f"Archive does not contain db/users.sql. Found: {members}"
            )

    def test_archive_contains_orders_sql(self):
        """The archive must contain orders.sql in the db/ folder."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            orders_sql = [m for m in members if m.endswith("db/orders.sql")]
            assert len(orders_sql) > 0, (
                f"Archive does not contain db/orders.sql. Found: {members}"
            )

    def test_archive_contains_products_sql(self):
        """The archive must contain products.sql in the db/ folder."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            products_sql = [m for m in members if m.endswith("db/products.sql")]
            assert len(products_sql) > 0, (
                f"Archive does not contain db/products.sql. Found: {members}"
            )

    def test_archive_contains_logs_directory(self):
        """The archive must contain a logs/ directory (to verify selective extraction)."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            log_entries = [m for m in members if "/logs/" in m or m.endswith("/logs")]
            assert len(log_entries) > 0, (
                f"Archive does not contain logs/ directory. "
                "This is needed to verify selective extraction works."
            )

    def test_archive_contains_uploads_directory(self):
        """The archive must contain an uploads/ directory (to verify selective extraction)."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            members = tar.getnames()
            upload_entries = [m for m in members if "/uploads/" in m or m.endswith("/uploads")]
            assert len(upload_entries) > 0, (
                f"Archive does not contain uploads/ directory. "
                "This is needed to verify selective extraction works."
            )


class TestDbFileContents:
    """Test that the SQL files in the archive have expected content."""

    def test_users_sql_content(self):
        """users.sql must contain the expected dump marker."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("db/users.sql"):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode("utf-8")
                        assert "-- users table dump" in content, (
                            f"users.sql does not contain expected content. "
                            f"Found: {content[:100]}"
                        )
                        return
            pytest.fail("Could not find db/users.sql in archive")

    def test_orders_sql_content(self):
        """orders.sql must contain the expected dump marker."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("db/orders.sql"):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode("utf-8")
                        assert "-- orders table dump" in content, (
                            f"orders.sql does not contain expected content. "
                            f"Found: {content[:100]}"
                        )
                        return
            pytest.fail("Could not find db/orders.sql in archive")

    def test_products_sql_content(self):
        """products.sql must contain the expected dump marker."""
        with tarfile.open(ARCHIVE_PATH, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith("db/products.sql"):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode("utf-8")
                        assert "-- products table dump" in content, (
                            f"products.sql does not contain expected content. "
                            f"Found: {content[:100]}"
                        )
                        return
            pytest.fail("Could not find db/products.sql in archive")


class TestOutputDirectoryNotExists:
    """Test that the output directory does not exist yet."""

    def test_restored_db_does_not_exist(self):
        """The restored_db directory must not exist before the task."""
        assert not os.path.exists(RESTORED_DB_PATH), (
            f"{RESTORED_DB_PATH} already exists. "
            "It should not exist before the student performs the extraction."
        )


class TestRequiredTools:
    """Test that required tools are available."""

    def test_tar_available(self):
        """tar command must be available."""
        result = subprocess.run(
            ["which", "tar"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "tar command is not available. It is required for this task."
        )

    def test_gzip_available(self):
        """gzip command must be available."""
        result = subprocess.run(
            ["which", "gzip"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "gzip command is not available. It is required for this task."
        )


class TestHomeDirectoryWritable:
    """Test that the home directory is writable."""

    def test_home_directory_exists(self):
        """Home directory must exist."""
        assert os.path.isdir(HOME_DIR), (
            f"Home directory {HOME_DIR} does not exist."
        )

    def test_home_directory_writable(self):
        """Home directory must be writable."""
        assert os.access(HOME_DIR, os.W_OK), (
            f"Home directory {HOME_DIR} is not writable. "
            "The student needs to create directories here."
        )
