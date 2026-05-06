# test_final_state.py
"""
Tests to validate the final state after the student has fixed the CI frontend
build artifact staging issue. The fix should ensure artifacts land directly
in /home/user/ci/artifacts/frontend/ (not in a dist/ subdirectory).
"""

import os
import subprocess
import pytest


class TestPipelineConfigUnchanged:
    """Verify the pipeline config still has the original glob patterns (invariant)."""

    def test_frontend_yaml_exists(self):
        """The pipeline config /home/user/ci/frontend.yaml must still exist."""
        assert os.path.isfile("/home/user/ci/frontend.yaml"), \
            "Pipeline config /home/user/ci/frontend.yaml does not exist"

    def test_frontend_yaml_contains_js_glob(self):
        """The pipeline config must still contain artifacts/frontend/*.js glob."""
        with open("/home/user/ci/frontend.yaml", "r") as f:
            content = f.read()
        assert "artifacts/frontend/*.js" in content, \
            "Pipeline config must still reference 'artifacts/frontend/*.js' - do not modify the pipeline config"

    def test_frontend_yaml_contains_css_glob(self):
        """The pipeline config must still contain artifacts/frontend/*.css glob."""
        with open("/home/user/ci/frontend.yaml", "r") as f:
            content = f.read()
        assert "artifacts/frontend/*.css" in content, \
            "Pipeline config must still reference 'artifacts/frontend/*.css' - do not modify the pipeline config"

    def test_frontend_yaml_contains_html_glob(self):
        """The pipeline config must still contain artifacts/frontend/*.html glob."""
        with open("/home/user/ci/frontend.yaml", "r") as f:
            content = f.read()
        assert "artifacts/frontend/*.html" in content, \
            "Pipeline config must still reference 'artifacts/frontend/*.html' - do not modify the pipeline config"

    def test_frontend_yaml_no_dist_glob(self):
        """The pipeline config should NOT have been changed to point to dist/ subdirectory."""
        with open("/home/user/ci/frontend.yaml", "r") as f:
            content = f.read()
        # Check that the globs weren't changed to include dist/
        assert "artifacts/frontend/dist/" not in content, \
            "Pipeline config should not be modified to point to dist/ - fix the build script instead"


class TestBuildScriptProducesAllFileTypes:
    """Verify the build script still produces all three file types."""

    def test_build_script_exists(self):
        """The build script must still exist."""
        assert os.path.isfile("/home/user/ci/scripts/build-frontend.sh"), \
            "Build script /home/user/ci/scripts/build-frontend.sh does not exist"

    def test_build_script_is_executable(self):
        """The build script must be executable."""
        assert os.access("/home/user/ci/scripts/build-frontend.sh", os.X_OK), \
            "Build script is not executable"

    def test_build_script_creates_js(self):
        """The build script content should still create .js files."""
        with open("/home/user/ci/scripts/build-frontend.sh", "r") as f:
            content = f.read()
        # Check that it still creates a .js file
        assert ".js" in content, \
            "Build script must still produce .js files"

    def test_build_script_creates_css(self):
        """The build script content should still create .css files."""
        with open("/home/user/ci/scripts/build-frontend.sh", "r") as f:
            content = f.read()
        assert ".css" in content, \
            "Build script must still produce .css files"

    def test_build_script_creates_html(self):
        """The build script content should still create .html files."""
        with open("/home/user/ci/scripts/build-frontend.sh", "r") as f:
            content = f.read()
        assert ".html" in content, \
            "Build script must still produce .html files"


class TestFreshBuildAndCheck:
    """
    Anti-shortcut guard: Clear artifacts, run build, then check.
    This ensures the fix is in the build script, not just manually placed files.
    """

    def test_fresh_build_then_check_succeeds(self):
        """
        After clearing artifacts/frontend/ and running build-frontend.sh,
        check-artifacts.sh must succeed.
        """
        # Clear the artifacts directory
        clear_result = subprocess.run(
            ["rm", "-rf", "/home/user/ci/artifacts/frontend/*"],
            shell=False,
            capture_output=True,
            text=True
        )
        # Use shell=True for glob expansion
        subprocess.run(
            "rm -rf /home/user/ci/artifacts/frontend/*",
            shell=True,
            capture_output=True,
            text=True
        )

        # Run the build script
        build_result = subprocess.run(
            ["/home/user/ci/scripts/build-frontend.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/ci"
        )
        assert build_result.returncode == 0, \
            f"build-frontend.sh failed with exit code {build_result.returncode}.\n" \
            f"stdout: {build_result.stdout}\nstderr: {build_result.stderr}"

        # Run the check script
        check_result = subprocess.run(
            ["/home/user/ci/scripts/check-artifacts.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/ci"
        )
        assert check_result.returncode == 0, \
            f"check-artifacts.sh failed with exit code {check_result.returncode}.\n" \
            f"stdout: {check_result.stdout}\nstderr: {check_result.stderr}\n" \
            "Artifacts are not landing in the correct location after running build-frontend.sh"


class TestArtifactsInCorrectLocation:
    """
    After the fix (and fresh build), verify files are directly in artifacts/frontend/.
    """

    @pytest.fixture(autouse=True)
    def run_fresh_build(self):
        """Clear and rebuild before checking artifact locations."""
        subprocess.run(
            "rm -rf /home/user/ci/artifacts/frontend/*",
            shell=True,
            capture_output=True
        )
        subprocess.run(
            ["/home/user/ci/scripts/build-frontend.sh"],
            capture_output=True,
            cwd="/home/user/ci"
        )

    def test_js_file_in_frontend_root(self):
        """At least one .js file must exist directly in artifacts/frontend/."""
        frontend_dir = "/home/user/ci/artifacts/frontend"
        js_files = [f for f in os.listdir(frontend_dir)
                    if f.endswith('.js') and os.path.isfile(os.path.join(frontend_dir, f))]
        assert len(js_files) >= 1, \
            f"No .js files found directly in {frontend_dir}. " \
            "The build script must place .js files directly in artifacts/frontend/, not in a subdirectory."

    def test_css_file_in_frontend_root(self):
        """At least one .css file must exist directly in artifacts/frontend/."""
        frontend_dir = "/home/user/ci/artifacts/frontend"
        css_files = [f for f in os.listdir(frontend_dir)
                     if f.endswith('.css') and os.path.isfile(os.path.join(frontend_dir, f))]
        assert len(css_files) >= 1, \
            f"No .css files found directly in {frontend_dir}. " \
            "The build script must place .css files directly in artifacts/frontend/, not in a subdirectory."

    def test_html_file_in_frontend_root(self):
        """At least one .html file must exist directly in artifacts/frontend/."""
        frontend_dir = "/home/user/ci/artifacts/frontend"
        html_files = [f for f in os.listdir(frontend_dir)
                      if f.endswith('.html') and os.path.isfile(os.path.join(frontend_dir, f))]
        assert len(html_files) >= 1, \
            f"No .html files found directly in {frontend_dir}. " \
            "The build script must place .html files directly in artifacts/frontend/, not in a subdirectory."


class TestBuildScriptExitsSuccessfully:
    """Verify the build script runs without errors."""

    def test_build_script_exit_zero(self):
        """Running build-frontend.sh should exit with code 0."""
        # Clear first to ensure clean state
        subprocess.run(
            "rm -rf /home/user/ci/artifacts/frontend/*",
            shell=True,
            capture_output=True
        )

        result = subprocess.run(
            ["/home/user/ci/scripts/build-frontend.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/ci"
        )
        assert result.returncode == 0, \
            f"build-frontend.sh exited with code {result.returncode}.\n" \
            f"stdout: {result.stdout}\nstderr: {result.stderr}"


class TestCheckArtifactsSucceeds:
    """Verify the check-artifacts.sh script succeeds after the fix."""

    def test_check_artifacts_exit_zero(self):
        """Running check-artifacts.sh should exit with code 0 and find artifacts."""
        # Clear and rebuild first
        subprocess.run(
            "rm -rf /home/user/ci/artifacts/frontend/*",
            shell=True,
            capture_output=True
        )
        subprocess.run(
            ["/home/user/ci/scripts/build-frontend.sh"],
            capture_output=True,
            cwd="/home/user/ci"
        )

        result = subprocess.run(
            ["/home/user/ci/scripts/check-artifacts.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/ci"
        )
        assert result.returncode == 0, \
            f"check-artifacts.sh exited with code {result.returncode}.\n" \
            f"stdout: {result.stdout}\nstderr: {result.stderr}\n" \
            "The artifact check failed - files are not in the expected location."

    def test_check_artifacts_reports_found(self):
        """The check script should report finding artifact(s)."""
        # Clear and rebuild first
        subprocess.run(
            "rm -rf /home/user/ci/artifacts/frontend/*",
            shell=True,
            capture_output=True
        )
        subprocess.run(
            ["/home/user/ci/scripts/build-frontend.sh"],
            capture_output=True,
            cwd="/home/user/ci"
        )

        result = subprocess.run(
            ["/home/user/ci/scripts/check-artifacts.sh"],
            capture_output=True,
            text=True,
            cwd="/home/user/ci"
        )
        # The script should print something about finding artifacts
        output = result.stdout.lower() + result.stderr.lower()
        assert "found" in output or "artifact" in output, \
            f"check-artifacts.sh should report finding artifacts.\nOutput: {result.stdout}"
