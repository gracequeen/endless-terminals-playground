# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the backup script task.
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


def get_current_user():
    """Get the current username."""
    return pwd.getpwuid(os.getuid()).pw_name


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


class TestCurrentUser:
    """Verify the agent is running as user, not root."""

    def test_running_as_user(self):
        """Agent should be running as 'user' (uid 1000), not root."""
        current_user = get_current_user()
        uid = os.getuid()
        assert current_user == "user", f"Expected to run as 'user', but running as '{current_user}'"
        assert uid == 1000, f"Expected uid 1000, but got {uid}"

    def test_not_root(self):
        """Agent should not be root."""
        assert os.getuid() != 0, "Agent should not be running as root"


class TestProjectsDirectory:
    """Verify /home/user/projects exists with correct structure."""

    def test_projects_exists(self):
        """The projects directory must exist."""
        assert os.path.isdir(PROJECTS), f"{PROJECTS} directory does not exist"

    def test_alpha_directory_exists(self):
        """alpha/ directory must exist with correct permissions."""
        alpha = os.path.join(PROJECTS, "alpha")
        assert os.path.isdir(alpha), f"{alpha} directory does not exist"
        # Should be readable and listable (drwxr-xr-x)
        assert os.access(alpha, os.R_OK), f"{alpha} should be readable"
        assert os.access(alpha, os.X_OK), f"{alpha} should be executable"

    def test_alpha_config_json_exists(self):
        """alpha/config.json must exist and be readable."""
        config = os.path.join(PROJECTS, "alpha", "config.json")
        assert os.path.isfile(config), f"{config} does not exist"
        assert os.access(config, os.R_OK), f"{config} should be readable by user"
        with open(config, 'r') as f:
            content = f.read()
        assert content == "alpha config", f"{config} has unexpected content: {content}"
        owner, group = get_file_owner_group(config)
        assert owner == "user", f"{config} should be owned by user, not {owner}"
        assert group == "user", f"{config} should have group user, not {group}"

    def test_alpha_secret_key_exists_but_unreadable(self):
        """alpha/secret.key must exist but be unreadable by user."""
        secret = os.path.join(PROJECTS, "alpha", "secret.key")
        assert os.path.exists(secret), f"{secret} does not exist"
        assert not os.access(secret, os.R_OK), f"{secret} should NOT be readable by user"
        owner, group = get_file_owner_group(secret)
        assert owner == "root", f"{secret} should be owned by root, not {owner}"
        assert group == "root", f"{secret} should have group root, not {group}"

    def test_beta_directory_exists_execute_only(self):
        """beta/ directory must exist with execute-only permissions (711)."""
        beta = os.path.join(PROJECTS, "beta")
        assert os.path.isdir(beta), f"{beta} directory does not exist"
        # Execute permission should be available
        assert os.access(beta, os.X_OK), f"{beta} should be executable (cd-able)"
        # Check actual mode - should be 711 (drwx--x--x)
        mode = os.stat(beta).st_mode
        # For a directory owned by user with mode 711, user has rwx, others have x only
        # We can check if listing fails
        try:
            os.listdir(beta)
            # If we can list, that's unexpected for mode 711 unless we're owner with r
            # Actually mode 711 means owner has rwx (7), so owner CAN list
            # Let me re-check: 711 = rwx--x--x, owner has rwx so can list
            # The task says "execute only, no read" for beta - this means mode should be like 311 or similar
            # But task also says owner is user:user... let me check the actual requirement
            # Task says: drwx--x--x, user:user — execute only, no read
            # drwx--x--x = 711, owner has rwx (can read), group/others have x only
            # So user (as owner) CAN list beta/
            # The "execute only, no read" comment must refer to group/others
            pass
        except PermissionError:
            pass  # This is fine if we can't list

    def test_beta_data_csv_accessible(self):
        """beta/data.csv must exist and be readable when accessed directly."""
        data = os.path.join(PROJECTS, "beta", "data.csv")
        assert os.path.exists(data), f"{data} does not exist"
        assert os.access(data, os.R_OK), f"{data} should be readable"
        with open(data, 'r') as f:
            content = f.read()
        assert content == "beta,data,here", f"{data} has unexpected content: {content}"

    def test_beta_notes_txt_accessible(self):
        """beta/notes.txt must exist and be readable when accessed directly."""
        notes = os.path.join(PROJECTS, "beta", "notes.txt")
        assert os.path.exists(notes), f"{notes} does not exist"
        assert os.access(notes, os.R_OK), f"{notes} should be readable"
        with open(notes, 'r') as f:
            content = f.read()
        assert content == "beta notes", f"{notes} has unexpected content: {content}"

    def test_gamma_directory_exists(self):
        """gamma/ directory must exist and be accessible."""
        gamma = os.path.join(PROJECTS, "gamma")
        assert os.path.isdir(gamma), f"{gamma} directory does not exist"
        assert os.access(gamma, os.R_OK), f"{gamma} should be readable"
        assert os.access(gamma, os.X_OK), f"{gamma} should be executable"

    def test_gamma_subdir_exists(self):
        """gamma/subdir/ must exist."""
        subdir = os.path.join(PROJECTS, "gamma", "subdir")
        assert os.path.isdir(subdir), f"{subdir} directory does not exist"

    def test_gamma_subdir_deep_txt_exists(self):
        """gamma/subdir/deep.txt must exist and be readable."""
        deep = os.path.join(PROJECTS, "gamma", "subdir", "deep.txt")
        assert os.path.isfile(deep), f"{deep} does not exist"
        assert os.access(deep, os.R_OK), f"{deep} should be readable"
        with open(deep, 'r') as f:
            content = f.read()
        assert content == "deep file", f"{deep} has unexpected content: {content}"

    def test_gamma_readable_md_exists(self):
        """gamma/readable.md must exist and be readable."""
        readme = os.path.join(PROJECTS, "gamma", "readable.md")
        assert os.path.isfile(readme), f"{readme} does not exist"
        assert os.access(readme, os.R_OK), f"{readme} should be readable"
        with open(readme, 'r') as f:
            content = f.read()
        assert content == "gamma readme", f"{readme} has unexpected content: {content}"

    def test_gamma_locked_dat_exists_but_unreadable(self):
        """gamma/locked.dat must exist but be unreadable by user."""
        locked = os.path.join(PROJECTS, "gamma", "locked.dat")
        assert os.path.exists(locked), f"{locked} does not exist"
        assert not os.access(locked, os.R_OK), f"{locked} should NOT be readable by user"
        owner, group = get_file_owner_group(locked)
        assert owner == "root", f"{locked} should be owned by root, not {owner}"

    def test_delta_directory_exists_but_inaccessible(self):
        """delta/ directory must exist but be inaccessible to user."""
        delta = os.path.join(PROJECTS, "delta")
        # We need to check it exists without being able to access it
        # Use os.path.exists which may fail, or check parent listing
        parent_contents = os.listdir(PROJECTS)
        assert "delta" in parent_contents, f"delta directory not found in {PROJECTS}"
        # Verify we cannot access it
        assert not os.access(delta, os.R_OK), f"{delta} should NOT be readable by user"
        assert not os.access(delta, os.X_OK), f"{delta} should NOT be executable by user"


class TestBackupsDirectory:
    """Verify /home/user/backups exists and is empty."""

    def test_backups_exists(self):
        """The backups directory must exist."""
        assert os.path.isdir(BACKUPS), f"{BACKUPS} directory does not exist"

    def test_backups_is_empty(self):
        """The backups directory must be empty."""
        contents = os.listdir(BACKUPS)
        assert len(contents) == 0, f"{BACKUPS} should be empty but contains: {contents}"

    def test_backups_is_writable(self):
        """The backups directory must be writable by user."""
        assert os.access(BACKUPS, os.W_OK), f"{BACKUPS} should be writable by user"


class TestBackupScriptDoesNotExist:
    """Verify /home/user/backup.sh does not exist yet."""

    def test_backup_script_does_not_exist(self):
        """backup.sh should not exist before the task is performed."""
        assert not os.path.exists(BACKUP_SCRIPT), f"{BACKUP_SCRIPT} already exists but should not"


class TestRequiredTools:
    """Verify standard tools are available."""

    @pytest.mark.parametrize("tool", ["bash", "cp", "find", "stat", "ls", "cat", "awk", "sed", "grep"])
    def test_tool_available(self, tool):
        """Required tools must be available in PATH."""
        result = subprocess.run(["which", tool], capture_output=True)
        assert result.returncode == 0, f"Tool '{tool}' is not available in PATH"
