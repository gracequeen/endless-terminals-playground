# test_final_state.py
"""
Tests to validate the final state after the student has optimized the deploy script
to complete in under 10 seconds without breaking deployment functionality.
"""

import os
import subprocess
import pytest
import glob
import time
import re


# Base paths
HOME = "/home/user"
RELEASE_DIR = f"{HOME}/release"
CONF_DIR = f"{RELEASE_DIR}/conf.d"
CHECKS_DIR = f"{RELEASE_DIR}/checks"
APP_DIR = f"{RELEASE_DIR}/app"
STAGING_DIR = f"{RELEASE_DIR}/staging"
DEPLOY_SCRIPT = f"{RELEASE_DIR}/deploy.sh"


class TestDeployScriptPerformance:
    """Test that the deploy script now completes in under 10 seconds."""

    def test_deploy_completes_under_10_seconds(self):
        """The primary requirement: deploy.sh must complete in under 10 seconds."""
        # Clean up staging directory if it exists from previous runs
        if os.path.isdir(STAGING_DIR):
            subprocess.run(['rm', '-rf', STAGING_DIR], check=False)

        start_time = time.time()
        result = subprocess.run(
            ['bash', DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60  # Safety timeout
        )
        elapsed_time = time.time() - start_time

        assert result.returncode == 0, \
            f"Deploy script failed with exit code {result.returncode}.\nStderr: {result.stderr}\nStdout: {result.stdout}"
        assert elapsed_time < 10, \
            f"Deploy script took {elapsed_time:.2f} seconds, which exceeds the 10 second requirement"

    def test_deploy_exits_zero(self):
        """Deploy script must exit with code 0."""
        result = subprocess.run(
            ['bash', DEPLOY_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, \
            f"Deploy script exited with code {result.returncode}, expected 0.\nStderr: {result.stderr}"


class TestDeploymentArtifacts:
    """Test that deployment produces the expected artifacts."""

    def test_staging_directory_created(self):
        """Staging directory must exist after deployment."""
        # Run deploy first
        subprocess.run(['bash', DEPLOY_SCRIPT], capture_output=True, timeout=60)
        assert os.path.isdir(STAGING_DIR), \
            f"Staging directory {STAGING_DIR} was not created by deploy script"

    def test_manifest_file_exists(self):
        """Manifest file must exist in staging after deployment."""
        subprocess.run(['bash', DEPLOY_SCRIPT], capture_output=True, timeout=60)
        manifest_path = os.path.join(STAGING_DIR, "manifest.txt")
        assert os.path.isfile(manifest_path), \
            f"Manifest file {manifest_path} was not created by deploy script"

    def test_manifest_contains_app_name(self):
        """Manifest must contain APP_NAME."""
        subprocess.run(['bash', DEPLOY_SCRIPT], capture_output=True, timeout=60)
        manifest_path = os.path.join(STAGING_DIR, "manifest.txt")
        with open(manifest_path, 'r') as f:
            content = f.read()
        # Check for APP_NAME or the actual app name value
        assert 'APP_NAME' in content or 'app' in content.lower(), \
            f"Manifest does not contain APP_NAME. Content: {content}"

    def test_manifest_contains_version(self):
        """Manifest must contain VERSION."""
        subprocess.run(['bash', DEPLOY_SCRIPT], capture_output=True, timeout=60)
        manifest_path = os.path.join(STAGING_DIR, "manifest.txt")
        with open(manifest_path, 'r') as f:
            content = f.read()
        # Check for VERSION or version number pattern
        assert 'VERSION' in content or re.search(r'\d+\.\d+', content), \
            f"Manifest does not contain VERSION. Content: {content}"

    def test_manifest_contains_timestamp(self):
        """Manifest must contain a timestamp."""
        subprocess.run(['bash', DEPLOY_SCRIPT], capture_output=True, timeout=60)
        manifest_path = os.path.join(STAGING_DIR, "manifest.txt")
        with open(manifest_path, 'r') as f:
            content = f.read()
        # Check for common timestamp patterns (date, time, epoch)
        has_timestamp = (
            re.search(r'\d{4}-\d{2}-\d{2}', content) or  # ISO date
            re.search(r'\d{2}:\d{2}:\d{2}', content) or  # Time
            re.search(r'\d{10,}', content) or  # Epoch timestamp
            'date' in content.lower() or
            'time' in content.lower()
        )
        assert has_timestamp, \
            f"Manifest does not appear to contain a timestamp. Content: {content}"

    def test_tarball_created_or_copied(self):
        """A tarball should be created and content copied to staging."""
        subprocess.run(['bash', DEPLOY_SCRIPT], capture_output=True, timeout=60)
        # Check for tarball in staging or release directory
        tarballs_staging = glob.glob(f"{STAGING_DIR}/*.tar*") + glob.glob(f"{STAGING_DIR}/*.tgz")
        tarballs_release = glob.glob(f"{RELEASE_DIR}/*.tar*") + glob.glob(f"{RELEASE_DIR}/*.tgz")
        # Or check that app content was copied
        staging_has_content = os.path.isdir(STAGING_DIR) and len(os.listdir(STAGING_DIR)) > 0

        assert tarballs_staging or tarballs_release or staging_has_content, \
            "No tarball found and staging directory is empty - deployment may have failed"


class TestConfigFilesPreserved:
    """Test that config files are preserved and still functional."""

    def test_conf_d_still_sourced(self):
        """Deploy script must still source files from conf.d/."""
        with open(DEPLOY_SCRIPT, 'r') as f:
            content = f.read()
        assert 'conf.d' in content, \
            "Deploy script no longer references conf.d directory - sourcing loop may have been removed"
        # Check for sourcing pattern
        has_sourcing = 'source' in content or re.search(r'\.\s+["\']?\$', content) or re.search(r'\.\s+["\']?/', content)
        assert has_sourcing, \
            "Deploy script does not appear to source config files anymore"

    def test_40_health_conf_exists(self):
        """40-health.conf must still exist (not deleted)."""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        assert os.path.isfile(health_conf), \
            f"40-health.conf was deleted - it should be fixed, not removed"

    def test_40_health_conf_contains_health_reference(self):
        """40-health.conf must still contain health-related configuration."""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        result = subprocess.run(
            ['grep', '-l', 'HEALTH_ENDPOINTS\\|health', health_conf],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "40-health.conf no longer contains HEALTH_ENDPOINTS or health references - config was gutted instead of fixed"

    def test_health_endpoints_variable_still_defined(self):
        """HEALTH_ENDPOINTS variable should still be defined for downstream use."""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()
        assert 'HEALTH_ENDPOINTS' in content, \
            "HEALTH_ENDPOINTS variable definition was removed - it should be preserved for downstream use"

    def test_other_conf_files_unchanged(self):
        """Other conf files should still exist."""
        expected_files = [
            "00-base.conf",
            "10-paths.conf", 
            "20-services.conf",
            "30-validators.conf",
            "50-notify.conf",
        ]
        for conf_file in expected_files:
            conf_path = os.path.join(CONF_DIR, conf_file)
            assert os.path.isfile(conf_path), \
                f"Config file {conf_file} is missing - it should not have been modified or deleted"


class TestCheckScriptsUnchanged:
    """Test that check scripts are preserved."""

    def test_check_scripts_exist(self):
        """All check scripts should still exist."""
        expected_scripts = ["disk_space.sh", "permissions.sh", "syntax_check.sh"]
        for script in expected_scripts:
            script_path = os.path.join(CHECKS_DIR, script)
            assert os.path.isfile(script_path), \
                f"Check script {script} is missing - check scripts should not be modified"


class TestAppDirectoryUnchanged:
    """Test that app directory is preserved."""

    def test_app_directory_exists(self):
        """App directory must still exist."""
        assert os.path.isdir(APP_DIR), \
            f"App directory {APP_DIR} is missing"

    def test_app_directory_not_empty(self):
        """App directory must still have content."""
        contents = os.listdir(APP_DIR)
        assert len(contents) > 0, \
            f"App directory {APP_DIR} is empty - content should not have been removed"


class TestVariablesStillSet:
    """Test that sourcing configs still sets required variables."""

    def test_app_name_set_after_sourcing(self):
        """APP_NAME should be set after sourcing all configs."""
        # Create a test script that sources configs and echoes APP_NAME
        test_script = """
        set -e
        for conf in /home/user/release/conf.d/*.conf; do
            source "$conf" 2>/dev/null || true
        done
        echo "APP_NAME=$APP_NAME"
        """
        result = subprocess.run(
            ['bash', '-c', test_script],
            capture_output=True,
            text=True,
            timeout=15  # Should be fast now
        )
        assert 'APP_NAME=' in result.stdout, \
            f"APP_NAME not set after sourcing configs. Output: {result.stdout}, Stderr: {result.stderr}"
        # Check it has a value
        match = re.search(r'APP_NAME=(\S+)', result.stdout)
        assert match and match.group(1), \
            f"APP_NAME is empty after sourcing configs"

    def test_version_set_after_sourcing(self):
        """VERSION should be set after sourcing all configs."""
        test_script = """
        set -e
        for conf in /home/user/release/conf.d/*.conf; do
            source "$conf" 2>/dev/null || true
        done
        echo "VERSION=$VERSION"
        """
        result = subprocess.run(
            ['bash', '-c', test_script],
            capture_output=True,
            text=True,
            timeout=15
        )
        assert 'VERSION=' in result.stdout, \
            f"VERSION not set after sourcing configs. Output: {result.stdout}"


class TestBlockingCurlsEliminated:
    """Test that the blocking curl calls have been eliminated or deferred."""

    def test_sourcing_configs_is_fast(self):
        """Sourcing all config files should now be fast (under 5 seconds)."""
        test_script = """
        for conf in /home/user/release/conf.d/*.conf; do
            source "$conf"
        done
        echo "done"
        """
        start_time = time.time()
        result = subprocess.run(
            ['bash', '-c', test_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        elapsed = time.time() - start_time

        assert elapsed < 5, \
            f"Sourcing config files took {elapsed:.2f} seconds - blocking curls may not have been fixed"
        assert result.returncode == 0, \
            f"Sourcing config files failed: {result.stderr}"

    def test_curl_timeout_not_just_zeroed(self):
        """Fix should not just set --connect-timeout to 0."""
        health_conf = os.path.join(CONF_DIR, "40-health.conf")
        with open(health_conf, 'r') as f:
            content = f.read()
        # If curl is still there, timeout shouldn't be 0
        if 'curl' in content:
            # Check for --connect-timeout 0 pattern which would be a lazy fix
            zero_timeout = re.search(r'--connect-timeout\s+0\b', content)
            # This is acceptable if curls are in a function or background
            if zero_timeout:
                # Verify curls are not blocking (in function or backgrounded)
                has_function = 'function ' in content or re.search(r'\w+\s*\(\)\s*\{', content)
                has_background = '&' in content and 'curl' in content
                assert has_function or has_background, \
                    "Curl timeout set to 0 without deferring execution - this is not a proper fix"
