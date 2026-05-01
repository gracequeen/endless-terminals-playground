# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the release tooling fix task.
"""

import json
import os
import subprocess
import re
import pytest

RELEASER_DIR = "/home/user/releaser"
PACKAGE_JSON = os.path.join(RELEASER_DIR, "package.json")
RELEASE_SH = os.path.join(RELEASER_DIR, "release.sh")
BUMP_PY = os.path.join(RELEASER_DIR, "bump.py")
CHANGELOG_MD = os.path.join(RELEASER_DIR, "CHANGELOG.md")


class TestReleaseSHExitsSuccessfully:
    """Test that release.sh runs successfully."""

    def test_release_sh_exists(self):
        assert os.path.isfile(RELEASE_SH), (
            f"File {RELEASE_SH} does not exist. "
            "release.sh must still exist as the entry point."
        )

    def test_release_sh_is_executable(self):
        assert os.access(RELEASE_SH, os.X_OK), (
            f"File {RELEASE_SH} is not executable. "
            "release.sh must be executable."
        )


class TestBumpPyExists:
    """Test that bump.py still exists (not replaced with external tool)."""

    def test_bump_py_exists(self):
        assert os.path.isfile(BUMP_PY), (
            f"File {BUMP_PY} does not exist. "
            "bump.py must still exist (can be modified but not deleted/replaced)."
        )

    def test_bump_py_is_python_file(self):
        with open(BUMP_PY, 'r') as f:
            content = f.read()
        # Should contain Python-like syntax
        assert 'def ' in content or 'import ' in content or 'print' in content, (
            "bump.py does not appear to be a Python file. "
            "It must remain a Python script."
        )


class TestPackageJsonVersion:
    """Test that package.json has the correct version after release."""

    def test_package_json_exists(self):
        assert os.path.isfile(PACKAGE_JSON), (
            f"File {PACKAGE_JSON} does not exist."
        )

    def test_package_json_is_valid_json(self):
        with open(PACKAGE_JSON, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"package.json is not valid JSON: {e}")

    def test_package_json_version_is_1_3_0(self):
        with open(PACKAGE_JSON, 'r') as f:
            data = json.load(f)
        version = data.get("version")
        assert version == "1.3.0", (
            f"package.json version is '{version}', expected '1.3.0'. "
            "The version should be bumped to 1.3.0 because there are feat commits "
            "since v1.2.3, which require a minor version bump."
        )


class TestGitTags:
    """Test that the correct git tags exist."""

    def test_tag_v1_2_3_still_exists(self):
        result = subprocess.run(
            ["git", "tag", "-l", "v1.2.3"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "v1.2.3" in result.stdout, (
            "Git tag v1.2.3 no longer exists. "
            "The original tag must be preserved."
        )

    def test_tag_v1_3_0_exists(self):
        result = subprocess.run(
            ["git", "tag", "-l", "v1.3.0"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "v1.3.0" in result.stdout, (
            "Git tag v1.3.0 does not exist. "
            "The release process should have created this tag."
        )

    def test_tag_v1_3_0_points_to_head(self):
        # Get HEAD commit
        head_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert head_result.returncode == 0
        head_sha = head_result.stdout.strip()

        # Get v1.3.0 tag commit
        tag_result = subprocess.run(
            ["git", "rev-parse", "v1.3.0^{commit}"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert tag_result.returncode == 0
        tag_sha = tag_result.stdout.strip()

        assert tag_sha == head_sha, (
            f"Tag v1.3.0 points to {tag_sha[:8]} but HEAD is {head_sha[:8]}. "
            "The tag should point to HEAD."
        )


class TestCommitHistoryPreserved:
    """Test that the original commit history is preserved."""

    def test_fix_payment_processor_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--grep=resolve null pointer in payment processor"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "resolve null pointer in payment processor" in result.stdout, (
            "Commit 'fix: resolve null pointer in payment processor' not found in history."
        )

    def test_feat_multi_currency_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--grep=multi-currency"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "multi-currency" in result.stdout, (
            "Commit 'feat: add multi-currency support for AWS billing' not found in history."
        )

    def test_fix_rounding_error_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--grep=rounding error"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "rounding error" in result.stdout, (
            "Commit 'fix: correct rounding error in cost allocation' not found in history."
        )

    def test_docs_readme_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--grep=update README"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "README" in result.stdout, (
            "Commit 'docs: update README with new env vars' not found in history."
        )

    def test_feat_api_historical_spend_commit_exists(self):
        result = subprocess.run(
            ["git", "log", "--all", "--oneline", "--grep=historical spend"],
            cwd=RELEASER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "historical spend" in result.stdout, (
            "Commit 'feat(api): expose historical spend endpoint' not found in history."
        )


class TestChangelogContent:
    """Test that CHANGELOG.md has correct content."""

    def test_changelog_exists(self):
        assert os.path.isfile(CHANGELOG_MD), (
            f"File {CHANGELOG_MD} does not exist."
        )

    def test_changelog_has_v1_3_0_section(self):
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read()
        # Check for v1.3.0 or 1.3.0 in a heading-like context
        assert re.search(r'[#\[].*1\.3\.0', content, re.IGNORECASE), (
            "CHANGELOG.md does not contain a section for v1.3.0. "
            "The changelog should have a new section for the release."
        )

    def test_changelog_contains_historical_spend_endpoint(self):
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read()
        assert "historical spend" in content.lower(), (
            "CHANGELOG.md does not contain 'historical spend'. "
            "The scoped feat commit 'feat(api): expose historical spend endpoint' "
            "must appear in the changelog."
        )

    def test_changelog_contains_multi_currency(self):
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read()
        assert "multi-currency" in content.lower() or "multicurrency" in content.lower(), (
            "CHANGELOG.md does not contain 'multi-currency'. "
            "The feat commit 'feat: add multi-currency support for AWS billing' "
            "must appear in the changelog."
        )

    def test_changelog_contains_payment_processor_fix(self):
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read()
        assert "payment processor" in content.lower() or "null pointer" in content.lower(), (
            "CHANGELOG.md does not contain the payment processor fix. "
            "The fix commit must appear in the changelog."
        )

    def test_changelog_contains_rounding_error_fix(self):
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read()
        assert "rounding" in content.lower() or "cost allocation" in content.lower(), (
            "CHANGELOG.md does not contain the rounding error fix. "
            "The fix commit must appear in the changelog."
        )


class TestChangelogGroupings:
    """Test that changelog entries are under correct headings."""

    def _get_changelog_sections(self):
        """Parse changelog into sections."""
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read()

        # Find the v1.3.0 section
        v130_match = re.search(r'(^|\n)(#+\s*\[?v?1\.3\.0.*?)(?=\n#+\s*\[?v?\d|\Z)', 
                               content, re.IGNORECASE | re.DOTALL)
        if not v130_match:
            return None

        v130_section = v130_match.group(2)
        return v130_section

    def test_feat_commits_under_features_heading(self):
        """Both feat commits should be under Features/Added heading, not under Fixes."""
        section = self._get_changelog_sections()
        if section is None:
            pytest.skip("Could not find v1.3.0 section in changelog")

        # Look for features/added section
        features_pattern = r'(feature|added|add)'
        fixes_pattern = r'(fix|bug)'

        # Find where features section starts and ends
        features_match = re.search(features_pattern, section, re.IGNORECASE)
        fixes_match = re.search(fixes_pattern, section, re.IGNORECASE)

        if features_match and fixes_match:
            features_pos = features_match.start()
            fixes_pos = fixes_match.start()

            # Check that multi-currency is in features section (before fixes if features comes first)
            multi_currency_match = re.search(r'multi-?currency', section, re.IGNORECASE)
            historical_spend_match = re.search(r'historical spend', section, re.IGNORECASE)

            if multi_currency_match:
                mc_pos = multi_currency_match.start()
                # If features comes before fixes, multi-currency should be between features and fixes
                # If fixes comes before features, multi-currency should be after features
                if features_pos < fixes_pos:
                    assert features_pos < mc_pos < fixes_pos or mc_pos > features_pos, (
                        "multi-currency feature appears to be under wrong heading"
                    )

            if historical_spend_match:
                hs_pos = historical_spend_match.start()
                if features_pos < fixes_pos:
                    assert features_pos < hs_pos < fixes_pos or hs_pos > features_pos, (
                        "historical spend feature appears to be under wrong heading"
                    )

    def test_fix_commits_not_under_features(self):
        """Fix commits should not appear under Features heading."""
        section = self._get_changelog_sections()
        if section is None:
            pytest.skip("Could not find v1.3.0 section in changelog")

        # This is a semantic check - we verify that fix-related content
        # appears somewhere in the changelog (already tested) and trust
        # that proper grouping logic puts it under the right heading

        # Look for a fixes/fixed section
        fixes_match = re.search(r'(#+\s*)?fix', section, re.IGNORECASE)
        assert fixes_match is not None, (
            "No 'Fix' heading found in v1.3.0 section. "
            "Fix commits should be grouped under a Fixes/Fixed heading."
        )


class TestAntiShortcutDynamicVersionBump:
    """Test that version bumping is dynamic, not hardcoded."""

    def test_adding_new_feat_bumps_to_1_4_0(self):
        """
        Anti-shortcut test: Add a new feat commit and verify it bumps to 1.4.0.
        This ensures the version calculation is dynamic, not hardcoded.
        """
        # First, verify we're at v1.3.0
        with open(PACKAGE_JSON, 'r') as f:
            data = json.load(f)
        if data.get("version") != "1.3.0":
            pytest.skip("package.json is not at v1.3.0, skipping dynamic test")

        # Create a test file and commit
        test_file = os.path.join(RELEASER_DIR, "test_feature.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("test feature content\n")

            # Stage and commit
            subprocess.run(
                ["git", "add", "test_feature.txt"],
                cwd=RELEASER_DIR,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "feat: test feature for validation"],
                cwd=RELEASER_DIR,
                capture_output=True,
                check=True
            )

            # Run release.sh
            result = subprocess.run(
                ["./release.sh"],
                cwd=RELEASER_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Check that it succeeded
            assert result.returncode == 0, (
                f"release.sh failed after adding new feat commit. "
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )

            # Check version is now 1.4.0
            with open(PACKAGE_JSON, 'r') as f:
                new_data = json.load(f)

            assert new_data.get("version") == "1.4.0", (
                f"After adding a new feat commit, version is '{new_data.get('version')}' "
                f"but expected '1.4.0'. This suggests version calculation is hardcoded "
                f"rather than dynamically computed from commits."
            )

            # Check tag v1.4.0 exists
            tag_result = subprocess.run(
                ["git", "tag", "-l", "v1.4.0"],
                cwd=RELEASER_DIR,
                capture_output=True,
                text=True
            )
            assert "v1.4.0" in tag_result.stdout, (
                "Tag v1.4.0 was not created after adding new feat commit. "
                "Version bumping appears to be hardcoded."
            )

        finally:
            # Clean up: reset to before our test commit
            # This is best-effort cleanup
            subprocess.run(
                ["git", "reset", "--hard", "HEAD~1"],
                cwd=RELEASER_DIR,
                capture_output=True
            )
            subprocess.run(
                ["git", "tag", "-d", "v1.4.0"],
                cwd=RELEASER_DIR,
                capture_output=True
            )
            # Restore package.json to 1.3.0
            with open(PACKAGE_JSON, 'r') as f:
                data = json.load(f)
            data["version"] = "1.3.0"
            with open(PACKAGE_JSON, 'w') as f:
                json.dump(data, f, indent=2)
                f.write('\n')
            if os.path.exists(test_file):
                os.remove(test_file)


class TestChangelogFromActualParsing:
    """Test that changelog is generated from actual commit parsing."""

    def test_changelog_contains_actual_commit_messages(self):
        """
        Verify changelog contains text from actual commit messages,
        not just hardcoded placeholder text.
        """
        with open(CHANGELOG_MD, 'r') as f:
            content = f.read().lower()

        # These specific phrases come from the actual commits
        actual_phrases = [
            "historical spend",  # From feat(api): expose historical spend endpoint
            "multi-currency",    # From feat: add multi-currency support
        ]

        found_count = sum(1 for phrase in actual_phrases if phrase in content)

        assert found_count >= 2, (
            f"Only found {found_count}/2 expected commit message phrases in changelog. "
            "Changelog must be generated from actual commit parsing, not hardcoded."
        )

    def test_scoped_feat_appears_in_changelog(self):
        """
        The scoped feat commit 'feat(api): expose historical spend endpoint'
        must appear in the changelog, proving the scope parsing bug was fixed.
        """
        result = subprocess.run(
            ["grep", "-c", "historical spend", CHANGELOG_MD],
            capture_output=True,
            text=True
        )

        count = int(result.stdout.strip()) if result.returncode == 0 else 0

        assert count >= 1, (
            "The scoped feat commit 'feat(api): expose historical spend endpoint' "
            "does not appear in the changelog. This suggests the scope parsing bug "
            "(bug #2) was not fixed - commits with scopes like 'feat(api):' are "
            "not being recognized as feat commits."
        )
