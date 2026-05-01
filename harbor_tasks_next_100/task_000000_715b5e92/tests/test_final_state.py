# test_final_state.py
"""
Tests to validate the final state of the system after the student has fixed the backup verification issue.
The fix should involve setting appropriate trust on GPG key 0x22222222.
"""

import os
import subprocess
import time
import pytest


class TestScriptSucceeds:
    """Test that the check.sh script now succeeds."""

    def test_script_exits_zero(self):
        """The check.sh script should now exit with status 0."""
        result = subprocess.run(
            ['/home/user/backup-verify/check.sh'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'},
            cwd='/home/user/backup-verify'
        )
        assert result.returncode == 0, \
            f"Script should exit 0 after fix, but exited {result.returncode}. " \
            f"stdout: {result.stdout}, stderr: {result.stderr}"

    def test_script_does_not_output_verification_failed(self):
        """The script should no longer output 'verification failed'."""
        result = subprocess.run(
            ['/home/user/backup-verify/check.sh'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'},
            cwd='/home/user/backup-verify'
        )
        combined_output = (result.stdout + result.stderr).lower()
        # Only check if the script succeeded - if it failed, the other test will catch it
        if result.returncode == 0:
            assert 'verification failed' not in combined_output, \
                f"Script should not output 'verification failed' when succeeding"


class TestSentinelFile:
    """Test that the sentinel file is properly touched by the script."""

    def test_sentinel_file_exists(self):
        """The sentinel file should exist after running the script."""
        # Run the script first to ensure sentinel is touched
        subprocess.run(
            ['/home/user/backup-verify/check.sh'],
            capture_output=True,
            env={**os.environ, 'HOME': '/home/user'},
            cwd='/home/user/backup-verify'
        )

        sentinel_path = "/home/user/backup-verify/.last-verified"
        assert os.path.exists(sentinel_path), \
            f"Sentinel file {sentinel_path} should exist after successful script run"

    def test_sentinel_file_is_recent(self):
        """The sentinel file should have been touched recently (within 60 seconds)."""
        sentinel_path = "/home/user/backup-verify/.last-verified"

        # Record time before running script
        time_before = time.time()

        # Run the script
        result = subprocess.run(
            ['/home/user/backup-verify/check.sh'],
            capture_output=True,
            env={**os.environ, 'HOME': '/home/user'},
            cwd='/home/user/backup-verify'
        )

        time_after = time.time()

        assert result.returncode == 0, \
            f"Script must succeed for sentinel to be touched. Exit code: {result.returncode}"

        assert os.path.exists(sentinel_path), \
            f"Sentinel file {sentinel_path} should exist"

        mtime = os.path.getmtime(sentinel_path)

        # Sentinel mtime should be between time_before and time_after (with small tolerance)
        assert mtime >= time_before - 1, \
            f"Sentinel file mtime ({mtime}) should be >= script start time ({time_before})"
        assert mtime <= time_after + 1, \
            f"Sentinel file mtime ({mtime}) should be <= script end time ({time_after})"


class TestKeyTrustFixed:
    """Test that the GPG key trust has been properly configured."""

    def test_new_signing_key_is_trusted(self):
        """The new signing key 0x22222222 should now have sufficient trust."""
        result = subprocess.run(
            ['gpg', '--export-ownertrust'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        output = result.stdout.upper()

        # Look for the key in ownertrust output
        # Trust levels: 2=unknown, 3=untrusted, 4=marginal, 5=full, 6=ultimate
        # The key should have trust level 4, 5, or 6 (marginal, full, or ultimate)
        lines_with_new_key = [line for line in output.split('\n') if '22222222' in line]

        assert lines_with_new_key, \
            "Key 0x22222222 should be in ownertrust output with sufficient trust level"

        found_sufficient_trust = False
        for line in lines_with_new_key:
            # Format is: KEYFINGERPRINT:TRUSTLEVEL:
            parts = line.split(':')
            if len(parts) >= 2:
                trust_level = parts[1]
                if trust_level in ['4', '5', '6']:
                    found_sufficient_trust = True
                    break

        assert found_sufficient_trust, \
            f"Key 0x22222222 should have trust level 4, 5, or 6 (marginal/full/ultimate). " \
            f"Found lines: {lines_with_new_key}"

    def test_gpg_verify_shows_trusted(self):
        """GPG verify should not show TRUST_UNDEFINED for the new backup signature."""
        result = subprocess.run(
            ['gpg', '--verify', '--status-fd', '1',
             '/var/backups/encrypted/backup-2024-01-20.tar.sig',
             '/var/backups/encrypted/backup-2024-01-20.tar.gpg'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )

        combined_output = result.stdout + result.stderr

        assert 'GOODSIG' in combined_output, \
            f"GPG verify should show GOODSIG. Output: {combined_output}"

        assert 'TRUST_UNDEFINED' not in combined_output, \
            f"GPG verify should NOT show TRUST_UNDEFINED after fix. Output: {combined_output}"

        assert 'TRUST_NEVER' not in combined_output, \
            f"GPG verify should NOT show TRUST_NEVER. Output: {combined_output}"


class TestScriptUnmodified:
    """Test that the script itself was not modified (the fix should be in GPG config)."""

    def test_script_still_checks_trust(self):
        """The script should still contain the TRUST_UNDEFINED check (not bypassed)."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            content = f.read()

        assert 'TRUST_UNDEFINED' in content, \
            "Script should still contain TRUST_UNDEFINED check - " \
            "the fix should be in GPG trust settings, not modifying the script"

    def test_script_still_checks_goodsig(self):
        """The script should still contain the GOODSIG check."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            content = f.read()

        assert 'GOODSIG' in content, \
            "Script should still contain GOODSIG check"

    def test_script_still_uses_status_fd(self):
        """The script should still use --status-fd."""
        path = "/home/user/backup-verify/check.sh"
        with open(path, 'r') as f:
            content = f.read()

        assert 'status-fd' in content or 'status_fd' in content, \
            "Script should still use --status-fd"


class TestBackupFilesUnchanged:
    """Test that the backup files were not modified."""

    def test_backup_files_exist(self):
        """All backup files should still exist."""
        files = [
            "/var/backups/encrypted/backup-2024-01-15.tar.gpg",
            "/var/backups/encrypted/backup-2024-01-15.tar.sig",
            "/var/backups/encrypted/backup-2024-01-20.tar.gpg",
            "/var/backups/encrypted/backup-2024-01-20.tar.sig",
        ]
        for f in files:
            assert os.path.isfile(f), f"Backup file {f} should still exist"


class TestBothSigningKeysExist:
    """Test that both signing keys are still in the keyring."""

    def test_old_signing_key_still_exists(self):
        """The old signing key should still be in the keyring."""
        result = subprocess.run(
            ['gpg', '--list-keys', '--keyid-format', 'long'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        output = (result.stdout + result.stderr).upper()
        assert '11111111' in output or 'OLD SIGNING KEY' in output.upper(), \
            "Old signing key 0x11111111 should still be in GPG keyring"

    def test_new_signing_key_still_exists(self):
        """The new signing key should still be in the keyring."""
        result = subprocess.run(
            ['gpg', '--list-keys', '--keyid-format', 'long'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        output = (result.stdout + result.stderr).upper()
        assert '22222222' in output or 'NEW SIGNING KEY' in output.upper(), \
            "New signing key 0x22222222 should still be in GPG keyring"


class TestDecryptionStillWorks:
    """Test that decryption still works after the fix."""

    def test_can_still_decrypt_new_backup(self):
        """Should still be able to decrypt the new backup file."""
        result = subprocess.run(
            ['gpg', '--decrypt', '--output', '/dev/null',
             '/var/backups/encrypted/backup-2024-01-20.tar.gpg'],
            capture_output=True,
            text=True,
            env={**os.environ, 'HOME': '/home/user'}
        )
        assert result.returncode == 0, \
            f"Should still be able to decrypt new backup: {result.stderr}"
