# test_initial_state.py
"""
Tests to validate the initial state of the OS/filesystem before the student
performs the symlink creation task.
"""

import os
import json
import pytest


class TestInitialState:
    """Validate the initial state before the task is performed."""

    def test_shortcuts_directory_exists(self):
        """Verify /home/user/shortcuts/ directory exists."""
        shortcuts_dir = "/home/user/shortcuts"
        assert os.path.exists(shortcuts_dir), (
            f"Directory {shortcuts_dir} does not exist. "
            "The shortcuts directory must exist before the task."
        )
        assert os.path.isdir(shortcuts_dir), (
            f"{shortcuts_dir} exists but is not a directory. "
            "It must be a directory."
        )

    def test_shortcuts_directory_is_empty(self):
        """Verify /home/user/shortcuts/ is empty."""
        shortcuts_dir = "/home/user/shortcuts"
        if os.path.exists(shortcuts_dir) and os.path.isdir(shortcuts_dir):
            contents = os.listdir(shortcuts_dir)
            assert len(contents) == 0, (
                f"Directory {shortcuts_dir} is not empty. "
                f"Found: {contents}. It should be empty initially."
            )

    def test_shortcuts_directory_is_writable(self):
        """Verify /home/user/shortcuts/ is writable by the agent."""
        shortcuts_dir = "/home/user/shortcuts"
        assert os.access(shortcuts_dir, os.W_OK), (
            f"Directory {shortcuts_dir} is not writable. "
            "The agent must have write permissions."
        )

    def test_app_directory_exists(self):
        """Verify /home/user/app/ directory exists."""
        app_dir = "/home/user/app"
        assert os.path.exists(app_dir), (
            f"Directory {app_dir} does not exist. "
            "The app directory must exist before the task."
        )
        assert os.path.isdir(app_dir), (
            f"{app_dir} exists but is not a directory. "
            "It must be a directory."
        )

    def test_app_directory_is_writable(self):
        """Verify /home/user/app/ is writable."""
        app_dir = "/home/user/app"
        assert os.access(app_dir, os.W_OK), (
            f"Directory {app_dir} is not writable. "
            "The agent must have write permissions."
        )

    def test_settings_json_exists(self):
        """Verify /home/user/app/settings.json exists."""
        settings_file = "/home/user/app/settings.json"
        assert os.path.exists(settings_file), (
            f"File {settings_file} does not exist. "
            "The settings.json file must exist before the task."
        )

    def test_settings_json_is_regular_file(self):
        """Verify /home/user/app/settings.json is a regular file (not a symlink)."""
        settings_file = "/home/user/app/settings.json"
        assert os.path.isfile(settings_file), (
            f"{settings_file} is not a regular file."
        )
        assert not os.path.islink(settings_file), (
            f"{settings_file} is a symbolic link, but it should be a regular file."
        )

    def test_settings_json_has_correct_content(self):
        """Verify /home/user/app/settings.json contains the expected JSON content."""
        settings_file = "/home/user/app/settings.json"
        expected_content = {"debug": False, "timeout": 30}

        with open(settings_file, 'r') as f:
            content = f.read()

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(
                f"{settings_file} does not contain valid JSON. "
                f"Error: {e}"
            )

        assert parsed_content == expected_content, (
            f"{settings_file} does not have the expected content. "
            f"Expected: {expected_content}, Got: {parsed_content}"
        )

    def test_config_symlink_does_not_exist_yet(self):
        """Verify /home/user/shortcuts/config does not exist yet (task not done)."""
        config_link = "/home/user/shortcuts/config"
        assert not os.path.exists(config_link) and not os.path.islink(config_link), (
            f"{config_link} already exists. "
            "The symlink should not exist before the task is performed."
        )
