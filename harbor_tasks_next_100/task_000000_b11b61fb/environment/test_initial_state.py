# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the release tooling fix task.
"""

import json
import os
import subprocess
import pytest

RELEASER_DIR = "/home/user/releaser"
PACKAGE_JSON = os.path.join(RELEASER_DIR, "package.json")
RELEASE_SH = os.path.join(RELEASER_DIR, "release.sh")
BUMP_PY = os.path.join(RELEASER_DIR, "bump.py")
CHANGELOG_MD = os.path.join(RELEASER_DIR, "CHANGELOG.md")


class TestReleaserDirectoryExists:
    """Test that the releaser directory exists and is a git repository."""

    def test_releaser_directory_exists(self):
        assert os.path.isdir(RELEASER_DIR), (
            f"Directory {RELEASER_DIR} does not exist. "
            "The releaser tooling directory must be present."
        )

    def test_releaser_is_git_repository(self):
        git_dir = os.path.join(RELEASER_DIR, ".git")
        assert os.path.isdir(git_dir), (
            f"{RELEASER_DIR} is not a git repository. "
            "Expected .git directory to exist."
        )


class TestRequiredFilesExist:
    """Test that all required files exist in the releaser directory."""

    def test_package_json_exists(self):
        assert os.path.isfile(PACKAGE_JSON), (
            f"File {PACKAGE_JSON} does not exist. "
            "package.json is required for version tracking."
        )

    def test_release_sh_exists(self):
        assert os.path.isfile(RELEASE_SH), (
            f"File {RELEASE_SH} does not exist. "
            "release.sh is the main entry point script."
        )

    def test_release_sh_is_executable(self):
        assert os.access(RELEASE_SH, os.X_OK), (
            f"File {RELEASE_SH} is not executable. "
            "release.sh must be executable to run."
        )

    def test_bump_py_exists(self):
        assert os.path.isfile(BUMP_PY), (
            f"File {BUMP_PY} does not exist. "
            "bump.py is required for version calculation."
        )

    def test_changelog_exists(self):
        assert os.path.isfile(CHANGELOG_MD), (
            f"File {CHANGELOG_MD} does not exist. "
            "CHANGELOG.md must exist with prior entries."
        )


class TestPackageJsonContent:
    """Test that package.json has the expected initial version."""

    def test_package_json_is_valid_json(self):
        with open(PACKAGE_JSON, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"package.json is not valid JSON: {e}")

    def test_package_json_has_version_field(self):
        with open(PACKAGE_JSON, 'r') as f:
            data = json.load(f)
        assert "version" in data, (
            "package.json does not contain a 'version' field. "
            "Version field is required for version bumping."
        )

    def test_package_json_version_is_1_2_3(self):
        with open(PACKAGE_JSON, 'r') as f:
            data = json.load(f)
        assert data.get("version") == "1.2.3", (
            f"package.json version is '{data.get('version')}', expected '1.2.3'. "
            "Initial version must be 1.2.3 before the release process."
        )


class TestGitTagExists:
    """Test that the v1.2.3 tag exists."""

    def test_tag_v1_2_3_exists(self):
        result = subprocess.run(
            ["git", "tag", "-l", "v1.2.3"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Failed to list git tags: {result.stderr}"
        )
        assert "v1.2.3" in result.stdout, (
            "Git tag v1.2.3 does not exist. "
            "The tag must exist as the baseline for version bumping."
        )


class TestGitCommitHistory:
    """Test that the expected commits exist since v1.2.3."""

    def test_commits_since_v1_2_3_exist(self):
        # Get commits since v1.2.3
        result = subprocess.run(
            ["git", "log", "v1.2.3..HEAD", "--oneline"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Failed to get git log: {result.stderr}"
        )
        commits = result.stdout.strip()
        assert commits, (
            "No commits found since v1.2.3. "
            "Expected at least 5 commits for testing."
        )

    def test_fix_payment_processor_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "v1.2.3..HEAD", "--oneline", "--grep=fix: resolve null pointer in payment processor"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "resolve null pointer in payment processor" in result.stdout, (
            "Commit 'fix: resolve null pointer in payment processor' not found. "
            "This fix commit must exist in the history."
        )

    def test_feat_multi_currency_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "v1.2.3..HEAD", "--oneline", "--grep=feat: add multi-currency support"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "multi-currency" in result.stdout, (
            "Commit 'feat: add multi-currency support for AWS billing' not found. "
            "This feat commit must exist in the history."
        )

    def test_fix_rounding_error_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "v1.2.3..HEAD", "--oneline", "--grep=fix: correct rounding error"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "rounding error" in result.stdout, (
            "Commit 'fix: correct rounding error in cost allocation' not found. "
            "This fix commit must exist in the history."
        )

    def test_docs_readme_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "v1.2.3..HEAD", "--oneline", "--grep=docs: update README"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "README" in result.stdout, (
            "Commit 'docs: update README with new env vars' not found. "
            "This docs commit must exist in the history."
        )

    def test_feat_api_historical_spend_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "v1.2.3..HEAD", "--oneline", "--grep=historical spend"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "historical spend" in result.stdout, (
            "Commit 'feat(api): expose historical spend endpoint' not found. "
            "This scoped feat commit must exist in the history."
        )

    def test_at_least_five_commits_since_tag(self):
        result = subprocess.run(
            ["git", "rev-list", "--count", "v1.2.3..HEAD"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Failed to count commits: {result.stderr}"
        )
        count = int(result.stdout.strip())
        assert count >= 5, (
            f"Only {count} commits found since v1.2.3, expected at least 5. "
            "The commit history must contain all required test commits."
        )


class TestRequiredToolsAvailable:
    """Test that required tools are available on the system."""

    def test_git_available(self):
        result = subprocess.run(
            ["which", "git"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "git is not available. Git must be installed."
        )

    def test_python3_available(self):
        result = subprocess.run(
            ["which", "python3"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "python3 is not available. Python 3 must be installed."
        )

    def test_python_version_is_3_11_or_higher(self):
        result = subprocess.run(
            ["python3", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        version_str = result.stdout.strip()
        # Parse version like "Python 3.11.x"
        parts = version_str.split()[1].split('.')
        major = int(parts[0])
        minor = int(parts[1])
        assert major == 3 and minor >= 11, (
            f"Python version is {version_str}, expected Python 3.11 or higher."
        )

    def test_jq_available(self):
        result = subprocess.run(
            ["which", "jq"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "jq is not available. jq must be installed for JSON processing."
        )

    def test_sed_available(self):
        result = subprocess.run(
            ["which", "sed"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            "sed is not available. sed must be installed for text processing."
        )


class TestDirectoryWritable:
    """Test that the releaser directory is writable."""

    def test_releaser_directory_is_writable(self):
        assert os.access(RELEASER_DIR, os.W_OK), (
            f"Directory {RELEASER_DIR} is not writable. "
            "The directory must be writable to update files."
        )

    def test_package_json_is_writable(self):
        assert os.access(PACKAGE_JSON, os.W_OK), (
            f"File {PACKAGE_JSON} is not writable. "
            "package.json must be writable to update version."
        )

    def test_changelog_is_writable(self):
        assert os.access(CHANGELOG_MD, os.W_OK), (
            f"File {CHANGELOG_MD} is not writable. "
            "CHANGELOG.md must be writable to add new entries."
        )

    def test_bump_py_is_writable(self):
        assert os.access(BUMP_PY, os.W_OK), (
            f"File {BUMP_PY} is not writable. "
            "bump.py must be writable to fix the bugs."
        )

    def test_release_sh_is_writable(self):
        assert os.access(RELEASE_SH, os.W_OK), (
            f"File {RELEASE_SH} is not writable. "
            "release.sh must be writable to fix the bugs."
        )


class TestTagV1_3_0DoesNotExist:
    """Test that the v1.3.0 tag does not exist yet (expected final state)."""

    def test_tag_v1_3_0_does_not_exist(self):
        result = subprocess.run(
            ["git", "tag", "-l", "v1.3.0"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "v1.3.0" not in result.stdout, (
            "Git tag v1.3.0 already exists. "
            "The tag should only be created after running the fixed release.sh."
        )


class TestBumpPyContainsBugs:
    """Test that bump.py exists and contains the buggy patterns described."""

    def test_bump_py_contains_three_dots(self):
        """Verify the three-dot bug exists (bug #1)."""
        with open(BUMP_PY, 'r') as f:
            content = f.read()
        # Looking for the three-dot pattern in git log command
        assert "..." in content, (
            "bump.py does not contain '...' pattern. "
            "Expected to find the three-dot git log bug."
        )

    def test_bump_py_uses_max_for_bump_type(self):
        """Verify the string max comparison bug exists (bug #3)."""
        with open(BUMP_PY, 'r') as f:
            content = f.read()
        # Looking for max() being used on bump types
        assert "max(" in content, (
            "bump.py does not use max() function. "
            "Expected to find the string comparison bug using max()."
        )
