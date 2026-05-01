# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has fixed the backup script to remove the --rsyncable flag.
"""

import os
import stat
import subprocess
import tempfile
import shutil
import pytest


HOME = "/home/user"
BACKUP_DIR = os.path.join(HOME, "backup")
COMPRESS_SCRIPT = os.path.join(BACKUP_DIR, "compress.sh")
SIMULATE_SCRIPT = os.path.join(BACKUP_DIR, "simulate_remote_extract.sh")
TESTDATA_DIR = os.path.join(BACKUP_DIR, "testdata")
OUTPUT_FILE = os.path.join(BACKUP_DIR, "output.tar.gz")


class TestCompressScriptFixed:
    """Tests that compress.sh has been properly fixed"""

    def test_compress_script_exists(self):
        """compress.sh must still exist"""
        assert os.path.exists(COMPRESS_SCRIPT), (
            f"compress.sh not found at {COMPRESS_SCRIPT}"
        )

    def test_compress_script_is_file(self):
        """compress.sh must be a regular file"""
        assert os.path.isfile(COMPRESS_SCRIPT), (
            f"{COMPRESS_SCRIPT} exists but is not a regular file"
        )

    def test_compress_script_is_executable(self):
        """compress.sh must be executable"""
        mode = os.stat(COMPRESS_SCRIPT).st_mode
        assert mode & stat.S_IXUSR, (
            f"{COMPRESS_SCRIPT} is not executable by owner"
        )

    def test_compress_script_no_rsyncable_flag(self):
        """compress.sh must NOT contain --rsyncable flag (the fix)"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "--rsyncable" not in content, (
            "compress.sh still contains '--rsyncable' flag - this must be removed to fix the bug"
        )

    def test_compress_script_still_uses_gzip(self):
        """compress.sh must still use gzip for compression"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "gzip" in content, (
            "compress.sh must still use gzip for compression (not switch to bzip2, xz, etc.)"
        )

    def test_compress_script_still_uses_tar(self):
        """compress.sh must still use tar for archiving"""
        with open(COMPRESS_SCRIPT, 'r') as f:
            content = f.read()
        assert "tar" in content, (
            "compress.sh must still use tar for archiving"
        )

    def test_compress_script_has_valid_syntax(self):
        """compress.sh must have valid bash syntax"""
        result = subprocess.run(
            ["bash", "-n", COMPRESS_SCRIPT],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"compress.sh has syntax errors: {result.stderr}"
        )


class TestSimulateScriptUnchanged:
    """Tests that simulate_remote_extract.sh has NOT been modified"""

    def test_simulate_script_exists(self):
        """simulate_remote_extract.sh must still exist"""
        assert os.path.exists(SIMULATE_SCRIPT), (
            f"simulate_remote_extract.sh not found at {SIMULATE_SCRIPT}"
        )

    def test_simulate_script_is_file(self):
        """simulate_remote_extract.sh must be a regular file"""
        assert os.path.isfile(SIMULATE_SCRIPT), (
            f"{SIMULATE_SCRIPT} exists but is not a regular file"
        )

    def test_simulate_script_checks_rsyncable(self):
        """simulate_remote_extract.sh must still check for rsyncable markers"""
        with open(SIMULATE_SCRIPT, 'r') as f:
            content = f.read()
        assert "00 00 ff ff" in content, (
            "simulate_remote_extract.sh should still check for rsyncable sync flush markers - it should not have been modified"
        )

    def test_simulate_script_has_size_check(self):
        """simulate_remote_extract.sh must still have 2MB size threshold"""
        with open(SIMULATE_SCRIPT, 'r') as f:
            content = f.read()
        assert "2000000" in content, (
            "simulate_remote_extract.sh should still have 2MB threshold check - it should not have been modified"
        )


class TestTestDataUnchanged:
    """Tests that testdata directory has NOT been modified"""

    def test_testdata_dir_exists(self):
        """testdata directory must still exist"""
        assert os.path.exists(TESTDATA_DIR), (
            f"testdata directory not found at {TESTDATA_DIR}"
        )

    def test_testdata_is_directory(self):
        """testdata must be a directory"""
        assert os.path.isdir(TESTDATA_DIR), (
            f"{TESTDATA_DIR} exists but is not a directory"
        )

    def test_testdata_has_approximately_50_files(self):
        """testdata directory should still contain ~50 files"""
        files = []
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            files.extend(filenames)
        # Allow some flexibility: 40-60 files
        assert 40 <= len(files) <= 60, (
            f"{TESTDATA_DIR} should contain ~50 files, found {len(files)} - testdata should not have been modified"
        )

    def test_testdata_has_approximately_8mb(self):
        """testdata directory should still total ~8MB uncompressed"""
        total_size = 0
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        # Allow 6MB to 10MB range
        min_size = 6 * 1024 * 1024  # 6MB
        max_size = 10 * 1024 * 1024  # 10MB
        assert min_size <= total_size <= max_size, (
            f"{TESTDATA_DIR} should total ~8MB, found {total_size / (1024*1024):.2f}MB - testdata should not have been modified"
        )


class TestCompressScriptProducesValidOutput:
    """Tests that running compress.sh produces valid output"""

    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Clean up any existing output file before and after tests"""
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        yield
        # Don't remove after - other tests may need it

    def test_compress_script_runs_successfully(self):
        """compress.sh should run without errors"""
        result = subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        assert result.returncode == 0, (
            f"compress.sh failed with exit code {result.returncode}. "
            f"stdout: {result.stdout}, stderr: {result.stderr}"
        )

    def test_compress_script_produces_output_file(self):
        """compress.sh should produce output.tar.gz"""
        # Run the script first
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        assert os.path.exists(OUTPUT_FILE), (
            f"compress.sh did not produce {OUTPUT_FILE}"
        )

    def test_output_is_valid_gzip(self):
        """output.tar.gz must be a valid gzip file"""
        # Run the script first
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        # Test with gzip -t
        result = subprocess.run(
            ["gzip", "-t", OUTPUT_FILE],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"output.tar.gz is not a valid gzip file: {result.stderr}"
        )

    def test_output_is_valid_tar_gz(self):
        """output.tar.gz must be extractable with standard tar -xzf"""
        # Run the script first
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        # Create a temp directory for extraction test
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["tar", "-xzf", OUTPUT_FILE, "-C", tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, (
                f"output.tar.gz cannot be extracted with tar -xzf: {result.stderr}"
            )

    def test_output_has_reasonable_compression(self):
        """output.tar.gz must have reasonable compression (not store-only)"""
        # Run the script first
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        # Get compressed size
        compressed_size = os.path.getsize(OUTPUT_FILE)
        # Get uncompressed size
        total_size = 0
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
        # Compression ratio should be at least 10% (compressed should be < 90% of original)
        # This is a very lenient check - gzip typically achieves much better
        assert compressed_size < total_size * 0.9, (
            f"Compression appears ineffective: compressed={compressed_size}, "
            f"original={total_size}. Compression must be enabled (not store-only)."
        )


class TestSimulatedRemoteExtraction:
    """Tests that the fixed archive works with the simulated remote extraction"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure output file exists by running compress.sh"""
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        yield

    def test_simulate_remote_extract_succeeds(self):
        """simulate_remote_extract.sh must succeed with the fixed archive"""
        assert os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist - compress.sh must be run first"
        )
        result = subprocess.run(
            [SIMULATE_SCRIPT, OUTPUT_FILE],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        assert result.returncode == 0, (
            f"simulate_remote_extract.sh failed with exit code {result.returncode}. "
            f"stdout: {result.stdout}, stderr: {result.stderr}. "
            "The archive still has issues that prevent extraction on the remote server."
        )

    def test_simulate_remote_extract_prints_success(self):
        """simulate_remote_extract.sh must print 'Extraction successful'"""
        assert os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist"
        )
        result = subprocess.run(
            [SIMULATE_SCRIPT, OUTPUT_FILE],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        assert "Extraction successful" in result.stdout, (
            f"simulate_remote_extract.sh did not print 'Extraction successful'. "
            f"Output was: {result.stdout}"
        )

    def test_no_unexpected_end_of_file_error(self):
        """simulate_remote_extract.sh must NOT produce 'unexpected end of file' error"""
        assert os.path.exists(OUTPUT_FILE), (
            f"Output file {OUTPUT_FILE} does not exist"
        )
        result = subprocess.run(
            [SIMULATE_SCRIPT, OUTPUT_FILE],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        combined_output = result.stdout + result.stderr
        assert "unexpected end of file" not in combined_output.lower(), (
            "simulate_remote_extract.sh still produces 'unexpected end of file' error. "
            "The --rsyncable flag must be removed from compress.sh."
        )


class TestExtractedContentsMatch:
    """Tests that extracted contents match the original testdata"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure output file exists by running compress.sh"""
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        yield

    def test_extracted_file_count_matches(self):
        """Extracted archive should have same number of files as testdata"""
        # Count original files
        original_files = []
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            original_files.extend(filenames)
        original_count = len(original_files)

        # Extract and count
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["tar", "-xzf", OUTPUT_FILE, "-C", tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Extraction failed: {result.stderr}"

            extracted_files = []
            for root, dirs, filenames in os.walk(tmpdir):
                extracted_files.extend(filenames)
            extracted_count = len(extracted_files)

            assert extracted_count == original_count, (
                f"Extracted file count ({extracted_count}) does not match "
                f"original ({original_count})"
            )

    def test_extracted_total_size_matches(self):
        """Extracted archive should have approximately same total size as testdata"""
        # Calculate original size
        original_size = 0
        for root, dirs, filenames in os.walk(TESTDATA_DIR):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    original_size += os.path.getsize(filepath)

        # Extract and calculate size
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["tar", "-xzf", OUTPUT_FILE, "-C", tmpdir],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Extraction failed: {result.stderr}"

            extracted_size = 0
            for root, dirs, filenames in os.walk(tmpdir):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    if os.path.isfile(filepath):
                        extracted_size += os.path.getsize(filepath)

            # Allow 1% tolerance for any rounding/metadata differences
            tolerance = original_size * 0.01
            assert abs(extracted_size - original_size) <= tolerance, (
                f"Extracted total size ({extracted_size}) does not match "
                f"original ({original_size}) within tolerance"
            )


class TestOutputFileIsLargeEnough:
    """Tests that the output file is large enough to trigger the original bug"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure output file exists by running compress.sh"""
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        subprocess.run(
            [COMPRESS_SCRIPT],
            capture_output=True,
            text=True,
            cwd=BACKUP_DIR
        )
        yield

    def test_output_file_over_2mb(self):
        """Output file should be over 2MB to properly test the fix"""
        assert os.path.exists(OUTPUT_FILE), f"Output file {OUTPUT_FILE} does not exist"
        file_size = os.path.getsize(OUTPUT_FILE)
        # The bug only manifests for files > 2MB, so our test file should be larger
        assert file_size > 2000000, (
            f"Output file is only {file_size} bytes, should be > 2MB to properly test the fix. "
            "This suggests the testdata may have been modified or compression is too aggressive."
        )
