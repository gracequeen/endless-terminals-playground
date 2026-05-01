# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the archive-validator build fix task.
"""

import os
import subprocess
import pytest


class TestProjectStructure:
    """Verify the archive-validator project structure exists."""

    BASE_DIR = "/home/user/archive-validator"

    def test_project_directory_exists(self):
        """The archive-validator project directory must exist."""
        assert os.path.isdir(self.BASE_DIR), \
            f"Project directory {self.BASE_DIR} does not exist"

    def test_makefile_exists(self):
        """Makefile must exist in the project root."""
        makefile_path = os.path.join(self.BASE_DIR, "Makefile")
        assert os.path.isfile(makefile_path), \
            f"Makefile not found at {makefile_path}"

    def test_src_directory_exists(self):
        """src/ directory must exist."""
        src_dir = os.path.join(self.BASE_DIR, "src")
        assert os.path.isdir(src_dir), \
            f"Source directory {src_dir} does not exist"

    def test_main_c_exists(self):
        """src/main.c must exist."""
        main_c = os.path.join(self.BASE_DIR, "src", "main.c")
        assert os.path.isfile(main_c), \
            f"Source file {main_c} does not exist"

    def test_checksum_c_exists(self):
        """src/checksum.c must exist."""
        checksum_c = os.path.join(self.BASE_DIR, "src", "checksum.c")
        assert os.path.isfile(checksum_c), \
            f"Source file {checksum_c} does not exist"

    def test_deps_sh_exists(self):
        """deps.sh bootstrap script must exist."""
        deps_sh = os.path.join(self.BASE_DIR, "deps.sh")
        assert os.path.isfile(deps_sh), \
            f"Bootstrap script {deps_sh} does not exist"

    def test_bin_directory_exists(self):
        """bin/ directory must exist."""
        bin_dir = os.path.join(self.BASE_DIR, "bin")
        assert os.path.isdir(bin_dir), \
            f"Binary output directory {bin_dir} does not exist"

    def test_bin_directory_is_empty(self):
        """bin/ directory should be empty initially (no validator binary yet)."""
        bin_dir = os.path.join(self.BASE_DIR, "bin")
        contents = os.listdir(bin_dir)
        assert len(contents) == 0, \
            f"bin/ directory should be empty initially, but contains: {contents}"

    def test_readme_exists(self):
        """README.md must exist."""
        readme = os.path.join(self.BASE_DIR, "README.md")
        assert os.path.isfile(readme), \
            f"README.md not found at {readme}"


class TestMakefileContent:
    """Verify Makefile has expected initial content."""

    MAKEFILE_PATH = "/home/user/archive-validator/Makefile"

    def test_makefile_references_larchive(self):
        """Makefile should reference -larchive for linking."""
        with open(self.MAKEFILE_PATH, 'r') as f:
            content = f.read()
        assert '-larchive' in content, \
            "Makefile should contain -larchive linker flag"

    def test_makefile_references_lcrypto(self):
        """Makefile should reference -lcrypto for OpenSSL linking."""
        with open(self.MAKEFILE_PATH, 'r') as f:
            content = f.read()
        assert '-lcrypto' in content, \
            "Makefile should contain -lcrypto linker flag"

    def test_makefile_has_build_target(self):
        """Makefile should have a build target."""
        with open(self.MAKEFILE_PATH, 'r') as f:
            content = f.read()
        assert 'build:' in content or 'build :' in content, \
            "Makefile should have a 'build' target"


class TestVendorLibarchive:
    """Verify vendor/libarchive directory with pre-downloaded files exists."""

    VENDOR_DIR = "/home/user/archive-validator/vendor/libarchive"

    def test_vendor_libarchive_directory_exists(self):
        """vendor/libarchive directory must exist."""
        assert os.path.isdir(self.VENDOR_DIR), \
            f"Vendor libarchive directory {self.VENDOR_DIR} does not exist"

    def test_vendor_include_directory_exists(self):
        """vendor/libarchive/include directory must exist."""
        include_dir = os.path.join(self.VENDOR_DIR, "include")
        assert os.path.isdir(include_dir), \
            f"Vendor include directory {include_dir} does not exist"

    def test_vendor_lib_directory_exists(self):
        """vendor/libarchive/lib directory must exist."""
        lib_dir = os.path.join(self.VENDOR_DIR, "lib")
        assert os.path.isdir(lib_dir), \
            f"Vendor lib directory {lib_dir} does not exist"

    def test_vendor_archive_h_exists(self):
        """vendor/libarchive/include/archive.h must exist."""
        archive_h = os.path.join(self.VENDOR_DIR, "include", "archive.h")
        assert os.path.isfile(archive_h), \
            f"Vendor archive.h header not found at {archive_h}"

    def test_vendor_archive_entry_h_exists(self):
        """vendor/libarchive/include/archive_entry.h must exist."""
        archive_entry_h = os.path.join(self.VENDOR_DIR, "include", "archive_entry.h")
        assert os.path.isfile(archive_entry_h), \
            f"Vendor archive_entry.h header not found at {archive_entry_h}"

    def test_vendor_libarchive_a_exists(self):
        """vendor/libarchive/lib/libarchive.a static library must exist."""
        libarchive_a = os.path.join(self.VENDOR_DIR, "lib", "libarchive.a")
        assert os.path.isfile(libarchive_a), \
            f"Vendor static library not found at {libarchive_a}"


class TestSystemState:
    """Verify system state - what's installed and what's not."""

    def test_gcc_is_installed(self):
        """gcc compiler must be installed."""
        result = subprocess.run(['which', 'gcc'], capture_output=True)
        assert result.returncode == 0, \
            "gcc is not installed or not in PATH"

    def test_make_is_installed(self):
        """make utility must be installed."""
        result = subprocess.run(['which', 'make'], capture_output=True)
        assert result.returncode == 0, \
            "make is not installed or not in PATH"

    def test_libarchive_dev_not_installed_system_wide(self):
        """libarchive-dev should NOT be installed system-wide (the problem scenario)."""
        # Check if system libarchive.so exists in standard locations
        system_lib_paths = [
            '/usr/lib/libarchive.so',
            '/usr/lib/x86_64-linux-gnu/libarchive.so',
            '/usr/local/lib/libarchive.so',
            '/lib/libarchive.so',
            '/lib/x86_64-linux-gnu/libarchive.so'
        ]

        # Also check for archive.h in system include paths
        system_include_paths = [
            '/usr/include/archive.h',
            '/usr/local/include/archive.h'
        ]

        # At least the library should be missing for the linking to fail
        lib_found = any(os.path.exists(p) for p in system_lib_paths)

        assert not lib_found, \
            "System libarchive library should NOT be installed (this is the problem scenario)"

    def test_libssl_dev_is_installed(self):
        """libssl-dev should be installed (OpenSSL headers available)."""
        # Check for OpenSSL headers in standard locations
        openssl_header_paths = [
            '/usr/include/openssl/evp.h',
            '/usr/local/include/openssl/evp.h'
        ]

        header_found = any(os.path.exists(p) for p in openssl_header_paths)
        assert header_found, \
            "libssl-dev (OpenSSL headers) should be installed"


class TestDepsScript:
    """Verify deps.sh script characteristics."""

    DEPS_SH_PATH = "/home/user/archive-validator/deps.sh"

    def test_deps_sh_is_executable_or_readable(self):
        """deps.sh should be readable."""
        assert os.access(self.DEPS_SH_PATH, os.R_OK), \
            f"deps.sh at {self.DEPS_SH_PATH} is not readable"

    def test_deps_sh_always_exits_zero(self):
        """deps.sh should always exit 0 (part of the problem - silent failure)."""
        with open(self.DEPS_SH_PATH, 'r') as f:
            content = f.read()
        assert 'exit 0' in content, \
            "deps.sh should contain 'exit 0' (always succeeds regardless of actual result)"

    def test_deps_sh_swallows_errors(self):
        """deps.sh should have error swallowing pattern (2>/dev/null or similar)."""
        with open(self.DEPS_SH_PATH, 'r') as f:
            content = f.read()
        # Check for error redirection pattern
        assert '2>/dev/null' in content or '2>&1' in content, \
            "deps.sh should swallow stderr (part of the silent failure problem)"


class TestBuildCurrentlyFails:
    """Verify that make build currently fails (the problem state)."""

    BASE_DIR = "/home/user/archive-validator"

    def test_make_build_fails(self):
        """Running 'make build' should currently fail due to missing libarchive."""
        result = subprocess.run(
            ['make', 'build'],
            cwd=self.BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "make build should fail initially (cannot find -larchive)"

    def test_make_build_error_mentions_larchive(self):
        """The build error should mention the -larchive linking problem."""
        result = subprocess.run(
            ['make', 'build'],
            cwd=self.BASE_DIR,
            capture_output=True,
            text=True
        )
        combined_output = result.stdout + result.stderr
        assert 'larchive' in combined_output.lower() or 'archive' in combined_output.lower(), \
            f"Build error should mention libarchive linking issue. Got: {combined_output}"


class TestReadmeContent:
    """Verify README.md contains helpful hints."""

    README_PATH = "/home/user/archive-validator/README.md"

    def test_readme_mentions_vendor_libarchive(self):
        """README should mention the vendor/libarchive fallback."""
        with open(self.README_PATH, 'r') as f:
            content = f.read().lower()
        assert 'vendor' in content and 'libarchive' in content, \
            "README.md should mention vendor/libarchive as fallback option"
