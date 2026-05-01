# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student
performs the policy-as-code pipeline fix task.
"""

import os
import subprocess
import stat
import pytest

POLICYGATE_DIR = "/home/user/policygate"
BASELINE_DIR = os.path.join(POLICYGATE_DIR, "baseline")
INCOMING_DIR = os.path.join(POLICYGATE_DIR, "incoming")
LIB_DIR = os.path.join(POLICYGATE_DIR, "lib")


class TestPolicygateDirectoryStructure:
    """Test that the main policygate directory and its structure exist."""

    def test_policygate_directory_exists(self):
        assert os.path.isdir(POLICYGATE_DIR), \
            f"Directory {POLICYGATE_DIR} does not exist"

    def test_validate_sh_exists(self):
        validate_sh = os.path.join(POLICYGATE_DIR, "validate.sh")
        assert os.path.isfile(validate_sh), \
            f"validate.sh not found at {validate_sh}"

    def test_validate_sh_is_executable(self):
        validate_sh = os.path.join(POLICYGATE_DIR, "validate.sh")
        assert os.path.isfile(validate_sh), \
            f"validate.sh not found at {validate_sh}"
        mode = os.stat(validate_sh).st_mode
        assert mode & stat.S_IXUSR, \
            f"validate.sh at {validate_sh} is not executable"

    def test_policy_md_exists(self):
        policy_md = os.path.join(POLICYGATE_DIR, "policy.md")
        assert os.path.isfile(policy_md), \
            f"policy.md not found at {policy_md}"

    def test_allowlist_txt_exists(self):
        allowlist = os.path.join(POLICYGATE_DIR, "allowlist.txt")
        assert os.path.isfile(allowlist), \
            f"allowlist.txt not found at {allowlist}"

    def test_baseline_directory_exists(self):
        assert os.path.isdir(BASELINE_DIR), \
            f"baseline/ directory not found at {BASELINE_DIR}"

    def test_incoming_directory_exists(self):
        assert os.path.isdir(INCOMING_DIR), \
            f"incoming/ directory not found at {INCOMING_DIR}"

    def test_lib_directory_exists(self):
        assert os.path.isdir(LIB_DIR), \
            f"lib/ directory not found at {LIB_DIR}"

    def test_diff_check_py_exists(self):
        diff_check = os.path.join(LIB_DIR, "diff_check.py")
        assert os.path.isfile(diff_check), \
            f"lib/diff_check.py not found at {diff_check}"


class TestBaselineContents:
    """Test that baseline directory contains the expected files."""

    def test_baseline_nginx_conf_exists(self):
        nginx_conf = os.path.join(BASELINE_DIR, "etc/nginx/nginx.conf")
        assert os.path.isfile(nginx_conf), \
            f"baseline/etc/nginx/nginx.conf not found at {nginx_conf}"

    def test_baseline_config_yaml_exists(self):
        config_yaml = os.path.join(BASELINE_DIR, "etc/app/config.yaml")
        assert os.path.isfile(config_yaml), \
            f"baseline/etc/app/config.yaml not found at {config_yaml}"

    def test_baseline_shadow_exists(self):
        shadow = os.path.join(BASELINE_DIR, "etc/shadow")
        assert os.path.isfile(shadow), \
            f"baseline/etc/shadow not found at {shadow}"

    def test_baseline_var_log_keep_exists(self):
        keep = os.path.join(BASELINE_DIR, "var/log/.keep")
        assert os.path.isfile(keep), \
            f"baseline/var/log/.keep not found at {keep}"

    def test_baseline_app_binary_exists(self):
        app = os.path.join(BASELINE_DIR, "usr/local/bin/app")
        assert os.path.isfile(app), \
            f"baseline/usr/local/bin/app not found at {app}"


class TestIncomingPatches:
    """Test that incoming directory contains the expected patch files."""

    def test_vendor_nginx_fix_patch_exists(self):
        patch = os.path.join(INCOMING_DIR, "vendor-nginx-fix.patch")
        assert os.path.isfile(patch), \
            f"vendor-nginx-fix.patch not found at {patch}"

    def test_vendor_config_update_patch_exists(self):
        patch = os.path.join(INCOMING_DIR, "vendor-config-update.patch")
        assert os.path.isfile(patch), \
            f"vendor-config-update.patch not found at {patch}"

    def test_vendor_backdoor_patch_exists(self):
        patch = os.path.join(INCOMING_DIR, "vendor-backdoor.patch")
        assert os.path.isfile(patch), \
            f"vendor-backdoor.patch not found at {patch}"

    def test_exactly_three_patches_in_incoming(self):
        patches = [f for f in os.listdir(INCOMING_DIR) if f.endswith('.patch')]
        assert len(patches) == 3, \
            f"Expected exactly 3 .patch files in incoming/, found {len(patches)}: {patches}"


class TestAllowlistContent:
    """Test that allowlist.txt has the expected content."""

    def test_allowlist_contains_nginx_pattern(self):
        allowlist = os.path.join(POLICYGATE_DIR, "allowlist.txt")
        with open(allowlist, 'r') as f:
            content = f.read()
        assert "etc/nginx/" in content or "etc/nginx/*" in content, \
            "allowlist.txt should contain pattern for etc/nginx/"

    def test_allowlist_contains_app_pattern(self):
        allowlist = os.path.join(POLICYGATE_DIR, "allowlist.txt")
        with open(allowlist, 'r') as f:
            content = f.read()
        assert "etc/app/" in content or "etc/app/*" in content, \
            "allowlist.txt should contain pattern for etc/app/"

    def test_allowlist_contains_usr_local_bin_pattern(self):
        allowlist = os.path.join(POLICYGATE_DIR, "allowlist.txt")
        with open(allowlist, 'r') as f:
            content = f.read()
        assert "usr/local/bin/" in content or "usr/local/bin/*" in content, \
            "allowlist.txt should contain pattern for usr/local/bin/"

    def test_allowlist_does_not_contain_shadow(self):
        allowlist = os.path.join(POLICYGATE_DIR, "allowlist.txt")
        with open(allowlist, 'r') as f:
            content = f.read()
        # etc/shadow should NOT be in the allowlist
        assert "etc/shadow" not in content, \
            "allowlist.txt should NOT contain etc/shadow (that's the backdoor path)"


class TestPatchContent:
    """Test that patches have the expected characteristics (CRLF issue)."""

    def test_nginx_patch_targets_nginx_conf(self):
        patch = os.path.join(INCOMING_DIR, "vendor-nginx-fix.patch")
        with open(patch, 'r') as f:
            content = f.read()
        assert "nginx.conf" in content or "etc/nginx" in content, \
            "vendor-nginx-fix.patch should target nginx.conf"

    def test_config_patch_targets_config_yaml(self):
        patch = os.path.join(INCOMING_DIR, "vendor-config-update.patch")
        with open(patch, 'r') as f:
            content = f.read()
        assert "config.yaml" in content or "etc/app" in content, \
            "vendor-config-update.patch should target config.yaml"

    def test_backdoor_patch_targets_shadow(self):
        patch = os.path.join(INCOMING_DIR, "vendor-backdoor.patch")
        with open(patch, 'r') as f:
            content = f.read()
        assert "shadow" in content or "etc/shadow" in content, \
            "vendor-backdoor.patch should target etc/shadow"

    def test_nginx_patch_contains_crlf_content(self):
        """The nginx patch should have CRLF in the content being patched in."""
        patch = os.path.join(INCOMING_DIR, "vendor-nginx-fix.patch")
        with open(patch, 'rb') as f:
            content = f.read()
        # CRLF is \r\n (0x0d 0x0a)
        assert b'\r\n' in content, \
            "vendor-nginx-fix.patch should contain CRLF line endings in patched content (this is the bug)"

    def test_config_patch_contains_crlf_content(self):
        """The config patch should have CRLF in the content being patched in."""
        patch = os.path.join(INCOMING_DIR, "vendor-config-update.patch")
        with open(patch, 'rb') as f:
            content = f.read()
        assert b'\r\n' in content, \
            "vendor-config-update.patch should contain CRLF line endings in patched content (this is the bug)"


class TestBaselineLineEndings:
    """Test that baseline files have LF line endings (not CRLF)."""

    def test_baseline_nginx_conf_has_lf_endings(self):
        nginx_conf = os.path.join(BASELINE_DIR, "etc/nginx/nginx.conf")
        with open(nginx_conf, 'rb') as f:
            content = f.read()
        # Should have LF but not CRLF
        if b'\n' in content:
            assert b'\r\n' not in content, \
                "baseline/etc/nginx/nginx.conf should have LF endings, not CRLF"

    def test_baseline_config_yaml_has_lf_endings(self):
        config_yaml = os.path.join(BASELINE_DIR, "etc/app/config.yaml")
        with open(config_yaml, 'rb') as f:
            content = f.read()
        if b'\n' in content:
            assert b'\r\n' not in content, \
                "baseline/etc/app/config.yaml should have LF endings, not CRLF"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_patch_command_available(self):
        result = subprocess.run(['which', 'patch'], capture_output=True)
        assert result.returncode == 0, \
            "GNU patch command is not available"

    def test_diff_command_available(self):
        result = subprocess.run(['which', 'diff'], capture_output=True)
        assert result.returncode == 0, \
            "GNU diff command is not available"

    def test_python3_available(self):
        result = subprocess.run(['which', 'python3'], capture_output=True)
        assert result.returncode == 0, \
            "python3 is not available"


class TestValidateShContent:
    """Test that validate.sh has expected structure."""

    def test_validate_sh_calls_patch(self):
        validate_sh = os.path.join(POLICYGATE_DIR, "validate.sh")
        with open(validate_sh, 'r') as f:
            content = f.read()
        assert "patch" in content, \
            "validate.sh should call patch command"

    def test_validate_sh_references_diff_check(self):
        validate_sh = os.path.join(POLICYGATE_DIR, "validate.sh")
        with open(validate_sh, 'r') as f:
            content = f.read()
        assert "diff_check" in content or "lib/" in content, \
            "validate.sh should reference lib/diff_check.py"

    def test_validate_sh_references_incoming(self):
        validate_sh = os.path.join(POLICYGATE_DIR, "validate.sh")
        with open(validate_sh, 'r') as f:
            content = f.read()
        assert "incoming" in content, \
            "validate.sh should reference incoming/ directory"


class TestDiffCheckPyContent:
    """Test that diff_check.py exists and has expected structure."""

    def test_diff_check_is_python(self):
        diff_check = os.path.join(LIB_DIR, "diff_check.py")
        with open(diff_check, 'r') as f:
            content = f.read()
        # Should contain Python-like syntax
        assert "def " in content or "import " in content, \
            "lib/diff_check.py should be a Python file"

    def test_diff_check_uses_diff(self):
        diff_check = os.path.join(LIB_DIR, "diff_check.py")
        with open(diff_check, 'r') as f:
            content = f.read()
        assert "diff" in content.lower(), \
            "lib/diff_check.py should use diff for comparison"


class TestDirectoryWritable:
    """Test that policygate directory is writable."""

    def test_policygate_is_writable(self):
        assert os.access(POLICYGATE_DIR, os.W_OK), \
            f"{POLICYGATE_DIR} is not writable"

    def test_lib_is_writable(self):
        assert os.access(LIB_DIR, os.W_OK), \
            f"{LIB_DIR} is not writable"


class TestCurrentBuggyBehavior:
    """Test that the current validate.sh exhibits the buggy behavior (all three fail)."""

    def test_validate_sh_currently_fails_all_patches(self):
        """
        Running validate.sh should currently reject all three patches
        (this is the bug we need to fix).
        """
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        output = result.stdout + result.stderr

        # The current buggy behavior should show failures for all patches
        # We check that it runs without crashing and produces some output
        assert result.returncode != 0 or "fail" in output.lower() or "reject" in output.lower() or "unauthorized" in output.lower(), \
            "validate.sh should currently be exhibiting buggy behavior (rejecting patches)"
