# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the archive-validator build fix task.
"""

import os
import subprocess
import pytest


class TestBuildSuccess:
    """Verify that make build now succeeds."""

    BASE_DIR = "/home/user/archive-validator"

    def test_make_build_exits_zero(self):
        """Running 'make build' should now succeed (exit 0)."""
        result = subprocess.run(
            ['make', 'build'],
            cwd=self.BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"make build should succeed. Exit code: {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"


class TestValidatorBinary:
    """Verify the validator binary exists and is functional."""

    BASE_DIR = "/home/user/archive-validator"
    BINARY_PATH = "/home/user/archive-validator/bin/validator"

    def test_validator_binary_exists(self):
        """bin/validator binary must exist."""
        assert os.path.isfile(self.BINARY_PATH), \
            f"Validator binary not found at {self.BINARY_PATH}"

    def test_validator_binary_is_executable(self):
        """bin/validator must be executable."""
        assert os.access(self.BINARY_PATH, os.X_OK), \
            f"Validator binary at {self.BINARY_PATH} is not executable"

    def test_validator_help_runs_without_shared_object_error(self):
        """./bin/validator --help should run without 'cannot open shared object' errors."""
        result = subprocess.run(
            [self.BINARY_PATH, '--help'],
            cwd=self.BASE_DIR,
            capture_output=True,
            text=True
        )
        combined_output = result.stdout + result.stderr

        # Should not have shared object loading errors
        assert 'cannot open shared object' not in combined_output.lower(), \
            f"Binary has shared library loading errors: {combined_output}"
        assert 'error while loading shared libraries' not in combined_output.lower(), \
            f"Binary has shared library loading errors: {combined_output}"

    def test_validator_help_exits_zero_or_prints_usage(self):
        """./bin/validator --help should exit 0 or print usage information."""
        result = subprocess.run(
            [self.BINARY_PATH, '--help'],
            cwd=self.BASE_DIR,
            capture_output=True,
            text=True
        )
        combined_output = (result.stdout + result.stderr).lower()

        # Either exits 0 or prints usage info
        has_usage = 'usage' in combined_output or 'validator' in combined_output
        exits_zero = result.returncode == 0

        assert exits_zero or has_usage, \
            f"--help should exit 0 or print usage. Exit code: {result.returncode}, output: {combined_output}"

    def test_validator_help_prints_expected_usage(self):
        """./bin/validator --help should print usage mentioning archive.tar.gz."""
        result = subprocess.run(
            [self.BINARY_PATH, '--help'],
            cwd=self.BASE_DIR,
            capture_output=True,
            text=True
        )
        combined_output = result.stdout + result.stderr

        # Should contain the expected usage pattern
        assert 'Usage:' in combined_output or 'usage:' in combined_output.lower(), \
            f"--help should print usage information. Got: {combined_output}"


class TestBinaryLinksLibarchive:
    """Verify the binary actually links against libarchive (not stubbed)."""

    BINARY_PATH = "/home/user/archive-validator/bin/validator"

    def test_binary_contains_archive_read_new_symbol(self):
        """Binary must contain archive_read_new symbol (proves real libarchive linking)."""
        result = subprocess.run(
            ['nm', self.BINARY_PATH],
            capture_output=True,
            text=True
        )

        # nm might fail on stripped binaries, try objdump or strings as fallback
        if result.returncode != 0:
            # Try with -D flag for dynamic symbols
            result = subprocess.run(
                ['nm', '-D', self.BINARY_PATH],
                capture_output=True,
                text=True
            )

        combined_output = result.stdout + result.stderr

        # Check for archive_read_new symbol
        assert 'archive_read_new' in combined_output, \
            f"Binary should contain archive_read_new symbol (proves libarchive linking). nm output: {combined_output}"


class TestMakefileModified:
    """Verify Makefile was modified to use vendor paths."""

    MAKEFILE_PATH = "/home/user/archive-validator/Makefile"

    def test_makefile_references_vendor_or_libarchive_path(self):
        """Makefile must reference vendor path for libarchive."""
        with open(self.MAKEFILE_PATH, 'r') as f:
            content = f.read()

        # Should contain reference to vendor directory or libarchive path
        has_vendor_ref = 'vendor' in content.lower()
        has_libarchive_path = 'libarchive' in content and ('/' in content or '-I' in content or '-L' in content)

        assert has_vendor_ref or has_libarchive_path, \
            f"Makefile should reference vendor/libarchive path. Content:\n{content}"

    def test_makefile_grep_vendor_or_libarchive(self):
        """grep -E 'vendor|libarchive' Makefile should match."""
        result = subprocess.run(
            ['grep', '-E', 'vendor|libarchive', self.MAKEFILE_PATH],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0 and result.stdout.strip(), \
            f"Makefile should contain 'vendor' or 'libarchive' path references. grep found nothing."


class TestSourceFilesUnchanged:
    """Verify source files were not modified (invariant check)."""

    BASE_DIR = "/home/user/archive-validator"

    def test_main_c_exists(self):
        """src/main.c must still exist."""
        main_c = os.path.join(self.BASE_DIR, "src", "main.c")
        assert os.path.isfile(main_c), \
            f"Source file {main_c} must still exist"

    def test_checksum_c_exists(self):
        """src/checksum.c must still exist."""
        checksum_c = os.path.join(self.BASE_DIR, "src", "checksum.c")
        assert os.path.isfile(checksum_c), \
            f"Source file {checksum_c} must still exist"

    def test_main_c_contains_archive_includes(self):
        """src/main.c should still contain archive.h include (not modified to stub)."""
        main_c = os.path.join(self.BASE_DIR, "src", "main.c")
        with open(main_c, 'r') as f:
            content = f.read()

        assert 'archive.h' in content, \
            "src/main.c should still include archive.h"

    def test_main_c_contains_archive_calls(self):
        """src/main.c should still contain libarchive API calls."""
        main_c = os.path.join(self.BASE_DIR, "src", "main.c")
        with open(main_c, 'r') as f:
            content = f.read()

        assert 'archive_read_new' in content or 'archive_read_support' in content, \
            "src/main.c should still contain libarchive API calls"


class TestVendorFilesUnchanged:
    """Verify vendor/libarchive contents were not modified (invariant check)."""

    VENDOR_DIR = "/home/user/archive-validator/vendor/libarchive"

    def test_vendor_archive_h_exists(self):
        """vendor/libarchive/include/archive.h must still exist."""
        archive_h = os.path.join(self.VENDOR_DIR, "include", "archive.h")
        assert os.path.isfile(archive_h), \
            f"Vendor archive.h header must still exist at {archive_h}"

    def test_vendor_archive_entry_h_exists(self):
        """vendor/libarchive/include/archive_entry.h must still exist."""
        archive_entry_h = os.path.join(self.VENDOR_DIR, "include", "archive_entry.h")
        assert os.path.isfile(archive_entry_h), \
            f"Vendor archive_entry.h header must still exist at {archive_entry_h}"

    def test_vendor_libarchive_a_exists(self):
        """vendor/libarchive/lib/libarchive.a static library must still exist."""
        libarchive_a = os.path.join(self.VENDOR_DIR, "lib", "libarchive.a")
        assert os.path.isfile(libarchive_a), \
            f"Vendor static library must still exist at {libarchive_a}"


class TestNoSystemPackagesInstalled:
    """Verify no system packages were installed (user has no sudo)."""

    def test_system_libarchive_still_not_installed(self):
        """System libarchive should still NOT be installed (no sudo available)."""
        # Check if system libarchive.so exists in standard locations
        system_lib_paths = [
            '/usr/lib/libarchive.so',
            '/usr/lib/x86_64-linux-gnu/libarchive.so',
            '/usr/local/lib/libarchive.so',
            '/lib/libarchive.so',
            '/lib/x86_64-linux-gnu/libarchive.so'
        ]

        # The solution should use vendor, not install system packages
        lib_found = any(os.path.exists(p) for p in system_lib_paths)

        # This is a soft check - if system lib exists, it might have been pre-existing
        # but we verify the Makefile uses vendor path regardless
        if lib_found:
            # If system lib exists, at least verify Makefile references vendor
            makefile_path = "/home/user/archive-validator/Makefile"
            with open(makefile_path, 'r') as f:
                content = f.read()
            assert 'vendor' in content.lower(), \
                "If system libarchive exists, Makefile should still reference vendor path"
