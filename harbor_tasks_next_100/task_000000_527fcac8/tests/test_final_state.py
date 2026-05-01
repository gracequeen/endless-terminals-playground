# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the backup key rotation task.
"""

import os
import subprocess
import hashlib
import pytest


HOME = "/home/user"
BACKUPS_DIR = os.path.join(HOME, "backups")
ENCRYPTED_FILE = os.path.join(BACKUPS_DIR, "db-2024-01-15.tar.gz.gpg")
NEW_ENCRYPTED_FILE = os.path.join(BACKUPS_DIR, "db-2024-01-15.tar.gz.gpg.new")
OLD_KEY_FILE = os.path.join(HOME, ".old_backup_key")
NEW_KEY_FILE = os.path.join(HOME, ".new_backup_key")


class TestNewEncryptedFileExists:
    """Test that the new encrypted file exists."""

    def test_new_encrypted_file_exists(self):
        """The .new output file must exist after task completion."""
        assert os.path.isfile(NEW_ENCRYPTED_FILE), (
            f"Output file {NEW_ENCRYPTED_FILE} does not exist. "
            "The task requires creating this file."
        )

    def test_new_encrypted_file_not_empty(self):
        """The .new output file must not be empty."""
        assert os.path.getsize(NEW_ENCRYPTED_FILE) > 0, (
            f"Output file {NEW_ENCRYPTED_FILE} is empty."
        )


class TestNewFileIsGPGEncrypted:
    """Test that the new file is properly GPG encrypted."""

    def test_new_file_is_gpg_data(self):
        """The new file must be GPG encrypted data."""
        result = subprocess.run(
            ["file", NEW_ENCRYPTED_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to check file type of {NEW_ENCRYPTED_FILE}"
        output = result.stdout.lower()
        assert "gpg" in output or "pgp" in output or "encrypted" in output, (
            f"File {NEW_ENCRYPTED_FILE} does not appear to be GPG encrypted. "
            f"File type: {result.stdout.strip()}"
        )


class TestDecryptionWithNewKey:
    """Test that the new file can be decrypted with the new key."""

    def test_can_decrypt_with_new_key(self):
        """The new encrypted file must be decryptable with the new key."""
        result = subprocess.run(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", NEW_KEY_FILE,
                "--decrypt", NEW_ENCRYPTED_FILE
            ],
            capture_output=True
        )
        assert result.returncode == 0, (
            f"Failed to decrypt {NEW_ENCRYPTED_FILE} with new key. "
            f"GPG error: {result.stderr.decode('utf-8', errors='replace')}"
        )

    def test_decrypted_content_is_valid_tarball(self):
        """Decrypted content from new file must be a valid gzipped tarball."""
        decrypt_proc = subprocess.Popen(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", NEW_KEY_FILE,
                "--decrypt", NEW_ENCRYPTED_FILE
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
            f"Decrypted content from {NEW_ENCRYPTED_FILE} is not a valid gzipped tarball. "
            f"tar error: {tar_err.decode('utf-8', errors='replace')}"
        )

    def test_tarball_contains_dump_sql(self):
        """The tarball from new file must contain dump.sql."""
        decrypt_proc = subprocess.Popen(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", NEW_KEY_FILE,
                "--decrypt", NEW_ENCRYPTED_FILE
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
            f"Tarball from {NEW_ENCRYPTED_FILE} does not contain dump.sql. "
            f"Contents: {files_in_tarball}"
        )

    def test_verification_command_succeeds(self):
        """The verification command from the task must succeed."""
        # This is the exact verification command from the truth
        result = subprocess.run(
            f"gpg --batch --passphrase-file {NEW_KEY_FILE} --decrypt {NEW_ENCRYPTED_FILE} 2>/dev/null | tar -tzf - | grep -q dump.sql",
            shell=True
        )
        assert result.returncode == 0, (
            "Verification command failed. The new encrypted file does not "
            "properly contain the expected tarball with dump.sql."
        )


class TestAntiShortcutDecryptionWithOldKeyFails:
    """Test that the new file cannot be decrypted with the old key."""

    def test_cannot_decrypt_new_file_with_old_key(self):
        """Decrypting the new file with the old key must fail."""
        result = subprocess.run(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", OLD_KEY_FILE,
                "--decrypt", NEW_ENCRYPTED_FILE
            ],
            capture_output=True
        )
        assert result.returncode != 0, (
            f"ANTI-SHORTCUT FAILED: {NEW_ENCRYPTED_FILE} can be decrypted with the OLD key. "
            "This suggests the file was not re-encrypted with the new key, "
            "or is a copy of the original."
        )


class TestContentIntegrity:
    """Test that the content is byte-identical to original."""

    def _get_decrypted_content(self, encrypted_file, key_file):
        """Helper to decrypt a file and return its content."""
        result = subprocess.run(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", key_file,
                "--decrypt", encrypted_file
            ],
            capture_output=True
        )
        if result.returncode != 0:
            return None
        return result.stdout

    def test_content_matches_original(self):
        """The decrypted content from new file must match the original."""
        # Decrypt original with old key
        original_content = self._get_decrypted_content(ENCRYPTED_FILE, OLD_KEY_FILE)
        assert original_content is not None, (
            f"Failed to decrypt original file {ENCRYPTED_FILE}"
        )

        # Decrypt new file with new key
        new_content = self._get_decrypted_content(NEW_ENCRYPTED_FILE, NEW_KEY_FILE)
        assert new_content is not None, (
            f"Failed to decrypt new file {NEW_ENCRYPTED_FILE}"
        )

        # Compare content
        original_hash = hashlib.sha256(original_content).hexdigest()
        new_hash = hashlib.sha256(new_content).hexdigest()

        assert original_hash == new_hash, (
            f"Content mismatch! The decrypted content from {NEW_ENCRYPTED_FILE} "
            f"does not match the original plaintext. "
            f"Original SHA256: {original_hash}, New SHA256: {new_hash}"
        )


class TestOriginalFileUnchanged:
    """Test that the original encrypted file is unchanged."""

    def test_original_file_still_exists(self):
        """The original encrypted file must still exist."""
        assert os.path.isfile(ENCRYPTED_FILE), (
            f"Original file {ENCRYPTED_FILE} no longer exists! "
            "The task requires keeping the original file intact."
        )

    def test_original_file_still_decryptable_with_old_key(self):
        """The original file must still be decryptable with the old key."""
        result = subprocess.run(
            [
                "gpg", "--batch", "--yes",
                "--passphrase-file", OLD_KEY_FILE,
                "--decrypt", ENCRYPTED_FILE
            ],
            capture_output=True
        )
        assert result.returncode == 0, (
            f"Original file {ENCRYPTED_FILE} can no longer be decrypted with old key. "
            f"The original file may have been modified. "
            f"GPG error: {result.stderr.decode('utf-8', errors='replace')}"
        )


class TestKeyFilesUnchanged:
    """Test that key files are unchanged."""

    def test_old_key_file_unchanged(self):
        """Old key file must still contain the expected passphrase."""
        assert os.path.isfile(OLD_KEY_FILE), f"Old key file {OLD_KEY_FILE} is missing"
        with open(OLD_KEY_FILE, 'r') as f:
            content = f.read()
        assert content == "hunter2-old-key", (
            f"Old key file was modified. Expected 'hunter2-old-key', got '{content}'"
        )

    def test_new_key_file_unchanged(self):
        """New key file must still contain the expected passphrase."""
        assert os.path.isfile(NEW_KEY_FILE), f"New key file {NEW_KEY_FILE} is missing"
        with open(NEW_KEY_FILE, 'r') as f:
            content = f.read()
        assert content == "correcthorse-new-key", (
            f"New key file was modified. Expected 'correcthorse-new-key', got '{content}'"
        )


class TestNewFileIsNotCopyOfOriginal:
    """Additional anti-shortcut test to ensure new file is different from original."""

    def test_new_file_is_different_from_original(self):
        """The new encrypted file must be different from the original."""
        with open(ENCRYPTED_FILE, 'rb') as f:
            original_bytes = f.read()
        with open(NEW_ENCRYPTED_FILE, 'rb') as f:
            new_bytes = f.read()

        # They should be different because they use different encryption keys
        # (even if content is the same, GPG encryption produces different ciphertext)
        assert original_bytes != new_bytes, (
            f"ANTI-SHORTCUT FAILED: {NEW_ENCRYPTED_FILE} is byte-identical to the original. "
            "This suggests the file was simply copied instead of being re-encrypted."
        )
