# test_final_state.py
"""
Tests to verify the final state after the student has fixed the checksums.manifest file.
The verification script should now pass all 5 artifacts with 0 failures.
"""

import os
import subprocess
import hashlib
import pytest

QA_DIR = "/home/user/qa"
ARTIFACTS_DIR = "/home/user/qa/artifacts"
VERIFY_SCRIPT = "/home/user/qa/verify_artifacts.sh"
MANIFEST_FILE = "/home/user/qa/checksums.manifest"

EXPECTED_ARTIFACTS = [
    "api-server.tar.gz",
    "frontend.tar.gz",
    "worker.tar.gz",
    "migrations.sql",
    "config.json"
]


def get_file_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class TestVerificationScriptSuccess:
    """Test that the verification script now passes completely."""

    def test_script_exits_zero(self):
        """The verification script must exit with code 0 (no failures)."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Verification script should exit 0, but exited {result.returncode}. Output:\n{result.stdout}\nStderr:\n{result.stderr}"

    def test_script_reports_zero_failures(self):
        """The script output must show 'Failures: 0'."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "Failures: 0" in result.stdout, \
            f"Expected 'Failures: 0' in output. Got:\n{result.stdout}"

    @pytest.mark.parametrize("artifact", EXPECTED_ARTIFACTS)
    def test_script_reports_ok_for_artifact(self, artifact):
        """Each artifact must show 'OK' in the verification output."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        expected_ok = f"OK: {artifact}"
        assert expected_ok in result.stdout, \
            f"Expected '{expected_ok}' in output. Got:\n{result.stdout}"

    def test_no_failures_reported(self):
        """No 'FAIL:' lines should appear in the output."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "FAIL:" not in result.stdout, \
            f"Found 'FAIL:' in output when all should pass. Output:\n{result.stdout}"


class TestManifestCorrectness:
    """Test that the manifest contains correct checksums matching actual artifacts."""

    def test_manifest_still_has_five_entries(self):
        """Manifest must still contain exactly 5 artifact entries."""
        with open(MANIFEST_FILE, 'r') as f:
            lines = [line for line in f.readlines() if line.strip()]
        assert len(lines) == 5, \
            f"Manifest should have 5 entries, found {len(lines)}"

    def test_manifest_contains_all_artifact_names(self):
        """All 5 artifact filenames must be present in the manifest."""
        with open(MANIFEST_FILE, 'r') as f:
            content = f.read()
        for artifact in EXPECTED_ARTIFACTS:
            assert artifact in content, \
                f"Manifest does not contain reference to {artifact}"

    @pytest.mark.parametrize("artifact", EXPECTED_ARTIFACTS)
    def test_manifest_checksum_matches_actual_file(self, artifact):
        """Each checksum in manifest must match the actual SHA256 of the artifact."""
        artifact_path = os.path.join(ARTIFACTS_DIR, artifact)
        actual_checksum = get_file_sha256(artifact_path)

        # Parse manifest to find the checksum for this artifact
        manifest_checksum = None
        with open(MANIFEST_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[1] == artifact:
                    manifest_checksum = parts[0]
                    break

        assert manifest_checksum is not None, \
            f"Could not find checksum entry for {artifact} in manifest"
        assert manifest_checksum == actual_checksum, \
            f"Manifest checksum for {artifact} ({manifest_checksum}) does not match actual file checksum ({actual_checksum})"

    def test_no_bracket_typo_in_manifest(self):
        """The stray ']' character should be removed from the manifest."""
        with open(MANIFEST_FILE, 'r') as f:
            content = f.read()
        # Check that no line has a ']' in the checksum portion
        for line in content.splitlines():
            if line.strip():
                parts = line.split()
                if parts:
                    checksum = parts[0]
                    assert ']' not in checksum, \
                        f"Found stray ']' in checksum: {checksum}"

    def test_checksums_are_valid_sha256_format(self):
        """All checksums in manifest should be valid 64-character hex strings."""
        import re
        sha256_pattern = re.compile(r'^[a-f0-9]{64}$')

        with open(MANIFEST_FILE, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if parts:
                    checksum = parts[0]
                    assert sha256_pattern.match(checksum), \
                        f"Line {line_num}: Invalid SHA256 format '{checksum}' - must be 64 hex characters"


class TestArtifactsUnchanged:
    """Test that artifact files were not modified (they should remain byte-identical)."""

    @pytest.mark.parametrize("artifact", EXPECTED_ARTIFACTS)
    def test_artifact_still_exists(self, artifact):
        """All artifact files must still exist."""
        artifact_path = os.path.join(ARTIFACTS_DIR, artifact)
        assert os.path.isfile(artifact_path), \
            f"Artifact file {artifact_path} no longer exists"

    @pytest.mark.parametrize("artifact", EXPECTED_ARTIFACTS)
    def test_artifact_not_empty(self, artifact):
        """Artifact files must not be empty."""
        artifact_path = os.path.join(ARTIFACTS_DIR, artifact)
        size = os.path.getsize(artifact_path)
        assert size > 0, \
            f"Artifact {artifact} is empty (0 bytes) - files should not have been modified"


class TestScriptUnchanged:
    """Test that the verification script was not modified (it was not buggy)."""

    def test_script_still_exists(self):
        """The verification script must still exist."""
        assert os.path.isfile(VERIFY_SCRIPT), \
            f"Verification script {VERIFY_SCRIPT} no longer exists"

    def test_script_still_executable(self):
        """The verification script must still be executable."""
        assert os.access(VERIFY_SCRIPT, os.X_OK), \
            f"Script {VERIFY_SCRIPT} is no longer executable"

    def test_script_contains_sha256sum_verification(self):
        """Script must still perform actual sha256sum verification."""
        with open(VERIFY_SCRIPT, 'r') as f:
            content = f.read()
        assert 'sha256sum' in content, \
            "Script must still use sha256sum for verification - script should not have been modified"

    def test_script_reads_manifest(self):
        """Script must still read from checksums.manifest."""
        with open(VERIFY_SCRIPT, 'r') as f:
            content = f.read()
        assert 'checksums.manifest' in content, \
            "Script must still read checksums.manifest - script should not have been modified"

    def test_script_not_hardcoded_to_pass(self):
        """Script must not be modified to always exit 0 or skip verification."""
        with open(VERIFY_SCRIPT, 'r') as f:
            content = f.read()
        # Check it still has the comparison logic
        assert 'expected_sum' in content or 'expected' in content.lower(), \
            "Script appears to have been modified to skip checksum comparison"
        # Check it still tracks failures
        assert 'failures' in content or 'FAIL' in content, \
            "Script appears to have been modified to not track failures"


class TestFilesystemIntegrity:
    """Test overall filesystem integrity."""

    def test_qa_directory_exists(self):
        """QA directory must still exist."""
        assert os.path.isdir(QA_DIR), f"Directory {QA_DIR} does not exist"

    def test_artifacts_directory_exists(self):
        """Artifacts directory must still exist."""
        assert os.path.isdir(ARTIFACTS_DIR), f"Directory {ARTIFACTS_DIR} does not exist"

    def test_manifest_file_exists(self):
        """Manifest file must still exist."""
        assert os.path.isfile(MANIFEST_FILE), f"Manifest file {MANIFEST_FILE} does not exist"
