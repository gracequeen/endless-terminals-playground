# test_initial_state.py
"""
Tests to validate the initial state of the CI frontend build environment
before the student fixes the artifact staging issue.
"""

import os
import stat
import subprocess
import pytest


class TestDirectoryStructure:
    """Verify the expected directory structure exists."""

    def test_ci_directory_exists(self):
        """The /home/user/ci directory must exist."""
        assert os.path.isdir("/home/user/ci"), \
            "Directory /home/user/ci does not exist"

    def test_scripts_directory_exists(self):
        """The /home/user/ci/scripts directory must exist."""
        assert os.path.isdir("/home/user/ci/scripts"), \
            "Directory /home/user/ci/scripts does not exist"

    def test_artifacts_frontend_directory_exists(self):
        """The /home/user/ci/artifacts/frontend directory must exist."""
        assert os.path.isdir("/home/user/ci/artifacts/frontend"), \
            "Directory /home/user/ci/artifacts/frontend does not exist"

    def test_artifacts_frontend_dist_directory_exists(self):
        """The /home/user/ci/artifacts/frontend/dist directory must exist (the buggy location)."""
        assert os.path.isdir("/home/user/ci/artifacts/frontend/dist"), \
            "Directory /home/user/ci/artifacts/frontend/dist does not exist"

    def test_build_output_directory_exists(self):
        """The /home/user/ci/build_output directory must exist."""
        assert os.path.isdir("/home/user/ci/build_output"), \
            "Directory /home/user/ci/build_output does not exist"


class TestPipelineConfig:
    """Verify the pipeline configuration file exists and has expected content."""

    def test_frontend_yaml_exists(self):
        """The pipeline config /home/user/ci/frontend.yaml must exist."""
        assert os.path.isfile("/home/user/ci/frontend.yaml"), \
            "Pipeline config /home/user/ci/frontend.yaml does not exist"

    def test_frontend_yaml_contains_artifact_paths(self):
        """The pipeline config must contain the expected artifact glob patterns."""
        with open("/home/user/ci/frontend.yaml", "r") as f:
            content = f.read()

        assert "artifacts/frontend/*.js" in content, \
            "Pipeline config missing 'artifacts/frontend/*.js' glob pattern"
        assert "artifacts/frontend/*.css" in content, \
            "Pipeline config missing 'artifacts/frontend/*.css' glob pattern"
        assert "artifacts/frontend/*.html" in content, \
            "Pipeline config missing 'artifacts/frontend/*.html' glob pattern"


class TestBuildScript:
    """Verify the build script exists and has expected characteristics."""

    def test_build_script_exists(self):
        """The build script /home/user/ci/scripts/build-frontend.sh must exist."""
        assert os.path.isfile("/home/user/ci/scripts/build-frontend.sh"), \
            "Build script /home/user/ci/scripts/build-frontend.sh does not exist"

    def test_build_script_is_executable(self):
        """The build script must be executable."""
        script_path = "/home/user/ci/scripts/build-frontend.sh"
        assert os.access(script_path, os.X_OK), \
            f"Build script {script_path} is not executable"

    def test_build_script_contains_bug(self):
        """The build script should contain the buggy cp command to dist/ subdirectory."""
        with open("/home/user/ci/scripts/build-frontend.sh", "r") as f:
            content = f.read()

        # The bug is copying to $ARTIFACT_DIR/dist/ instead of $ARTIFACT_DIR/
        assert 'ARTIFACT_DIR/dist/' in content or '"$ARTIFACT_DIR/dist/"' in content, \
            "Build script does not contain the expected buggy path (copying to dist/ subdirectory)"


class TestCheckArtifactsScript:
    """Verify the artifact check script exists and works."""

    def test_check_script_exists(self):
        """The check script /home/user/ci/scripts/check-artifacts.sh must exist."""
        assert os.path.isfile("/home/user/ci/scripts/check-artifacts.sh"), \
            "Check script /home/user/ci/scripts/check-artifacts.sh does not exist"

    def test_check_script_is_executable(self):
        """The check script must be executable."""
        script_path = "/home/user/ci/scripts/check-artifacts.sh"
        assert os.access(script_path, os.X_OK), \
            f"Check script {script_path} is not executable"


class TestBuildOutputFiles:
    """Verify the build output files exist."""

    def test_build_output_js_exists(self):
        """The build output should contain a .js file."""
        build_dir = "/home/user/ci/build_output"
        js_files = [f for f in os.listdir(build_dir) if f.endswith('.js')]
        assert len(js_files) > 0, \
            f"No .js files found in {build_dir}"

    def test_build_output_css_exists(self):
        """The build output should contain a .css file."""
        build_dir = "/home/user/ci/build_output"
        css_files = [f for f in os.listdir(build_dir) if f.endswith('.css')]
        assert len(css_files) > 0, \
            f"No .css files found in {build_dir}"

    def test_build_output_html_exists(self):
        """The build output should contain a .html file."""
        build_dir = "/home/user/ci/build_output"
        html_files = [f for f in os.listdir(build_dir) if f.endswith('.html')]
        assert len(html_files) > 0, \
            f"No .html files found in {build_dir}"


class TestArtifactDistFiles:
    """Verify files exist in the wrong location (dist subdirectory)."""

    def test_dist_contains_js(self):
        """The dist subdirectory should contain a .js file."""
        dist_dir = "/home/user/ci/artifacts/frontend/dist"
        js_files = [f for f in os.listdir(dist_dir) if f.endswith('.js')]
        assert len(js_files) > 0, \
            f"No .js files found in {dist_dir}"

    def test_dist_contains_css(self):
        """The dist subdirectory should contain a .css file."""
        dist_dir = "/home/user/ci/artifacts/frontend/dist"
        css_files = [f for f in os.listdir(dist_dir) if f.endswith('.css')]
        assert len(css_files) > 0, \
            f"No .css files found in {dist_dir}"

    def test_dist_contains_html(self):
        """The dist subdirectory should contain a .html file."""
        dist_dir = "/home/user/ci/artifacts/frontend/dist"
        html_files = [f for f in os.listdir(dist_dir) if f.endswith('.html')]
        assert len(html_files) > 0, \
            f"No .html files found in {dist_dir}"


class TestArtifactFrontendNoDirectFiles:
    """Verify that artifacts/frontend/ does NOT have files directly (only dist/ subdir)."""

    def test_no_js_in_frontend_root(self):
        """There should be no .js files directly in artifacts/frontend/."""
        frontend_dir = "/home/user/ci/artifacts/frontend"
        js_files = [f for f in os.listdir(frontend_dir) 
                    if f.endswith('.js') and os.path.isfile(os.path.join(frontend_dir, f))]
        assert len(js_files) == 0, \
            f"Found .js files directly in {frontend_dir} - bug state not set up correctly"

    def test_no_css_in_frontend_root(self):
        """There should be no .css files directly in artifacts/frontend/."""
        frontend_dir = "/home/user/ci/artifacts/frontend"
        css_files = [f for f in os.listdir(frontend_dir) 
                     if f.endswith('.css') and os.path.isfile(os.path.join(frontend_dir, f))]
        assert len(css_files) == 0, \
            f"Found .css files directly in {frontend_dir} - bug state not set up correctly"

    def test_no_html_in_frontend_root(self):
        """There should be no .html files directly in artifacts/frontend/."""
        frontend_dir = "/home/user/ci/artifacts/frontend"
        html_files = [f for f in os.listdir(frontend_dir) 
                      if f.endswith('.html') and os.path.isfile(os.path.join(frontend_dir, f))]
        assert len(html_files) == 0, \
            f"Found .html files directly in {frontend_dir} - bug state not set up correctly"


class TestCheckScriptFailsInitially:
    """Verify that the check script fails in the initial buggy state."""

    def test_check_artifacts_fails(self):
        """The check-artifacts.sh script should fail (exit non-zero) in the initial state."""
        result = subprocess.run(
            ["/home/user/ci/scripts/check-artifacts.sh"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, \
            "check-artifacts.sh should fail in the initial buggy state, but it succeeded"


class TestFilesWritable:
    """Verify that relevant files are writable by the agent."""

    def test_build_script_writable(self):
        """The build script must be writable."""
        assert os.access("/home/user/ci/scripts/build-frontend.sh", os.W_OK), \
            "Build script /home/user/ci/scripts/build-frontend.sh is not writable"

    def test_artifacts_frontend_writable(self):
        """The artifacts/frontend directory must be writable."""
        assert os.access("/home/user/ci/artifacts/frontend", os.W_OK), \
            "Directory /home/user/ci/artifacts/frontend is not writable"

    def test_ci_directory_writable(self):
        """The /home/user/ci directory must be writable."""
        assert os.access("/home/user/ci", os.W_OK), \
            "Directory /home/user/ci is not writable"
