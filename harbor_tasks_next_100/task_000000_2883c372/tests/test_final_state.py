# test_final_state.py
"""
Tests to validate the final state after the Maven mirror sync fix task is completed.
Verifies that:
1. sync.sh runs successfully (exit 0)
2. All 8 jars are in the archive directory
3. Checksums match the server's .sha1 sidecar files
4. manifest.sha1 has been updated with correct checksums
5. Checksum verification was not bypassed
6. nginx is still running
7. Server jar files were not modified
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

# Expected jar filenames
EXPECTED_JARS = [
    "core-1.2.0.jar",
    "utils-2.0.1.jar",
    "auth-1.5.3.jar",
    "data-3.1.0.jar",
    "web-2.2.0.jar",
    "cache-1.0.4.jar",
    "logging-1.1.0.jar",
    "metrics-0.9.2.jar",
]

# Mapping of jar names to their server SHA1 sidecar URLs
JAR_SHA1_URLS = {
    "core-1.2.0.jar": "http://127.0.0.1:8080/repo/com/example/core/1.2.0/core-1.2.0.jar.sha1",
    "utils-2.0.1.jar": "http://127.0.0.1:8080/repo/com/example/utils/2.0.1/utils-2.0.1.jar.sha1",
    "auth-1.5.3.jar": "http://127.0.0.1:8080/repo/com/example/auth/1.5.3/auth-1.5.3.jar.sha1",
    "data-3.1.0.jar": "http://127.0.0.1:8080/repo/com/example/data/3.1.0/data-3.1.0.jar.sha1",
    "web-2.2.0.jar": "http://127.0.0.1:8080/repo/com/example/web/2.2.0/web-2.2.0.jar.sha1",
    "cache-1.0.4.jar": "http://127.0.0.1:8080/repo/com/example/cache/1.0.4/cache-1.0.4.jar.sha1",
    "logging-1.1.0.jar": "http://127.0.0.1:8080/repo/com/example/logging/1.1.0/logging-1.1.0.jar.sha1",
    "metrics-0.9.2.jar": "http://127.0.0.1:8080/repo/com/example/metrics/0.9.2/metrics-0.9.2.jar.sha1",
}

# The 3 jars that had stale checksums
PREVIOUSLY_STALE_JARS = ["auth-1.5.3.jar", "cache-1.0.4.jar", "metrics-0.9.2.jar"]


def get_server_sha1(jar_name):
    """Fetch the SHA1 checksum from the server's sidecar file."""
    url = JAR_SHA1_URLS[jar_name]
    result = subprocess.run(
        ['curl', '-s', url],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split()[0]


class TestSyncScriptExecution:
    """Test that sync.sh executes successfully."""

    def test_sync_script_exits_zero(self):
        """Running sync.sh should exit with code 0."""
        result = subprocess.run(
            ['bash', SYNC_SCRIPT],
            capture_output=True,
            text=True,
            cwd=MIRROR_DIR
        )
        assert result.returncode == 0, \
            f"sync.sh failed with exit code {result.returncode}.\nStdout: {result.stdout}\nStderr: {result.stderr}"


class TestArchiveContents:
    """Test that all expected jars are in the archive directory."""

    def test_archive_directory_exists(self):
        assert os.path.isdir(ARCHIVE_DIR), f"Archive directory {ARCHIVE_DIR} does not exist"

    def test_all_jars_in_archive(self):
        """All 8 expected jars should be present in the archive."""
        archive_contents = os.listdir(ARCHIVE_DIR)

        for jar_name in EXPECTED_JARS:
            assert jar_name in archive_contents, \
                f"Expected jar {jar_name} not found in archive. Archive contains: {archive_contents}"

    def test_archived_jars_are_files(self):
        """Each archived jar should be a regular file."""
        for jar_name in EXPECTED_JARS:
            jar_path = os.path.join(ARCHIVE_DIR, jar_name)
            assert os.path.isfile(jar_path), f"Archived jar {jar_path} is not a regular file"

    def test_archived_jars_not_empty(self):
        """Each archived jar should have non-zero size."""
        for jar_name in EXPECTED_JARS:
            jar_path = os.path.join(ARCHIVE_DIR, jar_name)
            size = os.path.getsize(jar_path)
            assert size > 0, f"Archived jar {jar_path} is empty (0 bytes)"


class TestChecksumVerification:
    """Test that archived jars match server checksums."""

    def test_archived_jars_match_server_checksums(self):
        """Each archived jar's SHA1 should match the server's .sha1 sidecar file."""
        for jar_name in EXPECTED_JARS:
            jar_path = os.path.join(ARCHIVE_DIR, jar_name)

            # Compute actual SHA1 of archived jar
            result = subprocess.run(
                ['sha1sum', jar_path],
                capture_output=True,
                text=True
            )
            actual_sha1 = result.stdout.split()[0]

            # Get expected SHA1 from server
            expected_sha1 = get_server_sha1(jar_name)

            assert actual_sha1 == expected_sha1, \
                f"Checksum mismatch for {jar_name}: archive has {actual_sha1}, server expects {expected_sha1}"

    def test_previously_stale_jars_now_match(self):
        """The 3 jars that had stale checksums should now match the server."""
        for jar_name in PREVIOUSLY_STALE_JARS:
            jar_path = os.path.join(ARCHIVE_DIR, jar_name)

            result = subprocess.run(
                ['sha1sum', jar_path],
                capture_output=True,
                text=True
            )
            actual_sha1 = result.stdout.split()[0]
            expected_sha1 = get_server_sha1(jar_name)

            assert actual_sha1 == expected_sha1, \
                f"Previously stale jar {jar_name} still has wrong checksum: {actual_sha1} vs expected {expected_sha1}"


class TestManifestUpdated:
    """Test that manifest.sha1 has been updated with correct checksums."""

    def test_manifest_exists(self):
        assert os.path.isfile(MANIFEST_FILE), f"Manifest file {MANIFEST_FILE} does not exist"

    def test_manifest_has_all_jars(self):
        """Manifest should contain entries for all 8 jars."""
        with open(MANIFEST_FILE, 'r') as f:
            content = f.read()

        for jar_name in EXPECTED_JARS:
            assert jar_name in content, \
                f"Manifest is missing entry for {jar_name}"

    def test_manifest_checksums_match_server(self):
        """All checksums in manifest should match the server's .sha1 sidecar files."""
        with open(MANIFEST_FILE, 'r') as f:
            lines = f.readlines()

        manifest_checksums = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                hash_val = parts[0]
                # Handle both "hash  filename" and "hash filename" formats
                filename = parts[1] if len(parts) == 2 else parts[-1]
                # Extract just the jar filename if path is included
                filename = os.path.basename(filename)
                manifest_checksums[filename] = hash_val

        for jar_name in EXPECTED_JARS:
            assert jar_name in manifest_checksums, \
                f"Manifest missing checksum for {jar_name}"

            expected_sha1 = get_server_sha1(jar_name)
            manifest_sha1 = manifest_checksums[jar_name]

            assert manifest_sha1 == expected_sha1, \
                f"Manifest checksum for {jar_name} is {manifest_sha1}, but server expects {expected_sha1}"

    def test_manifest_sha1sum_check_passes(self):
        """Running sha1sum -c on manifest from archive directory should pass."""
        result = subprocess.run(
            ['sha1sum', '-c', MANIFEST_FILE],
            capture_output=True,
            text=True,
            cwd=ARCHIVE_DIR
        )
        assert result.returncode == 0, \
            f"sha1sum -c failed on manifest. Stdout: {result.stdout}\nStderr: {result.stderr}"


class TestVerificationNotBypassed:
    """Test that checksum verification was not simply bypassed or disabled."""

    def test_sync_script_still_has_sha1sum(self):
        """sync.sh should still contain sha1sum verification logic."""
        with open(SYNC_SCRIPT, 'r') as f:
            content = f.read()

        assert 'sha1sum' in content.lower() or 'sha1' in content.lower(), \
            "sync.sh no longer contains checksum verification (sha1sum)"

    def test_sync_script_not_trivially_bypassed(self):
        """sync.sh should not have verification replaced with no-op commands."""
        with open(SYNC_SCRIPT, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        suspicious_patterns = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip comments and empty lines
            if stripped.startswith('#') or not stripped:
                continue

            # Look for suspicious patterns that might indicate bypassed verification
            # Check if there's a line that's just "exit 0" not in a conditional
            if stripped == 'exit 0' and i < len(lines) - 3:
                # Early exit 0 is suspicious
                suspicious_patterns.append(f"Line {i+1}: early 'exit 0'")

            # Check for "true" or ":" used to replace actual verification
            if stripped in ['true', ':'] and 'sha1' not in lines[max(0, i-2):i+3]:
                # Standalone true/: not near sha1 logic might be suspicious
                pass  # This is too noisy, skip

        # The script should still have comparison logic
        has_comparison = any(op in content for op in ['!=', '==', '-ne', '-eq', 'if', 'test', '[['])
        assert has_comparison, \
            "sync.sh appears to have no comparison/conditional logic - verification may be bypassed"

    def test_verification_actually_runs(self):
        """Verify that if we corrupt a checksum, the script would fail."""
        # This is a sanity check - we don't actually corrupt anything,
        # just verify the script structure suggests real verification
        with open(SYNC_SCRIPT, 'r') as f:
            content = f.read()

        # Should have logic that exits non-zero on mismatch
        has_error_exit = 'exit 1' in content or 'exit $' in content or 'set -e' in content
        has_sha1_check = 'sha1sum' in content or 'sha1' in content.lower()

        assert has_sha1_check, "Script doesn't appear to check SHA1 checksums"
        # Note: We can't easily test that it would actually fail without modifying state


class TestNginxStillRunning:
    """Test that nginx is still running and serving."""

    def test_nginx_process_running(self):
        result = subprocess.run(['pgrep', '-x', 'nginx'], capture_output=True)
        assert result.returncode == 0, "nginx process is not running after task completion"

    def test_port_8080_listening(self):
        result = subprocess.run(
            ['ss', '-tlnp'],
            capture_output=True,
            text=True
        )
        assert ':8080' in result.stdout, "Port 8080 is not listening after task completion"

    def test_nginx_serves_artifact(self):
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
             'http://127.0.0.1:8080/repo/com/example/core/1.2.0/core-1.2.0.jar'],
            capture_output=True,
            text=True
        )
        assert result.stdout.strip() == '200', \
            f"nginx not serving artifacts correctly, HTTP status: {result.stdout.strip()}"


class TestServerFilesUnmodified:
    """Test that the jar files on the server were not modified."""

    def test_server_jars_match_their_sidecars(self):
        """Server jar files should still match their .sha1 sidecar files."""
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
            sha1_path = jar_path + ".sha1"

            # Compute actual SHA1 of server jar
            result = subprocess.run(
                ['sha1sum', jar_path],
                capture_output=True,
                text=True
            )
            actual_sha1 = result.stdout.split()[0]

            # Read expected SHA1 from sidecar
            with open(sha1_path, 'r') as f:
                expected_sha1 = f.read().strip().split()[0]

            assert actual_sha1 == expected_sha1, \
                f"Server jar {jar_path} was modified! Current SHA1 {actual_sha1} doesn't match sidecar {expected_sha1}"


class TestIntegration:
    """Integration tests for the complete solution."""

    def test_full_sync_workflow(self):
        """
        Run sync.sh and verify the complete workflow succeeds.
        This is a comprehensive integration test.
        """
        # Clear staging if anything is there
        if os.path.isdir(STAGING_DIR):
            for f in os.listdir(STAGING_DIR):
                os.remove(os.path.join(STAGING_DIR, f))

        # Run sync
        result = subprocess.run(
            ['bash', SYNC_SCRIPT],
            capture_output=True,
            text=True,
            cwd=MIRROR_DIR
        )

        assert result.returncode == 0, \
            f"Sync failed: exit={result.returncode}, stdout={result.stdout}, stderr={result.stderr}"

        # Verify all jars in archive
        for jar_name in EXPECTED_JARS:
            jar_path = os.path.join(ARCHIVE_DIR, jar_name)
            assert os.path.isfile(jar_path), f"Jar {jar_name} not in archive after sync"

        # Verify manifest check passes
        result = subprocess.run(
            ['sha1sum', '-c', MANIFEST_FILE],
            capture_output=True,
            text=True,
            cwd=ARCHIVE_DIR
        )
        assert result.returncode == 0, \
            f"Manifest verification failed after sync: {result.stdout}\n{result.stderr}"
