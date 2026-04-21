# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the documentation workspace setup task.
"""

import os
import subprocess
import stat
import pytest


class TestDirectoriesExist:
    """Tests to verify all required directories exist."""

    def test_docs_workspace_exists(self):
        """Verify /home/user/docs_workspace directory exists."""
        path = "/home/user/docs_workspace"
        assert os.path.isdir(path), (
            f"Directory {path} does not exist. "
            "The docs_workspace directory must be created."
        )

    def test_public_directory_exists(self):
        """Verify /home/user/docs_workspace/public directory exists."""
        path = "/home/user/docs_workspace/public"
        assert os.path.isdir(path), (
            f"Directory {path} does not exist. "
            "The public directory must be created under docs_workspace."
        )

    def test_drafts_directory_exists(self):
        """Verify /home/user/docs_workspace/drafts directory exists."""
        path = "/home/user/docs_workspace/drafts"
        assert os.path.isdir(path), (
            f"Directory {path} does not exist. "
            "The drafts directory must be created under docs_workspace."
        )

    def test_templates_directory_exists(self):
        """Verify /home/user/docs_workspace/templates directory exists."""
        path = "/home/user/docs_workspace/templates"
        assert os.path.isdir(path), (
            f"Directory {path} does not exist. "
            "The templates directory must be created under docs_workspace."
        )

    def test_archive_directory_exists(self):
        """Verify /home/user/docs_workspace/archive directory exists."""
        path = "/home/user/docs_workspace/archive"
        assert os.path.isdir(path), (
            f"Directory {path} does not exist. "
            "The archive directory must be created under docs_workspace."
        )


class TestDirectoryPermissions:
    """Tests to verify directory permissions are correct."""

    def _get_octal_permissions(self, path):
        """Get octal permissions string for a path."""
        result = subprocess.run(
            ["stat", "-c", "%a", path],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def test_public_directory_permissions(self):
        """Verify /home/user/docs_workspace/public has 755 permissions."""
        path = "/home/user/docs_workspace/public"
        perms = self._get_octal_permissions(path)
        assert perms == "755", (
            f"Directory {path} has permissions {perms}, expected 755 (drwxr-xr-x). "
            "Public directory should be readable and writable by owner, readable by group and others."
        )

    def test_drafts_directory_permissions(self):
        """Verify /home/user/docs_workspace/drafts has 700 permissions."""
        path = "/home/user/docs_workspace/drafts"
        perms = self._get_octal_permissions(path)
        assert perms == "700", (
            f"Directory {path} has permissions {perms}, expected 700 (drwx------). "
            "Drafts directory should be readable and writable by owner only."
        )

    def test_templates_directory_permissions(self):
        """Verify /home/user/docs_workspace/templates has 755 permissions."""
        path = "/home/user/docs_workspace/templates"
        perms = self._get_octal_permissions(path)
        assert perms == "755", (
            f"Directory {path} has permissions {perms}, expected 755 (drwxr-xr-x). "
            "Templates directory should be readable by everyone, writable only by owner."
        )

    def test_archive_directory_permissions(self):
        """Verify /home/user/docs_workspace/archive has 750 permissions."""
        path = "/home/user/docs_workspace/archive"
        perms = self._get_octal_permissions(path)
        assert perms == "750", (
            f"Directory {path} has permissions {perms}, expected 750 (drwxr-x---). "
            "Archive directory should be readable by owner and group, no access for others."
        )


class TestFilesExist:
    """Tests to verify all required files exist."""

    def test_index_md_exists(self):
        """Verify /home/user/docs_workspace/public/index.md exists."""
        path = "/home/user/docs_workspace/public/index.md"
        assert os.path.isfile(path), (
            f"File {path} does not exist. "
            "The index.md file must be created in the public directory."
        )

    def test_wip_feature_md_exists(self):
        """Verify /home/user/docs_workspace/drafts/wip-feature.md exists."""
        path = "/home/user/docs_workspace/drafts/wip-feature.md"
        assert os.path.isfile(path), (
            f"File {path} does not exist. "
            "The wip-feature.md file must be created in the drafts directory."
        )

    def test_article_template_md_exists(self):
        """Verify /home/user/docs_workspace/templates/article-template.md exists."""
        path = "/home/user/docs_workspace/templates/article-template.md"
        assert os.path.isfile(path), (
            f"File {path} does not exist. "
            "The article-template.md file must be created in the templates directory."
        )

    def test_v1_notes_md_exists(self):
        """Verify /home/user/docs_workspace/archive/v1-notes.md exists."""
        path = "/home/user/docs_workspace/archive/v1-notes.md"
        assert os.path.isfile(path), (
            f"File {path} does not exist. "
            "The v1-notes.md file must be created in the archive directory."
        )

    def test_permissions_manifest_exists(self):
        """Verify /home/user/docs_workspace/permissions_manifest.txt exists."""
        path = "/home/user/docs_workspace/permissions_manifest.txt"
        assert os.path.isfile(path), (
            f"File {path} does not exist. "
            "The permissions_manifest.txt file must be created."
        )

    def test_verify_permissions_script_exists(self):
        """Verify /home/user/docs_workspace/verify_permissions.sh exists."""
        path = "/home/user/docs_workspace/verify_permissions.sh"
        assert os.path.isfile(path), (
            f"File {path} does not exist. "
            "The verify_permissions.sh script must be created."
        )


class TestFilePermissions:
    """Tests to verify file permissions are correct."""

    def _get_octal_permissions(self, path):
        """Get octal permissions string for a path."""
        result = subprocess.run(
            ["stat", "-c", "%a", path],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def test_index_md_permissions(self):
        """Verify /home/user/docs_workspace/public/index.md has 644 permissions."""
        path = "/home/user/docs_workspace/public/index.md"
        perms = self._get_octal_permissions(path)
        assert perms == "644", (
            f"File {path} has permissions {perms}, expected 644 (-rw-r--r--). "
            "index.md should be readable by all, writable by owner."
        )

    def test_wip_feature_md_permissions(self):
        """Verify /home/user/docs_workspace/drafts/wip-feature.md has 600 permissions."""
        path = "/home/user/docs_workspace/drafts/wip-feature.md"
        perms = self._get_octal_permissions(path)
        assert perms == "600", (
            f"File {path} has permissions {perms}, expected 600 (-rw-------). "
            "wip-feature.md should be readable and writable by owner only."
        )

    def test_article_template_md_permissions(self):
        """Verify /home/user/docs_workspace/templates/article-template.md has 444 permissions."""
        path = "/home/user/docs_workspace/templates/article-template.md"
        perms = self._get_octal_permissions(path)
        assert perms == "444", (
            f"File {path} has permissions {perms}, expected 444 (-r--r--r--). "
            "article-template.md should be read-only for everyone."
        )

    def test_v1_notes_md_permissions(self):
        """Verify /home/user/docs_workspace/archive/v1-notes.md has 440 permissions."""
        path = "/home/user/docs_workspace/archive/v1-notes.md"
        perms = self._get_octal_permissions(path)
        assert perms == "440", (
            f"File {path} has permissions {perms}, expected 440 (-r--r-----). "
            "v1-notes.md should be readable by owner and group only."
        )

    def test_verify_permissions_script_permissions(self):
        """Verify /home/user/docs_workspace/verify_permissions.sh has 755 permissions."""
        path = "/home/user/docs_workspace/verify_permissions.sh"
        perms = self._get_octal_permissions(path)
        assert perms == "755", (
            f"File {path} has permissions {perms}, expected 755 (-rwxr-xr-x). "
            "verify_permissions.sh should be executable."
        )


class TestFileContents:
    """Tests to verify file contents are correct."""

    def test_index_md_content(self):
        """Verify /home/user/docs_workspace/public/index.md has correct content."""
        path = "/home/user/docs_workspace/public/index.md"
        expected_content = "# Documentation Home\n\nWelcome to the docs."
        with open(path, 'r') as f:
            content = f.read()
        # Allow optional trailing newline
        content_stripped = content.rstrip('\n')
        assert content_stripped == expected_content, (
            f"File {path} has incorrect content.\n"
            f"Expected: {repr(expected_content)}\n"
            f"Got: {repr(content_stripped)}"
        )

    def test_wip_feature_md_content(self):
        """Verify /home/user/docs_workspace/drafts/wip-feature.md has correct content."""
        path = "/home/user/docs_workspace/drafts/wip-feature.md"
        expected_content = "# Feature Draft\n\nWork in progress."
        with open(path, 'r') as f:
            content = f.read()
        content_stripped = content.rstrip('\n')
        assert content_stripped == expected_content, (
            f"File {path} has incorrect content.\n"
            f"Expected: {repr(expected_content)}\n"
            f"Got: {repr(content_stripped)}"
        )

    def test_article_template_md_content(self):
        """Verify /home/user/docs_workspace/templates/article-template.md has correct content."""
        path = "/home/user/docs_workspace/templates/article-template.md"
        expected_content = "# Title\n\n## Overview\n\n## Details\n\n## See Also"
        with open(path, 'r') as f:
            content = f.read()
        content_stripped = content.rstrip('\n')
        assert content_stripped == expected_content, (
            f"File {path} has incorrect content.\n"
            f"Expected: {repr(expected_content)}\n"
            f"Got: {repr(content_stripped)}"
        )

    def test_v1_notes_md_content(self):
        """Verify /home/user/docs_workspace/archive/v1-notes.md has correct content."""
        path = "/home/user/docs_workspace/archive/v1-notes.md"
        expected_content = "# Version 1 Notes\n\nLegacy documentation."
        with open(path, 'r') as f:
            content = f.read()
        content_stripped = content.rstrip('\n')
        assert content_stripped == expected_content, (
            f"File {path} has incorrect content.\n"
            f"Expected: {repr(expected_content)}\n"
            f"Got: {repr(content_stripped)}"
        )


class TestPermissionsManifest:
    """Tests to verify the permissions manifest file is correct."""

    def test_permissions_manifest_content(self):
        """Verify /home/user/docs_workspace/permissions_manifest.txt has exact content."""
        path = "/home/user/docs_workspace/permissions_manifest.txt"
        expected_content = """DIRECTORY_PERMISSIONS:
/home/user/docs_workspace/public:755
/home/user/docs_workspace/drafts:700
/home/user/docs_workspace/templates:755
/home/user/docs_workspace/archive:750

FILE_PERMISSIONS:
/home/user/docs_workspace/public/index.md:644
/home/user/docs_workspace/drafts/wip-feature.md:600
/home/user/docs_workspace/templates/article-template.md:444
/home/user/docs_workspace/archive/v1-notes.md:440
"""
        with open(path, 'r') as f:
            content = f.read()

        assert content == expected_content, (
            f"File {path} does not have the exact expected content.\n"
            f"Expected:\n{repr(expected_content)}\n"
            f"Got:\n{repr(content)}\n"
            "The manifest must have exactly the specified format with one blank line between sections "
            "and one trailing newline."
        )


class TestVerifyPermissionsScript:
    """Tests to verify the verify_permissions.sh script works correctly."""

    def test_verify_script_is_valid_bash(self):
        """Verify the script starts with proper bash shebang."""
        path = "/home/user/docs_workspace/verify_permissions.sh"
        with open(path, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash", (
            f"Script {path} does not start with #!/bin/bash shebang.\n"
            f"First line is: {repr(first_line)}"
        )

    def test_verify_script_outputs_pass(self):
        """Verify running the script outputs exactly 'PASS' when permissions are correct."""
        path = "/home/user/docs_workspace/verify_permissions.sh"
        result = subprocess.run(
            [path],
            capture_output=True,
            text=True,
            cwd="/home/user/docs_workspace"
        )
        output = result.stdout.strip()
        assert output == "PASS", (
            f"Script {path} did not output 'PASS'.\n"
            f"Output was: {repr(result.stdout)}\n"
            f"Stderr was: {repr(result.stderr)}\n"
            f"Return code: {result.returncode}\n"
            "The script should output exactly 'PASS' when all permissions match the manifest."
        )

    def test_verify_script_runs_successfully(self):
        """Verify the script runs without errors."""
        path = "/home/user/docs_workspace/verify_permissions.sh"
        result = subprocess.run(
            [path],
            capture_output=True,
            text=True,
            cwd="/home/user/docs_workspace"
        )
        # Script should return 0 when permissions match
        assert result.returncode == 0, (
            f"Script {path} returned non-zero exit code: {result.returncode}\n"
            f"Stdout: {repr(result.stdout)}\n"
            f"Stderr: {repr(result.stderr)}"
        )
