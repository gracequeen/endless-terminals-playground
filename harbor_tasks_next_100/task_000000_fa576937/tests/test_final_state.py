# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the tarball extraction task (extracting only etc/ files).
"""

import os
import tarfile
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the extraction task."""

    TARBALL_PATH = "/home/user/backups/site-2024-03-15.tar.gz"
    RESTORE_PATH = "/home/user/restore"

    EXPECTED_FILES = [
        "/home/user/restore/etc/apache2/apache2.conf",
        "/home/user/restore/etc/apache2/sites-available/000-default.conf",
        "/home/user/restore/etc/php/8.1/apache2/php.ini",
    ]

    def test_tarball_still_exists(self):
        """Verify the original tarball still exists (unchanged)."""
        assert os.path.isfile(self.TARBALL_PATH), \
            f"Tarball {self.TARBALL_PATH} should still exist after extraction"

    def test_tarball_still_valid(self):
        """Verify the tarball is still a valid gzipped tar archive."""
        try:
            with tarfile.open(self.TARBALL_PATH, "r:gz") as tf:
                members = tf.getnames()
                assert len(members) > 0, "Tarball should not be empty"
        except tarfile.TarError as e:
            pytest.fail(f"Tarball {self.TARBALL_PATH} is corrupted: {e}")

    def test_apache2_conf_exists(self):
        """Verify /home/user/restore/etc/apache2/apache2.conf exists."""
        path = "/home/user/restore/etc/apache2/apache2.conf"
        assert os.path.isfile(path), \
            f"Config file {path} was not extracted. Did you extract etc/ from the archive?"

    def test_sites_available_conf_exists(self):
        """Verify /home/user/restore/etc/apache2/sites-available/000-default.conf exists."""
        path = "/home/user/restore/etc/apache2/sites-available/000-default.conf"
        assert os.path.isfile(path), \
            f"Config file {path} was not extracted. Did you extract etc/ from the archive?"

    def test_php_ini_exists(self):
        """Verify /home/user/restore/etc/php/8.1/apache2/php.ini exists."""
        path = "/home/user/restore/etc/php/8.1/apache2/php.ini"
        assert os.path.isfile(path), \
            f"Config file {path} was not extracted. Did you extract etc/ from the archive?"

    def test_apache2_conf_content_matches_archive(self):
        """Verify apache2.conf content matches the archive."""
        extracted_path = "/home/user/restore/etc/apache2/apache2.conf"
        archive_member = "etc/apache2/apache2.conf"

        with tarfile.open(self.TARBALL_PATH, "r:gz") as tf:
            archive_content = tf.extractfile(archive_member).read()

        with open(extracted_path, "rb") as f:
            extracted_content = f.read()

        assert extracted_content == archive_content, \
            f"Content of {extracted_path} does not match the archive"

    def test_sites_available_conf_content_matches_archive(self):
        """Verify 000-default.conf content matches the archive."""
        extracted_path = "/home/user/restore/etc/apache2/sites-available/000-default.conf"
        archive_member = "etc/apache2/sites-available/000-default.conf"

        with tarfile.open(self.TARBALL_PATH, "r:gz") as tf:
            archive_content = tf.extractfile(archive_member).read()

        with open(extracted_path, "rb") as f:
            extracted_content = f.read()

        assert extracted_content == archive_content, \
            f"Content of {extracted_path} does not match the archive"

    def test_php_ini_content_matches_archive(self):
        """Verify php.ini content matches the archive."""
        extracted_path = "/home/user/restore/etc/php/8.1/apache2/php.ini"
        archive_member = "etc/php/8.1/apache2/php.ini"

        with tarfile.open(self.TARBALL_PATH, "r:gz") as tf:
            archive_content = tf.extractfile(archive_member).read()

        with open(extracted_path, "rb") as f:
            extracted_content = f.read()

        assert extracted_content == archive_content, \
            f"Content of {extracted_path} does not match the archive"

    def test_var_directory_not_extracted(self):
        """Verify /home/user/restore/var/ does NOT exist (no var/ extraction)."""
        path = "/home/user/restore/var"
        assert not os.path.exists(path), \
            f"Directory {path} should NOT exist. Only etc/ should be extracted, not var/"

    def test_exactly_three_files_extracted(self):
        """Verify exactly 3 files were extracted (the config files only)."""
        result = subprocess.run(
            ["find", self.RESTORE_PATH, "-type", "f"],
            capture_output=True,
            text=True
        )
        files = [f for f in result.stdout.strip().split("\n") if f]
        assert len(files) == 3, \
            f"Expected exactly 3 files extracted, but found {len(files)}: {files}"

    def test_no_log_files_extracted(self):
        """Verify no log files from var/log were extracted."""
        # Check that no access.log or error.log exist anywhere in restore
        for root, dirs, files in os.walk(self.RESTORE_PATH):
            for filename in files:
                assert "access.log" not in filename, \
                    f"Log file {filename} should not be extracted"
                assert "error.log" not in filename, \
                    f"Log file {filename} should not be extracted"

    def test_no_uploads_extracted(self):
        """Verify no uploads from var/www/html/uploads were extracted."""
        uploads_path = os.path.join(self.RESTORE_PATH, "var", "www", "html", "uploads")
        assert not os.path.exists(uploads_path), \
            f"Uploads directory {uploads_path} should not exist"

    def test_no_index_php_extracted(self):
        """Verify index.php from var/www/html was not extracted."""
        index_path = os.path.join(self.RESTORE_PATH, "var", "www", "html", "index.php")
        assert not os.path.exists(index_path), \
            f"File {index_path} should not exist - only etc/ should be extracted"

    def test_etc_directory_structure_exists(self):
        """Verify the etc/ directory structure was created properly."""
        expected_dirs = [
            "/home/user/restore/etc",
            "/home/user/restore/etc/apache2",
            "/home/user/restore/etc/apache2/sites-available",
            "/home/user/restore/etc/php",
            "/home/user/restore/etc/php/8.1",
            "/home/user/restore/etc/php/8.1/apache2",
        ]
        for dir_path in expected_dirs:
            assert os.path.isdir(dir_path), \
                f"Directory {dir_path} should exist as part of the extracted structure"

    def test_anti_shortcut_file_count(self):
        """Anti-shortcut: verify find command returns exactly 3 files."""
        result = subprocess.run(
            ["find", "/home/user/restore", "-type", "f"],
            capture_output=True,
            text=True
        )
        file_count = len([f for f in result.stdout.strip().split("\n") if f])
        assert file_count == 3, \
            f"Anti-shortcut check failed: expected 3 files, found {file_count}"

    def test_anti_shortcut_no_var_directory(self):
        """Anti-shortcut: verify var directory test prints OK."""
        result = subprocess.run(
            ["sh", "-c", "test -d /home/user/restore/var && echo FAIL || echo OK"],
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        assert output == "OK", \
            f"Anti-shortcut check failed: expected 'OK' but got '{output}'. " \
            f"The var/ directory should NOT be extracted."
