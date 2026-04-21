# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the container image audit task.
"""

import os
import subprocess
import pytest


class TestMigrationDirectoryStructure:
    """Test that the migration directory and required files exist."""

    def test_migration_directory_exists(self):
        """The /home/user/migration/ directory must exist."""
        migration_dir = "/home/user/migration"
        assert os.path.isdir(migration_dir), (
            f"Migration directory '{migration_dir}' does not exist. "
            "Please create it before proceeding."
        )

    def test_migration_directory_is_writable(self):
        """The /home/user/migration/ directory must be writable."""
        migration_dir = "/home/user/migration"
        assert os.access(migration_dir, os.W_OK), (
            f"Migration directory '{migration_dir}' is not writable. "
            "Please ensure write permissions."
        )

    def test_installed_packages_file_exists(self):
        """The installed_packages.txt file must exist."""
        installed_file = "/home/user/migration/installed_packages.txt"
        assert os.path.isfile(installed_file), (
            f"File '{installed_file}' does not exist. "
            "This file should contain the list of installed packages."
        )

    def test_required_packages_file_exists(self):
        """The required_packages.txt file must exist."""
        required_file = "/home/user/migration/required_packages.txt"
        assert os.path.isfile(required_file), (
            f"File '{required_file}' does not exist. "
            "This file should contain the list of required packages."
        )


class TestInstalledPackagesContent:
    """Test that installed_packages.txt has the correct content."""

    EXPECTED_INSTALLED_PACKAGES = [
        "curl",
        "wget",
        "vim",
        "nano",
        "git",
        "htop",
        "tree",
        "ncdu",
        "jq",
        "python3",
        "python3-pip",
        "nodejs",
        "npm",
        "nginx",
        "apache2",
        "mysql-client",
        "postgresql-client",
        "redis-tools",
        "netcat-openbsd",
        "tcpdump",
        "strace",
        "lsof",
        "dnsutils",
        "iputils-ping",
        "ca-certificates",
        "openssl",
        "libssl3",
        "zlib1g",
        "libc6",
        "coreutils",
        "bash",
    ]

    def test_installed_packages_file_readable(self):
        """The installed_packages.txt file must be readable."""
        installed_file = "/home/user/migration/installed_packages.txt"
        assert os.access(installed_file, os.R_OK), (
            f"File '{installed_file}' is not readable."
        )

    def test_installed_packages_count(self):
        """The installed_packages.txt file must contain exactly 31 packages."""
        installed_file = "/home/user/migration/installed_packages.txt"
        with open(installed_file, 'r') as f:
            packages = [line.strip() for line in f if line.strip()]
        assert len(packages) == 31, (
            f"Expected 31 packages in installed_packages.txt, found {len(packages)}. "
            f"Packages found: {packages}"
        )

    def test_installed_packages_content(self):
        """The installed_packages.txt file must contain the expected packages."""
        installed_file = "/home/user/migration/installed_packages.txt"
        with open(installed_file, 'r') as f:
            packages = [line.strip() for line in f if line.strip()]

        expected_set = set(self.EXPECTED_INSTALLED_PACKAGES)
        actual_set = set(packages)

        missing = expected_set - actual_set
        extra = actual_set - expected_set

        error_msg = []
        if missing:
            error_msg.append(f"Missing packages: {sorted(missing)}")
        if extra:
            error_msg.append(f"Unexpected packages: {sorted(extra)}")

        assert expected_set == actual_set, (
            f"installed_packages.txt content mismatch. {' '.join(error_msg)}"
        )


class TestRequiredPackagesContent:
    """Test that required_packages.txt has the correct content."""

    EXPECTED_REQUIRED_PACKAGES = [
        "curl",
        "python3",
        "python3-pip",
        "jq",
        "nginx",
        "ca-certificates",
        "openssl",
        "bash",
        "coreutils",
    ]

    def test_required_packages_file_readable(self):
        """The required_packages.txt file must be readable."""
        required_file = "/home/user/migration/required_packages.txt"
        assert os.access(required_file, os.R_OK), (
            f"File '{required_file}' is not readable."
        )

    def test_required_packages_count(self):
        """The required_packages.txt file must contain exactly 9 packages."""
        required_file = "/home/user/migration/required_packages.txt"
        with open(required_file, 'r') as f:
            packages = [line.strip() for line in f if line.strip()]
        assert len(packages) == 9, (
            f"Expected 9 packages in required_packages.txt, found {len(packages)}. "
            f"Packages found: {packages}"
        )

    def test_required_packages_content(self):
        """The required_packages.txt file must contain the expected packages."""
        required_file = "/home/user/migration/required_packages.txt"
        with open(required_file, 'r') as f:
            packages = [line.strip() for line in f if line.strip()]

        expected_set = set(self.EXPECTED_REQUIRED_PACKAGES)
        actual_set = set(packages)

        missing = expected_set - actual_set
        extra = actual_set - expected_set

        error_msg = []
        if missing:
            error_msg.append(f"Missing packages: {sorted(missing)}")
        if extra:
            error_msg.append(f"Unexpected packages: {sorted(extra)}")

        assert expected_set == actual_set, (
            f"required_packages.txt content mismatch. {' '.join(error_msg)}"
        )


class TestOutputFilesDoNotExist:
    """Test that output files do not exist initially."""

    def test_removal_report_does_not_exist(self):
        """The removal_report.json file must NOT exist initially."""
        report_file = "/home/user/migration/removal_report.json"
        assert not os.path.exists(report_file), (
            f"File '{report_file}' already exists. "
            "Please remove it before running the task - this is an output file."
        )

    def test_remove_packages_script_does_not_exist(self):
        """The remove_packages.sh script must NOT exist initially."""
        script_file = "/home/user/migration/remove_packages.sh"
        assert not os.path.exists(script_file), (
            f"File '{script_file}' already exists. "
            "Please remove it before running the task - this is an output file."
        )


class TestSystemTools:
    """Test that required system tools are available."""

    def test_dpkg_query_available(self):
        """The dpkg-query command must be available."""
        result = subprocess.run(
            ["which", "dpkg-query"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "dpkg-query command is not available. "
            "This is required for querying package information."
        )

    def test_apt_cache_available(self):
        """The apt-cache command must be available."""
        result = subprocess.run(
            ["which", "apt-cache"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "apt-cache command is not available. "
            "This is required for querying package dependencies and information."
        )

    def test_apt_cache_functional(self):
        """The apt-cache command must be functional (cache available)."""
        result = subprocess.run(
            ["apt-cache", "show", "bash"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "apt-cache is not functional. The apt cache may not be updated. "
            "Please run 'apt-get update' to update the package cache."
        )

    def test_apt_get_available(self):
        """The apt-get command must be available."""
        result = subprocess.run(
            ["which", "apt-get"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "apt-get command is not available. "
            "This system may not be Debian/Ubuntu-based."
        )


class TestSystemIsDebianBased:
    """Test that the system is Debian/Ubuntu-based."""

    def test_os_release_exists(self):
        """The /etc/os-release file should exist."""
        assert os.path.isfile("/etc/os-release"), (
            "/etc/os-release file does not exist. "
            "Cannot verify this is a Debian/Ubuntu-based system."
        )

    def test_is_debian_or_ubuntu(self):
        """The system should be Debian or Ubuntu-based."""
        os_release_file = "/etc/os-release"
        if not os.path.isfile(os_release_file):
            pytest.skip("Cannot check OS - /etc/os-release missing")

        with open(os_release_file, 'r') as f:
            content = f.read().lower()

        is_compatible = any(distro in content for distro in ['ubuntu', 'debian'])
        assert is_compatible, (
            "This system does not appear to be Ubuntu or Debian-based. "
            "The task requires a Debian-based system with apt package management."
        )
