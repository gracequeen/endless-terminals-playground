# test_final_state.py
"""
Tests to validate the final state of the filesystem after the student
has completed the Maven repository repair task.
"""

import os
import subprocess
import pytest


class TestSyncScriptFixed:
    """Verify the sync script exists and the bug is fixed."""

    def test_sync_script_exists(self):
        """The sync.sh script must still exist."""
        path = "/home/user/artifact-sync/sync.sh"
        assert os.path.isfile(path), f"Sync script not found at {path} - script should not be deleted"

    def test_sync_script_bug_fixed(self):
        """The sync.sh script should have the variable typo fixed."""
        path = "/home/user/artifact-sync/sync.sh"
        with open(path, 'r') as f:
            content = f.read()

        # Count occurrences of both variable names
        # The bug was using both CACHE_FILE and CACHED_FILE inconsistently
        # After fix, either:
        # 1. Only CACHE_FILE is used consistently, OR
        # 2. Only CACHED_FILE is used consistently, OR
        # 3. If both exist, they should be properly defined/used (not a typo)

        # Check that we don't have the inconsistent usage pattern
        # The original bug: one variable is defined, the other is used
        lines = content.split('\n')

        cache_file_assignments = []
        cached_file_assignments = []
        cache_file_usages = []
        cached_file_usages = []

        for line in lines:
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            # Check for assignments (VAR=something)
            if 'CACHE_FILE=' in line and not line.strip().startswith('#'):
                cache_file_assignments.append(line)
            if 'CACHED_FILE=' in line and not line.strip().startswith('#'):
                cached_file_assignments.append(line)

            # Check for usages ($VAR or ${VAR})
            if '$CACHE_FILE' in line or '${CACHE_FILE}' in line:
                cache_file_usages.append(line)
            if '$CACHED_FILE' in line or '${CACHED_FILE}' in line:
                cached_file_usages.append(line)

        # The bug scenario: one is assigned, the other is used in cp
        # After fix: consistent usage

        # If CACHED_FILE is assigned but CACHE_FILE is used (or vice versa) without being assigned, that's the bug
        has_cache_file_def = len(cache_file_assignments) > 0
        has_cached_file_def = len(cached_file_assignments) > 0
        has_cache_file_use = len(cache_file_usages) > 0
        has_cached_file_use = len(cached_file_usages) > 0

        # Bug pattern: defined one, used the other (without defining it)
        bug_pattern_1 = has_cached_file_def and has_cache_file_use and not has_cache_file_def
        bug_pattern_2 = has_cache_file_def and has_cached_file_use and not has_cached_file_def

        assert not (bug_pattern_1 or bug_pattern_2), \
            "Sync script still contains the variable typo bug (CACHE_FILE vs CACHED_FILE inconsistency)"

    def test_artifacts_txt_unchanged(self):
        """The artifacts.txt file must still exist."""
        path = "/home/user/artifact-sync/artifacts.txt"
        assert os.path.isfile(path), f"Artifacts list not found at {path}"


class TestCacheUnchanged:
    """Verify the cache directory contents are unchanged."""

    CACHE_BASE = "/home/user/artifact-sync/cache"

    EXPECTED_CACHE_JARS = [
        "com/example/core/1.2.0/core-1.2.0.jar",
        "com/example/utils/3.1.0/utils-3.1.0.jar",
        "org/internal/logging/2.0.0/logging-2.0.0.jar",
        "org/internal/config/1.5.2/config-1.5.2.jar",
        "net/tools/parser/4.0.1/parser-4.0.1.jar",
    ]

    def test_cache_directory_exists(self):
        """The cache directory must still exist."""
        assert os.path.isdir(self.CACHE_BASE), f"Cache directory not found at {self.CACHE_BASE}"

    @pytest.mark.parametrize("jar_path", EXPECTED_CACHE_JARS)
    def test_cache_jar_still_exists(self, jar_path):
        """Each cached jar must still exist."""
        full_path = os.path.join(self.CACHE_BASE, jar_path)
        assert os.path.isfile(full_path), f"Cache jar missing at {full_path} - cache should be unchanged"

    @pytest.mark.parametrize("jar_path", EXPECTED_CACHE_JARS)
    def test_cache_jar_still_non_empty(self, jar_path):
        """Each cached jar must still be non-empty."""
        full_path = os.path.join(self.CACHE_BASE, jar_path)
        assert os.path.isfile(full_path), f"Cache jar not found at {full_path}"
        size = os.path.getsize(full_path)
        assert size > 0, f"Cache jar at {full_path} is now empty - cache should be unchanged"


class TestMavenRepositoryRepaired:
    """Verify the Maven repository is in a consistent state."""

    REPO_BASE = "/var/repo/maven"

    PREVIOUSLY_BROKEN_JARS = [
        "com/example/core/1.2.0/core-1.2.0.jar",
        "com/example/utils/3.1.0/utils-3.1.0.jar",
        "org/internal/logging/2.0.0/logging-2.0.0.jar",
        "org/internal/config/1.5.2/config-1.5.2.jar",
        "net/tools/parser/4.0.1/parser-4.0.1.jar",
    ]

    def test_repo_directory_exists(self):
        """The Maven repository directory must exist."""
        assert os.path.isdir(self.REPO_BASE), f"Maven repo directory not found at {self.REPO_BASE}"

    def test_repo_still_has_12_jars(self):
        """Repository should still contain exactly 12 jar files."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f"],
            capture_output=True,
            text=True
        )
        jars = [line for line in result.stdout.strip().split("\n") if line]
        assert len(jars) == 12, f"Expected 12 jars in repo, found {len(jars)}"

    def test_repo_still_has_12_sha1_files(self):
        """Repository should still contain exactly 12 .sha1 sidecar files."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar.sha1", "-type", "f"],
            capture_output=True,
            text=True
        )
        sha1_files = [line for line in result.stdout.strip().split("\n") if line]
        assert len(sha1_files) == 12, \
            f"Expected 12 .sha1 files in repo, found {len(sha1_files)} - .sha1 files should not be deleted"

    def test_no_empty_jars(self):
        """No jars should be empty (zero bytes)."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f", "-empty"],
            capture_output=True,
            text=True
        )
        empty_jars = [line for line in result.stdout.strip().split("\n") if line]
        assert len(empty_jars) == 0, \
            f"Found {len(empty_jars)} empty jars that should have been repaired: {empty_jars}"

    @pytest.mark.parametrize("jar_path", PREVIOUSLY_BROKEN_JARS)
    def test_previously_broken_jar_now_non_empty(self, jar_path):
        """Each previously broken jar should now be non-empty."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        assert os.path.isfile(full_path), f"Jar not found at {full_path}"
        size = os.path.getsize(full_path)
        assert size > 0, f"Jar at {full_path} is still empty (0 bytes) - should have been repaired"

    @pytest.mark.parametrize("jar_path", PREVIOUSLY_BROKEN_JARS)
    def test_previously_broken_jar_has_sha1(self, jar_path):
        """Each previously broken jar should still have its .sha1 sidecar."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        sha1_path = full_path + ".sha1"
        assert os.path.isfile(sha1_path), \
            f"SHA1 sidecar missing at {sha1_path} - .sha1 files should not be deleted"


class TestChecksumVerification:
    """Verify all jars match their SHA1 sidecars."""

    REPO_BASE = "/var/repo/maven"

    def test_all_jars_match_sha1(self):
        """Every jar with a .sha1 sidecar must match the checksum."""
        # Find all jar files
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f"],
            capture_output=True,
            text=True
        )
        jars = [line for line in result.stdout.strip().split("\n") if line]

        assert len(jars) > 0, "No jar files found in repository"

        mismatches = []
        missing_sha1 = []

        for jar_path in jars:
            sha1_path = jar_path + ".sha1"

            if not os.path.isfile(sha1_path):
                missing_sha1.append(jar_path)
                continue

            # Compute actual SHA1
            result = subprocess.run(
                ["sha1sum", jar_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                mismatches.append(f"{jar_path}: failed to compute sha1sum")
                continue

            actual_sha1 = result.stdout.strip().split()[0].lower()

            # Read expected SHA1
            with open(sha1_path, 'r') as f:
                expected_sha1_content = f.read().strip()

            # SHA1 file might contain just the hash or "hash  filename" format
            expected_sha1 = expected_sha1_content.split()[0].lower()

            if actual_sha1 != expected_sha1:
                mismatches.append(
                    f"{jar_path}: actual={actual_sha1}, expected={expected_sha1}"
                )

        assert len(missing_sha1) == 0, \
            f"Jars missing .sha1 sidecars: {missing_sha1}"

        assert len(mismatches) == 0, \
            f"SHA1 checksum mismatches found:\n" + "\n".join(mismatches)

    def test_all_12_jars_verified(self):
        """Verify we're checking all 12 jars."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar", "-type", "f"],
            capture_output=True,
            text=True
        )
        jars = [line for line in result.stdout.strip().split("\n") if line]

        verified_count = 0
        for jar_path in jars:
            sha1_path = jar_path + ".sha1"
            if os.path.isfile(sha1_path):
                # Compute and verify
                result = subprocess.run(
                    ["sha1sum", jar_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    actual_sha1 = result.stdout.strip().split()[0].lower()
                    with open(sha1_path, 'r') as f:
                        expected_sha1 = f.read().strip().split()[0].lower()
                    if actual_sha1 == expected_sha1:
                        verified_count += 1

        assert verified_count == 12, \
            f"Expected 12 jars to pass verification, only {verified_count} passed"


class TestSha1FilesUnchanged:
    """Verify .sha1 files were not modified (they were already correct)."""

    REPO_BASE = "/var/repo/maven"

    def test_sha1_files_non_empty(self):
        """All .sha1 files should be non-empty."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar.sha1", "-type", "f"],
            capture_output=True,
            text=True
        )
        sha1_files = [line for line in result.stdout.strip().split("\n") if line]

        empty_sha1 = []
        for sha1_path in sha1_files:
            if os.path.getsize(sha1_path) == 0:
                empty_sha1.append(sha1_path)

        assert len(empty_sha1) == 0, f"Found empty .sha1 files: {empty_sha1}"

    def test_sha1_files_contain_valid_hashes(self):
        """All .sha1 files should contain valid 40-character hex hashes."""
        result = subprocess.run(
            ["find", self.REPO_BASE, "-name", "*.jar.sha1", "-type", "f"],
            capture_output=True,
            text=True
        )
        sha1_files = [line for line in result.stdout.strip().split("\n") if line]

        invalid_sha1 = []
        for sha1_path in sha1_files:
            with open(sha1_path, 'r') as f:
                content = f.read().strip()

            # Extract the hash (first token)
            hash_value = content.split()[0] if content else ""

            # Validate it's a 40-character hex string
            if len(hash_value) != 40:
                invalid_sha1.append(f"{sha1_path}: hash length {len(hash_value)} != 40")
            elif not all(c in '0123456789abcdefABCDEF' for c in hash_value):
                invalid_sha1.append(f"{sha1_path}: invalid hex characters")

        assert len(invalid_sha1) == 0, f"Invalid .sha1 files: {invalid_sha1}"


class TestSpecificJarsRepaired:
    """Test each specific jar that was broken is now repaired."""

    REPO_BASE = "/var/repo/maven"
    CACHE_BASE = "/home/user/artifact-sync/cache"

    BROKEN_JARS = [
        "com/example/core/1.2.0/core-1.2.0.jar",
        "com/example/utils/3.1.0/utils-3.1.0.jar",
        "org/internal/logging/2.0.0/logging-2.0.0.jar",
        "org/internal/config/1.5.2/config-1.5.2.jar",
        "net/tools/parser/4.0.1/parser-4.0.1.jar",
    ]

    @pytest.mark.parametrize("jar_path", BROKEN_JARS)
    def test_repaired_jar_matches_sha1(self, jar_path):
        """Each repaired jar must match its SHA1 checksum."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        sha1_path = full_path + ".sha1"

        assert os.path.isfile(full_path), f"Jar not found at {full_path}"
        assert os.path.isfile(sha1_path), f"SHA1 sidecar not found at {sha1_path}"

        # Compute actual SHA1
        result = subprocess.run(
            ["sha1sum", full_path],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to compute sha1sum for {full_path}"

        actual_sha1 = result.stdout.strip().split()[0].lower()

        # Read expected SHA1
        with open(sha1_path, 'r') as f:
            expected_sha1 = f.read().strip().split()[0].lower()

        assert actual_sha1 == expected_sha1, \
            f"Jar {full_path} SHA1 mismatch: actual={actual_sha1}, expected={expected_sha1}"

    @pytest.mark.parametrize("jar_path", BROKEN_JARS)
    def test_repaired_jar_has_reasonable_size(self, jar_path):
        """Each repaired jar should have a reasonable size (not tiny)."""
        full_path = os.path.join(self.REPO_BASE, jar_path)
        size = os.path.getsize(full_path)
        # Jars should be at least 1KB (actual ones are 50KB-2MB per task description)
        assert size >= 1024, \
            f"Jar at {full_path} is only {size} bytes - seems too small for a valid jar"
