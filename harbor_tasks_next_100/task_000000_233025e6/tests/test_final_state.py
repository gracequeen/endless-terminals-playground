# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has created the symlink for ndk-current pointing to ndk-r26b.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Validate the final filesystem state after the symlink task is completed."""

    def test_ndk_current_exists(self):
        """Verify /home/user/android/ndk-current exists and is accessible."""
        ndk_current_path = "/home/user/android/ndk-current"
        assert os.path.exists(ndk_current_path), (
            f"Path {ndk_current_path} does not exist. "
            "The symlink ndk-current must be created pointing to ndk-r26b."
        )

    def test_ndk_current_is_symlink(self):
        """Verify /home/user/android/ndk-current is a symbolic link (not a copy or hardlink)."""
        ndk_current_path = "/home/user/android/ndk-current"
        assert os.path.islink(ndk_current_path), (
            f"{ndk_current_path} exists but is not a symbolic link. "
            "The task requires creating a symlink, not copying or hardlinking."
        )

    def test_ndk_current_is_symlink_via_shell(self):
        """Anti-shortcut guard: use test -L to confirm it's a symlink."""
        result = subprocess.run(
            ["test", "-L", "/home/user/android/ndk-current"],
            capture_output=True
        )
        assert result.returncode == 0, (
            "Command 'test -L /home/user/android/ndk-current' failed. "
            "ndk-current must be a symbolic link."
        )

    def test_ndk_current_points_to_ndk_r26b(self):
        """Verify the symlink resolves to /home/user/android/ndk-r26b."""
        ndk_current_path = "/home/user/android/ndk-current"
        ndk_r26b_path = "/home/user/android/ndk-r26b"

        # Get the real path that the symlink resolves to
        resolved_path = os.path.realpath(ndk_current_path)
        expected_real_path = os.path.realpath(ndk_r26b_path)

        assert resolved_path == expected_real_path, (
            f"Symlink {ndk_current_path} resolves to {resolved_path}, "
            f"but expected it to resolve to {expected_real_path}."
        )

    def test_readlink_output(self):
        """Verify readlink shows the symlink target is ndk-r26b (absolute or relative)."""
        ndk_current_path = "/home/user/android/ndk-current"

        # Get the direct symlink target
        link_target = os.readlink(ndk_current_path)

        # The target could be absolute or relative
        # If relative, resolve it from the symlink's directory
        if os.path.isabs(link_target):
            resolved_target = os.path.realpath(link_target)
        else:
            symlink_dir = os.path.dirname(ndk_current_path)
            resolved_target = os.path.realpath(os.path.join(symlink_dir, link_target))

        expected_path = os.path.realpath("/home/user/android/ndk-r26b")

        assert resolved_target == expected_path, (
            f"Symlink target '{link_target}' does not resolve to ndk-r26b. "
            f"Resolved to: {resolved_target}, expected: {expected_path}"
        )

    def test_ndk_current_contents_match_ndk_r26b(self):
        """Verify ls /home/user/android/ndk-current/ shows same contents as ndk-r26b."""
        ndk_current_path = "/home/user/android/ndk-current"
        ndk_r26b_path = "/home/user/android/ndk-r26b"

        current_contents = set(os.listdir(ndk_current_path))
        r26b_contents = set(os.listdir(ndk_r26b_path))

        assert current_contents == r26b_contents, (
            f"Contents of {ndk_current_path} do not match {ndk_r26b_path}. "
            f"ndk-current has: {current_contents}, ndk-r26b has: {r26b_contents}"
        )

    def test_ndk_r26b_still_exists_as_directory(self):
        """Invariant: /home/user/android/ndk-r26b/ must still exist as a real directory."""
        ndk_r26b_path = "/home/user/android/ndk-r26b"
        assert os.path.exists(ndk_r26b_path), (
            f"Directory {ndk_r26b_path} no longer exists. "
            "The original NDK installation must not be moved or deleted."
        )
        assert os.path.isdir(ndk_r26b_path), (
            f"{ndk_r26b_path} is not a directory."
        )
        # Ensure it's not itself a symlink (it should be the real directory)
        assert not os.path.islink(ndk_r26b_path), (
            f"{ndk_r26b_path} has become a symlink. "
            "The original NDK directory must remain unchanged."
        )

    def test_ndk_r26b_contents_intact(self):
        """Invariant: ndk-r26b still contains expected files."""
        ndk_r26b_path = "/home/user/android/ndk-r26b"

        # Check key files still exist
        expected_items = [
            ("ndk-build", "file"),
            ("source.properties", "file"),
            ("toolchains", "directory"),
        ]

        for item_name, item_type in expected_items:
            item_path = os.path.join(ndk_r26b_path, item_name)
            assert os.path.exists(item_path), (
                f"{item_path} no longer exists. "
                "The original NDK installation contents must remain intact."
            )
            if item_type == "directory":
                assert os.path.isdir(item_path), (
                    f"{item_path} should be a directory."
                )

    def test_can_access_ndk_build_via_symlink(self):
        """Verify ndk-build is accessible through the symlink."""
        ndk_build_via_symlink = "/home/user/android/ndk-current/ndk-build"
        assert os.path.exists(ndk_build_via_symlink), (
            f"{ndk_build_via_symlink} is not accessible through the symlink. "
            "The symlink should allow access to all NDK files."
        )

    def test_can_access_source_properties_via_symlink(self):
        """Verify source.properties is accessible through the symlink."""
        source_props_via_symlink = "/home/user/android/ndk-current/source.properties"
        assert os.path.exists(source_props_via_symlink), (
            f"{source_props_via_symlink} is not accessible through the symlink. "
            "The symlink should allow access to all NDK files."
        )

    def test_can_access_toolchains_via_symlink(self):
        """Verify toolchains directory is accessible through the symlink."""
        toolchains_via_symlink = "/home/user/android/ndk-current/toolchains"
        assert os.path.exists(toolchains_via_symlink), (
            f"{toolchains_via_symlink} is not accessible through the symlink. "
            "The symlink should allow access to all NDK directories."
        )
        assert os.path.isdir(toolchains_via_symlink), (
            f"{toolchains_via_symlink} should be accessible as a directory."
        )
