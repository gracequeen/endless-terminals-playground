# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the symlink repointing task.
"""

import os
import pytest


class TestInitialState:
    """Validate the initial state before the symlink repointing task."""

    def test_deploy_directory_exists(self):
        """Verify /home/user/deploy directory exists."""
        deploy_path = "/home/user/deploy"
        assert os.path.isdir(deploy_path), (
            f"Directory {deploy_path} does not exist. "
            "The deploy directory must exist for this task."
        )

    def test_releases_directory_exists(self):
        """Verify /home/user/releases directory exists."""
        releases_path = "/home/user/releases"
        assert os.path.isdir(releases_path), (
            f"Directory {releases_path} does not exist. "
            "The releases directory must exist for this task."
        )

    def test_release_v2_3_9_exists(self):
        """Verify /home/user/releases/v2.3.9 directory exists."""
        v239_path = "/home/user/releases/v2.3.9"
        assert os.path.isdir(v239_path), (
            f"Directory {v239_path} does not exist. "
            "The v2.3.9 release directory must exist for this task."
        )

    def test_release_v2_3_9_marker_file_exists(self):
        """Verify /home/user/releases/v2.3.9/marker.txt exists with correct content."""
        marker_path = "/home/user/releases/v2.3.9/marker.txt"
        assert os.path.isfile(marker_path), (
            f"File {marker_path} does not exist. "
            "The marker.txt file must exist in v2.3.9 release."
        )
        with open(marker_path, 'r') as f:
            content = f.read().strip()
        assert content == "v2.3.9", (
            f"File {marker_path} contains '{content}' but expected 'v2.3.9'. "
            "The marker.txt must contain the correct version string."
        )

    def test_release_v2_4_1_exists(self):
        """Verify /home/user/releases/v2.4.1 directory exists."""
        v241_path = "/home/user/releases/v2.4.1"
        assert os.path.isdir(v241_path), (
            f"Directory {v241_path} does not exist. "
            "The v2.4.1 release directory must exist for this task."
        )

    def test_release_v2_4_1_marker_file_exists(self):
        """Verify /home/user/releases/v2.4.1/marker.txt exists with correct content."""
        marker_path = "/home/user/releases/v2.4.1/marker.txt"
        assert os.path.isfile(marker_path), (
            f"File {marker_path} does not exist. "
            "The marker.txt file must exist in v2.4.1 release."
        )
        with open(marker_path, 'r') as f:
            content = f.read().strip()
        assert content == "v2.4.1", (
            f"File {marker_path} contains '{content}' but expected 'v2.4.1'. "
            "The marker.txt must contain the correct version string."
        )

    def test_current_symlink_exists(self):
        """Verify /home/user/deploy/current exists and is a symlink."""
        current_path = "/home/user/deploy/current"
        assert os.path.islink(current_path), (
            f"{current_path} does not exist or is not a symlink. "
            "The 'current' symlink must exist for this task."
        )

    def test_current_symlink_points_to_v2_3_9(self):
        """Verify /home/user/deploy/current symlink points to v2.3.9 (the wrong version)."""
        current_path = "/home/user/deploy/current"
        expected_target = "/home/user/releases/v2.3.9"

        assert os.path.islink(current_path), (
            f"{current_path} is not a symlink."
        )

        actual_target = os.readlink(current_path)
        assert actual_target == expected_target, (
            f"Symlink {current_path} points to '{actual_target}' but expected '{expected_target}'. "
            "The initial state requires the symlink to point to the old v2.3.9 release."
        )

    def test_deploy_directory_is_writable(self):
        """Verify /home/user/deploy is writable."""
        deploy_path = "/home/user/deploy"
        assert os.access(deploy_path, os.W_OK), (
            f"Directory {deploy_path} is not writable. "
            "The deploy directory must be writable to update the symlink."
        )

    def test_releases_directory_is_writable(self):
        """Verify /home/user/releases is writable."""
        releases_path = "/home/user/releases"
        assert os.access(releases_path, os.W_OK), (
            f"Directory {releases_path} is not writable. "
            "The releases directory must be writable."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
