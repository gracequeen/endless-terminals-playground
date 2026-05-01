# test_final_state.py
"""
Tests to validate the final state of the Android signing pipeline
after the student has completed the fix.
"""

import os
import subprocess
import hashlib
import pytest


class TestSignedApkExists:
    """Test that the signed APK was created."""

    def test_signed_apk_exists(self):
        """Verify the signed APK file exists."""
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
        assert os.path.isfile(signed_apk), \
            f"Signed APK {signed_apk} does not exist. The signing script must create this file."

    def test_signed_apk_has_content(self):
        """Verify the signed APK has reasonable size."""
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
        if not os.path.isfile(signed_apk):
            pytest.skip("Signed APK does not exist")
        size = os.path.getsize(signed_apk)
        assert size > 1000, \
            f"Signed APK is too small ({size} bytes), expected at least 1KB"

    def test_signed_apk_is_valid_zip(self):
        """Verify the signed APK is a valid ZIP file."""
        import zipfile
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
        if not os.path.isfile(signed_apk):
            pytest.skip("Signed APK does not exist")
        assert zipfile.is_zipfile(signed_apk), \
            "Signed APK is not a valid ZIP/APK file"


class TestSignedApkValidity:
    """Test that the signed APK has a valid signature."""

    def test_apksigner_verify_succeeds(self):
        """Verify apksigner verify exits 0 for the signed APK."""
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
        if not os.path.isfile(signed_apk):
            pytest.fail(f"Signed APK {signed_apk} does not exist - cannot verify signature")

        result = subprocess.run(
            ["apksigner", "verify", signed_apk],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"apksigner verify failed with exit code {result.returncode}. " \
            f"stderr: {result.stderr}. stdout: {result.stdout}. " \
            "The signed APK must have a valid signature."

    def test_apksigner_verify_with_print_certs(self):
        """Verify apksigner verify --print-certs succeeds."""
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
        if not os.path.isfile(signed_apk):
            pytest.skip("Signed APK does not exist")

        result = subprocess.run(
            ["apksigner", "verify", "--print-certs", signed_apk],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"apksigner verify --print-certs failed: {result.stderr}"


class TestSigningScriptWorks:
    """Test that the signing script now works correctly."""

    def test_sign_apk_script_exits_zero(self):
        """Verify running sign_apk.sh exits with code 0."""
        # First, remove the signed APK if it exists to test fresh signing
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
        if os.path.isfile(signed_apk):
            os.remove(signed_apk)

        result = subprocess.run(
            ["/home/user/pipeline/sign_apk.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/pipeline"
        )
        assert result.returncode == 0, \
            f"sign_apk.sh failed with exit code {result.returncode}. " \
            f"stdout: {result.stdout}. stderr: {result.stderr}"

    def test_script_produces_valid_signed_apk(self):
        """Verify that after running the script, the signed APK is valid."""
        signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"

        # Run the script
        subprocess.run(
            ["/home/user/pipeline/sign_apk.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/pipeline"
        )

        # Verify the output
        assert os.path.isfile(signed_apk), \
            "sign_apk.sh did not produce app-release-signed.apk"

        result = subprocess.run(
            ["apksigner", "verify", signed_apk],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"APK produced by sign_apk.sh has invalid signature: {result.stderr}"


class TestKeystoreInvariants:
    """Test that the keystore was NOT modified (invariants)."""

    def test_keystore_still_exists(self):
        """Verify the keystore file still exists."""
        keystore = "/home/user/pipeline/keys/release.jks"
        assert os.path.isfile(keystore), \
            f"Keystore {keystore} was deleted - it must remain unchanged"

    def test_keystore_still_uses_sha256(self):
        """Verify the keystore certificate still uses SHA256withRSA."""
        result = subprocess.run(
            ["keytool", "-list", "-v", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Cannot read keystore: {result.stderr}"

        output_lower = result.stdout.lower()
        assert "sha256withrsa" in output_lower, \
            "Keystore certificate must still use SHA256withRSA - the keystore should not be regenerated"

    def test_keystore_still_has_release_key_alias(self):
        """Verify the keystore still contains 'release-key' alias."""
        result = subprocess.run(
            ["keytool", "-list", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        assert "release-key" in result.stdout, \
            "Keystore must still contain 'release-key' alias"

    def test_keystore_password_unchanged(self):
        """Verify the keystore password is still 'android123'."""
        result = subprocess.run(
            ["keytool", "-list", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Keystore password must remain 'android123'"


class TestUnsignedApkInvariants:
    """Test that the unsigned APK was NOT modified."""

    def test_unsigned_apk_still_exists(self):
        """Verify the unsigned APK still exists."""
        unsigned_apk = "/home/user/pipeline/builds/app-release-unsigned.apk"
        assert os.path.isfile(unsigned_apk), \
            f"Unsigned APK {unsigned_apk} was deleted - it must remain unchanged"

    def test_unsigned_apk_is_still_valid(self):
        """Verify the unsigned APK is still a valid ZIP file."""
        import zipfile
        unsigned_apk = "/home/user/pipeline/builds/app-release-unsigned.apk"
        assert zipfile.is_zipfile(unsigned_apk), \
            "Unsigned APK must remain a valid ZIP/APK file"


class TestConfigurationFix:
    """Test that the configuration was fixed appropriately."""

    def test_signing_yaml_still_exists(self):
        """Verify signing.yaml still exists."""
        config_path = "/home/user/pipeline/config/signing.yaml"
        assert os.path.isfile(config_path), \
            f"Config file {config_path} was deleted"

    def test_signing_yaml_has_required_keys(self):
        """Verify signing.yaml still has all required configuration keys."""
        config_path = "/home/user/pipeline/config/signing.yaml"
        with open(config_path, 'r') as f:
            content = f.read()

        # Must still have these keys (values may have changed)
        assert "keystore_path:" in content or "keystore_path" in content, \
            "signing.yaml must still have keystore_path configuration"
        assert "key_alias:" in content or "key_alias" in content, \
            "signing.yaml must still have key_alias configuration"

    def test_key_alias_unchanged(self):
        """Verify the key_alias is still 'release-key'."""
        config_path = "/home/user/pipeline/config/signing.yaml"
        with open(config_path, 'r') as f:
            content = f.read()

        # The alias must remain release-key
        assert "release-key" in content, \
            "key_alias must remain 'release-key' in signing.yaml"

    def test_algorithm_mismatch_fixed(self):
        """
        Verify the algorithm mismatch is fixed - either SHA1withRSA is removed/changed,
        or the script handles it differently.
        """
        # The real test is that signing works (tested above).
        # Here we just check that if SHA1withRSA is still in config,
        # the script must be handling it differently.
        config_path = "/home/user/pipeline/config/signing.yaml"
        with open(config_path, 'r') as f:
            content = f.read()

        # If SHA1withRSA is still present, that's only OK if signing still works
        # (which is verified by other tests). But ideally it should be fixed.
        # We'll just note it here - the critical test is that signing works.
        if "SHA1withRSA" in content:
            # Check that signing still works despite this
            signed_apk = "/home/user/pipeline/builds/app-release-signed.apk"
            if os.path.isfile(signed_apk):
                result = subprocess.run(
                    ["apksigner", "verify", signed_apk],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    pytest.fail(
                        "SHA1withRSA is still in signing.yaml and signing is broken. "
                        "The algorithm should be changed to SHA256withRSA or removed "
                        "to let apksigner auto-detect."
                    )


class TestPipelineIntegrity:
    """Test overall pipeline integrity."""

    def test_script_still_executable(self):
        """Verify sign_apk.sh is still executable."""
        assert os.access("/home/user/pipeline/sign_apk.sh", os.X_OK), \
            "sign_apk.sh must remain executable"

    def test_pipeline_directory_structure_intact(self):
        """Verify the pipeline directory structure is intact."""
        required_dirs = [
            "/home/user/pipeline",
            "/home/user/pipeline/config",
            "/home/user/pipeline/keys",
            "/home/user/pipeline/builds"
        ]
        for d in required_dirs:
            assert os.path.isdir(d), f"Directory {d} must exist"

    def test_required_files_exist(self):
        """Verify all required files exist."""
        required_files = [
            "/home/user/pipeline/sign_apk.sh",
            "/home/user/pipeline/config/signing.yaml",
            "/home/user/pipeline/keys/release.jks",
            "/home/user/pipeline/builds/app-release-unsigned.apk"
        ]
        for f in required_files:
            assert os.path.isfile(f), f"Required file {f} must exist"
