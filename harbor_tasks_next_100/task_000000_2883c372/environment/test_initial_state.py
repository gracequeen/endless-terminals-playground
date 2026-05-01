# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the Maven mirror sync fix task.
"""

import os
import subprocess
import pytest


# Base paths
MIRROR_DIR = "/home/user/mirror"
SYNC_SCRIPT = f"{MIRROR_DIR}/sync.sh"
ARTIFACTS_LIST = f"{MIRROR_DIR}/artifacts.list"
MANIFEST_FILE = f"{MIRROR_DIR}/manifest.sha1"
STAGING_DIR = f"{MIRROR_DIR}/staging"
ARCHIVE_DIR = f"{MIRROR_DIR}/archive"
NGINX_DOCROOT = "/var/www/repo"

# Expected artifact URLs
EXPECTED_ARTIFACTS = [
    "http://127.0.0.1:8080/repo/com/example/core/1.2.0/core-1.2.0.jar",
    "http://127.0.0.1:8080/repo/com/example/utils/2.0.1/utils-2.0.1.jar",
    "http://127.0.0.1:8080/repo/com/example/auth/1.5.3/auth-1.5.3.jar",
    "http://127.0.0.1:8080/repo/com/example/data/3.1.0/data-3.1.0.jar",
    "http://127.0.0.1:8080/repo/com/example/web/2.2.0/web-2.2.0.jar",
    "http://127.0.0.1:8080/repo/com/example/cache/1.0.4/cache-1.0.4.jar",
    "http://127.0.0.1:8080/repo/com/example/logging/1.1.0/logging-1.1.0.jar",
    "http://127.0.0.1:8080/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar",
]

# Jars that have stale checksums in manifest
STALE_CHECKSUM_JARS = ["auth-1.5.3.jar", "cache-1.0.4.jar", "metrics-0.9.2.jar"]


class TestMirrorDirectoryStructure:
    """Test that the mirror directory structure exists."""

    def test_mirror_directory_exists(self):
        assert os.path.isdir(MIRROR_DIR), f"Mirror directory {MIRROR_DIR} does not exist"

    def test_staging_directory_exists(self):
        assert os.path.isdir(STAGING_DIR), f"Staging directory {STAGING_DIR} does not exist"

    def test_archive_directory_exists(self):
        assert os.path.isdir(ARCHIVE_DIR), f"Archive directory {ARCHIVE_DIR} does not exist"

    def test_staging_directory_is_empty(self):
        contents = os.listdir(STAGING_DIR)
        assert len(contents) == 0, f"Staging directory should be empty but contains: {contents}"

    def test_mirror_directory_is_writable(self):
        assert os.access(MIRROR_DIR, os.W_OK), f"Mirror directory {MIRROR_DIR} is not writable"


class TestSyncScript:
    """Test that sync.sh exists and is a valid bash script."""

    def test_sync_script_exists(self):
        assert os.path.isfile(SYNC_SCRIPT), f"Sync script {SYNC_SCRIPT} does not exist"

    def test_sync_script_is_readable(self):
        assert os.access(SYNC_SCRIPT, os.R_OK), f"Sync script {SYNC_SCRIPT} is not readable"

    def test_sync_script_is_bash_script(self):
        with open(SYNC_SCRIPT, 'r') as f:
            first_line = f.readline().strip()
        assert first_line.startswith('#!') and 'bash' in first_line, \
            f"Sync script should be a bash script, got shebang: {first_line}"

    def test_sync_script_contains_checksum_verification(self):
        with open(SYNC_SCRIPT, 'r') as f:
            content = f.read()
        assert 'sha1sum' in content or 'sha1' in content.lower(), \
            "Sync script should contain checksum verification logic"

    def test_sync_script_reads_artifacts_list(self):
        with open(SYNC_SCRIPT, 'r') as f:
            content = f.read()
        assert 'artifacts.list' in content, \
            "Sync script should reference artifacts.list"

    def test_sync_script_uses_manifest(self):
        with open(SYNC_SCRIPT, 'r') as f:
            content = f.read()
        assert 'manifest.sha1' in content, \
            "Sync script should reference manifest.sha1"


class TestArtifactsList:
    """Test the artifacts.list file."""

    def test_artifacts_list_exists(self):
        assert os.path.isfile(ARTIFACTS_LIST), f"Artifacts list {ARTIFACTS_LIST} does not exist"

    def test_artifacts_list_contains_expected_urls(self):
        with open(ARTIFACTS_LIST, 'r') as f:
            content = f.read()
        urls = [line.strip() for line in content.strip().split('\n') if line.strip()]

        assert len(urls) == 8, f"Expected 8 artifact URLs, found {len(urls)}"

        for expected_url in EXPECTED_ARTIFACTS:
            assert expected_url in urls, f"Missing expected artifact URL: {expected_url}"


class TestManifestFile:
    """Test the manifest.sha1 file."""

    def test_manifest_exists(self):
        assert os.path.isfile(MANIFEST_FILE), f"Manifest file {MANIFEST_FILE} does not exist"

    def test_manifest_has_checksums(self):
        with open(MANIFEST_FILE, 'r') as f:
            content = f.read()
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]

        assert len(lines) >= 8, f"Manifest should have at least 8 checksum entries, found {len(lines)}"

    def test_manifest_format_is_valid(self):
        with open(MANIFEST_FILE, 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Format should be "HASH  filename" or "HASH filename"
            parts = line.split()
            assert len(parts) >= 2, f"Invalid manifest line format: {line}"
            # SHA1 hash should be 40 hex characters
            hash_part = parts[0]
            assert len(hash_part) == 40, f"Invalid SHA1 hash length in line: {line}"
            assert all(c in '0123456789abcdefABCDEF' for c in hash_part), \
                f"Invalid SHA1 hash characters in line: {line}"


class TestNginxServer:
    """Test that nginx is running and serving artifacts."""

    def test_nginx_process_running(self):
        result = subprocess.run(['pgrep', '-x', 'nginx'], capture_output=True)
        assert result.returncode == 0, "nginx process is not running"

    def test_port_8080_is_listening(self):
        result = subprocess.run(
            ['ss', '-tlnp'],
            capture_output=True,
            text=True
        )
        assert ':8080' in result.stdout, "No service listening on port 8080"

    def test_nginx_serves_artifacts(self):
        # Test that we can reach one of the artifacts
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             'http://127.0.0.1:8080/repo/com/example/core/1.2.0/core-1.2.0.jar'],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == '200', \
            f"Failed to fetch artifact from nginx, HTTP status: {result.stdout.strip()}"

    def test_nginx_serves_sha1_sidecars(self):
        # Test that .sha1 sidecar files are available
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             'http://127.0.0.1:8080/repo/com/example/core/1.2.0/core-1.2.0.jar.sha1'],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == '200', \
            f"Failed to fetch .sha1 sidecar from nginx, HTTP status: {result.stdout.strip()}"


class TestNginxDocroot:
    """Test the nginx document root contains expected files."""

    def test_docroot_exists(self):
        assert os.path.isdir(NGINX_DOCROOT), f"Nginx docroot {NGINX_DOCROOT} does not exist"

    def test_all_jars_exist_in_docroot(self):
        jar_paths = [
            "/var/www/repo/com/example/core/1.2.0/core-1.2.0.jar",
            "/var/www/repo/com/example/utils/2.0.1/utils-2.0.1.jar",
            "/var/www/repo/com/example/auth/1.5.3/auth-1.5.3.jar",
            "/var/www/repo/com/example/data/3.1.0/data-3.1.0.jar",
            "/var/www/repo/com/example/web/2.2.0/web-2.2.0.jar",
            "/var/www/repo/com/example/cache/1.0.4/cache-1.0.4.jar",
            "/var/www/repo/com/example/logging/1.1.0/logging-1.1.0.jar",
            "/var/www/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar",
        ]
        for jar_path in jar_paths:
            assert os.path.isfile(jar_path), f"Jar file missing: {jar_path}"

    def test_all_sha1_sidecars_exist(self):
        sha1_paths = [
            "/var/www/repo/com/example/core/1.2.0/core-1.2.0.jar.sha1",
            "/var/www/repo/com/example/utils/2.0.1/utils-2.0.1.jar.sha1",
            "/var/www/repo/com/example/auth/1.5.3/auth-1.5.3.jar.sha1",
            "/var/www/repo/com/example/data/3.1.0/data-3.1.0.jar.sha1",
            "/var/www/repo/com/example/web/2.2.0/web-2.2.0.jar.sha1",
            "/var/www/repo/com/example/cache/1.0.4/cache-1.0.4.jar.sha1",
            "/var/www/repo/com/example/logging/1.1.0/logging-1.1.0.jar.sha1",
            "/var/www/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar.sha1",
        ]
        for sha1_path in sha1_paths:
            assert os.path.isfile(sha1_path), f"SHA1 sidecar file missing: {sha1_path}"

    def test_sha1_sidecars_match_jars(self):
        """Verify that .sha1 sidecar files contain correct checksums for their jars."""
        jar_sha1_pairs = [
            ("/var/www/repo/com/example/core/1.2.0/core-1.2.0.jar",
             "/var/www/repo/com/example/core/1.2.0/core-1.2.0.jar.sha1"),
            ("/var/www/repo/com/example/auth/1.5.3/auth-1.5.3.jar",
             "/var/www/repo/com/example/auth/1.5.3/auth-1.5.3.jar.sha1"),
        ]

        for jar_path, sha1_path in jar_sha1_pairs:
            # Get actual sha1 of jar
            result = subprocess.run(['sha1sum', jar_path], capture_output=True, text=True)
            actual_sha1 = result.stdout.split()[0]

            # Get expected sha1 from sidecar
            with open(sha1_path, 'r') as f:
                expected_sha1 = f.read().strip().split()[0]

            assert actual_sha1 == expected_sha1, \
                f"SHA1 sidecar mismatch for {jar_path}: actual={actual_sha1}, sidecar={expected_sha1}"


class TestStaleManifestBug:
    """Verify the bug condition: manifest has stale checksums for some jars."""

    def test_manifest_has_stale_checksums(self):
        """At least one of the 'stale' jars should have mismatched checksum in manifest."""
        with open(MANIFEST_FILE, 'r') as f:
            manifest_content = f.read()

        mismatches_found = 0

        for jar_name in STALE_CHECKSUM_JARS:
            # Find the manifest entry for this jar
            for line in manifest_content.strip().split('\n'):
                if jar_name in line:
                    manifest_hash = line.split()[0]

                    # Get the actual hash from the server's sidecar file
                    if 'auth' in jar_name:
                        sha1_url = 'http://127.0.0.1:8080/repo/com/example/auth/1.5.3/auth-1.5.3.jar.sha1'
                    elif 'cache' in jar_name:
                        sha1_url = 'http://127.0.0.1:8080/repo/com/example/cache/1.0.4/cache-1.0.4.jar.sha1'
                    elif 'metrics' in jar_name:
                        sha1_url = 'http://127.0.0.1:8080/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar.sha1'
                    else:
                        continue

                    result = subprocess.run(
                        ['curl', '-s', sha1_url],
                        capture_output=True,
                        text=True
                    )
                    server_hash = result.stdout.strip().split()[0]

                    if manifest_hash != server_hash:
                        mismatches_found += 1
                    break

        assert mismatches_found >= 1, \
            "Expected at least one stale checksum in manifest (this is the bug to fix)"


class TestRequiredTools:
    """Test that required tools are available."""

    def test_curl_available(self):
        result = subprocess.run(['which', 'curl'], capture_output=True)
        assert result.returncode == 0, "curl is not available"

    def test_sha1sum_available(self):
        result = subprocess.run(['which', 'sha1sum'], capture_output=True)
        assert result.returncode == 0, "sha1sum is not available"

    def test_bash_available(self):
        result = subprocess.run(['which', 'bash'], capture_output=True)
        assert result.returncode == 0, "bash is not available"

    def test_wget_available(self):
        result = subprocess.run(['which', 'wget'], capture_output=True)
        assert result.returncode == 0, "wget is not available"
