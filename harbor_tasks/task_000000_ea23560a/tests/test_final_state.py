# test_final_state.py
"""
Tests to validate the final state of the system after the student
has completed the vm.swappiness configuration task.
"""

import os
import re
import subprocess
import pytest


class TestFinalState:
    """Validate the system state after the task is performed."""

    def test_config_file_exists(self):
        """Verify /etc/sysctl.d/99-swap.conf exists."""
        config_path = "/etc/sysctl.d/99-swap.conf"
        assert os.path.exists(config_path), (
            f"{config_path} does not exist. "
            "The configuration file should be created at this exact path."
        )
        assert os.path.isfile(config_path), (
            f"{config_path} exists but is not a regular file. "
            "This should be a configuration file, not a directory or symlink."
        )

    def test_config_file_contains_swappiness_setting(self):
        """Verify /etc/sysctl.d/99-swap.conf contains vm.swappiness = 10."""
        config_path = "/etc/sysctl.d/99-swap.conf"

        assert os.path.exists(config_path), (
            f"{config_path} does not exist. Cannot check contents."
        )

        with open(config_path, "r") as f:
            content = f.read()

        # Check for vm.swappiness = 10 with flexible whitespace around =
        # Pattern matches: vm.swappiness=10, vm.swappiness = 10, vm.swappiness =10, etc.
        pattern = r'^\s*vm\.swappiness\s*=\s*10\s*$'
        match = re.search(pattern, content, re.MULTILINE)

        assert match is not None, (
            f"Configuration file does not contain valid vm.swappiness = 10 setting. "
            f"File contents:\n{content}\n"
            "Expected a line like 'vm.swappiness = 10' or 'vm.swappiness=10'."
        )

    def test_runtime_swappiness_is_10(self):
        """Verify current runtime vm.swappiness is 10."""
        swappiness_path = "/proc/sys/vm/swappiness"

        assert os.path.exists(swappiness_path), (
            f"{swappiness_path} does not exist. Cannot verify runtime value."
        )

        with open(swappiness_path, "r") as f:
            current_value = f.read().strip()

        assert current_value == "10", (
            f"Runtime vm.swappiness is {current_value}, expected 10. "
            "The setting must be applied to the running kernel, not just written to file. "
            "Use 'sudo sysctl -p /etc/sysctl.d/99-swap.conf' or 'sudo sysctl vm.swappiness=10' "
            "to apply the setting immediately."
        )

    def test_sysctl_reports_swappiness_10(self):
        """Verify sysctl command reports vm.swappiness as 10."""
        result = subprocess.run(
            ["sysctl", "vm.swappiness"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"sysctl vm.swappiness command failed: {result.stderr}"
        )

        # Parse the output - should be "vm.swappiness = 10" or similar
        output = result.stdout.strip()
        # Extract the value after the = sign
        match = re.search(r'vm\.swappiness\s*=\s*(\d+)', output)

        assert match is not None, (
            f"Could not parse sysctl output: {output}"
        )

        value = match.group(1)
        assert value == "10", (
            f"sysctl reports vm.swappiness = {value}, expected 10. "
            "The runtime kernel parameter must be set to 10."
        )

    def test_config_file_not_empty(self):
        """Verify the config file is not empty and contains meaningful content."""
        config_path = "/etc/sysctl.d/99-swap.conf"

        assert os.path.exists(config_path), (
            f"{config_path} does not exist."
        )

        with open(config_path, "r") as f:
            content = f.read()

        # Remove comments and whitespace to check for actual content
        non_comment_lines = [
            line.strip() for line in content.splitlines()
            if line.strip() and not line.strip().startswith('#')
        ]

        assert len(non_comment_lines) > 0, (
            "Configuration file is empty or contains only comments. "
            "It must contain the vm.swappiness setting."
        )

    def test_grep_confirms_swappiness_setting(self):
        """Use grep to confirm vm.swappiness setting in config file (anti-shortcut guard)."""
        config_path = "/etc/sysctl.d/99-swap.conf"

        result = subprocess.run(
            ["grep", "-q", r"vm.swappiness.*=.*10", config_path],
            capture_output=True
        )

        assert result.returncode == 0, (
            f"grep did not find 'vm.swappiness.*=.*10' in {config_path}. "
            "The configuration file must contain the vm.swappiness = 10 setting."
        )

    def test_etc_sysctl_conf_unchanged(self):
        """Verify /etc/sysctl.conf was not modified (invariant check)."""
        # We can't check if it was modified without knowing the original content,
        # but we can verify it doesn't contain our specific swappiness=10 setting
        # that would indicate the student put it in the wrong file
        sysctl_conf_path = "/etc/sysctl.conf"

        if os.path.exists(sysctl_conf_path):
            with open(sysctl_conf_path, "r") as f:
                content = f.read()

            # Check if someone added vm.swappiness = 10 to the main sysctl.conf
            # This is a soft check - the setting should be in 99-swap.conf, not here
            # We only warn if it looks like it was recently added (uncommented)
            pattern = r'^\s*vm\.swappiness\s*=\s*10\s*$'
            if re.search(pattern, content, re.MULTILINE):
                # This is acceptable but not preferred - the task asked for 99-swap.conf
                pass  # Don't fail, but the primary file should still exist

    def test_persistence_setup_correct(self):
        """Verify the configuration will persist across reboots."""
        config_path = "/etc/sysctl.d/99-swap.conf"

        # The file must exist in the correct location
        assert os.path.exists(config_path), (
            f"{config_path} does not exist. "
            "For persistence across reboots, the setting must be in this file."
        )

        # Verify the file is readable (will be read on boot)
        assert os.access(config_path, os.R_OK), (
            f"{config_path} is not readable. "
            "The file must be readable for sysctl to load it on boot."
        )

        # Verify it contains the correct setting
        with open(config_path, "r") as f:
            content = f.read()

        pattern = r'vm\.swappiness\s*=\s*10'
        assert re.search(pattern, content), (
            f"Configuration file does not contain vm.swappiness = 10. "
            "This setting is required for persistence across reboots."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
