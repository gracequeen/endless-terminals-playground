# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student
performs the Maven repository repair task.
"""

import os
import subprocess
import pytest


class TestSyncScriptExists:
    """Verify the sync script and related files exist."""

    def test_sync_script_exists(self):
        """The sync.sh script must exist."""
        path = "/home/user/artifact-sync/sync.sh"
        assert os.path.isfile(path), f"Sync script not found at {path}"

    def test_sync_script_is_readable(self):
        """The sync.sh script must be readable."""
        path = "/home/user/artifact-sync/sync.sh"
        assert os.access(path, os.R_OK), f"Sync script at {path} is not readable"

    def test_artifacts_txt_exists(self):
        """The artifacts.txt file must exist."""
        path = "/home/user/artifact-sync/artifacts.txt"
        assert os.path.isfile(path), f"Artifacts list not found at {path}"

    def test_artifact_sync_directory_writable(self):
        """The artifact-sync directory must be writable."""
        path = "/home/user/artifact-sync"
        assert os.path.isdir(path), f"Directory {path} does not exist"
        assert os.access(path, os.W_OK), f"Directory {path} is not writable"


class TestCacheDirectory:
    """Verify the cache directory contains the expected artifacts."""

    CACHE_BASE = "/home/user/artifact-sync/cache"

    EXPECTED_CACHE_JARS = [
        "com/example/core/1.2.0/core-1.2.0.jar",
        "com/example/utils/3.1.0/utils-3.1.0.jar",
        "org/internal/logging/2.0.0/logging-2.0.0.jar",
        "org/internal/config/1.5.2/config-1.5.2.jar",
        "net/tools/parser/4.0.1/parser-4.0.1.jar",
    ]

    def test_cache_directory_exists(self):
        """The cache directory must exist."""
        assert os.path.isdir(self.CACHE_BASE), f"Cache directory not found at {self.CACHE_BASE}"

    @pytest.mark.parametrize("jar_path", EXPECTED_CACHE_JARS)
    def test_cache_jar_exists(self, jar_path):
        """Each expected jar must exist in the cache."""
        full_path = os.path.join(self.CACHE_BASE, jar_path)
        assert os.path.isfile(full_path), f"Cache jar not found at {full_path}"

    @pytest.mark.parametrize("jar_path", EXPECTED_CACHE_JARS)
    def test_cache_jar_non_empty(self, jar_path):
        """Each cached jar must be non-empty (valid source for repair)."""
        full_path = os.path.join(self.CACHE_BASE, jar_path)
        assert os.path.isfile(full_path), f"Cache jar not found at {full_path}"
        size = os.path.getsize(full_path)
        assert size > 0, f"Cache jar at {full_path} is empty (0 bytes), should contain valid data"

    def test_cache_has_at_least_12_jars(self):
        """Cache should contain at least 12 jar files."""
        result = subprocess.run(
            ["find", self.CACHE_BASE, "-name", "*.jar", "-type", "f"],
            capture_output=True,
            text=True
        )
        jars = [line for line in result.stdout.strip().split("\n") if line]
        assert len(jars) >= 12, f"Expected at least 12 jars in cache, found {len(jars)}"


class TestMavenRepository:
    """Verify the Maven repository has the expected structure with broken jars."""

    REPO_BASE = "/var/repo/maven"

    BROKEN_JARS = [
        "com/example/core/1.2.0/core-1.2.0.jar",
        "com/example/utils/3.1.0/utils-3.1.0.jar",
        "org/internal/logging/2.0.0/logging-2.0.0.jar",
        "org/internal/config/1.5.2/config-1.5.2.jar",
        "net/tools/parser/4.0.1/parser-4.0.1.jar",
    ]

    def test_repo_directory_exists(self):
        """The Maven repository directory must exist."""
        assert os.path.isdir(self.REPO_BASE), f"Maven repo directory not found at {self.REPO_BASE}"

    def test_repo_directory_writable(self):
        """The Maven repository directory must be writable."""
        assert os.access(self.REPO_BASE, os.W_OK), f"Maven repo directory {self.REPO_BASE} is not writable"

    def test_repo_has_12_jars(self):
        """Repository should contain exactly 12 jar files."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f"],
            capture_output=True,
            text=True
        )
        jars = [line for line in result.stdout.strip().split("\n") if line]
        assert len(jars) == 12, f"Expected 12 jars in repo, found {len(jars)}"

    def test_repo_has_12_sha1_files(self):
        """Repository should contain exactly 12 .sha1 sidecar files."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar.sha1", "-type", "f"],
            capture_output=True,
            text=True
        )
        sha1_files = [line for line in result.stdout.strip().split("\n") if line]
        assert len(sha1_files) == 12, f"Expected 12 .sha1 files in repo, found {len(sha1_files)}"

    @pytest.mark.parametrize("jar_path", BROKEN_JARS)
    def test_broken_jar_exists(self, jar_path):
        """Each broken jar file must exist in the repo."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        assert os.path.isfile(full_path), f"Broken jar not found at {full_path}"

    @pytest.mark.parametrize("jar_path", BROKEN_JARS)
    def test_broken_jar_is_zero_bytes(self, jar_path):
        """Each broken jar should be zero bytes (this is the bug to fix)."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        assert os.path.isfile(full_path), f"Jar not found at {full_path}"
        size = os.path.getsize(full_path)
        assert size == 0, f"Expected jar at {full_path} to be 0 bytes (broken), but it's {size} bytes"

    @pytest.mark.parametrize("jar_path", BROKEN_JARS)
    def test_broken_jar_has_sha1_sidecar(self, jar_path):
        """Each broken jar should have a corresponding .sha1 file."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        sha1_path = full_path + ".sha1"
        assert os.path.isfile(sha1_path), f"SHA1 sidecar not found at {sha1_path}"

    @pytest.mark.parametrize("jar_path", BROKEN_JARS)
    def test_sha1_file_non_empty(self, jar_path):
        """Each .sha1 file should be non-empty (contains valid checksum)."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        sha1_path = full_path + ".sha1"
        assert os.path.isfile(sha1_path), f"SHA1 sidecar not found at {sha1_path}"
        size = os.path.getsize(sha1_path)
        assert size > 0, f"SHA1 file at {sha1_path} is empty"

    def test_some_jars_are_valid(self):
        """At least 7 jars should be non-empty (the ones that weren't broken)."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f", "!", "-empty"],
            capture_output=True,
            text=True
        )
        valid_jars = [line for line in result.stdout.strip().split("\n") if line]
        assert len(valid_jars) >= 7, f"Expected at least 7 valid (non-empty) jars, found {len(valid_jars)}"

    def test_exactly_5_empty_jars(self):
        """Exactly 5 jars should be empty (zero bytes)."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f", "-empty"],
            capture_output=True,
            text=True
        )
        empty_jars = [line for line in result.stdout.strip().split("\n") if line]
        assert len(empty_jars) == 5, f"Expected exactly 5 empty jars, found {len(empty_jars)}"


class TestSyncScriptHasBug:
    """Verify the sync script contains the variable typo bug."""

    def test_sync_script_contains_variable_typo(self):
        """The sync.sh script should contain the bug (CACHE_FILE vs CACHED_FILE typo)."""
        path = "/home/user/artifact-sync/sync.sh"
        with open(path, 'r') as f:
            content = f.read()

        # The bug is that the script uses both $CACHE_FILE and $CACHED_FILE
        # One is defined, the other is used in cp (or vice versa)
        has_cache_file = "CACHE_FILE" in content or "$CACHE_FILE" in content
        has_cached_file = "CACHED_FILE" in content or "$CACHED_FILE" in content

        assert has_cache_file or has_cached_file, \
            "Sync script should contain CACHE_FILE or CACHED_FILE variable"

        # Check that both variants exist (indicating the typo)
        assert has_cache_file and has_cached_file, \
            "Sync script should contain the variable typo bug (both CACHE_FILE and CACHED_FILE present)"


class TestRequiredTools:
    """Verify required tools are available."""

    @pytest.mark.parametrize("tool", ["sha1sum", "find", "cp", "bash", "file", "diff"])
    def test_tool_available(self, tool):
        """Required tools must be available in PATH."""
        result = subprocess.run(["which", tool], capture_output=True)
        assert result.returncode == 0, f"Required tool '{tool}' not found in PATH"
