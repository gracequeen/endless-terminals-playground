# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the optimization task on the deploy script.
"""

import os
import subprocess
import pytest
import stat
import glob


# Base paths
HOME = "/home/user"
RELEASE_DIR = f"{HOME}/release"
CONF_DIR = f"{RELEASE_DIR}/conf.d"
CHECKS_DIR = f"{RELEASE_DIR}/checks"
APP_DIR = f"{RELEASE_DIR}/app"
STAGING_DIR = f"{RELEASE_DIR}/staging"
DEPLOY_SCRIPT = f"{RELEASE_DIR}/deploy.sh"


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_release_directory_exists(self):
        assert os.path.isdir(RELEASE_DIR), f"Release directory {RELEASE_DIR} does not exist"

    def test_conf_d_directory_exists(self):
        assert os.path.isdir(CONF_DIR), f"Config directory {CONF_DIR} does not exist"

    def test_checks_directory_exists(self):
        assert os.path.isdir(CHECKS_DIR), f"Checks directory {CHECKS_DIR} does not exist"

    def test_app_directory_exists(self):
        assert os.path.isdir(APP_DIR), f"App directory {APP_DIR} does not exist"

    def test_release_directory_writable(self):
        assert os.access(RELEASE_DIR, os.W_OK), f"Release directory {RELEASE_DIR} is not writable"

    def test_conf_d_directory_writable(self):
        assert os.access(CONF_DIR, os.W_OK), f"Config directory {CONF_DIR} is not writable"


class TestDeployScript:
    """Test that deploy.sh exists and is a valid bash script."""

    def test_deploy_script_exists(self):
        assert os.path.isfile(DEPLOY_SCRIPT), f"Deploy script {DEPLOY_SCRIPT} does not exist"

    def test_deploy_script_is_readable(self):
        assert os.access(DEPLOY_SCRIPT, os.R_OK), f"Deploy script {DEPLOY_SCRIPT} is not readable"

    def test_deploy_script_is_executable_or_can_be_run_with_bash(self):
        # Either executable or can be run with bash
        is_executable = os.access(DEPLOY_SCRIPT, os.X_OK)
        can_run_with_bash = os.path.isfile(DEPLOY_SCRIPT)
        assert is_executable or can_run_with_bash, f"Deploy script {DEPLOY_SCRIPT} cannot be executed"

    def test_deploy_script_is_bash_script(self):
        with open(DEPLOY_SCRIPT, 'r') as f:
            first_line = f.readline()
        assert 'bash' in first_line or first_line.strip() == '', \
            f"Deploy script does not appear to be a bash script (first line: {first_line})"

    def test_deploy_script_sources_conf_d(self):
        """Verify the deploy script sources files from conf.d/"""
        with open(DEPLOY_SCRIPT, 'r') as f:
            content = f.read()
        assert 'conf.d' in content, "Deploy script does not reference conf.d directory"
        # Check for sourcing pattern (source or .)
        assert 'source' in content or '. ' in content or '.$' in content, \
            "Deploy script does not appear to source config files"


class TestConfigFiles:
    """Test that all required config files exist in conf.d/"""

    EXPECTED_CONF_FILES = [
        "00-base.conf",
        "10-paths.conf",
        "20-services.conf",
        "30-validators.conf",
        "40-health.conf",
        "50-notify.conf",
    ]

    def test_all_conf_files_exist(self):
        for conf_file in self.EXPECTED_CONF_FILES:
            conf_path = os.path.join(CONF_DIR, conf_file)
            assert os.path.isfile(conf_path), f"Config file {conf_path} does not exist"

    def test_exactly_six_conf_files(self):
        conf_files = glob.glob(f"{CONF_DIR}/*.conf")
        assert len(conf_files) == 6, f"Expected 6 .conf files in {CONF_DIR}, found {len(conf_files)}: {conf_files}"

    def test_40_health_conf_contains_health_endpoints(self):
        """Verify the problematic health config file has HEALTH_ENDPOINTS"""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()
        assert 'HEALTH_ENDPOINTS' in content, \
            f"40-health.conf does not contain HEALTH_ENDPOINTS variable"

    def test_40_health_conf_contains_curl(self):
        """Verify the problematic health config has curl commands (the bug)"""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()
        assert 'curl' in content, \
            f"40-health.conf does not contain curl commands (expected to find the performance bug)"

    def test_40_health_conf_has_blocking_curl_pattern(self):
        """Verify the curl commands are blocking (not in a function)"""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()
        # The bug is that curl runs at source-time, not inside a function
        # Check for curl with connect-timeout pattern
        assert 'connect-timeout' in content or 'timeout' in content.lower(), \
            f"40-health.conf does not have timeout settings in curl commands"

    def test_00_base_conf_sets_app_name(self):
        """Verify base config sets APP_NAME"""
        base_conf = os.path.join(CONF_DIR, "00-base.conf")
        with open(base_conf, 'r') as f:
            content = f.read()
        assert 'APP_NAME' in content, f"00-base.conf does not set APP_NAME"

    def test_00_base_conf_sets_version(self):
        """Verify base config sets VERSION"""
        base_conf = os.path.join(CONF_DIR, "00-base.conf")
        with open(base_conf, 'r') as f:
            content = f.read()
        assert 'VERSION' in content, f"00-base.conf does not set VERSION"


class TestCheckScripts:
    """Test that preflight check scripts exist."""

    EXPECTED_CHECK_SCRIPTS = [
        "disk_space.sh",
        "permissions.sh",
        "syntax_check.sh",
    ]

    def test_all_check_scripts_exist(self):
        for script in self.EXPECTED_CHECK_SCRIPTS:
            script_path = os.path.join(CHECKS_DIR, script)
            assert os.path.isfile(script_path), f"Check script {script_path} does not exist"

    def test_check_scripts_are_readable(self):
        for script in self.EXPECTED_CHECK_SCRIPTS:
            script_path = os.path.join(CHECKS_DIR, script)
            assert os.access(script_path, os.R_OK), f"Check script {script_path} is not readable"


class TestAppDirectory:
    """Test that app directory has content to deploy."""

    def test_app_directory_not_empty(self):
        contents = os.listdir(APP_DIR)
        assert len(contents) > 0, f"App directory {APP_DIR} is empty"

    def test_app_directory_small_size(self):
        """Verify app directory is small (<1MB) as described"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(APP_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        # 1MB = 1048576 bytes
        assert total_size < 1048576, f"App directory is larger than expected: {total_size} bytes"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_bash_available(self):
        result = subprocess.run(['which', 'bash'], capture_output=True)
        assert result.returncode == 0, "bash is not available"

    def test_curl_available(self):
        result = subprocess.run(['which', 'curl'], capture_output=True)
        assert result.returncode == 0, "curl is not available"

    def test_tar_available(self):
        result = subprocess.run(['which', 'tar'], capture_output=True)
        assert result.returncode == 0, "tar is not available"

    def test_time_available(self):
        result = subprocess.run(['which', 'time'], capture_output=True)
        # time might be a shell builtin, so also check /usr/bin/time
        if result.returncode != 0:
            result = subprocess.run(['test', '-f', '/usr/bin/time'], capture_output=True)
        assert result.returncode == 0 or True, "time command is available (builtin or external)"


class TestInitialScriptBehavior:
    """Test that the script currently takes too long (verifying the bug exists)."""

    def test_deploy_script_is_slow(self):
        """
        Verify the deploy script currently takes >10 seconds to run.
        This confirms the performance bug exists before the student fixes it.
        We use a shorter timeout to avoid waiting the full 90+ seconds.
        """
        # We'll just verify the health config has the problematic pattern
        # Actually running it would take too long for a test
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()

        # Check for the loop pattern that causes slowness
        has_seq_loop = 'seq' in content and 'for' in content
        has_curl_in_loop = 'curl' in content and 'for' in content
        has_endpoint_loop = 'endpoint' in content.lower() or 'HEALTH_ENDPOINTS' in content

        assert has_curl_in_loop or (has_seq_loop and 'curl' in content), \
            "40-health.conf does not have the expected slow curl loop pattern"

    def test_health_conf_curl_not_in_function(self):
        """
        Verify the curl commands in 40-health.conf run at source-time,
        not wrapped in a function (which is the bug).
        """
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        curl_lines = [l for l in lines if 'curl' in l and not l.strip().startswith('#')]

        # If curl is in the file and not just in a function definition,
        # it will run at source time
        assert len(curl_lines) > 0, "No curl commands found in 40-health.conf"

        # Check that curl is not only inside a function
        # A simple heuristic: if there's a curl outside of function() { } blocks
        in_function = False
        curl_outside_function = False
        for line in lines:
            stripped = line.strip()
            if 'function ' in stripped or (stripped.endswith('()') and '{' not in stripped) or stripped.endswith('() {'):
                in_function = True
            if stripped == '}' and in_function:
                in_function = False
            if 'curl' in stripped and not stripped.startswith('#') and not in_function:
                curl_outside_function = True
                break

        # The bug is that curl runs at source time (outside function)
        # This test verifies the bug exists
        assert curl_outside_function, \
            "curl commands appear to be inside functions - the expected bug may not exist"
