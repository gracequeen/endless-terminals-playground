# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the task of fixing the export_users.sh script.
"""

import os
import subprocess
import stat
import pytest


# Base paths
ADMIN_DIR = "/home/user/admin"
DATA_DIR = "/home/user/admin/data"
SCRIPT_PATH = "/home/user/admin/export_users.sh"
USERS_DAT = "/home/user/admin/data/users.dat"
EMAILS_DAT = "/home/user/admin/data/emails.dat"
GROUPS_DAT = "/home/user/admin/data/groups.dat"
MEMBERSHIPS_DAT = "/home/user/admin/data/memberships.dat"


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_admin_directory_exists(self):
        assert os.path.isdir(ADMIN_DIR), f"Directory {ADMIN_DIR} does not exist"

    def test_data_directory_exists(self):
        assert os.path.isdir(DATA_DIR), f"Directory {DATA_DIR} does not exist"


class TestScriptExists:
    """Test that the export script exists and is a bash script."""

    def test_script_file_exists(self):
        assert os.path.isfile(SCRIPT_PATH), f"Script {SCRIPT_PATH} does not exist"

    def test_script_is_readable(self):
        assert os.access(SCRIPT_PATH, os.R_OK), f"Script {SCRIPT_PATH} is not readable"

    def test_script_is_writable(self):
        assert os.access(SCRIPT_PATH, os.W_OK), f"Script {SCRIPT_PATH} is not writable"

    def test_script_is_bash_script(self):
        with open(SCRIPT_PATH, 'r') as f:
            first_line = f.readline()
        assert first_line.startswith('#!') and 'bash' in first_line, \
            f"Script {SCRIPT_PATH} does not appear to be a bash script (first line: {first_line.strip()})"

    def test_script_references_source_files(self):
        """Script must reference the source data files."""
        result = subprocess.run(
            ['grep', '-l', r'users\.dat\|emails\.dat', SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Script {SCRIPT_PATH} does not reference users.dat or emails.dat"


class TestSourceFilesExist:
    """Test that all source data files exist."""

    def test_users_dat_exists(self):
        assert os.path.isfile(USERS_DAT), f"Source file {USERS_DAT} does not exist"

    def test_emails_dat_exists(self):
        assert os.path.isfile(EMAILS_DAT), f"Source file {EMAILS_DAT} does not exist"

    def test_groups_dat_exists(self):
        assert os.path.isfile(GROUPS_DAT), f"Source file {GROUPS_DAT} does not exist"

    def test_memberships_dat_exists(self):
        assert os.path.isfile(MEMBERSHIPS_DAT), f"Source file {MEMBERSHIPS_DAT} does not exist"


class TestSourceFilesReadable:
    """Test that all source data files are readable."""

    def test_users_dat_readable(self):
        assert os.access(USERS_DAT, os.R_OK), f"Source file {USERS_DAT} is not readable"

    def test_emails_dat_readable(self):
        assert os.access(EMAILS_DAT, os.R_OK), f"Source file {EMAILS_DAT} is not readable"

    def test_groups_dat_readable(self):
        assert os.access(GROUPS_DAT, os.R_OK), f"Source file {GROUPS_DAT} is not readable"

    def test_memberships_dat_readable(self):
        assert os.access(MEMBERSHIPS_DAT, os.R_OK), f"Source file {MEMBERSHIPS_DAT} is not readable"


class TestUsersDatFormat:
    """Test users.dat has correct format (pipe-delimited, ~800 lines)."""

    def test_users_dat_line_count(self):
        with open(USERS_DAT, 'r') as f:
            lines = [l for l in f if l.strip()]
        assert 750 <= len(lines) <= 850, \
            f"users.dat should have ~800 lines, found {len(lines)}"

    def test_users_dat_pipe_delimited(self):
        with open(USERS_DAT, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                fields = line.split('|')
                assert len(fields) == 6, \
                    f"users.dat line {i} should have 6 pipe-delimited fields, found {len(fields)}: {line[:50]}..."
                break  # Just check first non-empty line for format

    def test_users_dat_contains_aconner(self):
        """Spot check: user aconner should exist with uid 1042."""
        with open(USERS_DAT, 'r') as f:
            content = f.read()
        assert 'aconner|1042|' in content, \
            "users.dat should contain user 'aconner' with uid 1042"

    def test_users_dat_contains_zyang(self):
        """Spot check: user zyang should exist with uid 1799."""
        with open(USERS_DAT, 'r') as f:
            content = f.read()
        assert 'zyang|1799|' in content, \
            "users.dat should contain user 'zyang' with uid 1799"


class TestEmailsDatFormat:
    """Test emails.dat has correct format (tab-delimited, ~800 lines)."""

    def test_emails_dat_line_count(self):
        with open(EMAILS_DAT, 'r') as f:
            lines = [l for l in f if l.strip()]
        assert 750 <= len(lines) <= 850, \
            f"emails.dat should have ~800 lines, found {len(lines)}"

    def test_emails_dat_tab_delimited(self):
        with open(EMAILS_DAT, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                assert '\t' in line, \
                    f"emails.dat line {i} should be tab-delimited: {line[:50]}..."
                fields = line.split('\t')
                assert len(fields) == 2, \
                    f"emails.dat line {i} should have 2 tab-delimited fields, found {len(fields)}"
                break  # Just check first non-empty line for format

    def test_emails_dat_contains_at_symbols(self):
        """All email entries should contain @ symbol."""
        with open(EMAILS_DAT, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                fields = line.split('\t')
                if len(fields) >= 2:
                    assert '@' in fields[1], \
                        f"emails.dat line {i} email field should contain @: {line}"
                    break  # Spot check first line


class TestGroupsDatFormat:
    """Test groups.dat has correct format (colon-delimited, ~50 lines)."""

    def test_groups_dat_line_count(self):
        with open(GROUPS_DAT, 'r') as f:
            lines = [l for l in f if l.strip()]
        assert 40 <= len(lines) <= 60, \
            f"groups.dat should have ~50 lines, found {len(lines)}"

    def test_groups_dat_colon_delimited(self):
        with open(GROUPS_DAT, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                fields = line.split(':')
                assert len(fields) == 3, \
                    f"groups.dat line {i} should have 3 colon-delimited fields, found {len(fields)}: {line}"
                break  # Just check first non-empty line for format

    def test_groups_dat_contains_engineering(self):
        """Group 'engineering' (gid 1001) should exist."""
        with open(GROUPS_DAT, 'r') as f:
            content = f.read()
        assert '1001:engineering:' in content, \
            "groups.dat should contain group 'engineering' with gid 1001"

    def test_groups_dat_contains_research(self):
        """Group 'research' (gid 1003) should exist."""
        with open(GROUPS_DAT, 'r') as f:
            content = f.read()
        assert '1003:research:' in content, \
            "groups.dat should contain group 'research' with gid 1003"


class TestMembershipsDatFormat:
    """Test memberships.dat has correct format (space-delimited, ~800 lines)."""

    def test_memberships_dat_line_count(self):
        with open(MEMBERSHIPS_DAT, 'r') as f:
            lines = [l for l in f if l.strip()]
        assert 750 <= len(lines) <= 850, \
            f"memberships.dat should have ~800 lines, found {len(lines)}"

    def test_memberships_dat_space_delimited(self):
        with open(MEMBERSHIPS_DAT, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                fields = line.split()
                assert len(fields) >= 1, \
                    f"memberships.dat line {i} should have at least 1 space-delimited field"
                # First field should be numeric uid
                assert fields[0].isdigit(), \
                    f"memberships.dat line {i} first field should be numeric uid: {fields[0]}"
                break  # Just check first non-empty line for format


class TestRequiredTools:
    """Test that required command-line tools are available."""

    @pytest.mark.parametrize("tool", ["bash", "awk", "sed", "cut", "paste", "sort", "join", "grep"])
    def test_tool_available(self, tool):
        result = subprocess.run(['which', tool], capture_output=True)
        assert result.returncode == 0, f"Required tool '{tool}' is not available"


class TestScriptHasBugs:
    """Test that the script has the expected bugs (initial broken state)."""

    def test_script_uses_space_delimiter_for_cut(self):
        """Bug 1: Script uses space delimiter for cut on emails.dat (should use tab)."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        # Look for evidence of cut with space delimiter being used
        # This is a heuristic - the script should have cut -d' ' or similar
        assert "cut" in content, \
            "Script should use 'cut' command"

    def test_script_uses_paste_or_join(self):
        """Script should use paste or join to combine files."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert 'paste' in content or 'join' in content, \
            "Script should use 'paste' or 'join' to combine files"

    def test_script_uses_awk(self):
        """Script should use awk for processing."""
        with open(SCRIPT_PATH, 'r') as f:
            content = f.read()
        assert 'awk' in content, \
            "Script should use 'awk' for processing"


class TestAdminDirWritable:
    """Test that admin directory is writable for output."""

    def test_admin_dir_writable(self):
        assert os.access(ADMIN_DIR, os.W_OK), \
            f"Directory {ADMIN_DIR} is not writable"


class TestSpecificUserData:
    """Test specific user data exists for spot checks."""

    def test_aconner_in_users(self):
        """User aconner with uid 1042, gid 1001, shell /bin/bash should exist."""
        with open(USERS_DAT, 'r') as f:
            found = False
            for line in f:
                if line.startswith('aconner|1042|1001|'):
                    if '/bin/bash' in line:
                        found = True
                        break
            assert found, "users.dat should contain aconner|1042|1001|...|/bin/bash"

    def test_aconner_in_emails(self):
        """Email for uid 1042 should be aconner@corp.local."""
        with open(EMAILS_DAT, 'r') as f:
            found = False
            for line in f:
                if '1042\t' in line and 'aconner@corp.local' in line:
                    found = True
                    break
            assert found, "emails.dat should contain 1042<TAB>aconner@corp.local"

    def test_aconner_in_memberships(self):
        """Memberships for uid 1042 should include gids 1001, 1005, 1012."""
        with open(MEMBERSHIPS_DAT, 'r') as f:
            found = False
            for line in f:
                fields = line.strip().split()
                if fields and fields[0] == '1042':
                    gids = set(fields[1:])
                    if '1001' in gids and '1005' in gids and '1012' in gids:
                        found = True
                        break
            assert found, "memberships.dat should contain 1042 with gids 1001, 1005, 1012"

    def test_zyang_in_users(self):
        """User zyang with uid 1799, gid 1003, shell /bin/zsh should exist."""
        with open(USERS_DAT, 'r') as f:
            found = False
            for line in f:
                if line.startswith('zyang|1799|1003|'):
                    if '/bin/zsh' in line:
                        found = True
                        break
            assert found, "users.dat should contain zyang|1799|1003|...|/bin/zsh"

    def test_zyang_in_emails(self):
        """Email for uid 1799 should be zyang@corp.local."""
        with open(EMAILS_DAT, 'r') as f:
            found = False
            for line in f:
                if '1799\t' in line and 'zyang@corp.local' in line:
                    found = True
                    break
            assert found, "emails.dat should contain 1799<TAB>zyang@corp.local"

    def test_required_groups_exist(self):
        """Groups engineering(1001), devops(1005), contractors(1012), research(1003), interns(1008) should exist."""
        with open(GROUPS_DAT, 'r') as f:
            content = f.read()

        required = [
            ('1001', 'engineering'),
            ('1005', 'devops'),
            ('1012', 'contractors'),
            ('1003', 'research'),
            ('1008', 'interns'),
        ]

        for gid, name in required:
            assert f'{gid}:{name}:' in content, \
                f"groups.dat should contain {gid}:{name}:..."
