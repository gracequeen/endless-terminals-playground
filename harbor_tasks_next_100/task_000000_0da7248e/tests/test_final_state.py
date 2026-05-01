# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the task of extracting a database dump from a tarball.
"""

import os
import subprocess
import tarfile
import hashlib
import pytest


class TestFinalState:
    """Validate the final state after the task is performed."""

    def test_dump_sql_exists_in_restore(self):
        """Verify /home/user/restore/dump.sql exists."""
        dump_path = "/home/user/restore/dump.sql"
        assert os.path.isfile(dump_path), (
            f"File {dump_path} does not exist. "
            "The database dump must be extracted to /home/user/restore/dump.sql"
        )

    def test_dump_sql_is_regular_file(self):
        """Verify dump.sql is a regular file, not a directory or symlink."""
        dump_path = "/home/user/restore/dump.sql"
        assert os.path.isfile(dump_path) and not os.path.islink(dump_path), (
            f"{dump_path} must be a regular file, not a symlink or directory."
        )

    def test_dump_sql_contains_postgresql_header(self):
        """Verify dump.sql contains the PostgreSQL dump header near the top."""
        dump_path = "/home/user/restore/dump.sql"

        with open(dump_path, "r") as f:
            # Read first 20 lines to check for header near the top
            top_lines = []
            for i, line in enumerate(f):
                if i >= 20:
                    break
                top_lines.append(line)

        top_content = "".join(top_lines)
        assert "-- PostgreSQL dump" in top_content, (
            f"File {dump_path} does not contain '-- PostgreSQL dump' near the top. "
            "The extracted file should be a valid PostgreSQL dump."
        )

    def test_dump_sql_ends_with_dump_complete(self):
        """Verify dump.sql ends with '-- Dump complete'."""
        dump_path = "/home/user/restore/dump.sql"

        with open(dump_path, "r") as f:
            content = f.read()

        # Strip trailing whitespace and check for the ending marker
        stripped_content = content.rstrip()
        assert stripped_content.endswith("-- Dump complete"), (
            f"File {dump_path} does not end with '-- Dump complete'. "
            "The extracted file should be a complete PostgreSQL dump."
        )

    def test_dump_sql_matches_archive_content(self):
        """Verify extracted dump.sql is byte-identical to var/db/dump.sql in archive."""
        dump_path = "/home/user/restore/dump.sql"
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"

        # Read the extracted file
        with open(dump_path, "rb") as f:
            extracted_content = f.read()

        # Read the file from the archive
        with tarfile.open(tarball_path, "r:gz") as tf:
            member = tf.getmember("var/db/dump.sql")
            archive_file = tf.extractfile(member)
            archive_content = archive_file.read()

        # Compare using hash for efficiency
        extracted_hash = hashlib.sha256(extracted_content).hexdigest()
        archive_hash = hashlib.sha256(archive_content).hexdigest()

        assert extracted_hash == archive_hash, (
            f"Extracted file {dump_path} does not match var/db/dump.sql from archive. "
            f"Expected hash: {archive_hash}, got: {extracted_hash}. "
            "The extracted file must be byte-identical to the original."
        )

    def test_only_one_file_in_restore_directory(self):
        """Verify only one file exists in /home/user/restore/."""
        restore_dir = "/home/user/restore"

        # Use find command as specified in anti-shortcut guards
        result = subprocess.run(
            ["find", restore_dir, "-type", "f"],
            capture_output=True,
            text=True
        )

        files = [f for f in result.stdout.strip().split("\n") if f]
        file_count = len(files)

        assert file_count == 1, (
            f"Expected exactly 1 file in {restore_dir}, found {file_count}. "
            f"Files found: {files}. "
            "Only dump.sql should be extracted, no other files from the archive."
        )

    def test_no_nested_directories_in_restore(self):
        """Verify dump.sql is directly in /home/user/restore/, not in nested dirs."""
        restore_dir = "/home/user/restore"
        dump_path = "/home/user/restore/dump.sql"

        # Check that there are no subdirectories
        for item in os.listdir(restore_dir):
            item_path = os.path.join(restore_dir, item)
            assert not os.path.isdir(item_path), (
                f"Found directory '{item}' in {restore_dir}. "
                "The file should be extracted directly as dump.sql, "
                "not preserving the var/db/ directory structure."
            )

        # Verify dump.sql is directly in restore, not nested
        assert os.path.dirname(dump_path) == restore_dir, (
            f"dump.sql should be directly in {restore_dir}, not in a subdirectory."
        )

    def test_no_index_html_extracted(self):
        """Verify index.html was not extracted anywhere in /home/user/restore/."""
        restore_dir = "/home/user/restore"

        result = subprocess.run(
            ["find", restore_dir, "-name", "index.html"],
            capture_output=True,
            text=True
        )

        found_files = [f for f in result.stdout.strip().split("\n") if f]
        assert len(found_files) == 0, (
            f"Found index.html in restore directory: {found_files}. "
            "Only the database dump should be extracted."
        )

    def test_no_style_css_extracted(self):
        """Verify style.css was not extracted anywhere in /home/user/restore/."""
        restore_dir = "/home/user/restore"

        result = subprocess.run(
            ["find", restore_dir, "-name", "style.css"],
            capture_output=True,
            text=True
        )

        found_files = [f for f in result.stdout.strip().split("\n") if f]
        assert len(found_files) == 0, (
            f"Found style.css in restore directory: {found_files}. "
            "Only the database dump should be extracted."
        )

    def test_no_access_log_extracted(self):
        """Verify access.log was not extracted anywhere in /home/user/restore/."""
        restore_dir = "/home/user/restore"

        result = subprocess.run(
            ["find", restore_dir, "-name", "access.log"],
            capture_output=True,
            text=True
        )

        found_files = [f for f in result.stdout.strip().split("\n") if f]
        assert len(found_files) == 0, (
            f"Found access.log in restore directory: {found_files}. "
            "Only the database dump should be extracted."
        )

    def test_original_tarball_unchanged(self):
        """Verify the original tarball still exists and is valid."""
        tarball_path = "/home/user/backups/site-2024-03-15.tar.gz"

        assert os.path.isfile(tarball_path), (
            f"Original tarball {tarball_path} no longer exists. "
            "The archive should remain unchanged."
        )

        # Verify it's still a valid tar.gz with expected contents
        try:
            with tarfile.open(tarball_path, "r:gz") as tf:
                members = set(tf.getnames())
                expected_files = {
                    "var/www/html/index.html",
                    "var/www/html/style.css",
                    "var/db/dump.sql",
                    "var/log/access.log",
                }

                for expected in expected_files:
                    assert expected in members, (
                        f"Original tarball is missing '{expected}'. "
                        "The archive should remain unchanged."
                    )
        except tarfile.TarError as e:
            pytest.fail(
                f"Original tarball {tarball_path} is corrupted: {e}"
            )

    def test_dump_sql_is_readable(self):
        """Verify the extracted dump.sql is readable."""
        dump_path = "/home/user/restore/dump.sql"

        assert os.access(dump_path, os.R_OK), (
            f"File {dump_path} is not readable. "
            "The extracted database dump should be readable."
        )

    def test_dump_sql_has_content(self):
        """Verify dump.sql is not empty."""
        dump_path = "/home/user/restore/dump.sql"

        file_size = os.path.getsize(dump_path)
        assert file_size > 0, (
            f"File {dump_path} is empty. "
            "The extracted database dump should contain data."
        )
