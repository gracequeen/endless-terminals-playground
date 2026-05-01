# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student
performs the gzip recovery task.
"""

import os
import subprocess
import gzip
import zlib
import pytest

BACKUP_DIR = "/home/user/backup"
TABLES_DIR = "/home/user/backup/tables"
LOG_FILE = "/home/user/backup/backup.log"


class TestBackupDirectoryStructure:
    """Test that the backup directory structure exists."""

    def test_backup_directory_exists(self):
        """The /home/user/backup directory must exist."""
        assert os.path.isdir(BACKUP_DIR), f"Directory {BACKUP_DIR} does not exist"

    def test_tables_directory_exists(self):
        """The /home/user/backup/tables directory must exist."""
        assert os.path.isdir(TABLES_DIR), f"Directory {TABLES_DIR} does not exist"

    def test_backup_log_exists(self):
        """The backup log file must exist."""
        assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist"

    def test_backup_directory_is_writable(self):
        """The backup directory must be writable."""
        assert os.access(BACKUP_DIR, os.W_OK), f"Directory {BACKUP_DIR} is not writable"

    def test_tables_directory_is_writable(self):
        """The tables directory must be writable."""
        assert os.access(TABLES_DIR, os.W_OK), f"Directory {TABLES_DIR} is not writable"


class TestTableFiles:
    """Test that the expected table dump files exist."""

    def test_exactly_47_gz_files(self):
        """There must be exactly 47 .sql.gz files in the tables directory."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        assert len(files) == 47, f"Expected 47 .sql.gz files, found {len(files)}"

    def test_all_files_are_sql_gz(self):
        """All files in tables directory should be .sql.gz files."""
        files = os.listdir(TABLES_DIR)
        for f in files:
            assert f.endswith('.sql.gz'), f"File {f} does not have .sql.gz extension"

    def test_all_files_have_nonzero_size(self):
        """All .sql.gz files must have non-zero size."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            size = os.path.getsize(filepath)
            assert size > 0, f"File {filepath} has zero size"

    def test_files_start_with_gzip_magic(self):
        """All files must start with gzip magic bytes (1f 8b)."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            with open(filepath, 'rb') as fh:
                magic = fh.read(2)
            assert magic == b'\x1f\x8b', f"File {filepath} does not start with gzip magic bytes"


class TestCorruptionPattern:
    """Test that the expected corruption pattern exists."""

    def test_some_files_fail_gunzip_test(self):
        """Some files must fail gunzip -t (corrupted files)."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        failed_count = 0
        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            result = subprocess.run(
                ['gunzip', '-t', filepath],
                capture_output=True
            )
            if result.returncode != 0:
                failed_count += 1

        assert failed_count == 16, f"Expected 16 corrupted files, found {failed_count}"

    def test_some_files_pass_gunzip_test(self):
        """31 files must pass gunzip -t (valid files)."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        passed_count = 0
        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            result = subprocess.run(
                ['gunzip', '-t', filepath],
                capture_output=True
            )
            if result.returncode == 0:
                passed_count += 1

        assert passed_count == 31, f"Expected 31 valid files, found {passed_count}"

    def test_valid_files_contain_sql_dump(self):
        """Valid files must decompress to SQL dump content."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        valid_files_checked = 0

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            result = subprocess.run(
                ['gunzip', '-t', filepath],
                capture_output=True
            )
            if result.returncode == 0:
                # This file is valid, check its content
                with gzip.open(filepath, 'rt', errors='replace') as fh:
                    content = fh.read()
                assert '-- PostgreSQL dump' in content or 'PostgreSQL' in content, \
                    f"Valid file {filepath} does not contain PostgreSQL dump header"
                valid_files_checked += 1

        assert valid_files_checked > 0, "No valid files were checked"


class TestCorruptedFilesHaveValidFirstStream:
    """Test that corrupted files have a valid first gzip stream."""

    def test_corrupted_files_first_stream_is_valid(self):
        """Each corrupted file must have a valid first gzip stream."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        corrupted_with_valid_first_stream = 0

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            result = subprocess.run(
                ['gunzip', '-t', filepath],
                capture_output=True
            )
            if result.returncode != 0:
                # This is a corrupted file, try to decompress first stream
                with open(filepath, 'rb') as fh:
                    data = fh.read()

                # Try to decompress using zlib with wbits for gzip
                decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
                try:
                    decompressed = decompressor.decompress(data)
                    # If we get here without exception, first stream decompressed
                    # Check it contains SQL dump content
                    content = decompressed.decode('utf-8', errors='replace')
                    if '-- PostgreSQL dump' in content or 'PostgreSQL' in content:
                        corrupted_with_valid_first_stream += 1
                except Exception:
                    # First stream also corrupted - this shouldn't happen per spec
                    pass

        assert corrupted_with_valid_first_stream == 16, \
            f"Expected 16 corrupted files with valid first stream, found {corrupted_with_valid_first_stream}"


class TestBackupLog:
    """Test that the backup log has expected content."""

    def test_log_contains_dump_messages(self):
        """Log must contain DUMP: messages."""
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        assert 'DUMP:' in content, f"Log file does not contain DUMP: messages"

    def test_log_contains_progress_messages(self):
        """Log must contain PROGRESS: messages (correlating with corruption)."""
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        assert 'PROGRESS:' in content, f"Log file does not contain PROGRESS: messages"

    def test_log_contains_started_messages(self):
        """Log must contain 'started' messages."""
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        assert 'started' in content, f"Log file does not contain 'started' messages"

    def test_log_contains_complete_messages(self):
        """Log must contain 'complete' messages."""
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        assert 'complete' in content.lower(), f"Log file does not contain 'complete' messages"


class TestToolsAvailable:
    """Test that required tools are available."""

    def test_python3_available(self):
        """python3 must be available."""
        result = subprocess.run(['which', 'python3'], capture_output=True)
        assert result.returncode == 0, "python3 is not available"

    def test_gzip_available(self):
        """gzip must be available."""
        result = subprocess.run(['which', 'gzip'], capture_output=True)
        assert result.returncode == 0, "gzip is not available"

    def test_gunzip_available(self):
        """gunzip must be available."""
        result = subprocess.run(['which', 'gunzip'], capture_output=True)
        assert result.returncode == 0, "gunzip is not available"

    def test_zlib_python_available(self):
        """Python zlib module must be available."""
        result = subprocess.run(
            ['python3', '-c', 'import zlib; print(zlib.__name__)'],
            capture_output=True
        )
        assert result.returncode == 0, "Python zlib module is not available"

    def test_xxd_available(self):
        """xxd must be available."""
        result = subprocess.run(['which', 'xxd'], capture_output=True)
        assert result.returncode == 0, "xxd is not available"

    def test_hexdump_available(self):
        """hexdump must be available."""
        result = subprocess.run(['which', 'hexdump'], capture_output=True)
        assert result.returncode == 0, "hexdump is not available"

    def test_file_command_available(self):
        """file command must be available."""
        result = subprocess.run(['which', 'file'], capture_output=True)
        assert result.returncode == 0, "file command is not available"


class TestDatabaseNotAccessible:
    """Test that database access would fail (as expected)."""

    def test_psql_installed(self):
        """postgresql-client should be installed."""
        result = subprocess.run(['which', 'psql'], capture_output=True)
        assert result.returncode == 0, "psql is not installed (postgresql-client required)"
