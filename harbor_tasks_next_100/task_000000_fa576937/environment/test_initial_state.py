# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the tarball extraction task.
"""

import os
import tarfile
import subprocess
import pytest


class TestInitialState:
    """Validate the initial state before the extraction task."""

    def test_backups_directory_exists(self):
        """Verify /home/user/backups/ directory exists."""
        path = "/home/user/backups"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_tarball_exists(self):
        """Verify the tarball /home/user/backups/site-2024-03-15.tar.gz exists."""
        path = "/home/user/backups/site-2024-03-15.tar.gz"
        assert os.path.isfile(path), f"Tarball {path} does not exist"

    def test_tarball_is_valid_gzip(self):
        """Verify the tarball is a valid gzipped tar archive."""
        path = "/home/user/backups/site-2024-03-15.tar.gz"
        try:
            with tarfile.open(path, "r:gz") as tf:
                # Just try to get the members list to verify it's valid
                members = tf.getnames()
                assert len(members) > 0, "Tarball appears to be empty"
        except tarfile.TarError as e:
            pytest.fail(f"Tarball {path} is not a valid tar.gz file: {e}")

    def test_tarball_contains_expected_etc_files(self):
        """Verify the tarball contains the expected etc/ config files."""
        path = "/home/user/backups/site-2024-03-15.tar.gz"
        expected_etc_files = [
            "etc/apache2/apache2.conf",
            "etc/apache2/sites-available/000-default.conf",
            "etc/php/8.1/apache2/php.ini",
        ]

        with tarfile.open(path, "r:gz") as tf:
            members = tf.getnames()
            for expected_file in expected_etc_files:
                assert expected_file in members, \
                    f"Expected file '{expected_file}' not found in tarball"

    def test_tarball_contains_var_structure(self):
        """Verify the tarball contains var/ structure (which should NOT be extracted)."""
        path = "/home/user/backups/site-2024-03-15.tar.gz"

        with tarfile.open(path, "r:gz") as tf:
            members = tf.getnames()
            # Check that var/ content exists in archive
            var_files = [m for m in members if m.startswith("var/")]
            assert len(var_files) > 0, \
                "Tarball should contain var/ directory structure"

            # Verify specific var paths exist
            has_www = any("var/www" in m for m in members)
            has_log = any("var/log" in m for m in members)
            assert has_www, "Tarball should contain var/www/ content"
            assert has_log, "Tarball should contain var/log/ content"

    def test_restore_directory_exists(self):
        """Verify /home/user/restore/ directory exists."""
        path = "/home/user/restore"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_restore_directory_is_empty(self):
        """Verify /home/user/restore/ directory is empty."""
        path = "/home/user/restore"
        contents = os.listdir(path)
        assert len(contents) == 0, \
            f"Directory {path} should be empty but contains: {contents}"

    def test_backups_directory_is_writable(self):
        """Verify /home/user/backups/ is writable."""
        path = "/home/user/backups"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_restore_directory_is_writable(self):
        """Verify /home/user/restore/ is writable."""
        path = "/home/user/restore"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"

    def test_tar_command_available(self):
        """Verify tar command is available."""
        result = subprocess.run(
            ["which", "tar"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "tar command is not available"

    def test_gzip_command_available(self):
        """Verify gzip command is available."""
        result = subprocess.run(
            ["which", "gzip"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gzip command is not available"

    def test_restore_var_does_not_exist(self):
        """Verify /home/user/restore/var/ does not exist initially."""
        path = "/home/user/restore/var"
        assert not os.path.exists(path), \
            f"Directory {path} should not exist in initial state"

    def test_restore_etc_does_not_exist(self):
        """Verify /home/user/restore/etc/ does not exist initially."""
        path = "/home/user/restore/etc"
        assert not os.path.exists(path), \
            f"Directory {path} should not exist in initial state"
