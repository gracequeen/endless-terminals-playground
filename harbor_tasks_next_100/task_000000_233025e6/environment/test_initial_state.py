# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
creates the symlink for ndk-current pointing to ndk-r26b.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial filesystem state before the symlink task."""

    def test_android_directory_exists(self):
        """Verify /home/user/android/ directory exists."""
        android_dir = "/home/user/android"
        assert os.path.exists(android_dir), (
            f"Directory {android_dir} does not exist. "
            "The android directory must exist before creating the symlink."
        )
        assert os.path.isdir(android_dir), (
            f"{android_dir} exists but is not a directory."
        )

    def test_android_directory_is_writable(self):
        """Verify /home/user/android/ is writable."""
        android_dir = "/home/user/android"
        assert os.access(android_dir, os.W_OK), (
            f"Directory {android_dir} is not writable. "
            "Write permission is required to create the symlink."
        )

    def test_ndk_r26b_directory_exists(self):
        """Verify /home/user/android/ndk-r26b/ directory exists."""
        ndk_r26b_dir = "/home/user/android/ndk-r26b"
        assert os.path.exists(ndk_r26b_dir), (
            f"Directory {ndk_r26b_dir} does not exist. "
            "The NDK r26b installation must be present."
        )
        assert os.path.isdir(ndk_r26b_dir), (
            f"{ndk_r26b_dir} exists but is not a directory."
        )

    def test_ndk_r26b_contains_ndk_build(self):
        """Verify ndk-r26b contains ndk-build executable."""
        ndk_build_path = "/home/user/android/ndk-r26b/ndk-build"
        assert os.path.exists(ndk_build_path), (
            f"File {ndk_build_path} does not exist. "
            "The NDK installation should contain ndk-build."
        )

    def test_ndk_r26b_contains_source_properties(self):
        """Verify ndk-r26b contains source.properties file."""
        source_props_path = "/home/user/android/ndk-r26b/source.properties"
        assert os.path.exists(source_props_path), (
            f"File {source_props_path} does not exist. "
            "The NDK installation should contain source.properties."
        )

    def test_ndk_r26b_contains_toolchains_directory(self):
        """Verify ndk-r26b contains toolchains/ directory."""
        toolchains_path = "/home/user/android/ndk-r26b/toolchains"
        assert os.path.exists(toolchains_path), (
            f"Directory {toolchains_path} does not exist. "
            "The NDK installation should contain a toolchains directory."
        )
        assert os.path.isdir(toolchains_path), (
            f"{toolchains_path} exists but is not a directory."
        )

    def test_ndk_current_does_not_exist(self):
        """Verify /home/user/android/ndk-current does NOT exist."""
        ndk_current_path = "/home/user/android/ndk-current"
        assert not os.path.exists(ndk_current_path), (
            f"Path {ndk_current_path} already exists. "
            "The ndk-current path should not exist before creating the symlink."
        )
        # Also check that it's not a broken symlink
        assert not os.path.islink(ndk_current_path), (
            f"Path {ndk_current_path} is a symlink (possibly broken). "
            "The ndk-current path should not exist at all before the task."
        )
