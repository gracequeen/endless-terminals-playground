# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the backup script fix task.
"""

import os
import stat
import subprocess
import pytest


HOME = "/home/user"
INFRA_DIR = os.path.join(HOME, "infra")
SCRIPT_PATH = os.path.join(INFRA_DIR, "setup_backup.sh")
APPDATA_DIR = os.path.join(HOME, "appdata")
BACKUPS_DIR = os.path.join(HOME, "backups")
GNUPG_DIR = os.path.join(HOME, ".gnupg")


class TestScriptExists:
    """Tests for the backup script existence and properties."""

    def test_infra_directory_exists(self):
        """Verify /home/user/infra/ directory exists."""
        assert os.path.isdir(INFRA_DIR), f"Directory {INFRA_DIR} does not exist"

    def test_script_exists(self):
        """Verify /home/user/infra/setup_backup.sh exists."""
        assert os.path.isfile(SCRIPT_PATH), f"Script {SCRIPT_PATH} does not exist"

    def test_script_is_executable(self):
        """Verify the script is executable."""
        assert os.access(SCRIPT_PATH, os.X_OK), f"Script {SCRIPT_PATH} is not executable"

    def test_script_has_correct_shebang(self):
        """Verify the script starts with bash shebang."""
        with open(SCRIPT_PATH, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash", f"Script should have #!/bin/bash shebang, got: {first_line}"

    def test_script_contains_gpg_symmetric_encryption(self):
        """Verify the script uses gpg symmetric encryption."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert "gpg" in content, "Script should contain gpg command"
        assert "--symmetric" in content, "Script should use --symmetric flag for gpg"
        assert "AES256" in content, "Script should use AES256 cipher"

    def test_script_contains_passphrase(self):
        """Verify the script uses the expected passphrase."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert "backupkey2024" in content, "Script should contain passphrase 'backupkey2024'"

    def test_script_missing_batch_flag(self):
        """Verify the script is missing --batch flag (the bug)."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        # The bug is that --batch is missing
        assert "--batch" not in content, "Script should NOT have --batch flag initially (this is the bug to fix)"


class TestAppdataDirectory:
    """Tests for the appdata directory and its contents."""

    def test_appdata_directory_exists(self):
        """Verify /home/user/appdata/ directory exists."""
        assert os.path.isdir(APPDATA_DIR), f"Directory {APPDATA_DIR} does not exist"

    def test_appdata_has_content(self):
        """Verify appdata directory is not empty."""
        contents = os.listdir(APPDATA_DIR)
        assert len(contents) > 0, f"Directory {APPDATA_DIR} should not be empty"

    def test_appdata_has_subdirectories(self):
        """Verify appdata has subdirectories (several subdirectories expected)."""
        subdirs = [d for d in os.listdir(APPDATA_DIR) 
                   if os.path.isdir(os.path.join(APPDATA_DIR, d))]
        assert len(subdirs) > 0, f"Directory {APPDATA_DIR} should contain subdirectories"

    def test_appdata_size_approximately_15mb(self):
        """Verify appdata directory contains approximately 15MB of data."""
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
            f"Appdata should be ~15MB, got {total_size / (1024*1024):.2f}MB"


class TestBackupsDirectory:
    """Tests for the backups directory and corrupt files."""

    def test_backups_directory_exists(self):
        """Verify /home/user/backups/ directory exists."""
        assert os.path.isdir(BACKUPS_DIR), f"Directory {BACKUPS_DIR} does not exist"

    def test_backups_directory_is_writable(self):
        """Verify backups directory is writable."""
        assert os.access(BACKUPS_DIR, os.W_OK), f"Directory {BACKUPS_DIR} is not writable"

    def test_corrupt_backup_files_exist(self):
        """Verify there are corrupt .tar.gz.gpg files from previous cron attempts."""
        gpg_files = [f for f in os.listdir(BACKUPS_DIR) if f.endswith('.tar.gz.gpg')]
        assert len(gpg_files) >= 2, \
            f"Expected 2-3 corrupt .tar.gz.gpg files in {BACKUPS_DIR}, found {len(gpg_files)}"

    def test_corrupt_files_are_small(self):
        """Verify the existing backup files are suspiciously small (corrupt)."""
        gpg_files = [f for f in os.listdir(BACKUPS_DIR) if f.endswith('.tar.gz.gpg')]
        for gpg_file in gpg_files:
            filepath = os.path.join(BACKUPS_DIR, gpg_file)
            size = os.path.getsize(filepath)
            # Corrupt files should be very small (~200 bytes), not the expected ~15MB
            assert size < 10000, \
                f"File {gpg_file} is {size} bytes, expected small corrupt file (<10KB)"


class TestCrontab:
    """Tests for crontab configuration."""

    def test_crontab_entry_exists(self):
        """Verify user's crontab has the backup script entry."""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            env={"HOME": HOME, "USER": "user"}
        )
        # crontab -l returns 0 if there are entries
        assert result.returncode == 0, "User should have a crontab configured"
        assert "setup_backup.sh" in result.stdout, \
            "Crontab should contain entry for setup_backup.sh"
        assert "/home/user/infra/setup_backup.sh" in result.stdout, \
            "Crontab should reference the full path to setup_backup.sh"


class TestGPGInstallation:
    """Tests for GPG installation and configuration."""

    def test_gpg_installed(self):
        """Verify GPG is installed."""
        result = subprocess.run(["which", "gpg"], capture_output=True, text=True)
        assert result.returncode == 0, "GPG should be installed"

    def test_gpg_version_2x(self):
        """Verify GPG version is 2.x."""
        result = subprocess.run(["gpg", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "gpg --version should succeed"
        # Check for version 2.x
        assert "gpg (GnuPG) 2." in result.stdout, \
            f"Expected GPG 2.x, got: {result.stdout.split(chr(10))[0]}"

    def test_gnupg_directory_exists(self):
        """Verify ~/.gnupg directory exists and is initialized."""
        assert os.path.isdir(GNUPG_DIR), f"Directory {GNUPG_DIR} does not exist"


class TestInfraDirectoryWritable:
    """Tests for infra directory permissions."""

    def test_infra_directory_is_writable(self):
        """Verify /home/user/infra/ is writable."""
        assert os.access(INFRA_DIR, os.W_OK), f"Directory {INFRA_DIR} is not writable"


class TestRequiredTools:
    """Tests for required command-line tools."""

    def test_tar_installed(self):
        """Verify tar is installed."""
        result = subprocess.run(["which", "tar"], capture_output=True, text=True)
        assert result.returncode == 0, "tar should be installed"

    def test_bash_installed(self):
        """Verify bash is installed."""
        result = subprocess.run(["which", "bash"], capture_output=True, text=True)
        assert result.returncode == 0, "bash should be installed"

    def test_date_command_available(self):
        """Verify date command is available."""
        result = subprocess.run(["which", "date"], capture_output=True, text=True)
        assert result.returncode == 0, "date command should be available"
