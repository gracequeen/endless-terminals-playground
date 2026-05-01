# test_final_state.py
"""
Tests to validate the final state after the student has fixed the Makefile bug.
This verifies that `make release` works and produces the expected artifacts.
"""

import json
import os
import subprocess
import hashlib
import pytest

WEBAPP_DIR = "/home/user/webapp"
DIST_DIR = os.path.join(WEBAPP_DIR, "dist")
SCRIPTS_DIR = os.path.join(WEBAPP_DIR, "scripts")


def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class TestMakeReleaseSucceeds:
    """Test that make release now succeeds."""

    def test_make_clean_then_release_exits_zero(self):
        """Running 'make clean && make release' should exit with code 0."""
        # Run make clean first
        clean_result = subprocess.run(
            ['make', 'clean'],
            cwd=WEBAPP_DIR,
            capture_output=True
        )

        # Run make release
        release_result = subprocess.run(
            ['make', 'release'],
            cwd=WEBAPP_DIR,
            capture_output=True
        )

        assert release_result.returncode == 0, (
            f"'make release' should succeed but failed with exit code {release_result.returncode}.\n"
            f"stdout: {release_result.stdout.decode()}\n"
            f"stderr: {release_result.stderr.decode()}"
        )


class TestDistDirectoryExists:
    """Test that dist/ directory is created with artifacts."""

    def test_dist_directory_exists(self):
        """The dist/ directory should exist after release."""
        # Ensure we have a fresh release
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        assert os.path.isdir(DIST_DIR), f"Directory {DIST_DIR} should exist after make release"


class TestDistBundleJs:
    """Test that dist/bundle.js exists and has content."""

    def test_bundle_js_exists(self):
        """dist/bundle.js should exist."""
        # Ensure we have a fresh release
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        bundle_path = os.path.join(DIST_DIR, "bundle.js")
        assert os.path.isfile(bundle_path), f"File {bundle_path} should exist after make release"

    def test_bundle_js_has_content(self):
        """dist/bundle.js should have non-zero size."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        bundle_path = os.path.join(DIST_DIR, "bundle.js")
        assert os.path.getsize(bundle_path) > 0, f"File {bundle_path} should have non-zero size"


class TestDistServerPy:
    """Test that dist/server.py exists and has content."""

    def test_server_py_exists(self):
        """dist/server.py should exist."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        server_path = os.path.join(DIST_DIR, "server.py")
        assert os.path.isfile(server_path), f"File {server_path} should exist after make release"

    def test_server_py_has_content(self):
        """dist/server.py should have non-zero size."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        server_path = os.path.join(DIST_DIR, "server.py")
        assert os.path.getsize(server_path) > 0, f"File {server_path} should have non-zero size"


class TestManifestJson:
    """Test that dist/manifest.json exists and is valid."""

    def test_manifest_json_exists(self):
        """dist/manifest.json should exist."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        assert os.path.isfile(manifest_path), f"File {manifest_path} should exist after make release"

    def test_manifest_json_is_valid_json(self):
        """dist/manifest.json should be valid JSON."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            content = f.read()

        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"manifest.json is not valid JSON: {e}\nContent:\n{content}")

    def test_manifest_has_version_field(self):
        """manifest.json should have a 'version' field."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert 'version' in manifest, "manifest.json should have a 'version' field"

    def test_manifest_version_is_correct(self):
        """manifest.json version should be '2.4.1'."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert manifest.get('version') == '2.4.1', (
            f"manifest.json version should be '2.4.1', got '{manifest.get('version')}'"
        )

    def test_manifest_has_checksums_field(self):
        """manifest.json should have a 'checksums' field."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        assert 'checksums' in manifest, "manifest.json should have a 'checksums' field"

    def test_manifest_checksums_has_bundle_js(self):
        """manifest.json checksums should have 'bundle.js' key."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        checksums = manifest.get('checksums', {})
        assert 'bundle.js' in checksums, "manifest.json checksums should have 'bundle.js' key"

    def test_manifest_checksums_has_server_py(self):
        """manifest.json checksums should have 'server.py' key."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        checksums = manifest.get('checksums', {})
        assert 'server.py' in checksums, "manifest.json checksums should have 'server.py' key"

    def test_bundle_js_checksum_is_valid_sha256(self):
        """bundle.js checksum should be a 64-character hex string."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        checksum = manifest.get('checksums', {}).get('bundle.js', '')
        assert len(checksum) == 64, (
            f"bundle.js checksum should be 64 characters, got {len(checksum)}"
        )
        assert all(c in '0123456789abcdef' for c in checksum.lower()), (
            f"bundle.js checksum should be hexadecimal, got '{checksum}'"
        )

    def test_server_py_checksum_is_valid_sha256(self):
        """server.py checksum should be a 64-character hex string."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        manifest_path = os.path.join(DIST_DIR, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        checksum = manifest.get('checksums', {}).get('server.py', '')
        assert len(checksum) == 64, (
            f"server.py checksum should be 64 characters, got {len(checksum)}"
        )
        assert all(c in '0123456789abcdef' for c in checksum.lower()), (
            f"server.py checksum should be hexadecimal, got '{checksum}'"
        )


class TestChecksumsMatchFiles:
    """Test that checksums in manifest.json match actual file hashes."""

    def test_bundle_js_checksum_matches_file(self):
        """The checksum for bundle.js in manifest.json should match the actual file."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        bundle_path = os.path.join(DIST_DIR, "bundle.js")
        manifest_path = os.path.join(DIST_DIR, "manifest.json")

        actual_hash = compute_sha256(bundle_path)

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        manifest_hash = manifest.get('checksums', {}).get('bundle.js', '').lower()

        assert actual_hash == manifest_hash, (
            f"bundle.js checksum mismatch:\n"
            f"  Actual file hash:    {actual_hash}\n"
            f"  Manifest checksum:   {manifest_hash}"
        )

    def test_server_py_checksum_matches_file(self):
        """The checksum for server.py in manifest.json should match the actual file."""
        subprocess.run(['make', 'clean'], cwd=WEBAPP_DIR, capture_output=True)
        subprocess.run(['make', 'release'], cwd=WEBAPP_DIR, capture_output=True)

        server_path = os.path.join(DIST_DIR, "server.py")
        manifest_path = os.path.join(DIST_DIR, "manifest.json")

        actual_hash = compute_sha256(server_path)

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        manifest_hash = manifest.get('checksums', {}).get('server.py', '').lower()

        assert actual_hash == manifest_hash, (
            f"server.py checksum mismatch:\n"
            f"  Actual file hash:    {actual_hash}\n"
            f"  Manifest checksum:   {manifest_hash}"
        )


class TestInvariants:
    """Test that invariants are preserved."""

    def test_version_file_unchanged(self):
        """VERSION file should still contain '2.4.1'."""
        version_path = os.path.join(WEBAPP_DIR, "VERSION")
        with open(version_path, 'r') as f:
            content = f.read().strip()
        assert content == "2.4.1", f"VERSION file should contain '2.4.1', got '{content}'"

    def test_checksum_script_still_exists(self):
        """scripts/checksum.sh should still exist."""
        script_path = os.path.join(SCRIPTS_DIR, "checksum.sh")
        assert os.path.isfile(script_path), f"Script {script_path} should still exist"

    def test_checksum_script_is_executable(self):
        """scripts/checksum.sh should still be executable."""
        script_path = os.path.join(SCRIPTS_DIR, "checksum.sh")
        assert os.access(script_path, os.X_OK), f"Script {script_path} should be executable"

    def test_makefile_uses_checksum_script(self):
        """Makefile manifest target should still use scripts/checksum.sh."""
        makefile_path = os.path.join(WEBAPP_DIR, "Makefile")
        with open(makefile_path, 'r') as f:
            content = f.read()

        # Check that the checksum.sh script is referenced in the Makefile
        assert 'checksum.sh' in content or 'scripts/checksum' in content, (
            "Makefile should still reference checksum.sh script"
        )

    def test_source_frontend_files_exist(self):
        """Source frontend files should still exist."""
        index_path = os.path.join(WEBAPP_DIR, "src/frontend/index.html")
        app_path = os.path.join(WEBAPP_DIR, "src/frontend/app.js")
        assert os.path.isfile(index_path), f"Source file {index_path} should still exist"
        assert os.path.isfile(app_path), f"Source file {app_path} should still exist"

    def test_source_backend_files_exist(self):
        """Source backend files should still exist."""
        main_path = os.path.join(WEBAPP_DIR, "src/backend/main.py")
        assert os.path.isfile(main_path), f"Source file {main_path} should still exist"
