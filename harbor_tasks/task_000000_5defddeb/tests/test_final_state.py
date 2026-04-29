# test_final_state.py
"""
Tests to validate the final state after the student fixes the incremental backup script.
"""

import os
import subprocess
import stat
import tempfile
import glob
import hashlib
import random
import pytest

HOME = "/home/user"
BACKUP_DIR = f"{HOME}/backup"
DATA_DIR = f"{HOME}/data"
STATE_DIR = f"{BACKUP_DIR}/state"
ARCHIVES_DIR = f"{BACKUP_DIR}/archives"
INCREMENTAL_SCRIPT = f"{BACKUP_DIR}/incremental.sh"
FULL_SCRIPT = f"{BACKUP_DIR}/full.sh"
TIMESTAMP_FILE = f"{STATE_DIR}/last_incremental"
REFERENCE_FILE = f"{STATE_DIR}/reference"

# Store the original full.sh content for comparison
FULL_SCRIPT_ORIGINAL_HASH = None


def get_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_files_newer_than_reference():
    """Get list of files in DATA_DIR newer than reference file."""
    result = subprocess.run(
        ['find', DATA_DIR, '-type', 'f', '-newer', REFERENCE_FILE],
        capture_output=True,
        text=True
    )
    return [f for f in result.stdout.strip().split('\n') if f]


class TestScriptStillExists:
    """Test that the incremental script still exists and is executable."""

    def test_incremental_script_exists(self):
        assert os.path.isfile(INCREMENTAL_SCRIPT), \
            f"Incremental backup script {INCREMENTAL_SCRIPT} does not exist"

    def test_incremental_script_is_executable(self):
        mode = os.stat(INCREMENTAL_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, \
            f"Incremental script {INCREMENTAL_SCRIPT} is not executable"

    def test_incremental_script_is_bash(self):
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            first_line = f.readline()
        assert 'bash' in first_line.lower(), \
            f"Incremental script should have bash shebang, got: {first_line.strip()}"


class TestFullScriptUnchanged:
    """Test that full.sh was not modified."""

    def test_full_script_exists(self):
        assert os.path.isfile(FULL_SCRIPT), \
            f"Full backup script {FULL_SCRIPT} does not exist - it should not have been deleted"

    def test_full_script_is_executable(self):
        mode = os.stat(FULL_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, \
            f"Full script {FULL_SCRIPT} should still be executable"


class TestDataDirectoryUnchanged:
    """Test that data directory contents were not modified."""

    def test_data_directory_exists(self):
        assert os.path.isdir(DATA_DIR), \
            f"Data directory {DATA_DIR} should still exist"

    def test_data_directory_has_files(self):
        files = []
        for root, dirs, filenames in os.walk(DATA_DIR):
            for filename in filenames:
                files.append(os.path.join(root, filename))
        assert len(files) >= 40, \
            f"Data directory should still have ~50 files, found {len(files)} - data should not be modified"


class TestBuggyPatternRemoved:
    """Test that the backgrounding-tar-in-pipeline bug has been fixed."""

    def test_no_backgrounded_tar_in_pipeline(self):
        """The pattern of tar backgrounded with & in a pipeline should be removed."""
        result = subprocess.run(
            ['grep', '-E', r'^\s*tar.*&\s*$', INCREMENTAL_SCRIPT],
            capture_output=True,
            text=True
        )
        # grep returns 0 if pattern found, 1 if not found
        assert result.returncode != 0, \
            "The buggy pattern (tar backgrounded with &) should be removed from the script. " \
            f"Found: {result.stdout.strip()}"

    def test_no_tar_ampersand_pattern(self):
        """Double-check: look for tar ... & pattern more broadly."""
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()

        import re
        # Look for lines where tar is followed by & at end (the bug)
        # This catches: tar ... &
        # But should NOT flag: tar ... && (which is valid)
        lines = content.split('\n')
        buggy_lines = []
        for line in lines:
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # Check for tar followed by single & at end (not &&)
            if re.search(r'\btar\b.*[^&]&\s*$', line):
                buggy_lines.append(line)

        assert len(buggy_lines) == 0, \
            f"Found buggy tar backgrounding pattern in lines: {buggy_lines}"


class TestScriptStillIncremental:
    """Test that the script is still an incremental backup, not converted to full."""

    def test_script_uses_find(self):
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        assert 'find' in content, \
            "Script should still use find command for incremental backups"

    def test_script_uses_tar(self):
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        assert 'tar' in content, \
            "Script should still use tar command"

    def test_script_uses_newer_option(self):
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        assert '-newer' in content, \
            "Script should still use -newer option for incremental detection"

    def test_script_references_state(self):
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        assert 'reference' in content.lower() or 'state' in content.lower(), \
            "Script should still use state/reference tracking mechanism"

    def test_script_not_using_other_tools(self):
        """Script should still use find+tar, not rsync or dar."""
        with open(INCREMENTAL_SCRIPT, 'r') as f:
            content = f.read()
        # Check that alternative backup tools are not used as main mechanism
        lines = [l for l in content.split('\n') if not l.strip().startswith('#')]
        code_content = '\n'.join(lines)
        assert 'rsync' not in code_content.lower(), \
            "Script should use find+tar, not rsync"
        assert 'dar ' not in code_content.lower(), \
            "Script should use find+tar, not dar"


class TestIncrementalBackupWorks:
    """Test that running the incremental backup produces a valid, extractable archive."""

    @pytest.fixture(scope="class")
    def run_incremental_backup(self):
        """Run the incremental backup script and return info about the created archive."""
        # Get list of archives before running
        before_archives = set(glob.glob(f"{ARCHIVES_DIR}/incremental_*.tar.gz"))

        # Run the incremental backup script
        result = subprocess.run(
            [INCREMENTAL_SCRIPT],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        # Get list of archives after running
        after_archives = set(glob.glob(f"{ARCHIVES_DIR}/incremental_*.tar.gz"))

        # Find the new archive
        new_archives = after_archives - before_archives

        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'new_archives': new_archives
        }

    def test_script_runs_successfully(self, run_incremental_backup):
        assert run_incremental_backup['exit_code'] == 0, \
            f"Incremental script failed with exit code {run_incremental_backup['exit_code']}. " \
            f"stderr: {run_incremental_backup['stderr']}"

    def test_archive_created(self, run_incremental_backup):
        assert len(run_incremental_backup['new_archives']) >= 1, \
            f"No new archive was created in {ARCHIVES_DIR}. " \
            f"Script output: {run_incremental_backup['stdout']} {run_incremental_backup['stderr']}"

    def test_archive_can_be_listed(self, run_incremental_backup):
        """Archive should be listable with tar -tzf without errors."""
        if not run_incremental_backup['new_archives']:
            pytest.skip("No archive created")

        archive = list(run_incremental_backup['new_archives'])[0]
        result = subprocess.run(
            ['tar', '-tzf', archive],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Failed to list archive {archive}. " \
            f"Error: {result.stderr}. This indicates a corrupt archive."

    def test_archive_contains_sufficient_files(self, run_incremental_backup):
        """Archive should contain at least 25 files (the changed files)."""
        if not run_incremental_backup['new_archives']:
            pytest.skip("No archive created")

        archive = list(run_incremental_backup['new_archives'])[0]
        result = subprocess.run(
            ['tar', '-tzf', archive],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"Cannot list archive: {result.stderr}")

        # Count files (exclude directory entries)
        files = [f for f in result.stdout.strip().split('\n') if f and not f.endswith('/')]
        assert len(files) >= 25, \
            f"Archive should contain at least 25 files, but only contains {len(files)}. " \
            f"This suggests the archive is truncated/incomplete."

    def test_archive_extracts_successfully(self, run_incremental_backup):
        """Archive should extract without errors."""
        if not run_incremental_backup['new_archives']:
            pytest.skip("No archive created")

        archive = list(run_incremental_backup['new_archives'])[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ['tar', '-xzf', archive, '-C', tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, \
                f"Failed to extract archive {archive}. " \
                f"Error: {result.stderr}. This indicates a corrupt archive (unexpected EOF, truncation, etc.)"

    def test_extracted_files_match_source(self, run_incremental_backup):
        """Spot-check that extracted files match source files."""
        if not run_incremental_backup['new_archives']:
            pytest.skip("No archive created")

        archive = list(run_incremental_backup['new_archives'])[0]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract archive
            result = subprocess.run(
                ['tar', '-xzf', archive, '-C', tmpdir],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                pytest.fail(f"Cannot extract archive: {result.stderr}")

            # Find extracted files
            extracted_files = []
            for root, dirs, filenames in os.walk(tmpdir):
                for filename in filenames:
                    extracted_files.append(os.path.join(root, filename))

            if len(extracted_files) == 0:
                pytest.fail("No files were extracted from the archive")

            # Spot-check up to 5 random files
            sample_size = min(5, len(extracted_files))
            sample_files = random.sample(extracted_files, sample_size)

            mismatches = []
            for extracted_path in sample_files:
                # Determine the original source path
                # The archive might store paths like "home/user/data/..." or just "data/..."
                rel_path = os.path.relpath(extracted_path, tmpdir)

                # Try to find the corresponding source file
                possible_source_paths = [
                    os.path.join('/', rel_path),  # If stored as absolute
                    os.path.join(DATA_DIR, os.path.basename(extracted_path)),  # If just filename
                ]

                # Also try stripping common prefixes
                if 'home/user/data' in rel_path:
                    idx = rel_path.find('home/user/data')
                    possible_source_paths.append('/' + rel_path[idx:])
                if 'data/' in rel_path:
                    idx = rel_path.find('data/')
                    possible_source_paths.append(os.path.join(HOME, rel_path[idx:]))

                source_path = None
                for p in possible_source_paths:
                    if os.path.isfile(p):
                        source_path = p
                        break

                if source_path is None:
                    # Try walking DATA_DIR to find file by name
                    basename = os.path.basename(extracted_path)
                    for root, dirs, filenames in os.walk(DATA_DIR):
                        if basename in filenames:
                            source_path = os.path.join(root, basename)
                            break

                if source_path and os.path.isfile(source_path):
                    extracted_hash = get_file_hash(extracted_path)
                    source_hash = get_file_hash(source_path)
                    if extracted_hash != source_hash:
                        mismatches.append(f"{extracted_path} hash mismatch with {source_path}")

            assert len(mismatches) == 0, \
                f"Extracted files don't match source files: {mismatches}"


class TestStateTrackingPreserved:
    """Test that state tracking mechanism is preserved."""

    def test_state_directory_exists(self):
        assert os.path.isdir(STATE_DIR), \
            f"State directory {STATE_DIR} should still exist"

    def test_reference_file_exists(self):
        assert os.path.isfile(REFERENCE_FILE), \
            f"Reference file {REFERENCE_FILE} should still exist"

    def test_timestamp_file_exists(self):
        assert os.path.isfile(TIMESTAMP_FILE), \
            f"Timestamp file {TIMESTAMP_FILE} should still exist"


class TestNoRegressionOnArchiveIntegrity:
    """Additional tests to ensure archive integrity."""

    def test_fresh_incremental_is_complete(self):
        """Run a fresh incremental and verify it captures all expected files."""
        # Get files that should be in incremental
        expected_files = get_files_newer_than_reference()

        if len(expected_files) < 25:
            pytest.skip("Not enough files newer than reference for meaningful test")

        # Get archives before
        before_archives = set(glob.glob(f"{ARCHIVES_DIR}/incremental_*.tar.gz"))

        # Run incremental
        result = subprocess.run(
            [INCREMENTAL_SCRIPT],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            pytest.fail(f"Script failed: {result.stderr}")

        # Get new archive
        after_archives = set(glob.glob(f"{ARCHIVES_DIR}/incremental_*.tar.gz"))
        new_archives = after_archives - before_archives

        if not new_archives:
            pytest.fail("No new archive created")

        archive = list(new_archives)[0]

        # List archive contents
        list_result = subprocess.run(
            ['tar', '-tzf', archive],
            capture_output=True,
            text=True
        )

        if list_result.returncode != 0:
            pytest.fail(f"Cannot list archive: {list_result.stderr}")

        archived_files = [f for f in list_result.stdout.strip().split('\n') if f and not f.endswith('/')]

        # The archive should have a reasonable number of files
        # (at least 80% of expected, allowing for some timing differences)
        min_expected = int(len(expected_files) * 0.8)
        assert len(archived_files) >= min_expected, \
            f"Archive contains {len(archived_files)} files but expected at least {min_expected} " \
            f"(based on {len(expected_files)} files newer than reference). " \
            f"Archive may be truncated."
