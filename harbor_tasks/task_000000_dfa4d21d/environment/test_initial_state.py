# test_initial_state.py
"""
Tests to validate the initial state before the student performs the tar extraction task.
"""

import os
import tarfile
import subprocess
import pytest


class TestInitialState:
    """Validate the OS/filesystem state before the student action."""

    def test_backups_directory_exists(self):
        """Verify /home/user/backups/ directory exists."""
        backups_dir = "/home/user/backups"
        assert os.path.isdir(backups_dir), f"Directory {backups_dir} does not exist"

    def test_backups_directory_readable(self):
        """Verify /home/user/backups/ is readable."""
        backups_dir = "/home/user/backups"
        assert os.access(backups_dir, os.R_OK), f"Directory {backups_dir} is not readable"

    def test_tarball_exists(self):
        """Verify /home/user/backups/services-2024.tar.gz exists."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"
        assert os.path.isfile(tarball_path), f"Tarball {tarball_path} does not exist"

    def test_tarball_is_valid_gzipped_tar(self):
        """Verify the tarball is a valid gzipped tar archive."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"
        try:
            with tarfile.open(tarball_path, "r:gz") as tf:
                # Just try to get the list of members to verify it's valid
                members = tf.getnames()
                assert len(members) > 0, "Tarball is empty"
        except tarfile.TarError as e:
            pytest.fail(f"Tarball {tarball_path} is not a valid gzipped tar archive: {e}")
        except Exception as e:
            pytest.fail(f"Failed to open tarball {tarball_path}: {e}")

    def test_tarball_contains_nginx_config(self):
        """Verify the tarball contains etc/nginx/nginx.conf."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"
        target_file = "etc/nginx/nginx.conf"

        with tarfile.open(tarball_path, "r:gz") as tf:
            members = tf.getnames()
            assert target_file in members, (
                f"Tarball does not contain {target_file}. "
                f"Available members: {members}"
            )

    def test_tarball_contains_multiple_directories(self):
        """Verify the tarball contains multiple directories (var/log/, etc/systemd/, usr/local/bin/)."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"
        expected_dirs = ["var/log", "etc/systemd", "usr/local/bin"]

        with tarfile.open(tarball_path, "r:gz") as tf:
            members = tf.getnames()

            for expected_dir in expected_dirs:
                # Check if any member starts with this directory path
                found = any(m.startswith(expected_dir) for m in members)
                assert found, (
                    f"Tarball does not contain directory {expected_dir}. "
                    f"Available members: {members}"
                )

    def test_tarball_has_approximately_50_files(self):
        """Verify the tarball contains approximately 50 files (at least multiple files)."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"

        with tarfile.open(tarball_path, "r:gz") as tf:
            members = tf.getmembers()
            # Count actual files (not directories)
            file_count = sum(1 for m in members if m.isfile())
            assert file_count >= 10, (
                f"Tarball should contain many files (~50), but only has {file_count} files"
            )

    def test_nginx_config_content_in_tarball(self):
        """Verify etc/nginx/nginx.conf in tarball contains expected content."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"
        target_file = "etc/nginx/nginx.conf"

        with tarfile.open(tarball_path, "r:gz") as tf:
            member = tf.getmember(target_file)
            f = tf.extractfile(member)
            assert f is not None, f"Could not extract {target_file} from tarball"

            content = f.read().decode('utf-8')

            # Verify key content elements
            assert "worker_processes" in content, (
                f"nginx.conf in tarball does not contain 'worker_processes'"
            )
            assert "legacy.internal" in content, (
                f"nginx.conf in tarball does not contain 'legacy.internal'"
            )
            assert "worker_connections 1024" in content, (
                f"nginx.conf in tarball does not contain 'worker_connections 1024'"
            )

    def test_restored_directory_exists(self):
        """Verify /home/user/restored/ directory exists."""
        restored_dir = "/home/user/restored"
        assert os.path.isdir(restored_dir), f"Directory {restored_dir} does not exist"

    def test_restored_directory_is_empty(self):
        """Verify /home/user/restored/ directory is empty."""
        restored_dir = "/home/user/restored"
        contents = os.listdir(restored_dir)
        assert len(contents) == 0, (
            f"Directory {restored_dir} should be empty but contains: {contents}"
        )

    def test_restored_directory_writable(self):
        """Verify /home/user/restored/ is writable."""
        restored_dir = "/home/user/restored"
        assert os.access(restored_dir, os.W_OK), f"Directory {restored_dir} is not writable"

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
