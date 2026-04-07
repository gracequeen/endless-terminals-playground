# test_initial_state.py
"""
Tests to validate the initial state of the operating system/filesystem
before the student performs the documentation organization task.
"""

import os
import pytest


class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_docs_project_directory_exists(self):
        """The main docs_project directory must exist."""
        path = "/home/user/docs_project"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_api_directory_exists(self):
        """The api subdirectory must exist."""
        path = "/home/user/docs_project/api"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_guides_directory_exists(self):
        """The guides subdirectory must exist."""
        path = "/home/user/docs_project/guides"
        assert os.path.isdir(path), f"Directory {path} does not exist"

    def test_config_directory_exists(self):
        """The config subdirectory must exist."""
        path = "/home/user/docs_project/config"
        assert os.path.isdir(path), f"Directory {path} does not exist"


class TestMarkdownFiles:
    """Test that required markdown files exist with correct content."""

    def test_readme_md_exists(self):
        """The readme.md file must exist."""
        path = "/home/user/docs_project/readme.md"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_readme_md_content(self):
        """The readme.md file must have correct content."""
        path = "/home/user/docs_project/readme.md"
        with open(path, 'r') as f:
            content = f.read()
        assert "# Project Documentation" in content, f"File {path} missing expected header"
        assert "Welcome to our project" in content, f"File {path} missing expected content"

    def test_api_md_exists(self):
        """The api/api.md file must exist."""
        path = "/home/user/docs_project/api/api.md"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_api_md_content(self):
        """The api/api.md file must have correct content."""
        path = "/home/user/docs_project/api/api.md"
        with open(path, 'r') as f:
            content = f.read()
        assert "# API Reference" in content, f"File {path} missing expected header"

    def test_endpoints_md_exists(self):
        """The api/endpoints.md file must exist."""
        path = "/home/user/docs_project/api/endpoints.md"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_endpoints_md_content(self):
        """The api/endpoints.md file must have correct content."""
        path = "/home/user/docs_project/api/endpoints.md"
        with open(path, 'r') as f:
            content = f.read()
        assert "# Endpoints" in content, f"File {path} missing expected header"

    def test_installation_md_exists(self):
        """The guides/installation.md file must exist."""
        path = "/home/user/docs_project/guides/installation.md"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_installation_md_content(self):
        """The guides/installation.md file must have correct content."""
        path = "/home/user/docs_project/guides/installation.md"
        with open(path, 'r') as f:
            content = f.read()
        assert "# Installation Guide" in content, f"File {path} missing expected header"

    def test_quickstart_md_exists(self):
        """The guides/quickstart.md file must exist."""
        path = "/home/user/docs_project/guides/quickstart.md"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_quickstart_md_content(self):
        """The guides/quickstart.md file must have correct content."""
        path = "/home/user/docs_project/guides/quickstart.md"
        with open(path, 'r') as f:
            content = f.read()
        assert "# Quick Start" in content, f"File {path} missing expected header"


class TestRawNotesFile:
    """Test that raw_notes.txt exists with correct content."""

    def test_raw_notes_exists(self):
        """The raw_notes.txt file must exist."""
        path = "/home/user/docs_project/raw_notes.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_raw_notes_has_todo_items(self):
        """The raw_notes.txt file must contain TODO items."""
        path = "/home/user/docs_project/raw_notes.txt"
        with open(path, 'r') as f:
            content = f.read()

        todo_lines = [line for line in content.splitlines() if line.startswith("TODO:")]
        assert len(todo_lines) == 4, f"Expected 4 TODO lines in {path}, found {len(todo_lines)}"

    def test_raw_notes_specific_todos(self):
        """The raw_notes.txt file must contain specific TODO items."""
        path = "/home/user/docs_project/raw_notes.txt"
        with open(path, 'r') as f:
            content = f.read()

        expected_todos = [
            "TODO: Review the API documentation",
            "TODO: Update installation guide with new steps",
            "TODO: Add examples to quickstart guide",
            "TODO: Fix broken links in readme"
        ]

        for todo in expected_todos:
            assert todo in content, f"Missing TODO item in {path}: {todo}"


class TestConfigFile:
    """Test that settings.conf exists with correct content."""

    def test_settings_conf_exists(self):
        """The config/settings.conf file must exist."""
        path = "/home/user/docs_project/config/settings.conf"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_settings_conf_has_key_value_pairs(self):
        """The settings.conf file must contain key-value pairs."""
        path = "/home/user/docs_project/config/settings.conf"
        with open(path, 'r') as f:
            lines = f.readlines()

        # Count non-comment, non-empty lines with = sign
        kv_lines = [
            line.strip() for line in lines 
            if line.strip() and not line.strip().startswith('#') and '=' in line
        ]
        assert len(kv_lines) == 5, f"Expected 5 key-value pairs in {path}, found {len(kv_lines)}"

    def test_settings_conf_specific_keys(self):
        """The settings.conf file must contain specific configuration keys."""
        path = "/home/user/docs_project/config/settings.conf"
        with open(path, 'r') as f:
            content = f.read()

        expected_pairs = [
            "debug_mode=false",
            "api_version=2.1",
            "timeout=30",
            "log_level=info",
            "max_connections=100"
        ]

        for pair in expected_pairs:
            assert pair in content, f"Missing config entry in {path}: {pair}"

    def test_settings_conf_has_comments(self):
        """The settings.conf file should have comment lines."""
        path = "/home/user/docs_project/config/settings.conf"
        with open(path, 'r') as f:
            lines = f.readlines()

        comment_lines = [line for line in lines if line.strip().startswith('#')]
        assert len(comment_lines) >= 1, f"Expected at least 1 comment line in {path}"


class TestTotalMarkdownFileCount:
    """Test the total count of markdown files."""

    def test_exactly_five_markdown_files(self):
        """There should be exactly 5 markdown files in the docs_project tree."""
        base_path = "/home/user/docs_project"
        md_files = []

        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))

        assert len(md_files) == 5, (
            f"Expected exactly 5 markdown files in {base_path}, "
            f"found {len(md_files)}: {md_files}"
        )