# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the Maven build fix task.
"""

import os
import subprocess
import pytest
from pathlib import Path


HOME = Path("/home/user")
PROJECT_DIR = HOME / "invoice-service"
M2_DIR = HOME / ".m2"
SETTINGS_XML = M2_DIR / "settings.xml"
DEPENDENCY_CACHE_DIR = M2_DIR / "repository" / "com" / "internal" / "payment-utils" / "2.3.1"


class TestProjectStructure:
    """Tests for the Maven project structure."""

    def test_project_directory_exists(self):
        """Verify the invoice-service project directory exists."""
        assert PROJECT_DIR.exists(), f"Project directory {PROJECT_DIR} does not exist"
        assert PROJECT_DIR.is_dir(), f"{PROJECT_DIR} is not a directory"

    def test_pom_xml_exists(self):
        """Verify pom.xml exists in the project root."""
        pom_path = PROJECT_DIR / "pom.xml"
        assert pom_path.exists(), f"pom.xml not found at {pom_path}"
        assert pom_path.is_file(), f"{pom_path} is not a file"

    def test_src_main_java_exists(self):
        """Verify standard Maven source directory structure exists."""
        src_main_java = PROJECT_DIR / "src" / "main" / "java"
        assert src_main_java.exists(), f"Source directory {src_main_java} does not exist"
        assert src_main_java.is_dir(), f"{src_main_java} is not a directory"

    def test_pom_declares_payment_utils_dependency(self):
        """Verify pom.xml declares the com.internal:payment-utils:2.3.1 dependency."""
        pom_path = PROJECT_DIR / "pom.xml"
        content = pom_path.read_text()

        assert "com.internal" in content, "pom.xml does not contain groupId 'com.internal'"
        assert "payment-utils" in content, "pom.xml does not contain artifactId 'payment-utils'"
        assert "2.3.1" in content, "pom.xml does not contain version '2.3.1'"


class TestMavenConfiguration:
    """Tests for Maven configuration files."""

    def test_m2_directory_exists(self):
        """Verify .m2 directory exists."""
        assert M2_DIR.exists(), f"Maven directory {M2_DIR} does not exist"
        assert M2_DIR.is_dir(), f"{M2_DIR} is not a directory"

    def test_settings_xml_exists(self):
        """Verify settings.xml exists."""
        assert SETTINGS_XML.exists(), f"settings.xml not found at {SETTINGS_XML}"
        assert SETTINGS_XML.is_file(), f"{SETTINGS_XML} is not a file"

    def test_settings_xml_has_nexus_mirror(self):
        """Verify settings.xml configures the nexus-internal mirror."""
        content = SETTINGS_XML.read_text()

        assert "<mirrors>" in content, "settings.xml does not contain <mirrors> section"
        assert "nexus-internal" in content, "settings.xml does not contain 'nexus-internal' mirror id"
        assert "<mirrorOf>*</mirrorOf>" in content, "settings.xml does not have mirrorOf set to '*'"
        assert "localhost:8081" in content, "settings.xml does not reference localhost:8081"

    def test_m2_directory_is_writable(self):
        """Verify .m2 directory is writable."""
        assert os.access(M2_DIR, os.W_OK), f"{M2_DIR} is not writable"

    def test_project_directory_is_writable(self):
        """Verify project directory is writable."""
        assert os.access(PROJECT_DIR, os.W_OK), f"{PROJECT_DIR} is not writable"


class TestCachedDependency:
    """Tests for the pre-cached dependency."""

    def test_dependency_cache_directory_exists(self):
        """Verify the cached dependency directory exists."""
        assert DEPENDENCY_CACHE_DIR.exists(), f"Dependency cache directory {DEPENDENCY_CACHE_DIR} does not exist"
        assert DEPENDENCY_CACHE_DIR.is_dir(), f"{DEPENDENCY_CACHE_DIR} is not a directory"

    def test_cached_jar_exists(self):
        """Verify the cached jar file exists."""
        jar_file = DEPENDENCY_CACHE_DIR / "payment-utils-2.3.1.jar"
        assert jar_file.exists(), f"Cached jar not found at {jar_file}"

    def test_cached_pom_exists(self):
        """Verify the cached pom file exists."""
        pom_file = DEPENDENCY_CACHE_DIR / "payment-utils-2.3.1.pom"
        assert pom_file.exists(), f"Cached pom not found at {pom_file}"

    def test_remote_repositories_file_exists(self):
        """Verify _remote.repositories file exists."""
        remote_repos_file = DEPENDENCY_CACHE_DIR / "_remote.repositories"
        assert remote_repos_file.exists(), f"_remote.repositories not found at {remote_repos_file}"

    def test_remote_repositories_references_nexus_internal(self):
        """Verify _remote.repositories marks artifacts as sourced from nexus-internal."""
        remote_repos_file = DEPENDENCY_CACHE_DIR / "_remote.repositories"
        content = remote_repos_file.read_text()

        assert "nexus-internal" in content, "_remote.repositories does not reference 'nexus-internal'"
        assert "payment-utils-2.3.1.pom>nexus-internal" in content, \
            "_remote.repositories does not have pom marked for nexus-internal"
        assert "payment-utils-2.3.1.jar>nexus-internal" in content, \
            "_remote.repositories does not have jar marked for nexus-internal"


class TestNexusServerNotRunning:
    """Tests to verify Nexus server is NOT running."""

    def test_port_8081_not_listening(self):
        """Verify nothing is listening on localhost:8081."""
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True,
            text=True
        )

        # Check that port 8081 is not in the listening ports
        assert ":8081" not in result.stdout, \
            "Something is listening on port 8081, but Nexus should NOT be running"

    def test_nexus_url_unreachable(self):
        """Verify the Nexus mirror URL is unreachable."""
        # Try to connect to localhost:8081 - should fail
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
             "--connect-timeout", "2", "http://localhost:8081/repository/maven-public/"],
            capture_output=True,
            text=True
        )

        # Should get connection refused or timeout (exit code != 0 or http_code 000)
        http_code = result.stdout.strip()
        assert http_code == "000" or result.returncode != 0, \
            f"Nexus URL appears to be reachable (HTTP {http_code}), but it should be unreachable"


class TestMavenInstallation:
    """Tests for Maven and Java installation."""

    def test_maven_is_installed(self):
        """Verify Maven is installed and on PATH."""
        result = subprocess.run(
            ["which", "mvn"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Maven (mvn) is not installed or not on PATH"

    def test_maven_version(self):
        """Verify Maven 3.9.x is installed."""
        result = subprocess.run(
            ["mvn", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Failed to get Maven version"
        assert "Apache Maven 3.9" in result.stdout, \
            f"Expected Maven 3.9.x, got: {result.stdout}"

    def test_java_is_installed(self):
        """Verify Java is installed and on PATH."""
        result = subprocess.run(
            ["which", "java"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Java is not installed or not on PATH"

    def test_java_version(self):
        """Verify Java 17 is installed."""
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        # Java version info goes to stderr
        version_output = result.stderr + result.stdout
        assert result.returncode == 0, "Failed to get Java version"
        assert "17" in version_output, \
            f"Expected Java 17, got: {version_output}"


class TestNoTargetDirectory:
    """Tests to verify target directory does not contain built artifacts."""

    def test_no_jar_in_target(self):
        """Verify no jar file exists in target/ (build hasn't succeeded yet)."""
        target_dir = PROJECT_DIR / "target"
        if target_dir.exists():
            jars = list(target_dir.glob("invoice-service-*.jar"))
            assert len(jars) == 0, \
                f"Found existing jar files in target/: {jars}. Build should not have succeeded yet."
