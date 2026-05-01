# test_final_state.py
"""
Tests to validate the final state after the student has extracted the nginx.conf
from the tarball to /home/user/restored/.
"""

import os
import subprocess
import tarfile
import pytest


class TestFinalState:
    """Validate the OS/filesystem state after the student completes the task."""

    def test_nginx_config_extracted(self):
        """Verify nginx.conf was extracted to one of the acceptable locations."""
        # Two acceptable locations depending on extraction method
        path_with_dirs = "/home/user/restored/etc/nginx/nginx.conf"
        path_stripped = "/home/user/restored/nginx.conf"

        exists_with_dirs = os.path.isfile(path_with_dirs)
        exists_stripped = os.path.isfile(path_stripped)

        assert exists_with_dirs or exists_stripped, (
            f"nginx.conf was not extracted. Expected either:\n"
            f"  - {path_with_dirs} (with preserved path)\n"
            f"  - {path_stripped} (with --strip-components)\n"
            f"Neither file exists."
        )

    def _get_extracted_nginx_path(self):
        """Helper to find which path the nginx.conf was extracted to."""
        path_with_dirs = "/home/user/restored/etc/nginx/nginx.conf"
        path_stripped = "/home/user/restored/nginx.conf"

        if os.path.isfile(path_with_dirs):
            return path_with_dirs
        elif os.path.isfile(path_stripped):
            return path_stripped
        return None

    def test_extracted_file_contains_worker_processes(self):
        """Verify the extracted file contains 'worker_processes' directive."""
        nginx_path = self._get_extracted_nginx_path()
        assert nginx_path is not None, "nginx.conf was not extracted to any expected location"

        with open(nginx_path, 'r') as f:
            content = f.read()

        assert "worker_processes" in content, (
            f"Extracted file at {nginx_path} does not contain 'worker_processes'. "
            f"This suggests the wrong file was extracted or it's a stub."
        )

    def test_extracted_file_contains_legacy_internal(self):
        """Verify the extracted file contains 'legacy.internal' server name."""
        nginx_path = self._get_extracted_nginx_path()
        assert nginx_path is not None, "nginx.conf was not extracted to any expected location"

        with open(nginx_path, 'r') as f:
            content = f.read()

        assert "legacy.internal" in content, (
            f"Extracted file at {nginx_path} does not contain 'legacy.internal'. "
            f"This suggests the wrong file was extracted or it's a stub."
        )

    def test_extracted_file_matches_archive_content(self):
        """Verify the extracted file content matches the original in the archive."""
        nginx_path = self._get_extracted_nginx_path()
        assert nginx_path is not None, "nginx.conf was not extracted to any expected location"

        # Read extracted file
        with open(nginx_path, 'r') as f:
            extracted_content = f.read()

        # Read original from archive
        tarball_path = "/home/user/backups/services-2024.tar.gz"
        with tarfile.open(tarball_path, "r:gz") as tf:
            member = tf.getmember("etc/nginx/nginx.conf")
            f = tf.extractfile(member)
            original_content = f.read().decode('utf-8')

        assert extracted_content == original_content, (
            f"Extracted file content does not match the original from the archive.\n"
            f"Expected content length: {len(original_content)}\n"
            f"Actual content length: {len(extracted_content)}"
        )

    def test_only_one_file_extracted(self):
        """Verify only one file was extracted (not the entire archive)."""
        restored_dir = "/home/user/restored"

        # Use find to count all regular files under restored directory
        result = subprocess.run(
            ["find", restored_dir, "-type", "f"],
            capture_output=True,
            text=True
        )

        files = [f for f in result.stdout.strip().split('\n') if f]
        file_count = len(files)

        assert file_count == 1, (
            f"Expected exactly 1 file to be extracted, but found {file_count} files:\n"
            f"{files}\n"
            f"The task requires extracting only etc/nginx/nginx.conf, not the entire archive."
        )

    def test_tarball_unchanged(self):
        """Verify the original tarball still exists and is valid."""
        tarball_path = "/home/user/backups/services-2024.tar.gz"

        assert os.path.isfile(tarball_path), (
            f"Original tarball {tarball_path} no longer exists or was modified"
        )

        # Verify it's still a valid gzipped tar
        try:
            with tarfile.open(tarball_path, "r:gz") as tf:
                members = tf.getnames()
                assert "etc/nginx/nginx.conf" in members, (
                    "Original tarball appears to have been modified - "
                    "etc/nginx/nginx.conf is no longer present"
                )
        except tarfile.TarError as e:
            pytest.fail(f"Original tarball is no longer a valid archive: {e}")

    def test_no_other_archive_contents_extracted(self):
        """Verify no other files from the archive were extracted."""
        restored_dir = "/home/user/restored"

        # Check that var/log, etc/systemd, usr/local/bin directories don't exist
        # (unless they're part of the nginx.conf path, which they're not)
        unwanted_paths = [
            os.path.join(restored_dir, "var"),
            os.path.join(restored_dir, "usr"),
            os.path.join(restored_dir, "etc/systemd"),
        ]

        for unwanted in unwanted_paths:
            assert not os.path.exists(unwanted), (
                f"Unwanted directory {unwanted} exists. "
                f"Only the nginx.conf file should have been extracted."
            )

    def test_extracted_file_is_regular_file(self):
        """Verify the extracted nginx.conf is a regular file (not symlink, etc.)."""
        nginx_path = self._get_extracted_nginx_path()
        assert nginx_path is not None, "nginx.conf was not extracted to any expected location"

        assert os.path.isfile(nginx_path), f"{nginx_path} is not a regular file"
        assert not os.path.islink(nginx_path), f"{nginx_path} is a symlink, expected regular file"

    def test_extracted_file_readable(self):
        """Verify the extracted file is readable."""
        nginx_path = self._get_extracted_nginx_path()
        assert nginx_path is not None, "nginx.conf was not extracted to any expected location"

        assert os.access(nginx_path, os.R_OK), f"Extracted file {nginx_path} is not readable"

    def test_extracted_file_has_content(self):
        """Verify the extracted file is not empty."""
        nginx_path = self._get_extracted_nginx_path()
        assert nginx_path is not None, "nginx.conf was not extracted to any expected location"

        file_size = os.path.getsize(nginx_path)
        assert file_size > 0, f"Extracted file {nginx_path} is empty (0 bytes)"

        # The config should be at least a few hundred bytes
        assert file_size > 100, (
            f"Extracted file {nginx_path} is suspiciously small ({file_size} bytes). "
            f"Expected a complete nginx configuration."
        )
