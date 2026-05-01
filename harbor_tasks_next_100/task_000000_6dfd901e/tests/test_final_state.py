# test_final_state.py
"""
Tests to validate the final state of the filesystem after the student
has completed the gzip recovery task.
"""

import os
import subprocess
import gzip
import zlib
import hashlib
import pytest

BACKUP_DIR = "/home/user/backup"
TABLES_DIR = "/home/user/backup/tables"
LOG_FILE = "/home/user/backup/backup.log"


class TestDirectoryStructurePreserved:
    """Test that the directory structure is preserved."""

    def test_backup_directory_exists(self):
        """The /home/user/backup directory must still exist."""
        assert os.path.isdir(BACKUP_DIR), f"Directory {BACKUP_DIR} does not exist"

    def test_tables_directory_exists(self):
        """The /home/user/backup/tables directory must still exist."""
        assert os.path.isdir(TABLES_DIR), f"Directory {TABLES_DIR} does not exist"

    def test_backup_log_still_exists(self):
        """The backup log file must still exist."""
        assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist"


class TestAllFilesPresent:
    """Test that all 47 files are still present."""

    def test_exactly_47_gz_files(self):
        """There must still be exactly 47 .sql.gz files in the tables directory."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        assert len(files) == 47, f"Expected 47 .sql.gz files, found {len(files)}. No files should be deleted."

    def test_all_files_have_nonzero_size(self):
        """All .sql.gz files must have non-zero size."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            size = os.path.getsize(filepath)
            assert size > 0, f"File {filepath} has zero size - files should not be emptied"


class TestAllFilesValidGzip:
    """Test that all 47 files are now valid gzip archives."""

    def test_all_files_pass_gunzip_test(self):
        """All 47 files must pass gunzip -t."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        failed_files = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            result = subprocess.run(
                ['gunzip', '-t', filepath],
                capture_output=True
            )
            if result.returncode != 0:
                failed_files.append(f)

        assert len(failed_files) == 0, \
            f"The following files still fail gunzip -t (corrupted): {failed_files}"

    def test_no_fail_lines_from_validation_loop(self):
        """The validation loop from the task must produce no FAIL lines."""
        # Run the exact command from the task description
        cmd = 'for f in /home/user/backup/tables/*.sql.gz; do gunzip -t "$f" || echo "FAIL: $f"; done'
        result = subprocess.run(
            ['bash', '-c', cmd],
            capture_output=True,
            text=True
        )

        assert 'FAIL:' not in result.stdout, \
            f"Validation loop produced FAIL lines:\n{result.stdout}"

    def test_all_files_start_with_gzip_magic(self):
        """All files must start with gzip magic bytes (1f 8b)."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            with open(filepath, 'rb') as fh:
                magic = fh.read(2)
            assert magic == b'\x1f\x8b', \
                f"File {filepath} does not start with gzip magic bytes - not a valid gzip file"


class TestDecompressedContentValid:
    """Test that all files decompress to valid SQL dump content."""

    def test_all_files_contain_postgresql_dump_header(self):
        """All decompressed files must contain PostgreSQL dump header."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        files_without_header = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            try:
                with gzip.open(filepath, 'rt', errors='replace') as fh:
                    content = fh.read()
                if '-- PostgreSQL dump' not in content and 'PostgreSQL' not in content:
                    files_without_header.append(f)
            except Exception as e:
                files_without_header.append(f"{f} (error: {e})")

        assert len(files_without_header) == 0, \
            f"Files missing PostgreSQL dump header: {files_without_header}"

    def test_all_files_contain_dump_complete_footer(self):
        """All decompressed files must contain dump complete footer or similar ending."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        files_without_footer = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            try:
                with gzip.open(filepath, 'rt', errors='replace') as fh:
                    content = fh.read()
                # Check for various valid dump endings
                has_valid_footer = (
                    'Dump complete' in content or
                    'dump complete' in content.lower() or
                    '-- Dump completed' in content or
                    'PostgreSQL database dump complete' in content
                )
                if not has_valid_footer:
                    files_without_footer.append(f)
            except Exception as e:
                files_without_footer.append(f"{f} (error: {e})")

        assert len(files_without_footer) == 0, \
            f"Files missing dump complete footer (may be truncated): {files_without_footer}"

    def test_grep_dump_complete_succeeds_for_all(self):
        """grep for 'Dump complete' via zcat must succeed for all 47 files."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        files_missing_marker = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            # Use zcat and grep to check for dump complete marker
            result = subprocess.run(
                f'zcat "{filepath}" | grep -i "dump complete"',
                shell=True,
                capture_output=True
            )
            if result.returncode != 0:
                files_missing_marker.append(f)

        assert len(files_missing_marker) == 0, \
            f"Files where 'Dump complete' not found via zcat|grep: {files_missing_marker}"


class TestValidSQLContent:
    """Test that decompressed content is valid SQL."""

    def test_all_files_contain_sql_statements(self):
        """All files must contain recognizable SQL statements."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        files_without_sql = []

        sql_keywords = ['CREATE', 'INSERT', 'SELECT', 'TABLE', 'COPY', 'SET', 'ALTER']

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            try:
                with gzip.open(filepath, 'rt', errors='replace') as fh:
                    content = fh.read().upper()
                has_sql = any(kw in content for kw in sql_keywords)
                if not has_sql:
                    files_without_sql.append(f)
            except Exception as e:
                files_without_sql.append(f"{f} (error: {e})")

        assert len(files_without_sql) == 0, \
            f"Files without recognizable SQL content: {files_without_sql}"

    def test_no_truncated_sql_content(self):
        """Decompressed SQL should not appear truncated mid-statement."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        potentially_truncated = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            try:
                with gzip.open(filepath, 'rt', errors='replace') as fh:
                    content = fh.read()
                # Check that content doesn't end abruptly mid-line without newline
                # and contains the dump footer
                lines = content.strip().split('\n')
                if lines:
                    last_line = lines[-1].strip()
                    # Valid endings: comment, semicolon, or empty
                    valid_ending = (
                        last_line.startswith('--') or
                        last_line.endswith(';') or
                        last_line == '' or
                        'dump complete' in last_line.lower()
                    )
                    if not valid_ending and len(last_line) > 0:
                        # Check if dump complete marker exists anywhere
                        if 'dump complete' not in content.lower():
                            potentially_truncated.append(f)
            except Exception as e:
                potentially_truncated.append(f"{f} (error: {e})")

        # This is a soft check - some valid dumps might have unusual endings
        if len(potentially_truncated) > 5:
            pytest.fail(f"Many files appear truncated: {potentially_truncated}")


class TestNoMultipleGzipStreams:
    """Test that repaired files don't have multiple gzip streams."""

    def test_files_have_single_gzip_stream(self):
        """Repaired files should have only one gzip stream, not concatenated streams."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        files_with_multiple_streams = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            with open(filepath, 'rb') as fh:
                data = fh.read()

            # Count gzip magic bytes occurrences
            # A properly repaired file should have magic bytes only at the start
            magic = b'\x1f\x8b'
            count = 0
            pos = 0
            while True:
                idx = data.find(magic, pos)
                if idx == -1:
                    break
                count += 1
                pos = idx + 1

            # More than 1 occurrence might indicate concatenated streams
            # However, magic bytes could appear in compressed data by chance
            # So we do a more thorough check: try to decompress and see if there's leftover
            if count > 1:
                try:
                    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
                    decompressed = decompressor.decompress(data)
                    unused = decompressor.unused_data
                    # If there's significant unused data starting with gzip magic, it's multiple streams
                    if len(unused) > 10 and unused[:2] == magic:
                        files_with_multiple_streams.append(f)
                except Exception:
                    pass

        assert len(files_with_multiple_streams) == 0, \
            f"Files still have multiple gzip streams (not properly repaired): {files_with_multiple_streams}"


class TestFileIntegrity:
    """Test overall file integrity."""

    def test_python_gzip_module_can_read_all_files(self):
        """Python's gzip module must be able to read all files completely."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        unreadable_files = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            try:
                with gzip.open(filepath, 'rb') as fh:
                    content = fh.read()
                if len(content) == 0:
                    unreadable_files.append(f"{f} (empty content)")
            except Exception as e:
                unreadable_files.append(f"{f} (error: {e})")

        assert len(unreadable_files) == 0, \
            f"Files that Python gzip module cannot read: {unreadable_files}"

    def test_zcat_can_decompress_all_files(self):
        """zcat must be able to decompress all files without error."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        failed_files = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            result = subprocess.run(
                ['zcat', filepath],
                capture_output=True
            )
            if result.returncode != 0:
                failed_files.append(f)

        assert len(failed_files) == 0, \
            f"Files that zcat cannot decompress: {failed_files}"


class TestNoDataLoss:
    """Test that valid data was preserved, not lost."""

    def test_all_files_have_substantial_content(self):
        """All decompressed files should have substantial SQL content."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        too_small_files = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            try:
                with gzip.open(filepath, 'rb') as fh:
                    content = fh.read()
                # A valid PostgreSQL dump should have at least a few hundred bytes
                if len(content) < 100:
                    too_small_files.append(f"{f} ({len(content)} bytes)")
            except Exception as e:
                too_small_files.append(f"{f} (error: {e})")

        assert len(too_small_files) == 0, \
            f"Files with suspiciously small decompressed content: {too_small_files}"

    def test_table_names_in_content(self):
        """Each file's decompressed content should reference a table name."""
        files = [f for f in os.listdir(TABLES_DIR) if f.endswith('.sql.gz')]
        files_without_table_ref = []

        for f in files:
            filepath = os.path.join(TABLES_DIR, f)
            # Extract expected table name from filename
            table_name = f.replace('.sql.gz', '')

            try:
                with gzip.open(filepath, 'rt', errors='replace') as fh:
                    content = fh.read()
                # Table name should appear somewhere in the dump
                if table_name not in content and table_name.lower() not in content.lower():
                    files_without_table_ref.append(f)
            except Exception as e:
                files_without_table_ref.append(f"{f} (error: {e})")

        # Allow some flexibility - table names might be quoted or modified
        if len(files_without_table_ref) > 10:
            pytest.fail(f"Many files don't reference their table name: {files_without_table_ref}")
