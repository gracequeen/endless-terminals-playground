# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has fixed the backup script to work correctly in a cron (TTY-less) environment.
"""

import os
import subprocess
import tempfile
import pytest
import glob
import time


HOME = "/home/user"
INFRA_DIR = os.path.join(HOME, "infra")
SCRIPT_PATH = os.path.join(INFRA_DIR, "setup_backup.sh")
APPDATA_DIR = os.path.join(HOME, "appdata")
BACKUPS_DIR = os.path.join(HOME, "backups")
PASSPHRASE = "backupkey2024"


class TestScriptStillValid:
    """Tests to ensure the script still meets requirements after fix."""

    def test_script_exists(self):
        """Verify the script still exists."""
        assert os.path.isfile(SCRIPT_PATH), f"Script {SCRIPT_PATH} does not exist"

    def test_script_is_executable(self):
        """Verify the script is still executable."""
        assert os.access(SCRIPT_PATH, os.X_OK), f"Script {SCRIPT_PATH} is not executable"

    def test_script_uses_symmetric_encryption(self):
        """Verify the script still uses gpg symmetric encryption."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert "--symmetric" in content, "Script must still use --symmetric flag for gpg"

    def test_script_uses_aes256(self):
        """Verify the script still uses AES256 cipher."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert "AES256" in content, "Script must still use AES256 cipher"

    def test_script_uses_correct_passphrase(self):
        """Verify the script still uses the passphrase 'backupkey2024'."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert "backupkey2024" in content, "Script must still use passphrase 'backupkey2024'"


class TestAppdataUnchanged:
    """Tests to ensure appdata directory is unchanged."""

    def test_appdata_directory_exists(self):
        """Verify /home/user/appdata/ still exists."""
        assert os.path.isdir(APPDATA_DIR), f"Directory {APPDATA_DIR} must still exist"

    def test_appdata_has_content(self):
        """Verify appdata directory still has content."""
        contents = os.listdir(APPDATA_DIR)
        assert len(contents) > 0, f"Directory {APPDATA_DIR} should not be empty"

    def test_appdata_size_reasonable(self):
        """Verify appdata directory still contains approximately 15MB of data."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(APPDATA_DIR):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)

        # Allow some tolerance: 10MB to 25MB
        min_size = 10 * 1024 * 1024  # 10MB
        max_size = 25 * 1024 * 1024  # 25MB
        assert min_size <= total_size <= max_size, \
            f"Appdata should still be ~15MB, got {total_size / (1024*1024):.2f}MB"


class TestCrontabPreserved:
    """Tests to ensure crontab entry is preserved."""

    def test_crontab_entry_exists(self):
        """Verify user's crontab still has the backup script entry."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            env={"HOME": HOME, "USER": "user"}
        )
        assert result.returncode == 0, "User should still have a crontab configured"
        assert "/home/user/infra/setup_backup.sh" in result.stdout, \
            "Crontab should still reference /home/user/infra/setup_backup.sh"


class TestScriptRunsInCronEnvironment:
    """Tests to verify the script works in a TTY-less cron simulation."""

    def test_script_exits_zero_in_cron_env(self):
        """Verify running the script in cron-like environment exits 0."""
        result = subprocess.run(
            ["env", "-i", f"PATH=/usr/bin:/bin", f"HOME={HOME}", SCRIPT_PATH],
            capture_output=True,
            text=True,
            cwd=HOME
        )
        assert result.returncode == 0, \
            f"Script should exit 0 in cron environment, got {result.returncode}. stderr: {result.stderr}"

    def test_new_backup_file_created(self):
        """Verify a new .tar.gz.gpg file is created after running the script."""
        # Get list of existing files before
        existing_files = set(glob.glob(os.path.join(BACKUPS_DIR, "*.tar.gz.gpg")))

        # Run the script in cron environment
        result = subprocess.run(
            ["env", "-i", f"PATH=/usr/bin:/bin", f"HOME={HOME}", SCRIPT_PATH],
            capture_output=True,
            text=True,
            cwd=HOME
        )

        # Get list of files after
        all_files = set(glob.glob(os.path.join(BACKUPS_DIR, "*.tar.gz.gpg")))
        new_files = all_files - existing_files

        assert len(new_files) >= 1, \
            f"Expected at least one new .tar.gz.gpg file to be created in {BACKUPS_DIR}"


class TestBackupFileValid:
    """Tests to verify the created backup file is valid and can be decrypted."""

    @pytest.fixture
    def run_backup_and_get_newest_file(self):
        """Run the backup script and return the path to the newest backup file."""
        # Record time before running
        before_time = time.time()

        # Run the script in cron environment
        result = subprocess.run(
            ["env", "-i", f"PATH=/usr/bin:/bin", f"HOME={HOME}", SCRIPT_PATH],
            capture_output=True,
            text=True,
            cwd=HOME
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Find the newest .tar.gz.gpg file
        gpg_files = glob.glob(os.path.join(BACKUPS_DIR, "*.tar.gz.gpg"))
        assert len(gpg_files) > 0, "No .tar.gz.gpg files found in backups directory"

        # Get the newest file (by modification time)
        newest_file = max(gpg_files, key=os.path.getmtime)
        return newest_file

    def test_backup_file_has_reasonable_size(self, run_backup_and_get_newest_file):
        """Verify the backup file is not suspiciously small (corrupt)."""
        newest_file = run_backup_and_get_newest_file
        size = os.path.getsize(newest_file)

        # A valid encrypted ~15MB archive should be at least 1MB
        # (compression + encryption overhead varies, but definitely not 200 bytes)
        min_expected_size = 1 * 1024 * 1024  # 1MB minimum
        assert size >= min_expected_size, \
            f"Backup file {newest_file} is only {size} bytes, expected at least 1MB for valid encrypted archive"

    def test_backup_file_can_be_decrypted(self, run_backup_and_get_newest_file):
        """Verify the backup file can be decrypted with the correct passphrase."""
        newest_file = run_backup_and_get_newest_file

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Decrypt the file
            result = subprocess.run(
                [
                    "gpg", "--batch", "--yes",
                    "--passphrase", PASSPHRASE,
                    "--decrypt",
                    "--output", tmp_path,
                    newest_file
                ],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, \
                f"GPG decryption failed with passphrase '{PASSPHRASE}': {result.stderr}"

            # Verify the decrypted file exists and has content
            assert os.path.exists(tmp_path), "Decrypted file was not created"
            assert os.path.getsize(tmp_path) > 0, "Decrypted file is empty"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_decrypted_archive_is_valid_tarball(self, run_backup_and_get_newest_file):
        """Verify the decrypted archive is a valid tar.gz file."""
        newest_file = run_backup_and_get_newest_file

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Decrypt the file
            decrypt_result = subprocess.run(
                [
                    "gpg", "--batch", "--yes",
                    "--passphrase", PASSPHRASE,
                    "--decrypt",
                    "--output", tmp_path,
                    newest_file
                ],
                capture_output=True,
                text=True
            )
            assert decrypt_result.returncode == 0, f"Decryption failed: {decrypt_result.stderr}"

            # Test the tarball
            tar_result = subprocess.run(
                ["tar", "-tzf", tmp_path],
                capture_output=True,
                text=True
            )
            assert tar_result.returncode == 0, \
                f"tar -tzf failed on decrypted archive: {tar_result.stderr}"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_archive_contains_appdata_files(self, run_backup_and_get_newest_file):
        """Verify the archive contains files from the appdata directory."""
        newest_file = run_backup_and_get_newest_file

        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Decrypt the file
            decrypt_result = subprocess.run(
                [
                    "gpg", "--batch", "--yes",
                    "--passphrase", PASSPHRASE,
                    "--decrypt",
                    "--output", tmp_path,
                    newest_file
                ],
                capture_output=True,
                text=True
            )
            assert decrypt_result.returncode == 0, f"Decryption failed: {decrypt_result.stderr}"

            # List the tarball contents
            tar_result = subprocess.run(
                ["tar", "-tzf", tmp_path],
                capture_output=True,
                text=True
            )
            assert tar_result.returncode == 0, f"tar -tzf failed: {tar_result.stderr}"

            tar_contents = tar_result.stdout

            # Check that appdata is in the archive
            assert "appdata" in tar_contents, \
                f"Archive should contain 'appdata' directory. Contents: {tar_contents[:500]}"

            # Check that there are multiple entries (not just the directory)
            lines = [l for l in tar_contents.strip().split('\n') if l]
            assert len(lines) > 1, \
                f"Archive should contain multiple files/directories, found only {len(lines)} entries"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_archive_can_be_fully_extracted(self, run_backup_and_get_newest_file):
        """Verify the archive can be fully extracted and contains expected content."""
        newest_file = run_backup_and_get_newest_file

        with tempfile.TemporaryDirectory() as tmpdir:
            tar_path = os.path.join(tmpdir, "backup.tar.gz")
            extract_dir = os.path.join(tmpdir, "extracted")
            os.makedirs(extract_dir)

            # Decrypt the file
            decrypt_result = subprocess.run(
                [
                    "gpg", "--batch", "--yes",
                    "--passphrase", PASSPHRASE,
                    "--decrypt",
                    "--output", tar_path,
                    newest_file
                ],
                capture_output=True,
                text=True
            )
            assert decrypt_result.returncode == 0, f"Decryption failed: {decrypt_result.stderr}"

            # Extract the tarball
            extract_result = subprocess.run(
                ["tar", "-xzf", tar_path, "-C", extract_dir],
                capture_output=True,
                text=True
            )
            assert extract_result.returncode == 0, \
                f"tar extraction failed: {extract_result.stderr}"

            # Verify appdata directory was extracted
            extracted_appdata = os.path.join(extract_dir, "appdata")
            assert os.path.isdir(extracted_appdata), \
                f"Expected 'appdata' directory in extracted archive at {extracted_appdata}"

            # Verify extracted content has reasonable size (should match original appdata)
            extracted_size = 0
            for dirpath, dirnames, filenames in os.walk(extracted_appdata):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.isfile(filepath):
                        extracted_size += os.path.getsize(filepath)

            # Should be at least 10MB (original is ~15MB)
            min_expected = 10 * 1024 * 1024
            assert extracted_size >= min_expected, \
                f"Extracted appdata is only {extracted_size / (1024*1024):.2f}MB, expected ~15MB"
