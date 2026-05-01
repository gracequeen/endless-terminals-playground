# test_initial_state.py
"""
Tests to validate the initial state of the Android signing pipeline
before the student performs any fixes.
"""

import os
import subprocess
import pytest


class TestPipelineStructure:
    """Test that the pipeline directory structure exists."""

    def test_pipeline_directory_exists(self):
        """Verify /home/user/pipeline directory exists."""
        assert os.path.isdir("/home/user/pipeline"), \
            "Pipeline directory /home/user/pipeline does not exist"

    def test_config_directory_exists(self):
        """Verify config directory exists."""
        assert os.path.isdir("/home/user/pipeline/config"), \
            "Config directory /home/user/pipeline/config does not exist"

    def test_keys_directory_exists(self):
        """Verify keys directory exists."""
        assert os.path.isdir("/home/user/pipeline/keys"), \
            "Keys directory /home/user/pipeline/keys does not exist"

    def test_builds_directory_exists(self):
        """Verify builds directory exists."""
        assert os.path.isdir("/home/user/pipeline/builds"), \
            "Builds directory /home/user/pipeline/builds does not exist"


class TestSigningScript:
    """Test the main signing script exists and is executable."""

    def test_sign_apk_script_exists(self):
        """Verify sign_apk.sh script exists."""
        assert os.path.isfile("/home/user/pipeline/sign_apk.sh"), \
            "Signing script /home/user/pipeline/sign_apk.sh does not exist"

    def test_sign_apk_script_is_executable(self):
        """Verify sign_apk.sh is executable."""
        assert os.access("/home/user/pipeline/sign_apk.sh", os.X_OK), \
            "Signing script /home/user/pipeline/sign_apk.sh is not executable"


class TestSigningConfig:
    """Test the signing configuration file."""

    def test_signing_yaml_exists(self):
        """Verify signing.yaml config file exists."""
        assert os.path.isfile("/home/user/pipeline/config/signing.yaml"), \
            "Signing config /home/user/pipeline/config/signing.yaml does not exist"

    def test_signing_yaml_readable(self):
        """Verify signing.yaml is readable and contains expected keys."""
        config_path = "/home/user/pipeline/config/signing.yaml"
        with open(config_path, 'r') as f:
            content = f.read()

        # Check for expected configuration keys
        assert "keystore_path:" in content, \
            "signing.yaml missing keystore_path configuration"
        assert "key_alias:" in content, \
            "signing.yaml missing key_alias configuration"
        assert "keystore_pass:" in content, \
            "signing.yaml missing keystore_pass configuration"
        assert "key_pass:" in content, \
            "signing.yaml missing key_pass configuration"
        assert "signature_algorithm:" in content, \
            "signing.yaml missing signature_algorithm configuration"

    def test_signing_yaml_has_sha1_algorithm(self):
        """Verify signing.yaml contains the buggy SHA1withRSA algorithm setting."""
        config_path = "/home/user/pipeline/config/signing.yaml"
        with open(config_path, 'r') as f:
            content = f.read()

        # The bug is that it specifies SHA1withRSA
        assert "SHA1withRSA" in content, \
            "signing.yaml should contain SHA1withRSA (the buggy setting)"


class TestVerifyConfig:
    """Test the verify configuration file."""

    def test_verify_conf_exists(self):
        """Verify verify.conf config file exists."""
        assert os.path.isfile("/home/user/pipeline/config/verify.conf"), \
            "Verify config /home/user/pipeline/config/verify.conf does not exist"


class TestKeystore:
    """Test the keystore file and its properties."""

    def test_keystore_file_exists(self):
        """Verify the release keystore exists."""
        assert os.path.isfile("/home/user/pipeline/keys/release.jks"), \
            "Keystore /home/user/pipeline/keys/release.jks does not exist"

    def test_keystore_is_valid(self):
        """Verify the keystore is a valid JKS file."""
        result = subprocess.run(
            ["keytool", "-list", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Keystore is not valid or password is wrong: {result.stderr}"

    def test_keystore_contains_release_key_alias(self):
        """Verify the keystore contains the 'release-key' alias."""
        result = subprocess.run(
            ["keytool", "-list", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        assert "release-key" in result.stdout, \
            "Keystore does not contain 'release-key' alias"

    def test_keystore_uses_sha256_certificate(self):
        """Verify the keystore certificate uses SHA256withRSA (the actual cert algorithm)."""
        result = subprocess.run(
            ["keytool", "-list", "-v", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Failed to list keystore details: {result.stderr}"

        # The certificate should use SHA256withRSA
        output_lower = result.stdout.lower()
        assert "sha256withrsa" in output_lower, \
            "Keystore certificate should use SHA256withRSA algorithm"


class TestUnsignedApk:
    """Test the unsigned APK file."""

    def test_unsigned_apk_exists(self):
        """Verify the unsigned APK exists."""
        assert os.path.isfile("/home/user/pipeline/builds/app-release-unsigned.apk"), \
            "Unsigned APK /home/user/pipeline/builds/app-release-unsigned.apk does not exist"

    def test_unsigned_apk_has_content(self):
        """Verify the unsigned APK has reasonable size (not empty)."""
        apk_path = "/home/user/pipeline/builds/app-release-unsigned.apk"
        size = os.path.getsize(apk_path)
        assert size > 1000, \
            f"Unsigned APK is too small ({size} bytes), expected at least 1KB"

    def test_unsigned_apk_is_valid_zip(self):
        """Verify the unsigned APK is a valid ZIP file (APKs are ZIP archives)."""
        import zipfile
        apk_path = "/home/user/pipeline/builds/app-release-unsigned.apk"
        assert zipfile.is_zipfile(apk_path), \
            "Unsigned APK is not a valid ZIP/APK file"


class TestAndroidTools:
    """Test that required Android SDK tools are available."""

    def test_keytool_available(self):
        """Verify keytool is available."""
        result = subprocess.run(
            ["which", "keytool"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "keytool is not available in PATH"

    def test_apksigner_available(self):
        """Verify apksigner is available."""
        result = subprocess.run(
            ["which", "apksigner"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "apksigner is not available in PATH"

    def test_zipalign_available(self):
        """Verify zipalign is available."""
        result = subprocess.run(
            ["which", "zipalign"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "zipalign is not available in PATH"

    def test_java_available(self):
        """Verify Java is available."""
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            "Java is not available"


class TestDirectoryPermissions:
    """Test that directories are writable."""

    def test_pipeline_directory_writable(self):
        """Verify /home/user/pipeline is writable."""
        assert os.access("/home/user/pipeline", os.W_OK), \
            "/home/user/pipeline is not writable"

    def test_config_directory_writable(self):
        """Verify config directory is writable."""
        assert os.access("/home/user/pipeline/config", os.W_OK), \
            "/home/user/pipeline/config is not writable"

    def test_builds_directory_writable(self):
        """Verify builds directory is writable."""
        assert os.access("/home/user/pipeline/builds", os.W_OK), \
            "/home/user/pipeline/builds is not writable"


class TestAlgorithmMismatch:
    """Test that confirms the algorithm mismatch bug exists."""

    def test_config_has_wrong_algorithm(self):
        """
        Verify the signing.yaml specifies SHA1withRSA while keystore uses SHA256withRSA.
        This is the root cause of the bug.
        """
        # Check config specifies SHA1withRSA
        config_path = "/home/user/pipeline/config/signing.yaml"
        with open(config_path, 'r') as f:
            config_content = f.read()

        has_sha1_in_config = "SHA1withRSA" in config_content

        # Check keystore uses SHA256withRSA
        result = subprocess.run(
            ["keytool", "-list", "-v", "-keystore", "/home/user/pipeline/keys/release.jks",
             "-storepass", "android123"],
            capture_output=True,
            text=True
        )
        has_sha256_in_keystore = "sha256withrsa" in result.stdout.lower()

        assert has_sha1_in_config and has_sha256_in_keystore, \
            "Expected algorithm mismatch: config should have SHA1withRSA, keystore should have SHA256withRSA"
