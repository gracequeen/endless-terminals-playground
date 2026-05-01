# test_initial_state.py
"""
Tests to verify the initial state of the OS/filesystem before the student performs the task.
This validates the environment for the artifact verification debugging task.
"""

import os
import subprocess
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


class TestDirectoryStructure:
    """Test that the required directories exist."""

    def test_qa_directory_exists(self):
        assert os.path.isdir(QA_DIR), f"Directory {QA_DIR} does not exist"

    def test_artifacts_directory_exists(self):
        assert os.path.isdir(ARTIFACTS_DIR), f"Directory {ARTIFACTS_DIR} does not exist"


class TestRequiredFiles:
    """Test that all required files exist."""

    def test_verify_script_exists(self):
        assert os.path.isfile(VERIFY_SCRIPT), f"Verification script {VERIFY_SCRIPT} does not exist"

    def test_manifest_file_exists(self):
        assert os.path.isfile(MANIFEST_FILE), f"Manifest file {MANIFEST_FILE} does not exist"

    @pytest.mark.parametrize("artifact", EXPECTED_ARTIFACTS)
    def test_artifact_file_exists(self, artifact):
        artifact_path = os.path.join(ARTIFACTS_DIR, artifact)
        assert os.path.isfile(artifact_path), f"Artifact file {artifact_path} does not exist"


class TestFilePermissions:
    """Test that files have appropriate permissions."""

    def test_verify_script_is_executable(self):
        assert os.access(VERIFY_SCRIPT, os.X_OK), f"Script {VERIFY_SCRIPT} is not executable"

    def test_manifest_is_writable(self):
        assert os.access(MANIFEST_FILE, os.W_OK), f"Manifest {MANIFEST_FILE} is not writable"

    def test_verify_script_is_readable(self):
        assert os.access(VERIFY_SCRIPT, os.R_OK), f"Script {VERIFY_SCRIPT} is not readable"


class TestManifestContent:
    """Test the manifest file has expected structure and issues."""

    def test_manifest_has_five_entries(self):
        with open(MANIFEST_FILE, 'r') as f:
            lines = [line for line in f.readlines() if line.strip()]
        assert len(lines) == 5, f"Manifest should have 5 entries, found {len(lines)}"

    def test_manifest_contains_all_artifact_names(self):
        with open(MANIFEST_FILE, 'r') as f:
            content = f.read()
        for artifact in EXPECTED_ARTIFACTS:
            assert artifact in content, f"Manifest does not contain reference to {artifact}"

    def test_manifest_line_1_has_bracket_typo(self):
        """Verify the stray ']' character exists in line 1 (api-server.tar.gz line)."""
        with open(MANIFEST_FILE, 'r') as f:
            lines = f.readlines()
        # Find the line with api-server.tar.gz
        api_server_line = None
        for line in lines:
            if 'api-server.tar.gz' in line:
                api_server_line = line
                break
        assert api_server_line is not None, "Could not find api-server.tar.gz line in manifest"
        assert ']' in api_server_line, "Expected stray ']' character in api-server.tar.gz line (the typo to fix)"

    def test_manifest_worker_line_has_trailing_whitespace(self):
        """Verify the worker.tar.gz line has trailing tab/whitespace issue."""
        with open(MANIFEST_FILE, 'rb') as f:
            content = f.read()
        lines = content.split(b'\n')
        worker_line = None
        for line in lines:
            if b'worker.tar.gz' in line:
                worker_line = line
                break
        assert worker_line is not None, "Could not find worker.tar.gz line in manifest"
        # Check for trailing tab after filename
        assert worker_line.rstrip() != worker_line or b'\t' in worker_line, \
            "Expected trailing whitespace (tab) issue in worker.tar.gz line"


class TestVerificationScriptBehavior:
    """Test that the verification script runs and shows expected failures."""

    def test_script_runs_and_reports_two_failures(self):
        """Verify the script currently reports exactly 2 failures."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        # Script should exit with failure count (2)
        assert result.returncode == 2, \
            f"Expected script to exit with code 2 (2 failures), got {result.returncode}. Output: {result.stdout}"

    def test_script_reports_api_server_failure(self):
        """Verify api-server.tar.gz is reported as failing."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "FAIL: api-server.tar.gz" in result.stdout, \
            f"Expected 'FAIL: api-server.tar.gz' in output. Got: {result.stdout}"

    def test_script_reports_worker_failure(self):
        """Verify worker.tar.gz is reported as failing."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "FAIL: worker.tar.gz" in result.stdout, \
            f"Expected 'FAIL: worker.tar.gz' in output. Got: {result.stdout}"

    def test_script_reports_frontend_ok(self):
        """Verify frontend.tar.gz passes verification."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "OK: frontend.tar.gz" in result.stdout, \
            f"Expected 'OK: frontend.tar.gz' in output. Got: {result.stdout}"

    def test_script_reports_migrations_ok(self):
        """Verify migrations.sql passes verification."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "OK: migrations.sql" in result.stdout, \
            f"Expected 'OK: migrations.sql' in output. Got: {result.stdout}"

    def test_script_reports_config_ok(self):
        """Verify config.json passes verification."""
        result = subprocess.run(
            [VERIFY_SCRIPT],
            cwd=QA_DIR,
            capture_output=True,
            text=True
        )
        assert "OK: config.json" in result.stdout, \
            f"Expected 'OK: config.json' in output. Got: {result.stdout}"


class TestToolsAvailable:
    """Test that required tools are available."""

    @pytest.mark.parametrize("tool", ["sha256sum", "cat", "sed", "awk", "grep"])
    def test_tool_available(self, tool):
        result = subprocess.run(["which", tool], capture_output=True)
        assert result.returncode == 0, f"Required tool '{tool}' is not available"


class TestArtifactsAreReal:
    """Test that artifact files have actual content (not empty)."""

    @pytest.mark.parametrize("artifact", EXPECTED_ARTIFACTS)
    def test_artifact_not_empty(self, artifact):
        artifact_path = os.path.join(ARTIFACTS_DIR, artifact)
        size = os.path.getsize(artifact_path)
        assert size > 0, f"Artifact {artifact} is empty (0 bytes)"
