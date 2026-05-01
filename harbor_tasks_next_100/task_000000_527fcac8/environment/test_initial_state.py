# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the backup key rotation task.
"""

import os
import subprocess
import pytest


HOME = "/home/user"
BACKUPS_DIR = os.path.join(HOME, "backups")
ENCRYPTED_FILE = os.path.join(BACKUPS_DIR, "db-2024-01-15.tar.gz.gpg")
NEW_ENCRYPTED_FILE = os.path.join(BACKUPS_DIR, "db-2024-01-15.tar.gz.gpg.new")
OLD_KEY_FILE = os.path.join(HOME, ".old_backup_key")
NEW_KEY_FILE = os.path.join(HOME, ".new_backup_key")


class TestDirectoriesExist:
    """Test that required directories exist and are accessible."""

    def test_home_directory_exists(self):
        """Home directory must exist."""
        assert os.path.isdir(HOME), f"Home directory {HOME} does not exist"

    def test_backups_directory_exists(self):
        """Backups directory must exist."""
        assert os.path.isdir(BACKUPS_DIR), f"Backups directory {BACKUPS_DIR} does not exist"

    def test_backups_directory_is_writable(self):
        """Backups directory must be writable."""
        assert os.access(BACKUPS_DIR, os.W_OK), f"Backups directory {BACKUPS_DIR} is not writable"


class TestRequiredFilesExist:
    """Test that required input files exist."""

    def test_encrypted_backup_exists(self):
        """The encrypted backup file must exist."""
        assert os.path.isfile(ENCRYPTED_FILE), (
            f"Encrypted backup file {ENCRYPTED_FILE} does not exist"
        )

    def test_old_key_file_exists(self):
        """The old backup key file must exist."""
        assert os.path.isfile(OLD_KEY_FILE), (
            f"Old backup key file {OLD_KEY_FILE} does not exist"
        )

    def test_new_key_file_exists(self):
        """The new backup key file must exist."""
        assert os.path.isfile(NEW_KEY_FILE), (
            f"New backup key file {NEW_KEY_FILE} does not exist"
        )


class TestKeyFileContents:
    """Test that key files contain the expected passphrases."""

    def test_old_key_content(self):
        """Old key file must contain the expected passphrase."""
        with open(OLD_KEY_FILE, 'r') as f:
            content = f.read()
        assert content == "hunter2-old-key", (
            f"Old key file content mismatch. Expected 'hunter2-old-key', "
            f"got '{content}'"
        )

    def test_new_key_content(self):
        """New key file must contain the expected passphrase."""
        with open(NEW_KEY_FILE, 'r') as f:
            content = f.read()
        assert content == "correcthorse-new-key", (
            f"New key file content mismatch. Expected 'correcthorse-new-key', "
            f"got '{content}'"
        )


class TestGPGAvailability:
    """Test that GPG is installed and available."""

    def test_gpg_is_installed(self):
        """GPG must be installed and accessible."""
        result = subprocess.run(
            ["which", "gpg"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "gpg is not installed or not in PATH"

    def test_gpg_version_2x(self):
        """GPG must be version 2.x."""
        result = subprocess.run(
            ["gpg", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get gpg version"
        # Check that version line contains "2."
        version_line = result.stdout.split('\n')[0]
        assert "2." in version_line, (
            f"GPG version 2.x required, but got: {version_line}"
        )


class TestEncryptedFileValidity:
    """Test that the encrypted backup is a valid GPG file."""

    def test_file_is_gpg_encrypted(self):
        """The backup file must be a valid GPG encrypted file."""
        # Use file command to check if it's GPG data
        result = subprocess.run(
            ["file", ENCRYPTED_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to check file type of {ENCRYPTED_FILE}"
        output = result.stdout.lower()
        assert "gpg" in output or "pgp" in output or "encrypted" in output, (
            f"File {ENCRYPTED_FILE} does not appear to be GPG encrypted. "
            f"File type: {result.stdout.strip()}"
        )

    def test_can_decrypt_with_old_key(self):
        """The encrypted file must be decryptable with the old key."""
        result = subprocess.run(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", OLD_KEY_FILE,
                "--decrypt", ENCRYPTED_FILE
            ],
            capture_output=True
        )
        assert result.returncode == 0, (
            f"Failed to decrypt {ENCRYPTED_FILE} with old key. "
            f"GPG error: {result.stderr.decode('utf-8', errors='replace')}"
        )

    def test_decrypted_content_is_valid_tarball(self):
        """Decrypted content must be a valid gzipped tarball."""
        # Decrypt and pipe to tar to list contents
        decrypt_proc = subprocess.Popen(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", OLD_KEY_FILE,
                "--decrypt", ENCRYPTED_FILE
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        tar_proc = subprocess.Popen(
            ["tar", "-tzf", "-"],
            stdin=decrypt_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        decrypt_proc.stdout.close()
        tar_output, tar_err = tar_proc.communicate()
        decrypt_proc.wait()

        assert tar_proc.returncode == 0, (
            f"Decrypted content is not a valid gzipped tarball. "
            f"tar error: {tar_err.decode('utf-8', errors='replace')}"
        )

    def test_tarball_contains_dump_sql(self):
        """The tarball must contain dump.sql."""
        decrypt_proc = subprocess.Popen(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", OLD_KEY_FILE,
                "--decrypt", ENCRYPTED_FILE
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        tar_proc = subprocess.Popen(
            ["tar", "-tzf", "-"],
            stdin=decrypt_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        decrypt_proc.stdout.close()
        tar_output, _ = tar_proc.communicate()
        decrypt_proc.wait()

        files_in_tarball = tar_output.decode('utf-8').strip().split('\n')
        assert "dump.sql" in files_in_tarball, (
            f"Tarball does not contain dump.sql. Contents: {files_in_tarball}"
        )


class TestOutputFileDoesNotExist:
    """Test that the output file does not exist initially."""

    def test_new_encrypted_file_does_not_exist(self):
        """The .new output file must not exist initially."""
        assert not os.path.exists(NEW_ENCRYPTED_FILE), (
            f"Output file {NEW_ENCRYPTED_FILE} already exists. "
            "It should not exist before the task is performed."
        )


class TestRequiredTools:
    """Test that required tools are available."""

    def test_tar_is_available(self):
        """tar must be available."""
        result = subprocess.run(
            ["which", "tar"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "tar is not installed or not in PATH"
