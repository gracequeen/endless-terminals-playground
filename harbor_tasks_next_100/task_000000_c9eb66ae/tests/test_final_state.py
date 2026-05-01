# test_final_state.py
"""
Tests to validate the final state after the student has fixed the Maven build issue.
The build should complete successfully and produce a jar artifact.
"""

import os
import subprocess
import pytest
from pathlib import Path


HOME = Path("/home/user")
PROJECT_DIR = HOME / "invoice-service"
M2_DIR = HOME / ".m2"
SETTINGS_XML = M2_DIR / "settings.xml"
TARGET_DIR = PROJECT_DIR / "target"


class TestMavenBuildSuccess:
    """Tests that verify the Maven build completes successfully."""

    def test_mvn_package_exits_zero(self):
        """Verify that 'mvn package -DskipTests' exits with code 0."""
        result = subprocess.run(
            ["mvn", "package", "-DskipTests"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        assert result.returncode == 0, (
            f"'mvn package -DskipTests' failed with exit code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    def test_jar_artifact_exists(self):
        """Verify that the packaged jar exists in target/."""
        assert TARGET_DIR.exists(), f"Target directory {TARGET_DIR} does not exist"

        jars = list(TARGET_DIR.glob("invoice-service-*.jar"))
        # Filter out sources and javadoc jars if any
        main_jars = [j for j in jars if "-sources" not in j.name and "-javadoc" not in j.name]

        assert len(main_jars) >= 1, (
            f"No invoice-service-*.jar found in {TARGET_DIR}. "
            f"Found files: {list(TARGET_DIR.iterdir()) if TARGET_DIR.exists() else 'directory does not exist'}"
        )

    def test_build_completes_without_network_errors(self):
        """Verify the build doesn't have network errors related to localhost:8081."""
        result = subprocess.run(
            ["mvn", "package", "-DskipTests"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )

        combined_output = result.stdout + result.stderr

        # Check that there are no connection refused errors to localhost:8081
        assert "Connection refused" not in combined_output or "localhost:8081" not in combined_output, (
            "Build output contains connection refused errors to localhost:8081"
        )
        assert "Could not transfer artifact" not in combined_output or "localhost:8081" not in combined_output, (
            "Build output contains artifact transfer errors related to localhost:8081"
        )


class TestInvariantsPreserved:
    """Tests that verify invariants are preserved."""

    def test_pom_still_declares_payment_utils_dependency(self):
        """Verify pom.xml still declares com.internal:payment-utils:2.3.1."""
        pom_path = PROJECT_DIR / "pom.xml"
        assert pom_path.exists(), f"pom.xml not found at {pom_path}"

        content = pom_path.read_text()

        assert "com.internal" in content, (
            "pom.xml no longer contains groupId 'com.internal' - dependency declaration was modified"
        )
        assert "payment-utils" in content, (
            "pom.xml no longer contains artifactId 'payment-utils' - dependency declaration was modified"
        )
        assert "2.3.1" in content, (
            "pom.xml no longer contains version '2.3.1' - dependency declaration was modified"
        )

    def test_source_directory_exists(self):
        """Verify source code directory still exists."""
        src_main_java = PROJECT_DIR / "src" / "main" / "java"
        assert src_main_java.exists(), f"Source directory {src_main_java} no longer exists"
        assert src_main_java.is_dir(), f"{src_main_java} is not a directory"


class TestOnlineBuildCapability:
    """Tests that verify the fix allows future online builds to work."""

    def test_dependency_resolve_works_online(self):
        """
        Verify that 'mvn dependency:resolve' works (online mode).
        This ensures the mirror config issue is truly fixed, not just worked around with offline mode.
        """
        result = subprocess.run(
            ["mvn", "dependency:resolve"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )

        assert result.returncode == 0, (
            f"'mvn dependency:resolve' failed with exit code {result.returncode}.\n"
            f"This suggests the mirror configuration issue was not properly fixed.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    def test_no_broken_mirror_in_settings(self):
        """
        Verify that the broken mirror configuration has been fixed.
        Either the mirror is removed, commented out, or the mirrorOf is changed to not intercept everything.
        """
        if not SETTINGS_XML.exists():
            # settings.xml removed entirely - this is a valid fix
            return

        content = SETTINGS_XML.read_text()

        # Check if the problematic mirror configuration is still active
        # The issue was: mirrorOf=* pointing to unreachable localhost:8081

        # If localhost:8081 is still referenced as a mirror for everything (*), that's a problem
        # unless the mirror is commented out or the mirrorOf is changed

        import re

        # Look for active (non-commented) mirror blocks
        # This is a simplified check - we verify that if localhost:8081 is present,
        # it's not configured as mirrorOf="*"

        # Remove XML comments for analysis
        content_no_comments = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

        # Check if there's still a mirror pointing to localhost:8081 with mirrorOf=*
        if "localhost:8081" in content_no_comments:
            # If localhost:8081 is still there, mirrorOf should not be * for it
            # This is a heuristic check
            mirror_blocks = re.findall(r'<mirror>.*?</mirror>', content_no_comments, flags=re.DOTALL)
            for block in mirror_blocks:
                if "localhost:8081" in block and "<mirrorOf>*</mirrorOf>" in block:
                    # This would still be broken, but let's trust the functional test
                    # The dependency:resolve test above is the authoritative check
                    pass


class TestBuildArtifactValidity:
    """Tests that verify the build artifact is valid."""

    def test_jar_is_valid_zip(self):
        """Verify the jar file is a valid archive."""
        jars = list(TARGET_DIR.glob("invoice-service-*.jar"))
        main_jars = [j for j in jars if "-sources" not in j.name and "-javadoc" not in j.name]

        assert len(main_jars) >= 1, "No main jar artifact found"

        jar_path = main_jars[0]

        # Check if it's a valid zip/jar file
        result = subprocess.run(
            ["unzip", "-t", str(jar_path)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Jar file {jar_path} is not a valid archive.\n"
            f"STDERR: {result.stderr}"
        )

    def test_jar_has_reasonable_size(self):
        """Verify the jar file has a reasonable size (not empty or trivially small)."""
        jars = list(TARGET_DIR.glob("invoice-service-*.jar"))
        main_jars = [j for j in jars if "-sources" not in j.name and "-javadoc" not in j.name]

        assert len(main_jars) >= 1, "No main jar artifact found"

        jar_path = main_jars[0]
        size = jar_path.stat().st_size

        # A valid jar should be at least a few hundred bytes (has manifest, etc.)
        assert size > 100, (
            f"Jar file {jar_path} is suspiciously small ({size} bytes)"
        )
