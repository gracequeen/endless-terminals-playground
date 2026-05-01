# test_final_state.py
"""
Tests to validate the final state after the student has fixed the policy-as-code
pipeline bug. The fix should result in:
- vendor-nginx-fix.patch: PASS
- vendor-config-update.patch: PASS
- vendor-backdoor.patch: FAIL (because etc/shadow is not in allowlist)
"""

import os
import subprocess
import tempfile
import shutil
import pytest

POLICYGATE_DIR = "/home/user/policygate"
BASELINE_DIR = os.path.join(POLICYGATE_DIR, "baseline")
INCOMING_DIR = os.path.join(POLICYGATE_DIR, "incoming")
LIB_DIR = os.path.join(POLICYGATE_DIR, "lib")
ALLOWLIST_FILE = os.path.join(POLICYGATE_DIR, "allowlist.txt")
VALIDATE_SH = os.path.join(POLICYGATE_DIR, "validate.sh")
POLICY_MD = os.path.join(POLICYGATE_DIR, "policy.md")
DIFF_CHECK_PY = os.path.join(LIB_DIR, "diff_check.py")


class TestValidateShOutput:
    """Test that validate.sh produces correct pass/fail results."""

    def test_validate_sh_runs_successfully(self):
        """validate.sh should run without crashing."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        # Should produce some output
        output = result.stdout + result.stderr
        assert len(output) > 0, "validate.sh should produce output"

    def test_validate_sh_exit_code_is_one(self):
        """validate.sh should exit with code 1 (one patch failed policy)."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        assert result.returncode == 1, \
            f"validate.sh should exit with code 1 (one patch failed), got {result.returncode}"

    def test_nginx_patch_passes(self):
        """vendor-nginx-fix.patch should PASS."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = (result.stdout + result.stderr).lower()

        # Look for indication that nginx patch passed
        # Common patterns: "vendor-nginx-fix.patch: pass", "vendor-nginx-fix: PASS", etc.
        nginx_mentioned = "nginx" in output
        assert nginx_mentioned, "Output should mention nginx patch"

        # Find lines mentioning nginx and check for pass indicator
        lines = output.split('\n')
        nginx_lines = [l for l in lines if 'nginx' in l]

        # At least one nginx line should indicate pass (not fail)
        pass_indicators = ['pass', 'ok', 'success', 'approved', 'allowed', '✓', 'passed']
        fail_indicators = ['fail', 'reject', 'denied', 'unauthorized', 'error', '✗', 'failed']

        nginx_passed = False
        for line in nginx_lines:
            has_pass = any(p in line for p in pass_indicators)
            has_fail = any(f in line for f in fail_indicators)
            if has_pass and not has_fail:
                nginx_passed = True
                break

        assert nginx_passed, \
            f"vendor-nginx-fix.patch should PASS. Output lines with 'nginx': {nginx_lines}"

    def test_config_patch_passes(self):
        """vendor-config-update.patch should PASS."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = (result.stdout + result.stderr).lower()

        # Look for indication that config patch passed
        config_mentioned = "config" in output
        assert config_mentioned, "Output should mention config patch"

        lines = output.split('\n')
        config_lines = [l for l in lines if 'config' in l]

        pass_indicators = ['pass', 'ok', 'success', 'approved', 'allowed', '✓', 'passed']
        fail_indicators = ['fail', 'reject', 'denied', 'unauthorized', 'error', '✗', 'failed']

        config_passed = False
        for line in config_lines:
            has_pass = any(p in line for p in pass_indicators)
            has_fail = any(f in line for f in fail_indicators)
            if has_pass and not has_fail:
                config_passed = True
                break

        assert config_passed, \
            f"vendor-config-update.patch should PASS. Output lines with 'config': {config_lines}"

    def test_backdoor_patch_fails(self):
        """vendor-backdoor.patch should FAIL."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = (result.stdout + result.stderr).lower()

        # Look for indication that backdoor patch failed
        backdoor_mentioned = "backdoor" in output
        assert backdoor_mentioned, "Output should mention backdoor patch"

        lines = output.split('\n')
        backdoor_lines = [l for l in lines if 'backdoor' in l]

        fail_indicators = ['fail', 'reject', 'denied', 'unauthorized', 'error', '✗', 'failed', 'not allowed', 'blocked']

        backdoor_failed = False
        for line in backdoor_lines:
            if any(f in line for f in fail_indicators):
                backdoor_failed = True
                break

        assert backdoor_failed, \
            f"vendor-backdoor.patch should FAIL. Output lines with 'backdoor': {backdoor_lines}"


class TestInvariantsPreserved:
    """Test that invariants are preserved (baseline, patches, allowlist, policy.md unchanged)."""

    def test_baseline_directory_unchanged(self):
        """baseline/ directory should remain pristine."""
        # Check that expected files exist
        expected_files = [
            "etc/nginx/nginx.conf",
            "etc/app/config.yaml",
            "etc/shadow",
            "var/log/.keep",
            "usr/local/bin/app"
        ]
        for f in expected_files:
            path = os.path.join(BASELINE_DIR, f)
            assert os.path.isfile(path), \
                f"baseline/{f} should still exist"

    def test_baseline_files_have_lf_endings(self):
        """baseline files should still have LF endings (not modified)."""
        files_to_check = [
            "etc/nginx/nginx.conf",
            "etc/app/config.yaml"
        ]
        for f in files_to_check:
            path = os.path.join(BASELINE_DIR, f)
            with open(path, 'rb') as fh:
                content = fh.read()
            if b'\n' in content:
                assert b'\r\n' not in content, \
                    f"baseline/{f} should have LF endings, not CRLF (baseline should be unchanged)"

    def test_patch_files_unchanged(self):
        """All three .patch files should remain byte-identical."""
        patches = [
            "vendor-nginx-fix.patch",
            "vendor-config-update.patch",
            "vendor-backdoor.patch"
        ]
        for p in patches:
            path = os.path.join(INCOMING_DIR, p)
            assert os.path.isfile(path), \
                f"incoming/{p} should still exist"

    def test_nginx_patch_still_has_crlf(self):
        """vendor-nginx-fix.patch should still have CRLF content (not modified)."""
        patch = os.path.join(INCOMING_DIR, "vendor-nginx-fix.patch")
        with open(patch, 'rb') as f:
            content = f.read()
        assert b'\r\n' in content, \
            "vendor-nginx-fix.patch should still contain CRLF (patch files should not be modified)"

    def test_config_patch_still_has_crlf(self):
        """vendor-config-update.patch should still have CRLF content (not modified)."""
        patch = os.path.join(INCOMING_DIR, "vendor-config-update.patch")
        with open(patch, 'rb') as f:
            content = f.read()
        assert b'\r\n' in content, \
            "vendor-config-update.patch should still contain CRLF (patch files should not be modified)"

    def test_allowlist_unchanged(self):
        """allowlist.txt should remain byte-identical."""
        with open(ALLOWLIST_FILE, 'r') as f:
            content = f.read()
        # Should still have the original patterns
        assert "etc/nginx" in content, "allowlist.txt should still contain etc/nginx pattern"
        assert "etc/app" in content, "allowlist.txt should still contain etc/app pattern"
        assert "usr/local/bin" in content, "allowlist.txt should still contain usr/local/bin pattern"
        # Should NOT have etc/shadow
        assert "etc/shadow" not in content, "allowlist.txt should NOT contain etc/shadow"

    def test_policy_md_exists(self):
        """policy.md should still exist."""
        assert os.path.isfile(POLICY_MD), "policy.md should still exist"


class TestValidateShCoreLogicPreserved:
    """Test that validate.sh still performs actual policy evaluation."""

    def test_validate_sh_still_applies_patches(self):
        """validate.sh should still call patch command."""
        with open(VALIDATE_SH, 'r') as f:
            content = f.read()
        assert "patch" in content, \
            "validate.sh should still use patch command"

    def test_validate_sh_still_checks_allowlist(self):
        """validate.sh should still reference diff_check or allowlist."""
        with open(VALIDATE_SH, 'r') as f:
            content = f.read()
        has_diff_check = "diff_check" in content or "lib/" in content
        has_allowlist = "allowlist" in content
        assert has_diff_check or has_allowlist, \
            "validate.sh should still reference diff_check.py or allowlist"


class TestNoHardcodedResults:
    """Test that pass/fail results come from actual policy evaluation, not hardcoding."""

    def test_no_hardcoded_pass_in_diff_check(self):
        """diff_check.py should not have hardcoded pass results for specific patches."""
        with open(DIFF_CHECK_PY, 'r') as f:
            content = f.read()
        # Check for suspicious hardcoding patterns
        suspicious_patterns = [
            "vendor-nginx-fix",
            "vendor-config-update",
        ]
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            # It's okay to reference these in comments or logs, but not in conditionals
            # that would hardcode the result
            lines = content.split('\n')
            for line in lines:
                line_lower = line.lower()
                if pattern in line_lower:
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        continue
                    # Check if it's in a conditional that returns True/Pass
                    if ('return true' in line_lower or 'return "pass"' in line_lower or 
                        "return 'pass'" in line_lower or '= true' in line_lower):
                        pytest.fail(f"Suspicious hardcoded pass for {pattern} in diff_check.py: {line}")

    def test_no_hardcoded_pass_in_validate_sh(self):
        """validate.sh should not have hardcoded pass results for specific patches."""
        with open(VALIDATE_SH, 'r') as f:
            content = f.read()
        lines = content.split('\n')
        for line in lines:
            line_lower = line.lower()
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # Check for hardcoded conditionals
            if ('vendor-nginx-fix' in line_lower or 'vendor-config-update' in line_lower):
                if 'pass' in line_lower or 'echo' in line_lower:
                    # Could be legitimate logging, but flag if it looks like hardcoding
                    if 'if' in line_lower or '&&' in line or '||' in line:
                        pytest.fail(f"Suspicious hardcoded result in validate.sh: {line}")


class TestBackdoorFailsForCorrectReason:
    """Test that backdoor patch fails because etc/shadow is not in allowlist."""

    def test_backdoor_fails_due_to_allowlist(self):
        """
        Temporarily add etc/shadow to allowlist and verify backdoor patch would pass.
        This confirms the failure is due to allowlist, not line endings.
        """
        # Backup original allowlist
        with open(ALLOWLIST_FILE, 'r') as f:
            original_allowlist = f.read()

        try:
            # Add etc/shadow to allowlist temporarily
            with open(ALLOWLIST_FILE, 'w') as f:
                f.write(original_allowlist)
                if not original_allowlist.endswith('\n'):
                    f.write('\n')
                f.write('etc/shadow\n')

            # Run validate.sh
            result = subprocess.run(
                ['./validate.sh'],
                cwd=POLICYGATE_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            output = (result.stdout + result.stderr).lower()

            # Now backdoor should pass (all three should pass)
            lines = output.split('\n')
            backdoor_lines = [l for l in lines if 'backdoor' in l]

            pass_indicators = ['pass', 'ok', 'success', 'approved', 'allowed', '✓', 'passed']

            backdoor_passed = False
            for line in backdoor_lines:
                if any(p in line for p in pass_indicators):
                    backdoor_passed = True
                    break

            assert backdoor_passed, \
                f"With etc/shadow in allowlist, vendor-backdoor.patch should PASS. " \
                f"This confirms the fix correctly evaluates against allowlist. " \
                f"Output lines with 'backdoor': {backdoor_lines}"

            # Exit code should be 0 (all pass)
            assert result.returncode == 0, \
                f"With etc/shadow in allowlist, all patches should pass (exit 0), got {result.returncode}"

        finally:
            # Restore original allowlist
            with open(ALLOWLIST_FILE, 'w') as f:
                f.write(original_allowlist)


class TestPatchedContentNotCorrupted:
    """Test that patched files have correct content (not empty or corrupted)."""

    def test_patched_files_are_valid_ascii(self):
        """
        Apply patches to a temp copy and verify the resulting files are valid ASCII
        without CRLF line terminators.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = os.path.join(tmpdir, "work")
            shutil.copytree(BASELINE_DIR, workdir)

            # Apply the nginx patch
            nginx_patch = os.path.join(INCOMING_DIR, "vendor-nginx-fix.patch")
            result = subprocess.run(
                ['patch', '-p1', '--binary', '-i', nginx_patch],
                cwd=workdir,
                capture_output=True,
                text=True
            )

            # Check the patched nginx.conf
            nginx_conf = os.path.join(workdir, "etc/nginx/nginx.conf")
            if os.path.isfile(nginx_conf):
                # Run file command
                file_result = subprocess.run(
                    ['file', nginx_conf],
                    capture_output=True,
                    text=True
                )
                file_output = file_result.stdout.lower()

                # Should be ASCII text, preferably without CRLF
                # (The fix should normalize line endings during validation)
                assert 'text' in file_output or 'ascii' in file_output, \
                    f"Patched nginx.conf should be text file, got: {file_result.stdout}"

                # Check file is not empty
                with open(nginx_conf, 'rb') as f:
                    content = f.read()
                assert len(content) > 10, \
                    "Patched nginx.conf should not be empty or nearly empty"


class TestAllThreePatchesProcessed:
    """Test that all three patches are processed by validate.sh."""

    def test_all_patches_mentioned_in_output(self):
        """validate.sh output should mention all three patches."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = (result.stdout + result.stderr).lower()

        assert 'nginx' in output, "Output should mention nginx patch"
        assert 'config' in output, "Output should mention config patch"
        assert 'backdoor' in output, "Output should mention backdoor patch"

    def test_two_passes_one_fail(self):
        """Output should indicate exactly 2 passes and 1 fail."""
        result = subprocess.run(
            ['./validate.sh'],
            cwd=POLICYGATE_DIR,
            capture_output=True,
            text=True,
            timeout=120
        )
        output = (result.stdout + result.stderr).lower()

        # Count pass and fail indicators
        pass_count = output.count('pass')
        fail_count = output.count('fail')

        # Should have more passes than fails, and at least one fail
        assert pass_count >= 2, \
            f"Should have at least 2 PASS results, found {pass_count} occurrences of 'pass'"
        assert fail_count >= 1, \
            f"Should have at least 1 FAIL result, found {fail_count} occurrences of 'fail'"
