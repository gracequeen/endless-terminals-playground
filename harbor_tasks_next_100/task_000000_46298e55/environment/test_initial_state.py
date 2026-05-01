# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student fixes
the deploy script issue for build 47.
"""

import os
import pytest
import stat


class TestDirectoryStructure:
    """Test that the required directory structure exists."""

    def test_releases_directory_exists(self):
        """The /home/user/releases directory must exist."""
        path = "/home/user/releases"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_builds_directory_exists(self):
        """The /home/user/releases/builds directory must exist."""
        path = "/home/user/releases/builds"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_build_46_directory_exists(self):
        """The /home/user/releases/builds/46 directory must exist."""
        path = "/home/user/releases/builds/46"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_build_47_directory_exists(self):
        """The /home/user/releases/builds/47 directory must exist."""
        path = "/home/user/releases/builds/47"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_app_directory_exists(self):
        """The /home/user/app directory must exist."""
        path = "/home/user/app"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestDeployScript:
    """Test that the deploy script exists and is executable."""

    def test_deploy_script_exists(self):
        """The deploy.sh script must exist."""
        path = "/home/user/releases/deploy.sh"
        assert os.path.isfile(path), f"Deploy script {path} does not exist"

    def test_deploy_script_is_executable(self):
        """The deploy.sh script must be executable."""
        path = "/home/user/releases/deploy.sh"
        assert os.access(path, os.X_OK), f"Deploy script {path} is not executable"

    def test_deploy_script_is_bash(self):
        """The deploy.sh script should be a bash script."""
        path = "/home/user/releases/deploy.sh"
        with open(path, 'r') as f:
            first_line = f.readline()
        assert first_line.startswith("#!/bin/bash"), \
            f"Deploy script {path} does not start with #!/bin/bash"


class TestBuild46Structure:
    """Test that build 46 has the correct structure (with config subdirectory)."""

    def test_build_46_config_directory_exists(self):
        """Build 46 should have a config subdirectory."""
        path = "/home/user/releases/builds/46/config"
        assert os.path.isdir(path), \
            f"Build 46 config directory {path} does not exist"

    def test_build_46_app_conf_exists(self):
        """Build 46 should have app.conf in the config subdirectory."""
        path = "/home/user/releases/builds/46/config/app.conf"
        assert os.path.isfile(path), \
            f"Build 46 config file {path} does not exist"

    def test_build_46_app_conf_content(self):
        """Build 46 app.conf should contain version=46."""
        path = "/home/user/releases/builds/46/config/app.conf"
        with open(path, 'r') as f:
            content = f.read()
        assert "version=46" in content, \
            f"Build 46 config file {path} does not contain 'version=46'"


class TestBuild47Structure:
    """Test that build 47 has the INCORRECT structure (the bug)."""

    def test_build_47_app_conf_in_wrong_location(self):
        """Build 47 has app.conf directly in the build directory (bug)."""
        path = "/home/user/releases/builds/47/app.conf"
        assert os.path.isfile(path), \
            f"Build 47 config file {path} does not exist (expected in wrong location)"

    def test_build_47_app_conf_content(self):
        """Build 47 app.conf should contain version=47."""
        path = "/home/user/releases/builds/47/app.conf"
        with open(path, 'r') as f:
            content = f.read()
        assert "version=47" in content, \
            f"Build 47 config file {path} does not contain 'version=47'"

    def test_build_47_config_directory_missing(self):
        """Build 47 should NOT have a config subdirectory (this is the bug)."""
        path = "/home/user/releases/builds/47/config"
        assert not os.path.exists(path), \
            f"Build 47 config directory {path} already exists - bug may already be fixed"


class TestSymlinks:
    """Test that the symlink structure exists."""

    def test_current_symlink_exists(self):
        """The 'current' symlink must exist."""
        path = "/home/user/releases/current"
        assert os.path.islink(path), \
            f"Symlink {path} does not exist or is not a symlink"

    def test_current_symlink_points_to_build_46(self):
        """The 'current' symlink should point to builds/46."""
        path = "/home/user/releases/current"
        target = os.readlink(path)
        assert "46" in target or target.endswith("builds/46"), \
            f"Symlink {path} points to {target}, expected it to point to builds/46"

    def test_active_symlink_exists(self):
        """The 'active' symlink must exist."""
        path = "/home/user/releases/active"
        assert os.path.islink(path), \
            f"Symlink {path} does not exist or is not a symlink"

    def test_active_symlink_points_to_current(self):
        """The 'active' symlink should point to 'current'."""
        path = "/home/user/releases/active"
        target = os.readlink(path)
        assert "current" in target, \
            f"Symlink {path} points to {target}, expected it to point to 'current'"


class TestInitialRuntimeState:
    """Test that runtime.conf does not exist initially."""

    def test_runtime_conf_does_not_exist(self):
        """The runtime.conf should not exist initially."""
        path = "/home/user/app/runtime.conf"
        assert not os.path.exists(path), \
            f"Runtime config {path} already exists - should not exist initially"


class TestDeployScriptContent:
    """Test that the deploy script has the expected content structure."""

    def test_deploy_script_reads_from_active_config(self):
        """The deploy script should read config from /home/user/releases/active/config/app.conf."""
        path = "/home/user/releases/deploy.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "/home/user/releases/active/config/app.conf" in content, \
            f"Deploy script does not reference the expected config path"

    def test_deploy_script_updates_current_symlink(self):
        """The deploy script should update the 'current' symlink."""
        path = "/home/user/releases/deploy.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "ln" in content and "current" in content, \
            f"Deploy script does not appear to update the 'current' symlink"

    def test_deploy_script_copies_to_runtime(self):
        """The deploy script should copy config to /home/user/app/runtime.conf."""
        path = "/home/user/releases/deploy.sh"
        with open(path, 'r') as f:
            content = f.read()
        assert "/home/user/app/runtime.conf" in content, \
            f"Deploy script does not reference the runtime config destination"


class TestPermissions:
    """Test that necessary directories are writable."""

    def test_releases_directory_writable(self):
        """The releases directory should be writable."""
        path = "/home/user/releases"
        assert os.access(path, os.W_OK), \
            f"Directory {path} is not writable"

    def test_builds_directory_writable(self):
        """The builds directory should be writable."""
        path = "/home/user/releases/builds"
        assert os.access(path, os.W_OK), \
            f"Directory {path} is not writable"

    def test_build_47_directory_writable(self):
        """The build 47 directory should be writable."""
        path = "/home/user/releases/builds/47"
        assert os.access(path, os.W_OK), \
            f"Directory {path} is not writable"

    def test_app_directory_writable(self):
        """The app directory should be writable."""
        path = "/home/user/app"
        assert os.access(path, os.W_OK), \
            f"Directory {path} is not writable"
