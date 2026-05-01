# test_final_state.py
"""
Tests to validate the final state of the OS/filesystem after the student
has completed the symlink repointing task.
"""

import os
import subprocess
import pytest


class TestFinalState:
    """Validate the final state after the symlink repointing task."""

    def test_current_symlink_exists(self):
        """Verify /home/user/deploy/current exists and is a symlink."""
        current_path = "/home/user/deploy/current"
        assert os.path.islink(current_path), (
            f"{current_path} does not exist or is not a symlink. "
            "The 'current' must remain a symlink, not be converted to a regular file or directory."
        )

    def test_current_symlink_points_to_v2_4_1(self):
        """Verify /home/user/deploy/current symlink points to v2.4.1."""
        current_path = "/home/user/deploy/current"
        expected_target = "/home/user/releases/v2.4.1"

        assert os.path.islink(current_path), (
            f"{current_path} is not a symlink."
        )

        actual_target = os.readlink(current_path)
        assert actual_target == expected_target, (
            f"Symlink {current_path} points to '{actual_target}' but expected '{expected_target}'. "
            "The symlink should be repointed to v2.4.1."
        )

    def test_readlink_command_output(self):
        """Verify `readlink /home/user/deploy/current` outputs exactly '/home/user/releases/v2.4.1'."""
        current_path = "/home/user/deploy/current"
        expected_output = "/home/user/releases/v2.4.1"

        result = subprocess.run(
            ["readlink", current_path],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"readlink command failed with return code {result.returncode}. "
            f"stderr: {result.stderr}"
        )

        actual_output = result.stdout.strip()
        assert actual_output == expected_output, (
            f"readlink output is '{actual_output}' but expected '{expected_output}'."
        )

    def test_marker_file_through_symlink(self):
        """Verify `cat /home/user/deploy/current/marker.txt` outputs 'v2.4.1'."""
        marker_path = "/home/user/deploy/current/marker.txt"

        assert os.path.exists(marker_path), (
            f"File {marker_path} does not exist (symlink may be broken or pointing to wrong location)."
        )

        with open(marker_path, 'r') as f:
            content = f.read().strip()

        assert content == "v2.4.1", (
            f"File {marker_path} contains '{content}' but expected 'v2.4.1'. "
            "The symlink should point to the v2.4.1 release."
        )

    def test_release_v2_3_9_still_exists(self):
        """Verify /home/user/releases/v2.3.9 directory still exists (invariant)."""
        v239_path = "/home/user/releases/v2.3.9"
        assert os.path.isdir(v239_path), (
            f"Directory {v239_path} no longer exists. "
            "The old release directory should not be deleted."
        )

    def test_release_v2_3_9_marker_unchanged(self):
        """Verify /home/user/releases/v2.3.9/marker.txt is unchanged (invariant)."""
        marker_path = "/home/user/releases/v2.3.9/marker.txt"
        assert os.path.isfile(marker_path), (
            f"File {marker_path} no longer exists. "
            "The old release should remain unchanged."
        )
        with open(marker_path, 'r') as f:
            content = f.read().strip()
        assert content == "v2.3.9", (
            f"File {marker_path} contains '{content}' but expected 'v2.3.9'. "
            "The old release marker.txt should remain unchanged."
        )

    def test_release_v2_4_1_still_exists(self):
        """Verify /home/user/releases/v2.4.1 directory still exists (invariant)."""
        v241_path = "/home/user/releases/v2.4.1"
        assert os.path.isdir(v241_path), (
            f"Directory {v241_path} no longer exists. "
            "The target release directory should not be deleted."
        )

    def test_release_v2_4_1_marker_unchanged(self):
        """Verify /home/user/releases/v2.4.1/marker.txt is unchanged (invariant)."""
        marker_path = "/home/user/releases/v2.4.1/marker.txt"
        assert os.path.isfile(marker_path), (
            f"File {marker_path} no longer exists. "
            "The target release should remain unchanged."
        )
        with open(marker_path, 'r') as f:
            content = f.read().strip()
        assert content == "v2.4.1", (
            f"File {marker_path} contains '{content}' but expected 'v2.4.1'. "
            "The target release marker.txt should remain unchanged."
        )

    def test_current_is_symlink_not_directory(self):
        """Verify /home/user/deploy/current is a symlink, not a regular directory."""
        current_path = "/home/user/deploy/current"

        # Check it's a symlink (os.path.islink returns True only for symlinks)
        assert os.path.islink(current_path), (
            f"{current_path} is not a symlink. "
            "It may have been converted to a regular directory or file, which is incorrect."
        )

        # Additional check: lstat should show it's a link
        stat_info = os.lstat(current_path)
        import stat
        assert stat.S_ISLNK(stat_info.st_mode), (
            f"{current_path} is not a symbolic link according to lstat. "
            "The 'current' path must remain a symlink."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
