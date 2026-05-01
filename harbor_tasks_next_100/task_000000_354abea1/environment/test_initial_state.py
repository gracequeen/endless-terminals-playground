# test_initial_state.py
"""
Tests to validate the initial state of the filesystem before the student
performs the task of fixing the group membership issue.
"""

import os
import pytest

CUSTOMER_ENV_DIR = "/home/user/customer-env"


class TestCustomerEnvDirectoryExists:
    """Verify the customer-env directory exists and is accessible."""

    def test_customer_env_directory_exists(self):
        assert os.path.isdir(CUSTOMER_ENV_DIR), (
            f"Directory {CUSTOMER_ENV_DIR} does not exist. "
            "The customer environment directory must be present."
        )


class TestRequiredFilesExist:
    """Verify all required files exist in the customer-env directory."""

    @pytest.mark.parametrize("filename", [
        "passwd",
        "group",
        "shadow",
        "perms.txt",
        "notes.txt",
    ])
    def test_required_file_exists(self, filename):
        filepath = os.path.join(CUSTOMER_ENV_DIR, filename)
        assert os.path.isfile(filepath), (
            f"Required file {filepath} does not exist. "
            f"The {filename} file must be present in {CUSTOMER_ENV_DIR}."
        )


class TestFilesAreWritable:
    """Verify all files in customer-env are writable by the agent."""

    @pytest.mark.parametrize("filename", [
        "passwd",
        "group",
        "shadow",
        "perms.txt",
        "notes.txt",
    ])
    def test_file_is_writable(self, filename):
        filepath = os.path.join(CUSTOMER_ENV_DIR, filename)
        if os.path.isfile(filepath):
            assert os.access(filepath, os.W_OK), (
                f"File {filepath} is not writable. "
                "The agent must be able to modify files in customer-env."
            )


class TestPasswdFileContent:
    """Verify the passwd file contains the expected apprunner user entry."""

    def test_passwd_contains_apprunner_user(self):
        passwd_path = os.path.join(CUSTOMER_ENV_DIR, "passwd")
        with open(passwd_path, "r") as f:
            content = f.read()

        assert "apprunner:x:1005:1005:" in content, (
            "The passwd file must contain the apprunner user with UID 1005 and GID 1005. "
            "Expected line containing 'apprunner:x:1005:1005:'"
        )

    def test_apprunner_primary_group_is_1005(self):
        passwd_path = os.path.join(CUSTOMER_ENV_DIR, "passwd")
        with open(passwd_path, "r") as f:
            for line in f:
                if line.startswith("apprunner:"):
                    fields = line.strip().split(":")
                    assert len(fields) >= 4, (
                        "apprunner passwd entry is malformed - not enough fields"
                    )
                    assert fields[3] == "1005", (
                        f"apprunner's primary GID should be 1005, found {fields[3]}"
                    )
                    return
        pytest.fail("apprunner user not found in passwd file")


class TestGroupFileContent:
    """Verify the group file contains the expected entries with the typo."""

    def test_group_contains_datawriters_group(self):
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            content = f.read()

        assert "datawriters:x:1020:" in content, (
            "The group file must contain the datawriters group with GID 1020. "
            "Expected line starting with 'datawriters:x:1020:'"
        )

    def test_group_contains_apprunner_group(self):
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            content = f.read()

        assert "apprunner:x:1005:" in content, (
            "The group file must contain the apprunner group with GID 1005."
        )

    def test_datawriters_has_typo_appruner(self):
        """Verify the initial state has the typo 'appruner' (missing 'n')."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if line.startswith("datawriters:"):
                    assert "appruner" in line, (
                        "Initial state must have the typo 'appruner' (missing second 'n') "
                        "in the datawriters group line. This is the bug the student needs to find."
                    )
                    return
        pytest.fail("datawriters group not found in group file")

    def test_datawriters_gid_is_1020(self):
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if line.startswith("datawriters:"):
                    fields = line.strip().split(":")
                    assert len(fields) >= 3, (
                        "datawriters group entry is malformed - not enough fields"
                    )
                    assert fields[2] == "1020", (
                        f"datawriters GID should be 1020, found {fields[2]}"
                    )
                    return
        pytest.fail("datawriters group not found in group file")

    def test_group_file_is_valid_format(self):
        """Verify the group file is in valid group(5) format."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                fields = line.split(":")
                assert len(fields) == 4, (
                    f"Line {line_num} in group file is malformed: expected 4 colon-separated fields, "
                    f"got {len(fields)}. Line: {line}"
                )


class TestPermsFileContent:
    """Verify the perms.txt file contains the expected directory permission info."""

    def test_perms_shows_uploads_owned_by_datawriters(self):
        perms_path = os.path.join(CUSTOMER_ENV_DIR, "perms.txt")
        with open(perms_path, "r") as f:
            content = f.read()

        assert "datawriters" in content, (
            "perms.txt must show that /srv/data/uploads is owned by the datawriters group"
        )

    def test_perms_shows_uploads_directory(self):
        perms_path = os.path.join(CUSTOMER_ENV_DIR, "perms.txt")
        with open(perms_path, "r") as f:
            content = f.read()

        assert "uploads" in content, (
            "perms.txt must contain information about the uploads directory"
        )

    def test_perms_shows_group_writable(self):
        perms_path = os.path.join(CUSTOMER_ENV_DIR, "perms.txt")
        with open(perms_path, "r") as f:
            content = f.read()

        # Should show drwxrwx--- or 0770 permissions
        assert "rwxrwx---" in content or "0770" in content, (
            "perms.txt must show that uploads directory has group write permissions (0770/drwxrwx---)"
        )


class TestNotesFileContent:
    """Verify the notes.txt file contains the expected customer notes."""

    def test_notes_mentions_usermod_command(self):
        notes_path = os.path.join(CUSTOMER_ENV_DIR, "notes.txt")
        with open(notes_path, "r") as f:
            content = f.read()

        assert "usermod" in content.lower() or "datawriters" in content.lower(), (
            "notes.txt should mention the usermod command or datawriters group "
            "as part of the customer's troubleshooting notes"
        )

    def test_notes_mentions_apprunner(self):
        notes_path = os.path.join(CUSTOMER_ENV_DIR, "notes.txt")
        with open(notes_path, "r") as f:
            content = f.read()

        assert "apprunner" in content, (
            "notes.txt should mention the apprunner user"
        )


class TestInitialStateBugPresent:
    """Verify the bug (typo) is present in the initial state."""

    def test_apprunner_not_correctly_in_datawriters(self):
        """
        Verify that 'apprunner' (correctly spelled) is NOT in the datawriters group.
        This confirms the bug is present for the student to fix.
        """
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if line.startswith("datawriters:"):
                    fields = line.strip().split(":")
                    members = fields[3] if len(fields) > 3 else ""
                    member_list = [m.strip() for m in members.split(",") if m.strip()]

                    # apprunner (correctly spelled) should NOT be in the list initially
                    # Only the misspelled "appruner" should be there
                    assert "apprunner" not in member_list, (
                        "Initial state error: 'apprunner' (correctly spelled) should NOT be "
                        "in the datawriters group yet. The typo 'appruner' should be present instead. "
                        "This is the bug the student needs to discover and fix."
                    )
                    return
        pytest.fail("datawriters group not found in group file")
