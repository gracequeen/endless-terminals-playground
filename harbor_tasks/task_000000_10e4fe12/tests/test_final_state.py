# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the backup script task.
"""

import os
import stat
import subprocess
import pytest
import pwd
import grp


HOME = "/home/user"
PROJECTS = os.path.join(HOME, "projects")
BACKUPS = os.path.join(HOME, "backups")
BACKUP_SCRIPT = os.path.join(HOME, "backup.sh")
MANIFEST = os.path.join(BACKUPS, "manifest.txt")


def get_file_owner_group(path):
    """Get owner:group for a file."""
    st = os.stat(path)
    try:
        owner = pwd.getpwuid(st.st_uid).pw_name
    except KeyError:
        owner = str(st.st_uid)
    try:
        group = grp.getgrgid(st.st_gid).gr_name
    except KeyError:
        group = str(st.st_gid)
    return owner, group


class TestBackupScriptExists:
    """Verify /home/user/backup.sh exists and is executable."""

    def test_backup_script_exists(self):
        """backup.sh must exist."""
        assert os.path.isfile(BACKUP_SCRIPT), f"{BACKUP_SCRIPT} does not exist"

    def test_backup_script_is_executable(self):
        """backup.sh must be executable."""
        assert os.access(BACKUP_SCRIPT, os.X_OK), f"{BACKUP_SCRIPT} is not executable"


class TestBackupScriptExecution:
    """Verify running the backup script works correctly."""

    def test_script_exits_zero(self):
        """Running backup.sh should exit with code 0."""
        # First clear the backups directory to test fresh run
        for root, dirs, files in os.walk(BACKUPS, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        result = subprocess.run(
            ["bash", BACKUP_SCRIPT],
            capture_output=True,
            text=True,
            cwd=HOME
        )
        assert result.returncode == 0, f"backup.sh exited with code {result.returncode}, stderr: {result.stderr}"

    def test_script_no_stderr_errors(self):
        """Running backup.sh should not produce error output to stderr."""
        # Clear backups again
        for root, dirs, files in os.walk(BACKUPS, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        result = subprocess.run(
            ["bash", BACKUP_SCRIPT],
            capture_output=True,
            text=True,
            cwd=HOME
        )
        # Allow empty stderr or only whitespace
        stderr = result.stderr.strip()
        assert stderr == "", f"backup.sh produced stderr output: {result.stderr}"


class TestBackedUpFiles:
    """Verify the correct files were backed up."""

    @pytest.fixture(autouse=True)
    def run_backup_script(self):
        """Run the backup script before testing backed up files."""
        # Clear backups directory
        for root, dirs, files in os.walk(BACKUPS, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        # Run the script
        subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, cwd=HOME)

    def test_alpha_config_json_backed_up(self):
        """alpha/config.json should be backed up with correct content."""
        backup_path = os.path.join(BACKUPS, "alpha", "config.json")
        assert os.path.isfile(backup_path), f"{backup_path} was not created"
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == "alpha config", f"{backup_path} has wrong content: {content}"

    def test_gamma_readable_md_backed_up(self):
        """gamma/readable.md should be backed up with correct content."""
        backup_path = os.path.join(BACKUPS, "gamma", "readable.md")
        assert os.path.isfile(backup_path), f"{backup_path} was not created"
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == "gamma readme", f"{backup_path} has wrong content: {content}"

    def test_gamma_subdir_deep_txt_backed_up(self):
        """gamma/subdir/deep.txt should be backed up with correct content."""
        backup_path = os.path.join(BACKUPS, "gamma", "subdir", "deep.txt")
        assert os.path.isfile(backup_path), f"{backup_path} was not created"
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == "deep file", f"{backup_path} has wrong content: {content}"

    def test_beta_data_csv_backed_up(self):
        """beta/data.csv should be backed up with correct content."""
        backup_path = os.path.join(BACKUPS, "beta", "data.csv")
        assert os.path.isfile(backup_path), f"{backup_path} was not created - script may not handle execute-only directories correctly"
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == "beta,data,here", f"{backup_path} has wrong content: {content}"

    def test_beta_notes_txt_backed_up(self):
        """beta/notes.txt should be backed up with correct content."""
        backup_path = os.path.join(BACKUPS, "beta", "notes.txt")
        assert os.path.isfile(backup_path), f"{backup_path} was not created - script may not handle execute-only directories correctly"
        with open(backup_path, 'r') as f:
            content = f.read()
        assert content == "beta notes", f"{backup_path} has wrong content: {content}"


class TestExcludedFiles:
    """Verify files that should NOT be backed up are absent."""

    @pytest.fixture(autouse=True)
    def run_backup_script(self):
        """Run the backup script before testing."""
        # Clear backups directory
        for root, dirs, files in os.walk(BACKUPS, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        # Run the script
        subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, cwd=HOME)

    def test_alpha_secret_key_not_backed_up(self):
        """alpha/secret.key should NOT be backed up (unreadable by user)."""
        backup_path = os.path.join(BACKUPS, "alpha", "secret.key")
        assert not os.path.exists(backup_path), f"{backup_path} should not exist - unreadable files should be skipped"

    def test_gamma_locked_dat_not_backed_up(self):
        """gamma/locked.dat should NOT be backed up (unreadable by user)."""
        backup_path = os.path.join(BACKUPS, "gamma", "locked.dat")
        assert not os.path.exists(backup_path), f"{backup_path} should not exist - unreadable files should be skipped"

    def test_delta_directory_not_backed_up(self):
        """delta/ directory should NOT exist in backups (inaccessible)."""
        backup_path = os.path.join(BACKUPS, "delta")
        assert not os.path.exists(backup_path), f"{backup_path} should not exist - inaccessible directory should be skipped"

    def test_delta_forbidden_txt_not_backed_up(self):
        """delta/forbidden.txt should NOT be backed up."""
        backup_path = os.path.join(BACKUPS, "delta", "forbidden.txt")
        assert not os.path.exists(backup_path), f"{backup_path} should not exist"


class TestManifestFile:
    """Verify manifest.txt exists and has correct content."""

    @pytest.fixture(autouse=True)
    def run_backup_script(self):
        """Run the backup script before testing manifest."""
        # Clear backups directory
        for root, dirs, files in os.walk(BACKUPS, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        # Run the script
        subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, cwd=HOME)

    def test_manifest_exists(self):
        """manifest.txt must exist in backups directory."""
        assert os.path.isfile(MANIFEST), f"{MANIFEST} does not exist"

    def test_manifest_has_five_entries(self):
        """manifest.txt must have exactly 5 lines (one per copied file)."""
        with open(MANIFEST, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 5, f"manifest.txt should have 5 entries, but has {len(lines)}: {lines}"

    def test_manifest_contains_alpha_config(self):
        """manifest.txt must contain entry for alpha/config.json with user:user."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        # Check for the file path and ownership
        assert "alpha/config.json" in content, "manifest.txt missing alpha/config.json"
        # Find the line with alpha/config.json and verify ownership
        for line in content.strip().split('\n'):
            if "alpha/config.json" in line:
                assert "user:user" in line, f"alpha/config.json should have user:user ownership in manifest, got: {line}"
                break

    def test_manifest_contains_gamma_readable(self):
        """manifest.txt must contain entry for gamma/readable.md with user:user."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "gamma/readable.md" in content, "manifest.txt missing gamma/readable.md"
        for line in content.strip().split('\n'):
            if "gamma/readable.md" in line:
                assert "user:user" in line, f"gamma/readable.md should have user:user ownership in manifest, got: {line}"
                break

    def test_manifest_contains_gamma_subdir_deep(self):
        """manifest.txt must contain entry for gamma/subdir/deep.txt with user:user."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "gamma/subdir/deep.txt" in content, "manifest.txt missing gamma/subdir/deep.txt"
        for line in content.strip().split('\n'):
            if "gamma/subdir/deep.txt" in line:
                assert "user:user" in line, f"gamma/subdir/deep.txt should have user:user ownership in manifest, got: {line}"
                break

    def test_manifest_contains_beta_data_csv(self):
        """manifest.txt must contain entry for beta/data.csv with user:user."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "beta/data.csv" in content, "manifest.txt missing beta/data.csv - script may not handle execute-only directories"
        for line in content.strip().split('\n'):
            if "beta/data.csv" in line:
                assert "user:user" in line, f"beta/data.csv should have user:user ownership in manifest, got: {line}"
                break

    def test_manifest_contains_beta_notes_txt(self):
        """manifest.txt must contain entry for beta/notes.txt with user:user."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "beta/notes.txt" in content, "manifest.txt missing beta/notes.txt - script may not handle execute-only directories"
        for line in content.strip().split('\n'):
            if "beta/notes.txt" in line:
                assert "user:user" in line, f"beta/notes.txt should have user:user ownership in manifest, got: {line}"
                break

    def test_manifest_excludes_secret_key(self):
        """manifest.txt must NOT contain alpha/secret.key."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "secret.key" not in content, "manifest.txt should not contain secret.key (unreadable file)"

    def test_manifest_excludes_locked_dat(self):
        """manifest.txt must NOT contain gamma/locked.dat."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "locked.dat" not in content, "manifest.txt should not contain locked.dat (unreadable file)"

    def test_manifest_excludes_forbidden(self):
        """manifest.txt must NOT contain delta/forbidden.txt."""
        with open(MANIFEST, 'r') as f:
            content = f.read()
        assert "forbidden" not in content, "manifest.txt should not contain forbidden.txt (inaccessible directory)"

    def test_manifest_line_format(self):
        """Each manifest line should be in format 'path owner:group'."""
        with open(MANIFEST, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            parts = line.split()
            assert len(parts) >= 2, f"Manifest line should have at least path and owner:group: {line}"
            # Last part should contain a colon (owner:group)
            ownership = parts[-1]
            assert ':' in ownership, f"Manifest line should end with owner:group format: {line}"


class TestProjectsUnchanged:
    """Verify /home/user/projects remains unchanged."""

    def test_alpha_config_unchanged(self):
        """alpha/config.json should be unchanged."""
        path = os.path.join(PROJECTS, "alpha", "config.json")
        with open(path, 'r') as f:
            content = f.read()
        assert content == "alpha config", f"Source file {path} was modified!"

    def test_gamma_readable_unchanged(self):
        """gamma/readable.md should be unchanged."""
        path = os.path.join(PROJECTS, "gamma", "readable.md")
        with open(path, 'r') as f:
            content = f.read()
        assert content == "gamma readme", f"Source file {path} was modified!"

    def test_beta_data_unchanged(self):
        """beta/data.csv should be unchanged."""
        path = os.path.join(PROJECTS, "beta", "data.csv")
        with open(path, 'r') as f:
            content = f.read()
        assert content == "beta,data,here", f"Source file {path} was modified!"


class TestScriptRerunnable:
    """Verify script can be run multiple times without issues."""

    def test_rerun_produces_no_errors(self):
        """Running the script twice should not produce errors."""
        # First run
        subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, cwd=HOME)

        # Second run
        result = subprocess.run(
            ["bash", BACKUP_SCRIPT],
            capture_output=True,
            text=True,
            cwd=HOME
        )
        assert result.returncode == 0, f"Second run failed with code {result.returncode}, stderr: {result.stderr}"

    def test_rerun_no_duplicate_manifest_entries(self):
        """Running the script twice should not duplicate manifest entries."""
        # Clear and run twice
        for root, dirs, files in os.walk(BACKUPS, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, cwd=HOME)
        subprocess.run(["bash", BACKUP_SCRIPT], capture_output=True, cwd=HOME)

        with open(MANIFEST, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        # Should still have exactly 5 entries, not 10
        assert len(lines) == 5, f"After rerun, manifest should have 5 entries, not {len(lines)} (possible duplicates)"
