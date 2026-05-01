# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has fixed the changelog generator bugs in /home/user/releaser.
"""

import os
import subprocess
import pytest
import re
from pathlib import Path
from datetime import date


BASE_DIR = Path("/home/user/releaser")


class TestDirectoryStructure:
    """Verify the releaser directory and its contents still exist."""

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


class TestVersionFileFixed:
    """Verify the VERSION file no longer has CRLF and contains correct version."""

    def test_version_file_no_crlf(self):
        """VERSION file must not have CRLF line endings."""
        version_file = BASE_DIR / "VERSION"
        content = version_file.read_bytes()
        assert b"\r" not in content, \
            f"VERSION file still has CRLF/CR characters. Content bytes: {content!r}"

    def test_version_file_is_ascii_text(self):
        """file command must report VERSION as ASCII text, not CRLF."""
        result = subprocess.run(
            ["file", str(BASE_DIR / "VERSION")],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"file command failed: {result.stderr}"
        output = result.stdout.lower()
        assert "crlf" not in output, \
            f"VERSION file still has CRLF line terminators: {result.stdout}"

    def test_version_is_valid_semver(self):
        """VERSION file must contain a valid semver version."""
        version_file = BASE_DIR / "VERSION"
        content = version_file.read_text().strip()
        semver_pattern = r'^\d+\.\d+\.\d+$'
        assert re.match(semver_pattern, content), \
            f"VERSION file does not contain valid semver. Content: '{content}'"


class TestPatchBumpWorks:
    """Test that patch bump works correctly."""

    def test_patch_bump_exits_zero(self):
        """./bump.sh patch should exit with code 0."""
        # First, set VERSION to a known state
        version_file = BASE_DIR / "VERSION"
        version_file.write_text("1.0.0\n")

        result = subprocess.run(
            ["./bump.sh", "patch"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"./bump.sh patch failed with exit code {result.returncode}. stderr: {result.stderr}"

    def test_patch_bump_increments_patch_only(self):
        """Patch bump from 1.0.0 must produce 1.0.1, not 1.1.0."""
        version_file = BASE_DIR / "VERSION"
        version_file.write_text("1.0.0\n")

        result = subprocess.run(
            ["./bump.sh", "patch"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh patch failed: {result.stderr}"

        new_version = version_file.read_text().strip()
        assert new_version == "1.0.1", \
            f"Patch bump from 1.0.0 should produce 1.0.1, got '{new_version}'. " \
            "The fallback 'if patch is empty, bump minor' logic may still be active."

    def test_consecutive_patch_bumps(self):
        """Multiple patch bumps should increment correctly."""
        version_file = BASE_DIR / "VERSION"
        version_file.write_text("2.4.7\n")

        # First patch bump
        result = subprocess.run(["./bump.sh", "patch"], cwd=BASE_DIR, capture_output=True, text=True)
        assert result.returncode == 0, f"First patch bump failed: {result.stderr}"
        version1 = version_file.read_text().strip()
        assert version1 == "2.4.8", f"First patch bump should produce 2.4.8, got '{version1}'"

        # Second patch bump
        result = subprocess.run(["./bump.sh", "patch"], cwd=BASE_DIR, capture_output=True, text=True)
        assert result.returncode == 0, f"Second patch bump failed: {result.stderr}"
        version2 = version_file.read_text().strip()
        assert version2 == "2.4.9", f"Second patch bump should produce 2.4.9, got '{version2}'"


class TestMinorBumpWorks:
    """Test that minor bump works correctly."""

    def test_minor_bump_from_2_4_8(self):
        """Minor bump from 2.4.8 must produce 2.5.0."""
        version_file = BASE_DIR / "VERSION"
        version_file.write_text("2.4.8\n")

        result = subprocess.run(
            ["./bump.sh", "minor"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh minor failed: {result.stderr}"

        new_version = version_file.read_text().strip()
        assert new_version == "2.5.0", \
            f"Minor bump from 2.4.8 should produce 2.5.0, got '{new_version}'"


class TestMajorBumpWorks:
    """Test that major bump works correctly."""

    def test_major_bump_from_2_5_0(self):
        """Major bump from 2.5.0 must produce 3.0.0."""
        version_file = BASE_DIR / "VERSION"
        version_file.write_text("2.5.0\n")

        result = subprocess.run(
            ["./bump.sh", "major"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh major failed: {result.stderr}"

        new_version = version_file.read_text().strip()
        assert new_version == "3.0.0", \
            f"Major bump from 2.5.0 should produce 3.0.0, got '{new_version}'"


class TestChangelogNoDuplicates:
    """Test that changelog entries are not duplicated."""

    def test_commits_appear_once_not_twice(self):
        """Each commit should appear exactly once in the changelog block, not duplicated."""
        version_file = BASE_DIR / "VERSION"
        changelog_file = BASE_DIR / "CHANGELOG.md"

        # Reset to clean state
        version_file.write_text("5.0.0\n")
        # Save original changelog to restore later
        original_changelog = changelog_file.read_text()

        # Get today's commits
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=midnight"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        today_commits = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

        if not today_commits:
            pytest.skip("No commits from today to test duplication")

        # Run bump
        result = subprocess.run(
            ["./bump.sh", "patch"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh patch failed: {result.stderr}"

        # Read the new changelog
        new_changelog = changelog_file.read_text()

        # Check that each commit hash appears exactly once in the NEW content
        # (content added by this bump, not in original)
        new_content = new_changelog.replace(original_changelog, "")

        for commit_line in today_commits:
            # Extract the commit hash (first word)
            commit_hash = commit_line.split()[0] if commit_line.split() else ""
            if commit_hash:
                count = new_content.count(commit_hash)
                assert count == 1, \
                    f"Commit '{commit_hash}' appears {count} times in new changelog block. " \
                    "Expected exactly 1 (commits are being duplicated)."

    def test_grep_commit_count(self):
        """Anti-shortcut: grep count of known commit patterns should equal number of commits, not double."""
        version_file = BASE_DIR / "VERSION"
        changelog_file = BASE_DIR / "CHANGELOG.md"

        # Reset to clean state with empty changelog
        version_file.write_text("6.0.0\n")
        changelog_file.write_text("# Changelog\n\n")

        # Get today's commit hashes
        result = subprocess.run(
            ["git", "log", "--oneline", "--since=midnight"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        commit_lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        commit_hashes = [line.split()[0] for line in commit_lines if line.split()]

        if len(commit_hashes) < 1:
            pytest.skip("No commits from today to test")

        # Run bump
        result = subprocess.run(
            ["./bump.sh", "patch"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh patch failed: {result.stderr}"

        # Count occurrences of each hash
        changelog_content = changelog_file.read_text()
        total_occurrences = sum(changelog_content.count(h) for h in commit_hashes)
        expected_count = len(commit_hashes)

        assert total_occurrences == expected_count, \
            f"Expected {expected_count} commit occurrences, found {total_occurrences}. " \
            "Commits are being duplicated in the changelog."


class TestChangelogFormat:
    """Test that changelog has proper format."""

    def test_changelog_has_version_header(self):
        """Changelog should have a version header with today's date."""
        version_file = BASE_DIR / "VERSION"
        changelog_file = BASE_DIR / "CHANGELOG.md"

        version_file.write_text("7.0.0\n")
        changelog_file.write_text("# Changelog\n\n## [6.0.0] - 2024-01-01\n- Old entry\n")

        result = subprocess.run(
            ["./bump.sh", "patch"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh patch failed: {result.stderr}"

        changelog_content = changelog_file.read_text()
        today_str = date.today().strftime("%Y-%m-%d")

        # Check for version header with today's date
        expected_header_pattern = r"##\s*\[7\.0\.1\]\s*-\s*" + re.escape(today_str)
        assert re.search(expected_header_pattern, changelog_content), \
            f"Changelog should have header '## [7.0.1] - {today_str}'. Content:\n{changelog_content}"


class TestPriorChangelogPreserved:
    """Test that prior changelog entries are preserved."""

    def test_prior_entries_intact(self):
        """Prior changelog entries should remain unchanged."""
        version_file = BASE_DIR / "VERSION"
        changelog_file = BASE_DIR / "CHANGELOG.md"

        prior_content = "# Changelog\n\n## [1.0.0] - 2024-01-01\n- Initial release\n- Feature A\n"
        version_file.write_text("1.0.0\n")
        changelog_file.write_text(prior_content)

        result = subprocess.run(
            ["./bump.sh", "patch"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"bump.sh patch failed: {result.stderr}"

        new_changelog = changelog_file.read_text()

        # The prior content should still be present
        assert "## [1.0.0] - 2024-01-01" in new_changelog, \
            "Prior version entry [1.0.0] should be preserved"
        assert "Initial release" in new_changelog, \
            "Prior changelog content 'Initial release' should be preserved"
        assert "Feature A" in new_changelog, \
            "Prior changelog content 'Feature A' should be preserved"


class TestAllBumpTypesSupported:
    """Verify script still supports all three bump types."""

    def test_usage_message_on_invalid_arg(self):
        """Script should show usage or error on invalid argument."""
        result = subprocess.run(
            ["./bump.sh", "invalid"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        # Should either fail or show usage
        assert result.returncode != 0 or "usage" in result.stdout.lower() or "usage" in result.stderr.lower(), \
            "Script should reject invalid bump type"

    def test_all_bump_types_work(self):
        """All bump types (major, minor, patch) should work correctly."""
        version_file = BASE_DIR / "VERSION"

        test_cases = [
            ("1.0.0", "patch", "1.0.1"),
            ("1.0.1", "minor", "1.1.0"),
            ("1.1.0", "major", "2.0.0"),
        ]

        for start_version, bump_type, expected_version in test_cases:
            version_file.write_text(f"{start_version}\n")

            result = subprocess.run(
                ["./bump.sh", bump_type],
                cwd=BASE_DIR,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, \
                f"bump.sh {bump_type} failed from {start_version}: {result.stderr}"

            actual_version = version_file.read_text().strip()
            assert actual_version == expected_version, \
                f"{bump_type} bump from {start_version} should produce {expected_version}, got '{actual_version}'"


class TestGitHistoryUnchanged:
    """Verify git history was not modified."""

    def test_git_repo_still_valid(self):
        """Git repository should still be valid."""
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Not a valid git repository: {result.stderr}"

    def test_git_has_commits(self):
        """Git repository should still have commits."""
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to count commits: {result.stderr}"
        commit_count = int(result.stdout.strip())
        assert commit_count >= 3, f"Expected at least 3 commits, found {commit_count}"
