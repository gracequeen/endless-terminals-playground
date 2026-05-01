# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the action.
This verifies the backup verification scenario is properly set up.
"""

import os
import subprocess
import pytest


class TestBackupVerifyDirectory:
    """Test that the backup-verify directory and script exist."""

    def test_backup_verify_directory_exists(self):
        """The backup-verify directory should exist."""
        path = "/home/user/backup-verify"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_check_script_exists(self):
        """The check.sh script should exist."""
        path = "/home/user/backup-verify/check.sh"
        assert os.path.isfile(path), f"Script {path} does not exist"

    def test_check_script_is_executable(self):
        """The check.sh script should be executable."""
        path = "/home/user/backup-verify/check.sh"
        assert os.access(path, os.X_OK), f"Script {path} is not executable"

    def test_check_script_is_bash(self):
        """The check.sh script should be a bash script."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            first_line = f.readline()
        assert 'bash' in first_line or 'sh' in first_line, \
            f"Script {path} does not appear to be a shell script (first line: {first_line})"


class TestEncryptedBackupsDirectory:
    """Test that the encrypted backups directory and files exist."""

    def test_encrypted_backups_directory_exists(self):
        """The encrypted backups directory should exist."""
        path = "/var/backups/encrypted"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_old_backup_gpg_exists(self):
        """The older backup file should exist."""
        path = "/var/backups/encrypted/backup-2024-01-15.tar.gpg"
        assert os.path.isfile(path), f"Backup file {path} does not exist"

    def test_old_backup_sig_exists(self):
        """The older backup signature file should exist."""
        path = "/var/backups/encrypted/backup-2024-01-15.tar.sig"
        assert os.path.isfile(path), f"Signature file {path} does not exist"

    def test_new_backup_gpg_exists(self):
        """The newer backup file (the problem file) should exist."""
        path = "/var/backups/encrypted/backup-2024-01-20.tar.gpg"
        assert os.path.isfile(path), f"Backup file {path} does not exist"

    def test_new_backup_sig_exists(self):
        """The newer backup signature file should exist."""
        path = "/var/backups/encrypted/backup-2024-01-20.tar.sig"
        assert os.path.isfile(path), f"Signature file {path} does not exist"

    def test_new_backup_is_newest(self):
        """The 2024-01-20 backup should be newer than 2024-01-15."""
        old_path = "/var/backups/encrypted/backup-2024-01-15.tar.gpg"
        new_path = "/var/backups/encrypted/backup-2024-01-20.tar.gpg"
        old_mtime = os.path.getmtime(old_path)
        new_mtime = os.path.getmtime(new_path)
        assert new_mtime >= old_mtime, \
            f"backup-2024-01-20.tar.gpg should be newer than backup-2024-01-15.tar.gpg"


class TestGPGSetup:
    """Test that GPG is properly configured with the required keys."""

    def test_gnupg_directory_exists(self):
        """The .gnupg directory should exist."""
        path = "/home/user/.gnupg"
        assert os.path.isdir(path), f"GPG directory {path} does not exist"

    def test_gpg_command_available(self):
        """The gpg command should be available."""
        result = subprocess.run(['which', 'gpg'], capture_output=True)
        assert result.returncode == 0, "gpg command is not available"

    def test_decryption_key_exists(self):
        """The decryption private key should exist in the keyring."""
        result = subprocess.run(
            ['gpg', '--list-secret-keys', '--keyid-format', 'long'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        assert result.returncode == 0, "Failed to list GPG secret keys"
        # Check for the decryption key (ABCD1234)
        output = result.stdout + result.stderr
        assert 'ABCD1234' in output or 'Backup System' in output, \
            "Decryption key 0xABCD1234 not found in GPG secret keyring"

    def test_old_signing_key_exists(self):
        """The old signing public key should exist in the keyring."""
        result = subprocess.run(
            ['gpg', '--list-keys', '--keyid-format', 'long'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        assert result.returncode == 0, "Failed to list GPG public keys"
        output = result.stdout + result.stderr
        assert '11111111' in output or 'Old Signing Key' in output, \
            "Old signing key 0x11111111 not found in GPG keyring"

    def test_new_signing_key_exists(self):
        """The new signing public key should exist in the keyring."""
        result = subprocess.run(
            ['gpg', '--list-keys', '--keyid-format', 'long'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        assert result.returncode == 0, "Failed to list GPG public keys"
        output = result.stdout + result.stderr
        assert '22222222' in output or 'New Signing Key' in output, \
            "New signing key 0x22222222 not found in GPG keyring"

    def test_new_signing_key_not_trusted(self):
        """The new signing key should NOT be trusted (this is the bug)."""
        # Check ownertrust for key 22222222
        result = subprocess.run(
            ['gpg', '--export-ownertrust'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        output = result.stdout

        # Look for the key in ownertrust output
        # Trust levels: 2=unknown, 3=untrusted, 4=marginal, 5=full, 6=ultimate
        # The key should have trust level 2 (unknown) or not be in the output
        lines_with_new_key = [line for line in output.split('\n') if '22222222' in line.upper()]

        if lines_with_new_key:
            # If the key is in ownertrust, it should have low trust (2 or 3)
            for line in lines_with_new_key:
                # Format is: KEYID:TRUSTLEVEL:
                parts = line.split(':')
                if len(parts) >= 2:
                    trust_level = parts[1]
                    assert trust_level in ['2', '3', ''], \
                        f"New signing key 0x22222222 should not be trusted yet, but has trust level {trust_level}"
        # If not in ownertrust output, that's fine - it means unknown trust


class TestScriptBehavior:
    """Test that the script currently fails as expected."""

    def test_script_currently_fails(self):
        """The check.sh script should currently exit with non-zero status."""
        result = subprocess.run(
            ['/home/user/backup-verify/check.sh'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'},
            cwd='/home/user/backup-verify'
        )
        assert result.returncode != 0, \
            "Script should currently fail (exit non-zero) due to trust issue"

    def test_script_outputs_verification_failed(self):
        """The script should output 'verification failed' message."""
        result = subprocess.run(
            ['/home/user/backup-verify/check.sh'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'},
            cwd='/home/user/backup-verify'
        )
        combined_output = result.stdout + result.stderr
        assert 'verification failed' in combined_output.lower(), \
            f"Script should output 'verification failed', got: {combined_output}"


class TestDecryptionWorks:
    """Test that decryption itself works (the issue is trust, not decryption)."""

    def test_can_decrypt_old_backup(self):
        """Should be able to decrypt the old backup file."""
        result = subprocess.run(
            ['gpg', '--decrypt', '--output', '/dev/null', 
             '/var/backups/encrypted/backup-2024-01-15.tar.gpg'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        assert result.returncode == 0, \
            f"Failed to decrypt old backup: {result.stderr}"

    def test_can_decrypt_new_backup(self):
        """Should be able to decrypt the new backup file (decryption is not the issue)."""
        result = subprocess.run(
            ['gpg', '--decrypt', '--output', '/dev/null',
             '/var/backups/encrypted/backup-2024-01-20.tar.gpg'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        assert result.returncode == 0, \
            f"Failed to decrypt new backup: {result.stderr}"


class TestScriptContainsTrustCheck:
    """Verify the script contains the trust check logic."""

    def test_script_checks_for_trust_undefined(self):
        """The script should contain the TRUST_UNDEFINED check."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'TRUST_UNDEFINED' in content, \
            "Script should contain TRUST_UNDEFINED check (this is what causes the failure)"

    def test_script_checks_for_goodsig(self):
        """The script should contain the GOODSIG check."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'GOODSIG' in content, \
            "Script should contain GOODSIG check"

    def test_script_uses_status_fd(self):
        """The script should use --status-fd for GPG verification."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert 'status-fd' in content or 'status_fd' in content, \
            "Script should use --status-fd for GPG verification"
