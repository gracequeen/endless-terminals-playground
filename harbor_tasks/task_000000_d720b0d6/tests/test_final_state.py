# test_final_state.py
"""
Tests to validate the final state after the student has fixed the export_users.sh script.
The script should now correctly process user data and produce clean CSV output.
"""

import os
import subprocess
import hashlib
import pytest


# Base paths
ADMIN_DIR = "/home/user/admin"
DATA_DIR = "/home/user/admin/data"
SCRIPT_PATH = "/home/user/admin/export_users.sh"
EXPORT_CSV = "/home/user/admin/export.csv"
USERS_DAT = "/home/user/admin/data/users.dat"
EMAILS_DAT = "/home/user/admin/data/emails.dat"
GROUPS_DAT = "/home/user/admin/data/groups.dat"
MEMBERSHIPS_DAT = "/home/user/admin/data/memberships.dat"


class TestScriptExecution:
    """Test that the script runs successfully and produces output."""

    def test_script_exists(self):
        assert os.path.isfile(SCRIPT_PATH), f"Script {SCRIPT_PATH} does not exist"

    def test_script_is_executable_or_runnable(self):
        """Script should be runnable via bash."""
        assert os.access(SCRIPT_PATH, os.R_OK), f"Script {SCRIPT_PATH} is not readable"

    def test_script_references_source_files(self):
        """Anti-shortcut: Script must reference the source data files."""
        result = subprocess.run(
            ['grep', '-l', r'users\.dat\|emails\.dat', SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, \
            f"Script {SCRIPT_PATH} must reference users.dat or emails.dat (anti-shortcut guard)"

    def test_script_runs_successfully(self):
        """Running the script should exit with code 0."""
        result = subprocess.run(
            ['bash', SCRIPT_PATH],
            capture_output=True,
            text=True,
            cwd=ADMIN_DIR
        )
        assert result.returncode == 0, \
            f"Script exited with code {result.returncode}. stderr: {result.stderr}"

    def test_export_csv_created(self):
        """Script should produce export.csv."""
        # Run script first to ensure output exists
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)
        assert os.path.isfile(EXPORT_CSV), f"Output file {EXPORT_CSV} was not created"


class TestExportCsvStructure:
    """Test the structure of the export.csv file."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_export_csv_line_count(self):
        """export.csv should have exactly 801 lines (1 header + 800 data rows)."""
        result = subprocess.run(
            ['wc', '-l'],
            stdin=open(EXPORT_CSV, 'r'),
            capture_output=True,
            text=True
        )
        line_count = int(result.stdout.strip().split()[0])
        assert line_count == 801, \
            f"export.csv should have exactly 801 lines, found {line_count}"

    def test_header_line(self):
        """Header line should be: username,uid,primary_group,email,shell,supplementary_groups"""
        with open(EXPORT_CSV, 'r') as f:
            header = f.readline().strip()
        expected = "username,uid,primary_group,email,shell,supplementary_groups"
        assert header == expected, \
            f"Header should be '{expected}', found '{header}'"

    def test_all_rows_have_six_fields(self):
        """All rows should have exactly 6 comma-separated fields."""
        with open(EXPORT_CSV, 'r') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                # Count fields - need to handle potential commas in fields (though there shouldn't be any)
                fields = line.split(',')
                assert len(fields) == 6, \
                    f"Line {i} should have 6 fields, found {len(fields)}: {line[:80]}..."


class TestNoLeakedDelimiters:
    """Test that no raw delimiters from source files leak into output."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_no_tabs_in_output(self):
        """No tab characters should appear in export.csv."""
        result = subprocess.run(
            ['grep', '-P', '\t', EXPORT_CSV],
            capture_output=True,
            text=True
        )
        # grep returns 0 if matches found, 1 if no matches
        assert result.returncode == 1, \
            f"Found tab characters in export.csv (leaked delimiters): {result.stdout[:200]}"

    def test_no_pipes_in_data_rows(self):
        """No pipe characters should appear in data rows."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                assert '|' not in line, \
                    f"Line {i} contains pipe character (leaked delimiter): {line.strip()[:80]}"

    def test_no_colons_in_data_rows(self):
        """No colon characters should appear in data rows."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                assert ':' not in line, \
                    f"Line {i} contains colon character (leaked delimiter): {line.strip()[:80]}"


class TestEmailFieldValidity:
    """Test that email fields are properly formatted."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_all_emails_contain_at_symbol(self):
        """All email fields must contain exactly one @ symbol."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                fields = line.strip().split(',')
                if len(fields) >= 4:
                    email = fields[3]
                    at_count = email.count('@')
                    assert at_count == 1, \
                        f"Line {i} email field should contain exactly one @, found {at_count}: '{email}'"

    def test_emails_have_no_tabs(self):
        """Email fields should not contain tab characters."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                fields = line.strip().split(',')
                if len(fields) >= 4:
                    email = fields[3]
                    assert '\t' not in email, \
                        f"Line {i} email field contains tab character: '{repr(email)}'"


class TestGroupNameResolution:
    """Test that group names are resolved from numeric gids."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_no_numeric_primary_groups(self):
        """Primary group field should contain alphabetic names, not numeric gids."""
        result = subprocess.run(
            ['awk', '-F,', 'NR>1 && $3 ~ /^[0-9]+$/', EXPORT_CSV],
            capture_output=True,
            text=True
        )
        lines_with_numeric = result.stdout.strip()
        assert lines_with_numeric == "", \
            f"Found rows with numeric primary_group (should be group names): {lines_with_numeric[:200]}"

    def test_no_numeric_supplementary_groups(self):
        """Supplementary groups should be alphabetic names, not numeric gids."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                fields = line.strip().split(',')
                if len(fields) >= 6:
                    supp_groups = fields[5]
                    if supp_groups:  # May be empty
                        for group in supp_groups.split(';'):
                            group = group.strip()
                            if group:
                                assert not group.isdigit(), \
                                    f"Line {i} has numeric supplementary group '{group}' (should be name)"

    def test_primary_groups_are_alphabetic(self):
        """Primary group names should be alphabetic (letters, possibly with underscores/hyphens)."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                fields = line.strip().split(',')
                if len(fields) >= 3:
                    primary_group = fields[2]
                    # Group names should contain letters, not be purely numeric
                    has_letters = any(c.isalpha() for c in primary_group)
                    assert has_letters, \
                        f"Line {i} primary_group '{primary_group}' should contain letters"


class TestSpotCheckAconner:
    """Spot check: user aconner should have correct data."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_aconner_exists(self):
        """User aconner should exist in export.csv."""
        with open(EXPORT_CSV, 'r') as f:
            content = f.read()
        assert 'aconner,' in content, "User 'aconner' not found in export.csv"

    def test_aconner_full_record(self):
        """User aconner should have correct full record."""
        with open(EXPORT_CSV, 'r') as f:
            for line in f:
                if line.startswith('aconner,'):
                    fields = line.strip().split(',')
                    assert len(fields) == 6, f"aconner row should have 6 fields: {line}"

                    username, uid, primary_group, email, shell, supp_groups = fields

                    assert username == 'aconner', f"Username should be 'aconner': {username}"
                    assert uid == '1042', f"UID should be '1042': {uid}"
                    assert primary_group == 'engineering', \
                        f"Primary group should be 'engineering': {primary_group}"
                    assert email == 'aconner@corp.local', \
                        f"Email should be 'aconner@corp.local': {email}"
                    assert shell == '/bin/bash', f"Shell should be '/bin/bash': {shell}"

                    # Check supplementary groups (order may vary)
                    supp_set = set(supp_groups.split(';'))
                    expected_supp = {'engineering', 'devops', 'contractors'}
                    assert supp_set == expected_supp, \
                        f"Supplementary groups should be {expected_supp}: {supp_set}"
                    return

        pytest.fail("User 'aconner' not found in export.csv")


class TestSpotCheckZyang:
    """Spot check: user zyang should have correct data."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_zyang_exists(self):
        """User zyang should exist in export.csv."""
        with open(EXPORT_CSV, 'r') as f:
            content = f.read()
        assert 'zyang,' in content, "User 'zyang' not found in export.csv"

    def test_zyang_full_record(self):
        """User zyang should have correct full record."""
        with open(EXPORT_CSV, 'r') as f:
            for line in f:
                if line.startswith('zyang,'):
                    fields = line.strip().split(',')
                    assert len(fields) == 6, f"zyang row should have 6 fields: {line}"

                    username, uid, primary_group, email, shell, supp_groups = fields

                    assert username == 'zyang', f"Username should be 'zyang': {username}"
                    assert uid == '1799', f"UID should be '1799': {uid}"
                    assert primary_group == 'research', \
                        f"Primary group should be 'research': {primary_group}"
                    assert email == 'zyang@corp.local', \
                        f"Email should be 'zyang@corp.local': {email}"
                    assert shell == '/bin/zsh', f"Shell should be '/bin/zsh': {shell}"

                    # Check supplementary groups (order may vary)
                    supp_set = set(supp_groups.split(';'))
                    expected_supp = {'research', 'interns'}
                    assert supp_set == expected_supp, \
                        f"Supplementary groups should be {expected_supp}: {supp_set}"
                    return

        pytest.fail("User 'zyang' not found in export.csv")


class TestSourceFilesUnmodified:
    """Test that source files remain unmodified (invariant)."""

    def test_users_dat_exists(self):
        assert os.path.isfile(USERS_DAT), f"Source file {USERS_DAT} should still exist"

    def test_emails_dat_exists(self):
        assert os.path.isfile(EMAILS_DAT), f"Source file {EMAILS_DAT} should still exist"

    def test_groups_dat_exists(self):
        assert os.path.isfile(GROUPS_DAT), f"Source file {GROUPS_DAT} should still exist"

    def test_memberships_dat_exists(self):
        assert os.path.isfile(MEMBERSHIPS_DAT), f"Source file {MEMBERSHIPS_DAT} should still exist"

    def test_users_dat_still_pipe_delimited(self):
        """users.dat should still be pipe-delimited."""
        with open(USERS_DAT, 'r') as f:
            first_line = f.readline().strip()
        assert '|' in first_line, "users.dat should still be pipe-delimited"

    def test_emails_dat_still_tab_delimited(self):
        """emails.dat should still be tab-delimited."""
        with open(EMAILS_DAT, 'r') as f:
            first_line = f.readline().strip()
        assert '\t' in first_line, "emails.dat should still be tab-delimited"

    def test_groups_dat_still_colon_delimited(self):
        """groups.dat should still be colon-delimited."""
        with open(GROUPS_DAT, 'r') as f:
            first_line = f.readline().strip()
        assert ':' in first_line, "groups.dat should still be colon-delimited"

    def test_users_dat_line_count_unchanged(self):
        """users.dat should still have ~800 lines."""
        with open(USERS_DAT, 'r') as f:
            lines = [l for l in f if l.strip()]
        assert 750 <= len(lines) <= 850, \
            f"users.dat should still have ~800 lines, found {len(lines)}"


class TestOutputGeneratedByScript:
    """Test that output is actually generated by the script, not manually created."""

    def test_script_produces_output_when_run(self):
        """Running the script should produce/update export.csv."""
        # Remove existing export.csv if it exists
        if os.path.exists(EXPORT_CSV):
            os.remove(EXPORT_CSV)

        # Run the script
        result = subprocess.run(
            ['bash', SCRIPT_PATH],
            capture_output=True,
            text=True,
            cwd=ADMIN_DIR
        )

        assert result.returncode == 0, \
            f"Script should exit 0, got {result.returncode}. stderr: {result.stderr}"
        assert os.path.isfile(EXPORT_CSV), \
            "Script should create export.csv when run"

    def test_output_has_correct_row_count_after_fresh_run(self):
        """Fresh run should produce exactly 801 lines."""
        # Remove existing export.csv if it exists
        if os.path.exists(EXPORT_CSV):
            os.remove(EXPORT_CSV)

        # Run the script
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

        with open(EXPORT_CSV, 'r') as f:
            line_count = sum(1 for _ in f)

        assert line_count == 801, \
            f"Fresh run should produce exactly 801 lines, got {line_count}"


class TestDataIntegrity:
    """Test overall data integrity of the export."""

    @pytest.fixture(autouse=True)
    def run_script(self):
        """Run the script before each test in this class."""
        subprocess.run(['bash', SCRIPT_PATH], cwd=ADMIN_DIR, capture_output=True)

    def test_all_uids_are_numeric(self):
        """All UID fields should be numeric."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                fields = line.strip().split(',')
                if len(fields) >= 2:
                    uid = fields[1]
                    assert uid.isdigit(), \
                        f"Line {i} UID should be numeric: '{uid}'"

    def test_all_shells_are_paths(self):
        """All shell fields should be absolute paths starting with /."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            for i, line in enumerate(f, 2):
                fields = line.strip().split(',')
                if len(fields) >= 5:
                    shell = fields[4]
                    assert shell.startswith('/'), \
                        f"Line {i} shell should be absolute path: '{shell}'"

    def test_supplementary_groups_semicolon_separated(self):
        """Supplementary groups should be semicolon-separated."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            found_multiple_groups = False
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 6:
                    supp_groups = fields[5]
                    if ';' in supp_groups:
                        found_multiple_groups = True
                        # Verify it's semicolon-separated group names
                        groups = supp_groups.split(';')
                        for g in groups:
                            assert g.strip(), f"Empty group name in: {supp_groups}"
                        break

            # At least some users should have multiple supplementary groups
            assert found_multiple_groups, \
                "Expected some users to have multiple supplementary groups (semicolon-separated)"

    def test_unique_usernames(self):
        """All usernames should be unique."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            usernames = []
            for line in f:
                fields = line.strip().split(',')
                if fields:
                    usernames.append(fields[0])

        assert len(usernames) == len(set(usernames)), \
            "All usernames should be unique"

    def test_unique_uids(self):
        """All UIDs should be unique."""
        with open(EXPORT_CSV, 'r') as f:
            next(f)  # Skip header
            uids = []
            for line in f:
                fields = line.strip().split(',')
                if len(fields) >= 2:
                    uids.append(fields[1])

        assert len(uids) == len(set(uids)), \
            "All UIDs should be unique"
