# test_final_state.py
"""
Tests to validate the final state after the student has completed the pip cache purge task.
"""

import os
import subprocess
import pytest


class TestPipCachePurged:
    """Tests to verify the pip cache has been properly purged."""

    def test_pip_cache_wheels_is_empty_or_no_whl_files(self):
        """Verify that /home/user/.cache/pip/wheels/ is empty or contains no .whl files."""
        wheels_path = "/home/user/.cache/pip/wheels"

        if not os.path.exists(wheels_path):
            # Directory doesn't exist, which is acceptable
            return

        # Check for .whl files recursively
        whl_files = []
        for root, dirs, files in os.walk(wheels_path):
            for f in files:
                if f.endswith('.whl'):
                    whl_files.append(os.path.join(root, f))

        assert len(whl_files) == 0, (
            f"The wheels directory still contains .whl files: {whl_files[:5]}... "
            "The pip cache should have been purged with 'pip cache purge'."
        )

    def test_pip_cache_http_is_empty_or_does_not_exist(self):
        """Verify that /home/user/.cache/pip/http/ is empty or does not exist."""
        http_path = "/home/user/.cache/pip/http"

        if not os.path.exists(http_path):
            # Directory doesn't exist, which is acceptable
            return

        # Check if directory is empty (no files recursively)
        file_count = 0
        for root, dirs, files in os.walk(http_path):
            file_count += len(files)

        assert file_count == 0, (
            f"The http cache directory {http_path} still contains {file_count} files. "
            "The pip cache should have been purged with 'pip cache purge'."
        )

    def test_pip_cache_is_effectively_empty(self):
        """Verify that the pip cache is effectively empty (no cached packages)."""
        # Use pip cache info to verify cache is empty
        result = subprocess.run(
            ["pip3", "cache", "info"],
            capture_output=True,
            text=True
        )

        # Even if command fails, we can check the directories directly
        if result.returncode == 0:
            output = result.stdout.lower()
            # Look for indicators that cache is empty
            # pip cache info shows "Number of wheels: X" or similar
            # After purge, it should show 0 or very small numbers
            pass  # Additional validation could be done here

        # Primary check: ensure no significant cached data remains
        pip_cache_path = "/home/user/.cache/pip"
        if os.path.exists(pip_cache_path):
            total_size = 0
            for root, dirs, files in os.walk(pip_cache_path):
                for f in files:
                    filepath = os.path.join(root, f)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass

            # After purge, cache should be very small (< 1MB for metadata)
            # Original was ~2GB
            max_allowed_size = 10 * 1024 * 1024  # 10MB tolerance
            assert total_size < max_allowed_size, (
                f"Pip cache still contains {total_size / (1024*1024):.2f}MB of data. "
                "After 'pip cache purge', the cache should be essentially empty."
            )


class TestParentDirectoryIntact:
    """Tests to verify the parent .cache directory is still intact."""

    def test_user_cache_directory_exists(self):
        """Verify that /home/user/.cache/ directory still exists."""
        cache_path = "/home/user/.cache"
        assert os.path.exists(cache_path), (
            f"Directory {cache_path} no longer exists! "
            "The parent .cache directory should remain intact after pip cache purge."
        )
        assert os.path.isdir(cache_path), (
            f"{cache_path} exists but is not a directory."
        )


class TestProperCommandUsed:
    """Tests to verify the proper pip cache purge command was used."""

    def test_shell_history_shows_pip_cache_purge(self):
        """Check shell history for 'pip cache purge' command usage."""
        history_files = [
            "/home/user/.bash_history",
            "/home/user/.zsh_history",
            "/root/.bash_history",
            "/root/.zsh_history",
        ]

        pip_cache_purge_found = False
        rm_rf_found = False

        for history_file in history_files:
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r', errors='ignore') as f:
                        content = f.read().lower()
                        if 'pip cache purge' in content or 'pip3 cache purge' in content:
                            pip_cache_purge_found = True
                        if 'rm -rf /home/user/.cache/pip' in content or 'rm -r /home/user/.cache/pip' in content:
                            rm_rf_found = True
                except (IOError, PermissionError):
                    pass

        # Also check if the cache is actually purged as evidence
        pip_cache_path = "/home/user/.cache/pip"
        cache_appears_purged = True

        if os.path.exists(pip_cache_path):
            # Check wheels directory
            wheels_path = os.path.join(pip_cache_path, "wheels")
            if os.path.exists(wheels_path):
                for root, dirs, files in os.walk(wheels_path):
                    if any(f.endswith('.whl') for f in files):
                        cache_appears_purged = False
                        break

        # If we found rm -rf in history and not pip cache purge, that's a problem
        if rm_rf_found and not pip_cache_purge_found:
            pytest.fail(
                "It appears 'rm -rf' was used instead of 'pip cache purge'. "
                "The task requires using pip's proper cache purge command."
            )

        # The cache should be purged regardless of how we detect it
        assert cache_appears_purged, (
            "The pip cache does not appear to have been properly purged. "
            "Please run 'pip cache purge' or 'pip3 cache purge'."
        )

    def test_pip_cache_purge_command_would_succeed(self):
        """Verify that pip cache purge command works (exits 0)."""
        # Running it again should succeed with exit 0 even if cache is already empty
        result = subprocess.run(
            ["pip3", "cache", "purge"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"'pip3 cache purge' command failed with exit code {result.returncode}. "
            f"stderr: {result.stderr}"
        )


class TestOtherCacheContentsUntouched:
    """Tests to verify other cache contents were not affected."""

    def test_fontconfig_cache_untouched_if_existed(self):
        """Verify that /home/user/.cache/fontconfig/ was not removed if it existed."""
        # This is a soft check - we just verify the parent cache dir structure is intact
        cache_path = "/home/user/.cache"
        assert os.path.exists(cache_path), (
            f"The parent cache directory {cache_path} should still exist."
        )

        # If fontconfig exists, it should still be a directory
        fontconfig_path = "/home/user/.cache/fontconfig"
        if os.path.exists(fontconfig_path):
            assert os.path.isdir(fontconfig_path), (
                f"{fontconfig_path} should be a directory if it exists."
            )
