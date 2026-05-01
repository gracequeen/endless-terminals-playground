# test_initial_state.py
"""
Tests to validate the initial state of the system before the student
performs the vm.swappiness configuration task.
"""

import os
import subprocess
import pytest


class TestInitialState:
    """Validate the system state before the task is performed."""

    def test_proc_swappiness_exists(self):
        """Verify /proc/sys/vm/swappiness exists and is readable."""
        swappiness_path = "/proc/sys/vm/swappiness"
        assert os.path.exists(swappiness_path), (
            f"{swappiness_path} does not exist. "
            "This file should exist on a Linux system with swap support."
        )
        assert os.access(swappiness_path, os.R_OK), (
            f"{swappiness_path} is not readable. "
            "The file should be readable to check current swappiness value."
        )

    def test_current_swappiness_is_default_60(self):
        """Verify current vm.swappiness is at the default value of 60."""
        swappiness_path = "/proc/sys/vm/swappiness"
        with open(swappiness_path, "r") as f:
            current_value = f.read().strip()

        assert current_value == "60", (
            f"Current vm.swappiness is {current_value}, expected 60 (default). "
            "The initial state should have the default swappiness value."
        )

    def test_sysctl_d_directory_exists(self):
        """Verify /etc/sysctl.d/ directory exists."""
        sysctl_d_path = "/etc/sysctl.d"
        assert os.path.exists(sysctl_d_path), (
            f"{sysctl_d_path} directory does not exist. "
            "This directory should exist for sysctl configuration files."
        )
        assert os.path.isdir(sysctl_d_path), (
            f"{sysctl_d_path} exists but is not a directory. "
            "This should be a directory for sysctl configuration files."
        )

    def test_target_config_file_does_not_exist(self):
        """Verify /etc/sysctl.d/99-swap.conf does not exist yet."""
        config_path = "/etc/sysctl.d/99-swap.conf"
        assert not os.path.exists(config_path), (
            f"{config_path} already exists. "
            "The target configuration file should not exist in the initial state."
        )

    def test_sysctl_command_available(self):
        """Verify sysctl command is available on the system."""
        result = subprocess.run(
            ["which", "sysctl"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "sysctl command is not available. "
            "The sysctl command should be installed and accessible."
        )

    def test_sysctl_can_read_swappiness(self):
        """Verify sysctl can read the vm.swappiness value."""
        result = subprocess.run(
            ["sysctl", "vm.swappiness"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"sysctl vm.swappiness failed: {result.stderr}. "
            "Should be able to read vm.swappiness via sysctl."
        )
        assert "vm.swappiness" in result.stdout, (
            f"Unexpected sysctl output: {result.stdout}. "
            "Output should contain vm.swappiness."
        )

    def test_etc_sysctl_conf_exists(self):
        """Verify /etc/sysctl.conf exists (for invariant checking later)."""
        sysctl_conf_path = "/etc/sysctl.conf"
        assert os.path.exists(sysctl_conf_path), (
            f"{sysctl_conf_path} does not exist. "
            "This file should exist as the main sysctl configuration file."
        )

    def test_sysctl_d_is_writable(self):
        """Verify /etc/sysctl.d/ is writable (either directly or via sudo)."""
        sysctl_d_path = "/etc/sysctl.d"
        # Check if directory is writable directly or if we can use sudo
        if os.access(sysctl_d_path, os.W_OK):
            # Directly writable
            pass
        else:
            # Try to check if sudo would work (test with a dry-run type check)
            result = subprocess.run(
                ["sudo", "-n", "test", "-w", sysctl_d_path],
                capture_output=True
            )
            assert result.returncode == 0, (
                f"{sysctl_d_path} is not writable and sudo access may not be available. "
                "The agent needs write access to this directory."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
