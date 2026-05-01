# test_final_state.py
"""
Tests to validate the final state of the filesystem after the student
has fixed the group membership issue by correcting the typo in the group file.
"""

import os
import pytest

CUSTOMER_ENV_DIR = "/home/user/customer-env"


class TestCustomerEnvDirectoryExists:
    """Verify the customer-env directory still exists and is accessible."""

    def test_customer_env_directory_exists(self):
        assert os.path.isdir(CUSTOMER_ENV_DIR), (
            f"Directory {CUSTOMER_ENV_DIR} does not exist. "
            "The customer environment directory must be present."
        )


class TestRequiredFilesStillExist:
    """Verify all required files still exist in the customer-env directory."""

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
            f"The {filename} file must still be present in {CUSTOMER_ENV_DIR}."
        )


class TestGroupFileTypoFixed:
    """Verify the typo in the group file has been corrected."""

    def test_apprunner_correctly_spelled_in_datawriters(self):
        """
        Verify that 'apprunner' (correctly spelled) IS now in the datawriters group.
        """
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if line.startswith("datawriters:"):
                    fields = line.strip().split(":")
                    members = fields[3] if len(fields) > 3 else ""
                    member_list = [m.strip() for m in members.split(",") if m.strip()]

                    assert "apprunner" in member_list, (
                        f"The user 'apprunner' (correctly spelled) must be a member of the "
                        f"datawriters group. Current members: {member_list}. "
                        "The typo 'appruner' needed to be corrected to 'apprunner'."
                    )
                    return
        pytest.fail("datawriters group not found in group file")

    def test_typo_appruner_removed(self):
        """
        Verify that the misspelled 'appruner' is NO LONGER in the group file.
        """
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            content = f.read()

        # Check that the typo 'appruner' (missing second 'n') is not present anywhere
        # We need to be careful not to match 'apprunner' which contains 'appruner' as substring
        # So we check specifically for the typo pattern
        for line in content.splitlines():
            if line.startswith("datawriters:"):
                fields = line.strip().split(":")
                members = fields[3] if len(fields) > 3 else ""
                member_list = [m.strip() for m in members.split(",") if m.strip()]

                assert "appruner" not in member_list, (
                    "The typo 'appruner' (missing second 'n') must be removed from the "
                    "datawriters group. It should be corrected to 'apprunner', not left alongside it."
                )


class TestDatawritersGroupIntegrity:
    """Verify the datawriters group maintains its required properties."""

    def test_datawriters_gid_unchanged(self):
        """Verify the datawriters group GID is still 1020."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if line.startswith("datawriters:"):
                    fields = line.strip().split(":")
                    assert len(fields) >= 3, (
                        "datawriters group entry is malformed - not enough fields"
                    )
                    assert fields[2] == "1020", (
                        f"datawriters GID must remain 1020, but found {fields[2]}. "
                        "The GID should not be changed as part of the fix."
                    )
                    return
        pytest.fail("datawriters group not found in group file")

    def test_datawriters_group_exists(self):
        """Verify the datawriters group still exists."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            content = f.read()

        found = False
        for line in content.splitlines():
            if line.startswith("datawriters:"):
                found = True
                break

        assert found, (
            "The datawriters group must still exist in the group file. "
            "It should not be deleted or renamed."
        )


class TestGroupFileValidFormat:
    """Verify the group file is still in valid group(5) format."""

    def test_group_file_valid_format(self):
        """Verify all lines in the group file are properly formatted."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                fields = line.split(":")
                assert len(fields) == 4, (
                    f"Line {line_num} in group file is malformed: expected 4 colon-separated fields, "
                    f"got {len(fields)}. Line: '{line}'. "
                    "The group file must remain in valid group(5) format."
                )

    def test_group_file_not_corrupted(self):
        """Verify the group file can be read and parsed without errors."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        try:
            with open(group_path, "r") as f:
                lines = f.readlines()
            assert len(lines) > 0, "Group file should not be empty"
        except Exception as e:
            pytest.fail(f"Group file appears corrupted or unreadable: {e}")


class TestPasswdFileUnchanged:
    """Verify the passwd file was not modified."""

    def test_passwd_apprunner_unchanged(self):
        """Verify the apprunner user entry in passwd is unchanged."""
        passwd_path = os.path.join(CUSTOMER_ENV_DIR, "passwd")
        with open(passwd_path, "r") as f:
            for line in f:
                if line.startswith("apprunner:"):
                    fields = line.strip().split(":")
                    assert len(fields) >= 4, (
                        "apprunner passwd entry is malformed"
                    )
                    assert fields[0] == "apprunner", "Username should be apprunner"
                    assert fields[2] == "1005", (
                        f"apprunner's UID should remain 1005, found {fields[2]}"
                    )
                    assert fields[3] == "1005", (
                        f"apprunner's primary GID should remain 1005, found {fields[3]}"
                    )
                    return
        pytest.fail("apprunner user not found in passwd file - it should not be removed")


class TestOtherGroupsUnchanged:
    """Verify other groups were not altered."""

    def test_apprunner_group_unchanged(self):
        """Verify the apprunner group (GID 1005) still exists and is unchanged."""
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if line.startswith("apprunner:"):
                    fields = line.strip().split(":")
                    assert len(fields) >= 3, (
                        "apprunner group entry is malformed"
                    )
                    assert fields[2] == "1005", (
                        f"apprunner group GID should remain 1005, found {fields[2]}"
                    )
                    return
        pytest.fail("apprunner group not found in group file - it should not be removed")


class TestPermsFileUnchanged:
    """Verify the perms.txt file was not modified (it's a diagnostic dump)."""

    def test_perms_still_shows_datawriters(self):
        """Verify perms.txt still contains the original permission information."""
        perms_path = os.path.join(CUSTOMER_ENV_DIR, "perms.txt")
        with open(perms_path, "r") as f:
            content = f.read()

        assert "datawriters" in content, (
            "perms.txt should still show the original permission dump. "
            "This file is a diagnostic dump and should not be modified."
        )

    def test_perms_still_shows_uploads(self):
        """Verify perms.txt still contains uploads directory info."""
        perms_path = os.path.join(CUSTOMER_ENV_DIR, "perms.txt")
        with open(perms_path, "r") as f:
            content = f.read()

        assert "uploads" in content, (
            "perms.txt should still contain the uploads directory information. "
            "This file is a diagnostic dump and should not be modified."
        )


class TestShadowFileUnchanged:
    """Verify the shadow file was not modified."""

    def test_shadow_file_exists(self):
        """Verify the shadow file still exists."""
        shadow_path = os.path.join(CUSTOMER_ENV_DIR, "shadow")
        assert os.path.isfile(shadow_path), (
            "The shadow file must still exist in the customer-env directory."
        )


class TestGrepVerification:
    """Additional verification using grep-like checks as specified in anti-shortcut guards."""

    def test_grep_datawriters_shows_apprunner(self):
        """
        Simulate: grep datawriters /home/user/customer-env/group
        Should show 'apprunner' (correctly spelled) as a member.
        """
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            for line in f:
                if "datawriters" in line:
                    assert "apprunner" in line, (
                        "grep datawriters should show 'apprunner' as a member. "
                        f"Current line: {line.strip()}"
                    )
                    return
        pytest.fail("No line containing 'datawriters' found in group file")

    def test_grep_appruner_returns_empty(self):
        """
        Simulate: grep -E 'appruner' /home/user/customer-env/group
        Must return empty (the typo must be fixed, not left in place).
        """
        group_path = os.path.join(CUSTOMER_ENV_DIR, "group")
        with open(group_path, "r") as f:
            content = f.read()

        # Check for the exact typo 'appruner' (not 'apprunner')
        # We need to ensure 'appruner' as a standalone word is not present
        import re
        # Match 'appruner' as a word boundary or as a member in the group list
        # The typo would appear as ':appruner' or ',appruner' or 'appruner,'
        typo_patterns = [
            r':appruner$',      # at end of line after colon
            r':appruner,',      # followed by comma
            r',appruner$',      # at end after comma
            r',appruner,',      # between commas
        ]

        for pattern in typo_patterns:
            if re.search(pattern, content):
                pytest.fail(
                    f"The typo 'appruner' (missing second 'n') was found in the group file. "
                    "It must be corrected to 'apprunner', not left in place."
                )
