# test_final_state.py
"""
Tests to validate the final state after the student fixes the deploy script
issue for build 47. The fix should make build 47 deployable through the
standard symlink resolution without modifying deploy.sh.
"""

import os
import subprocess
import pytest


class TestDeployScriptUnchanged:
    """Verify that deploy.sh was not modified (fix should be in directory structure)."""

    def test_deploy_script_exists(self):
        """The deploy.sh script must still exist."""
        path = "/home/user/releases/deploy.sh"
        assert os.path.isfile(path), f"Deploy script {path} does not exist"

    def test_deploy_script_reads_from_active_config(self):
        """The deploy script should still read config from /home/user/releases/active/config/app.conf."""
        path = "/home/user/releases/deploy.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "/home/user/releases/active/config/app.conf" in content, \
            "Deploy script was modified - it should still reference /home/user/releases/active/config/app.conf"

    def test_deploy_script_copies_to_runtime(self):
        """The deploy script should still copy config to /home/user/app/runtime.conf."""
        path = "/home/user/releases/deploy.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "/home/user/app/runtime.conf" in content, \
            "Deploy script was modified - it should still reference /home/user/app/runtime.conf"


class TestBuild47ConfigAccessible:
    """Test that build 47's config is now accessible at the expected path."""

    def test_build_47_config_path_exists(self):
        """The config for build 47 must be accessible at builds/47/config/app.conf."""
        path = "/home/user/releases/builds/47/config/app.conf"
        assert os.path.exists(path), \
            f"Config path {path} does not exist - build 47 needs config/app.conf structure"

    def test_build_47_config_readable(self):
        """The config for build 47 must be readable."""
        path = "/home/user/releases/builds/47/config/app.conf"
        assert os.access(path, os.R_OK), \
            f"Config file {path} is not readable"

    def test_build_47_config_contains_version(self):
        """The config for build 47 must contain version=47."""
        path = "/home/user/releases/builds/47/config/app.conf"
        with open(path, 'r') as f:
            content = f.read()
        assert "version=47" in content, \
            f"Config file {path} does not contain 'version=47'"


class TestBuild46StillWorks:
    """Test that build 46 still has correct structure and works."""

    def test_build_46_config_exists(self):
        """Build 46 config should still exist at the correct path."""
        path = "/home/user/releases/builds/46/config/app.conf"
        assert os.path.exists(path), \
            f"Build 46 config {path} no longer exists"

    def test_build_46_config_content(self):
        """Build 46 config should still contain version=46."""
        path = "/home/user/releases/builds/46/config/app.conf"
        with open(path, 'r') as f:
            content = f.read()
        assert "version=46" in content, \
            f"Build 46 config does not contain 'version=46'"


class TestSymlinkStructure:
    """Test that the symlink mechanism is intact."""

    def test_active_symlink_exists(self):
        """The 'active' symlink must still exist."""
        path = "/home/user/releases/active"
        assert os.path.islink(path), \
            f"Symlink {path} does not exist or is not a symlink"

    def test_current_symlink_exists(self):
        """The 'current' symlink must still exist."""
        path = "/home/user/releases/current"
        assert os.path.islink(path), \
            f"Symlink {path} does not exist or is not a symlink"

    def test_current_symlink_points_to_build_47(self):
        """After deployment, 'current' should point to builds/47."""
        path = "/home/user/releases/current"
        # Resolve the symlink to see what it ultimately points to
        resolved = os.path.realpath(path)
        assert resolved.endswith("builds/47") or "/47" in resolved, \
            f"Symlink {path} resolves to {resolved}, expected it to point to builds/47"

    def test_active_config_resolves_to_build_47(self):
        """The active/config/app.conf path should resolve to build 47's config."""
        path = "/home/user/releases/active/config/app.conf"
        assert os.path.exists(path), \
            f"Path {path} does not exist through symlink chain"
        with open(path, 'r') as f:
            content = f.read()
        assert "version=47" in content, \
            f"Path {path} does not contain 'version=47' - symlink chain not resolving correctly"


class TestRuntimeConfig:
    """Test that the runtime config was created correctly."""

    def test_runtime_conf_exists(self):
        """The runtime.conf file must exist after deployment."""
        path = "/home/user/app/runtime.conf"
        assert os.path.isfile(path), \
            f"Runtime config {path} does not exist - deployment did not complete"

    def test_runtime_conf_contains_version_47(self):
        """The runtime.conf must contain version=47."""
        path = "/home/user/app/runtime.conf"
        with open(path, 'r') as f:
            content = f.read()
        assert "version=47" in content, \
            f"Runtime config {path} does not contain 'version=47' - wrong build deployed"


class TestDeployScriptExecution:
    """Test that the deploy script can be executed successfully for build 47."""

    def test_deploy_script_exits_zero_for_build_47(self):
        """Running deploy.sh 47 should exit with code 0."""
        result = subprocess.run(
            ["./deploy.sh", "47"],
            cwd="/home/user/releases",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Deploy script exited with code {result.returncode}. " \
            f"Stderr: {result.stderr}. Stdout: {result.stdout}"

    def test_deploy_script_outputs_success_message(self):
        """Running deploy.sh 47 should output 'deployed build 47'."""
        result = subprocess.run(
            ["./deploy.sh", "47"],
            cwd="/home/user/releases",
            capture_output=True,
            text=True
        )
        assert "deployed build 47" in result.stdout, \
            f"Deploy script did not output expected success message. " \
            f"Stdout: {result.stdout}. Stderr: {result.stderr}"

    def test_deploy_script_still_works_for_build_46(self):
        """Running deploy.sh 46 should still work (backward compatibility)."""
        result = subprocess.run(
            ["./deploy.sh", "46"],
            cwd="/home/user/releases",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Deploy script for build 46 exited with code {result.returncode}. " \
            f"Stderr: {result.stderr}. Stdout: {result.stdout}"
        assert "deployed build 46" in result.stdout, \
            f"Deploy script did not output expected success message for build 46"

        # Verify runtime.conf now has version=46
        with open("/home/user/app/runtime.conf", 'r') as f:
            content = f.read()
        assert "version=46" in content, \
            "After deploying build 46, runtime.conf should contain version=46"

    def test_redeploy_build_47_after_46(self):
        """After testing build 46, redeploy build 47 to leave system in expected state."""
        # First deploy 46 to ensure we're testing the full cycle
        subprocess.run(
            ["./deploy.sh", "46"],
            cwd="/home/user/releases",
            capture_output=True,
            text=True
        )

        # Now deploy 47
        result = subprocess.run(
            ["./deploy.sh", "47"],
            cwd="/home/user/releases",
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Redeploying build 47 failed with code {result.returncode}. " \
            f"Stderr: {result.stderr}"

        # Verify runtime.conf has version=47
        with open("/home/user/app/runtime.conf", 'r') as f:
            content = f.read()
        assert "version=47" in content, \
            "After redeploying build 47, runtime.conf should contain version=47"


class TestNoHardcodedPaths:
    """Test that the fix uses proper symlink resolution, not hardcoded paths."""

    def test_active_symlink_not_bypassed(self):
        """The active symlink should still be part of the resolution chain."""
        path = "/home/user/releases/active"
        assert os.path.islink(path), \
            "The 'active' symlink was removed - fix should preserve symlink mechanism"

        # Check that active still points to current (or something that resolves through current)
        target = os.readlink(path)
        assert "current" in target or os.path.realpath(path) == os.path.realpath("/home/user/releases/current"), \
            f"The 'active' symlink should resolve through 'current', but points to {target}"

    def test_symlink_chain_works(self):
        """The full symlink chain active -> current -> builds/47 should work."""
        # After deployment of 47, this path should resolve correctly
        active_config = "/home/user/releases/active/config/app.conf"
        current_config = "/home/user/releases/current/config/app.conf"

        # Both paths should exist and resolve to the same file
        assert os.path.exists(active_config), \
            f"Path through 'active' symlink does not resolve: {active_config}"
        assert os.path.exists(current_config), \
            f"Path through 'current' symlink does not resolve: {current_config}"

        assert os.path.realpath(active_config) == os.path.realpath(current_config), \
            "active/config/app.conf and current/config/app.conf should resolve to the same file"
