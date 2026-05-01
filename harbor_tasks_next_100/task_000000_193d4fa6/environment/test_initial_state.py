# test_initial_state.py
"""
Tests to validate the initial state of the system before the student performs the task.
This verifies the /home/user/webapp project exists with the expected structure and bug.
"""

import os
import stat
import subprocess
import pytest

WEBAPP_DIR = "/home/user/webapp"
SRC_FRONTEND_DIR = os.path.join(WEBAPP_DIR, "src/frontend")
SRC_BACKEND_DIR = os.path.join(WEBAPP_DIR, "src/backend")
SCRIPTS_DIR = os.path.join(WEBAPP_DIR, "scripts")


class TestWebappDirectoryStructure:
    """Test that the webapp directory and subdirectories exist."""

    def test_webapp_dir_exists(self):
        assert os.path.isdir(WEBAPP_DIR), f"Directory {WEBAPP_DIR} does not exist"

    def test_src_frontend_dir_exists(self):
        assert os.path.isdir(SRC_FRONTEND_DIR), f"Directory {SRC_FRONTEND_DIR} does not exist"

    def test_src_backend_dir_exists(self):
        assert os.path.isdir(SRC_BACKEND_DIR), f"Directory {SRC_BACKEND_DIR} does not exist"

    def test_scripts_dir_exists(self):
        assert os.path.isdir(SCRIPTS_DIR), f"Directory {SCRIPTS_DIR} does not exist"

    def test_webapp_dir_is_writable(self):
        assert os.access(WEBAPP_DIR, os.W_OK), f"Directory {WEBAPP_DIR} is not writable"


class TestSourceFiles:
    """Test that the source files exist."""

    def test_frontend_index_html_exists(self):
        path = os.path.join(SRC_FRONTEND_DIR, "index.html")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_frontend_app_js_exists(self):
        path = os.path.join(SRC_FRONTEND_DIR, "app.js")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_backend_main_py_exists(self):
        path = os.path.join(SRC_BACKEND_DIR, "main.py")
        assert os.path.isfile(path), f"File {path} does not exist"


class TestProjectFiles:
    """Test that the project configuration files exist."""

    def test_makefile_exists(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_version_file_exists(self):
        path = os.path.join(WEBAPP_DIR, "VERSION")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_version_file_contains_correct_version(self):
        path = os.path.join(WEBAPP_DIR, "VERSION")
        with open(path, 'r') as f:
            content = f.read().strip()
        assert content == "2.4.1", f"VERSION file should contain '2.4.1', but contains '{content}'"

    def test_checksum_script_exists(self):
        path = os.path.join(SCRIPTS_DIR, "checksum.sh")
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_checksum_script_is_executable(self):
        path = os.path.join(SCRIPTS_DIR, "checksum.sh")
        assert os.access(path, os.X_OK), f"Script {path} is not executable"


class TestMakefileTargets:
    """Test that the Makefile has the expected targets."""

    def test_makefile_has_frontend_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'frontend' in content, "Makefile should have a 'frontend' target"

    def test_makefile_has_backend_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'backend' in content, "Makefile should have a 'backend' target"

    def test_makefile_has_bundle_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'bundle' in content, "Makefile should have a 'bundle' target"

    def test_makefile_has_manifest_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'manifest' in content, "Makefile should have a 'manifest' target"

    def test_makefile_has_tag_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'tag' in content, "Makefile should have a 'tag' target"

    def test_makefile_has_release_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'release' in content, "Makefile should have a 'release' target"

    def test_makefile_has_clean_target(self):
        path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(path, 'r') as f:
            content = f.read()
        assert 'clean' in content, "Makefile should have a 'clean' target"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_make_is_available(self):
        result = subprocess.run(['which', 'make'], capture_output=True)
        assert result.returncode == 0, "make command is not available"

    def test_sha256sum_is_available(self):
        result = subprocess.run(['which', 'sha256sum'], capture_output=True)
        assert result.returncode == 0, "sha256sum command is not available"

    def test_bash_is_available(self):
        result = subprocess.run(['which', 'bash'], capture_output=True)
        assert result.returncode == 0, "bash is not available"


class TestMakeTargetsWorkStandalone:
    """Test that individual make targets work when run standalone (as described in task)."""

    def test_make_frontend_works(self):
        # Clean first to ensure fresh state
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        result = subprocess.run(['make', 'frontend'], cwd=WEBAPP_DIR, capture_output=True)
        assert result.returncode == 0, f"'make frontend' should work standalone but failed: {result.stderr.decode()}"
        # Clean up
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)

    def test_make_backend_works(self):
        # Clean first to ensure fresh state
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        result = subprocess.run(['make', 'backend'], cwd=WEBAPP_DIR, capture_output=True)
        assert result.returncode == 0, f"'make backend' should work standalone but failed: {result.stderr.decode()}"
        # Clean up
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)


class TestMakeReleaseFails:
    """Test that make release currently fails (the bug the student needs to fix)."""

    def test_make_release_fails(self):
        # Clean first
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        result = subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)
        # The release should fail due to the bug
        assert result.returncode != 0, "'make release' should currently fail due to the bug, but it succeeded"
        # Clean up
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)


class TestChecksumScriptUsesVersionFile:
    """Test that checksum.sh references VERSION file."""

    def test_checksum_script_reads_version(self):
        path = os.path.join(SCRIPTS_DIR, "checksum.sh")
        with open(path, 'r') as f:
            content = f.read()
        assert 'VERSION' in content, "checksum.sh should reference the VERSION file"
