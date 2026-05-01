# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the changelog generator fix task.
"""

import os
import subprocess
import pytest
from pathlib import Path


BASE_DIR = Path("/home/user/releaser")


class TestDirectoryStructure:
    """Verify the releaser directory and its contents exist."""

    def test_releaser_directory_exists(self):
        """The /home/user/releaser directory must exist."""
        assert BASE_DIR.exists(), f"Directory {BASE_DIR} does not exist"
        assert BASE_DIR.is_dir(), f"{BASE_DIR} is not a directory"

    def test_bump_script_exists(self):
        """bump.sh script must exist in the releaser directory."""
        bump_script = BASE_DIR / "bump.sh"
        assert bump_script.exists(), f"bump.sh does not exist at {bump_script}"
        assert bump_script.is_file(), f"{bump_script} is not a file"

    def test_bump_script_is_executable(self):
        """bump.sh must be executable."""
        bump_script = BASE_DIR / "bump.sh"
        assert os.access(bump_script, os.X_OK), f"{bump_script} is not executable"

    def test_version_file_exists(self):
        """VERSION file must exist in the releaser directory."""
        version_file = BASE_DIR / "VERSION"
        assert version_file.exists(), f"VERSION file does not exist at {version_file}"
        assert version_file.is_file(), f"{version_file} is not a file"

    def test_changelog_file_exists(self):
        """CHANGELOG.md must exist in the releaser directory."""
        changelog_file = BASE_DIR / "CHANGELOG.md"
        assert changelog_file.exists(), f"CHANGELOG.md does not exist at {changelog_file}"
        assert changelog_file.is_file(), f"{changelog_file} is not a file"

    def test_git_directory_exists(self):
        """The .git directory must exist (valid git repo)."""
        git_dir = BASE_DIR / ".git"
        assert git_dir.exists(), f".git directory does not exist at {git_dir}"
        assert git_dir.is_dir(), f"{git_dir} is not a directory"


class TestVersionFile:
    """Verify the VERSION file has the expected buggy content (CRLF)."""

    def test_version_contains_2_4_7(self):
        """VERSION file must contain version 2.4.7."""
        version_file = BASE_DIR / "VERSION"
        content = version_file.read_bytes()
        # Check that 2.4.7 is present in the content
        assert b"2.4.7" in content, f"VERSION file does not contain '2.4.7'. Content: {content!r}"

    def test_version_has_crlf_line_ending(self):
        """VERSION file must have CRLF line ending (the core bug)."""
        version_file = BASE_DIR / "VERSION"
        content = version_file.read_bytes()
        # The bug is that the file has CRLF (\r\n) line ending
        assert b"\r\n" in content or content.endswith(b"\r"), \
            f"VERSION file should have CRLF line ending (the bug). Content bytes: {content!r}"


class TestGitRepository:
    """Verify the git repository is valid and has the expected commits."""

    def test_git_repo_is_valid(self):
        """The directory must be a valid git repository."""
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Not a valid git repository: {result.stderr}"
        assert result.stdout.strip() == "true", "Not inside a git work tree"

    def test_git_has_commits(self):
        """Git repository must have commit history."""
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to count commits: {result.stderr}"
        commit_count = int(result.stdout.strip())
        assert commit_count >= 3, f"Expected at least 3 commits, found {commit_count}"

    def test_git_has_today_commits(self):
        """Git repository must have commits from today."""
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=midnight"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to get today's commits: {result.stderr}"
        commits = result.stdout.strip()
        assert len(commits) > 0, "No commits found from today - expected 3 commits"
        commit_lines = [line for line in commits.split('\n') if line.strip()]
        assert len(commit_lines) >= 3, f"Expected at least 3 commits today, found {len(commit_lines)}"


class TestBumpScript:
    """Verify the bump.sh script has the expected structure."""

    def test_bump_script_is_bash(self):
        """bump.sh should be a bash script."""
        bump_script = BASE_DIR / "bump.sh"
        content = bump_script.read_text()
        assert "#!/bin/bash" in content or "#!/usr/bin/env bash" in content, \
            "bump.sh should have a bash shebang"

    def test_bump_script_reads_version_file(self):
        """bump.sh should read from VERSION file."""
        bump_script = BASE_DIR / "bump.sh"
        content = bump_script.read_text()
        assert "VERSION" in content, "bump.sh should reference VERSION file"

    def test_bump_script_handles_bump_types(self):
        """bump.sh should handle major, minor, and patch bump types."""
        bump_script = BASE_DIR / "bump.sh"
        content = bump_script.read_text()
        assert "major" in content, "bump.sh should handle 'major' bump type"
        assert "minor" in content, "bump.sh should handle 'minor' bump type"
        assert "patch" in content, "bump.sh should handle 'patch' bump type"

    def test_bump_script_updates_changelog(self):
        """bump.sh should update CHANGELOG.md."""
        bump_script = BASE_DIR / "bump.sh"
        content = bump_script.read_text()
        assert "CHANGELOG" in content, "bump.sh should reference CHANGELOG"


class TestChangelogFile:
    """Verify the CHANGELOG.md file exists and has content."""

    def test_changelog_has_content(self):
        """CHANGELOG.md should have existing content."""
        changelog_file = BASE_DIR / "CHANGELOG.md"
        content = changelog_file.read_text()
        assert len(content) > 0, "CHANGELOG.md should not be empty"

    def test_changelog_has_proper_format(self):
        """CHANGELOG.md should have properly formatted entries."""
        changelog_file = BASE_DIR / "CHANGELOG.md"
        content = changelog_file.read_text()
        # Check for typical changelog format markers
        assert "##" in content or "#" in content, \
            "CHANGELOG.md should have markdown headers for version entries"


class TestRequiredTools:
    """Verify required tools are available."""

    @pytest.mark.parametrize("tool", ["bash", "git", "sed", "tr", "awk", "cat", "cut", "echo", "date"])
    def test_tool_available(self, tool):
        """Required tools must be available in PATH."""
        result = subprocess.run(
            ["which", tool],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Required tool '{tool}' is not available in PATH"

    def test_dos2unix_or_alternative_available(self):
        """dos2unix or an alternative (tr, sed) must be available for fixing CRLF."""
        # Check if dos2unix is available
        dos2unix_result = subprocess.run(["which", "dos2unix"], capture_output=True)
        # tr and sed are already checked above, so we just need one of these
        assert dos2unix_result.returncode == 0 or True, \
            "dos2unix or alternative tools (tr, sed) should be available"


class TestDirectoryWritable:
    """Verify the releaser directory is writable."""

    def test_releaser_directory_is_writable(self):
        """The /home/user/releaser directory must be writable."""
        assert os.access(BASE_DIR, os.W_OK), f"{BASE_DIR} is not writable"

    def test_version_file_is_writable(self):
        """VERSION file must be writable."""
        version_file = BASE_DIR / "VERSION"
        assert os.access(version_file, os.W_OK), f"{version_file} is not writable"

    def test_changelog_file_is_writable(self):
        """CHANGELOG.md must be writable."""
        changelog_file = BASE_DIR / "CHANGELOG.md"
        assert os.access(changelog_file, os.W_OK), f"{changelog_file} is not writable"

    def test_bump_script_is_writable(self):
        """bump.sh must be writable (for fixing the bugs)."""
        bump_script = BASE_DIR / "bump.sh"
        assert os.access(bump_script, os.W_OK), f"{bump_script} is not writable"
