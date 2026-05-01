# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of extracting a database dump from a tarball.
"""

import os
import subprocess
import tarfile
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    def test_backups_directory_exists(self):
        """Verify /home/user/backups directory exists."""
        backups_dir = "/home/user/backups"
        assert os.path.isdir(backups_dir), (
            f"Directory {backups_dir} does not exist. "
            "The backups directory must exist to contain the tarball."
        )

    def test_tarball_exists(self):
        """Verify the tarball /home/user/backups/site-2024-03-15.tar.gz exists."""
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"
        assert os.path.isfile(tarball_path), (
            f"Tarball {tarball_path} does not exist. "
            "The source archive must be present for the task."
        )

    def test_tarball_is_readable(self):
        """Verify the tarball is readable."""
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"
        assert os.access(tarball_path, os.R_OK), (
            f"Tarball {tarball_path} is not readable. "
            "The archive must be readable to extract files from it."
        )

    def test_tarball_is_valid_gzip(self):
        """Verify the tarball is a valid gzip-compressed tar archive."""
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"
        try:
            with tarfile.open(tarball_path, "r:gz") as tf:
                # Just verify we can open it
                members = tf.getnames()
                assert len(members) > 0, (
                    f"Tarball {tarball_path} appears to be empty."
                )
        except tarfile.TarError as e:
            pytest.fail(
                f"Tarball {tarball_path} is not a valid tar.gz archive: {e}"
            )

    def test_tarball_contains_expected_files(self):
        """Verify the tarball contains the expected files including dump.sql."""
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"
        expected_files = {
            "var/www/html/index.html",
            "var/www/html/style.css",
            "var/db/dump.sql",
            "var/log/access.log",
        }

        with tarfile.open(tarball_path, "r:gz") as tf:
            members = set(tf.getnames())

            for expected in expected_files:
                assert expected in members, (
                    f"Expected file '{expected}' not found in tarball. "
                    f"Archive contains: {sorted(members)}"
                )

    def test_tarball_contains_dump_sql(self):
        """Verify the tarball contains var/db/dump.sql specifically."""
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"

        with tarfile.open(tarball_path, "r:gz") as tf:
            members = tf.getnames()
            dump_files = [m for m in members if m.endswith("dump.sql") or m.endswith("db.sql")]

            assert len(dump_files) > 0, (
                "No database dump file (dump.sql or db.sql) found in the tarball. "
                f"Archive contains: {sorted(members)}"
            )
            assert "var/db/dump.sql" in members, (
                "Expected 'var/db/dump.sql' in the tarball but it was not found. "
                f"Archive contains: {sorted(members)}"
            )

    def test_restore_directory_exists(self):
        """Verify /home/user/restore/ directory exists."""
        restore_dir = "/home/user/restore"
        assert os.path.isdir(restore_dir), (
            f"Directory {restore_dir} does not exist. "
            "The restore directory must exist as the target for extraction."
        )

    def test_restore_directory_is_empty(self):
        """Verify /home/user/restore/ directory is empty."""
        restore_dir = "/home/user/restore"
        contents = os.listdir(restore_dir)
        assert len(contents) == 0, (
            f"Directory {restore_dir} is not empty. "
            f"Found: {contents}. The restore directory must be empty initially."
        )

    def test_tar_command_available(self):
        """Verify tar command is available."""
        result = subprocess.run(
            ["which", "tar"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'tar' command is not available. "
            "tar must be installed to extract files from the archive."
        )

    def test_gzip_command_available(self):
        """Verify gzip command is available."""
        result = subprocess.run(
            ["which", "gzip"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "The 'gzip' command is not available. "
            "gzip must be installed to handle .gz compressed archives."
        )

    def test_home_user_writable(self):
        """Verify /home/user is writable."""
        home_dir = "/home/user"
        assert os.access(home_dir, os.W_OK), (
            f"Directory {home_dir} is not writable. "
            "The home directory must be writable for the task."
        )

    def test_restore_directory_writable(self):
        """Verify /home/user/restore is writable."""
        restore_dir = "/home/user/restore"
        assert os.access(restore_dir, os.W_OK), (
            f"Directory {restore_dir} is not writable. "
            "The restore directory must be writable to extract files into it."
        )
