# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the documentation organization task.
"""

import os
import pytest


class TestOutputDirectoryExists:
    """Test that the output directory was created."""

    def test_output_directory_exists(self):
        """The output directory must exist."""
        path = "/home/user/docs_project/output"
        assert os.path.isdir(path), f"Directory {path} does not exist. The output directory must be created."


class TestFileInventory:
    """Test the file_inventory.txt output file."""

    def test_file_inventory_exists(self):
        """The file_inventory.txt file must exist."""
        path = "/home/user/docs_project/output/file_inventory.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_file_inventory_has_five_lines(self):
        """The file_inventory.txt must have exactly 5 lines."""
        path = "/home/user/docs_project/output/file_inventory.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]
        assert len(lines) == 5, (
            f"Expected exactly 5 lines in {path}, found {len(lines)}. "
            f"Lines found: {lines}"
        )

    def test_file_inventory_format(self):
        """Each line must be in format 'FILENAME: FULL_PATH'."""
        path = "/home/user/docs_project/output/file_inventory.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        for line in lines:
            assert ': ' in line, (
                f"Line '{line}' in {path} does not contain ': ' separator. "
                f"Expected format: 'FILENAME: FULL_PATH'"
            )
            parts = line.split(': ', 1)
            assert len(parts) == 2, f"Line '{line}' does not have exactly two parts separated by ': '"
            filename, full_path = parts
            assert filename.endswith('.md'), f"Filename '{filename}' does not end with .md"
            assert full_path.startswith('/home/user/docs_project/'), (
                f"Path '{full_path}' does not start with /home/user/docs_project/"
            )

    def test_file_inventory_sorted_alphabetically(self):
        """Lines must be sorted alphabetically by filename."""
        path = "/home/user/docs_project/output/file_inventory.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        filenames = [line.split(': ')[0] for line in lines]
        sorted_filenames = sorted(filenames)
        assert filenames == sorted_filenames, (
            f"Files in {path} are not sorted alphabetically. "
            f"Found order: {filenames}, expected order: {sorted_filenames}"
        )

    def test_file_inventory_exact_content(self):
        """The file_inventory.txt must have exact expected content."""
        path = "/home/user/docs_project/output/file_inventory.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        expected_lines = [
            "api.md: /home/user/docs_project/api/api.md",
            "endpoints.md: /home/user/docs_project/api/endpoints.md",
            "installation.md: /home/user/docs_project/guides/installation.md",
            "quickstart.md: /home/user/docs_project/guides/quickstart.md",
            "readme.md: /home/user/docs_project/readme.md"
        ]

        assert lines == expected_lines, (
            f"Content of {path} does not match expected.\n"
            f"Expected:\n{chr(10).join(expected_lines)}\n"
            f"Found:\n{chr(10).join(lines)}"
        )


class TestActionItems:
    """Test the action_items.txt output file."""

    def test_action_items_exists(self):
        """The action_items.txt file must exist."""
        path = "/home/user/docs_project/output/action_items.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_action_items_has_four_lines(self):
        """The action_items.txt must have exactly 4 lines."""
        path = "/home/user/docs_project/output/action_items.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]
        assert len(lines) == 4, (
            f"Expected exactly 4 lines in {path}, found {len(lines)}. "
            f"Lines found: {lines}"
        )

    def test_action_items_no_todo_prefix(self):
        """Lines must not contain 'TODO:' prefix."""
        path = "/home/user/docs_project/output/action_items.txt"
        with open(path, 'r') as f:
            content = f.read()
        assert 'TODO:' not in content, (
            f"File {path} still contains 'TODO:' prefix which should have been removed"
        )

    def test_action_items_numbered_format(self):
        """Each line must be in format 'N. ACTION_TEXT'."""
        path = "/home/user/docs_project/output/action_items.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        for i, line in enumerate(lines, 1):
            expected_prefix = f"{i}. "
            assert line.startswith(expected_prefix), (
                f"Line {i} in {path} does not start with '{expected_prefix}'. "
                f"Found: '{line}'"
            )

    def test_action_items_exact_content(self):
        """The action_items.txt must have exact expected content."""
        path = "/home/user/docs_project/output/action_items.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        expected_lines = [
            "1. Review the API documentation",
            "2. Update installation guide with new steps",
            "3. Add examples to quickstart guide",
            "4. Fix broken links in readme"
        ]

        assert lines == expected_lines, (
            f"Content of {path} does not match expected.\n"
            f"Expected:\n{chr(10).join(expected_lines)}\n"
            f"Found:\n{chr(10).join(lines)}"
        )


class TestProcessedConfig:
    """Test the processed_config.txt output file."""

    def test_processed_config_exists(self):
        """The processed_config.txt file must exist."""
        path = "/home/user/docs_project/output/processed_config.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_processed_config_has_five_lines(self):
        """The processed_config.txt must have exactly 5 lines."""
        path = "/home/user/docs_project/output/processed_config.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]
        assert len(lines) == 5, (
            f"Expected exactly 5 lines in {path}, found {len(lines)}. "
            f"Lines found: {lines}"
        )

    def test_processed_config_no_comments(self):
        """The processed_config.txt must not contain comment lines."""
        path = "/home/user/docs_project/output/processed_config.txt"
        with open(path, 'r') as f:
            lines = f.read().splitlines()

        comment_lines = [line for line in lines if line.strip().startswith('#')]
        assert len(comment_lines) == 0, (
            f"File {path} contains comment lines which should have been removed: {comment_lines}"
        )

    def test_processed_config_keys_uppercase(self):
        """All keys must be uppercase."""
        path = "/home/user/docs_project/output/processed_config.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        for line in lines:
            if '=' in line:
                key = line.split('=')[0]
                assert key == key.upper(), (
                    f"Key '{key}' in {path} is not uppercase. "
                    f"Expected: '{key.upper()}'"
                )

    def test_processed_config_sorted_alphabetically(self):
        """Lines must be sorted alphabetically by key."""
        path = "/home/user/docs_project/output/processed_config.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        keys = [line.split('=')[0] for line in lines if '=' in line]
        sorted_keys = sorted(keys)
        assert keys == sorted_keys, (
            f"Keys in {path} are not sorted alphabetically. "
            f"Found order: {keys}, expected order: {sorted_keys}"
        )

    def test_processed_config_exact_content(self):
        """The processed_config.txt must have exact expected content."""
        path = "/home/user/docs_project/output/processed_config.txt"
        with open(path, 'r') as f:
            lines = [line for line in f.read().splitlines() if line.strip()]

        expected_lines = [
            "API_VERSION=2.1",
            "DEBUG_MODE=false",
            "LOG_LEVEL=info",
            "MAX_CONNECTIONS=100",
            "TIMEOUT=30"
        ]

        assert lines == expected_lines, (
            f"Content of {path} does not match expected.\n"
            f"Expected:\n{chr(10).join(expected_lines)}\n"
            f"Found:\n{chr(10).join(lines)}"
        )


class TestSummaryReport:
    """Test the summary_report.txt output file."""

    def test_summary_report_exists(self):
        """The summary_report.txt file must exist."""
        path = "/home/user/docs_project/output/summary_report.txt"
        assert os.path.isfile(path), f"File {path} does not exist"

    def test_summary_report_header(self):
        """The summary_report.txt must have correct header."""
        path = "/home/user/docs_project/output/summary_report.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "DOCUMENTATION SUMMARY REPORT" in content, (
            f"File {path} missing header 'DOCUMENTATION SUMMARY REPORT'"
        )
        assert "============================" in content, (
            f"File {path} missing separator line '============================'"
        )

    def test_summary_report_markdown_count(self):
        """The summary_report.txt must show correct markdown file count (5)."""
        path = "/home/user/docs_project/output/summary_report.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "Total markdown files: 5" in content, (
            f"File {path} does not contain 'Total markdown files: 5'. "
            f"Content: {content}"
        )

    def test_summary_report_action_items_count(self):
        """The summary_report.txt must show correct action items count (4)."""
        path = "/home/user/docs_project/output/summary_report.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "Total action items: 4" in content, (
            f"File {path} does not contain 'Total action items: 4'. "
            f"Content: {content}"
        )

    def test_summary_report_config_entries_count(self):
        """The summary_report.txt must show correct config entries count (5)."""
        path = "/home/user/docs_project/output/summary_report.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "Total config entries: 5" in content, (
            f"File {path} does not contain 'Total config entries: 5'. "
            f"Content: {content}"
        )

    def test_summary_report_complete_marker(self):
        """The summary_report.txt must have 'Report generated: COMPLETE'."""
        path = "/home/user/docs_project/output/summary_report.txt"
        with open(path, 'r') as f:
            content = f.read()

        assert "Report generated: COMPLETE" in content, (
            f"File {path} does not contain 'Report generated: COMPLETE'. "
            f"Content: {content}"
        )

    def test_summary_report_exact_content(self):
        """The summary_report.txt must have exact expected content."""
        path = "/home/user/docs_project/output/summary_report.txt"
        with open(path, 'r') as f:
            lines = [line.rstrip() for line in f.read().splitlines()]

        # Remove any trailing empty lines for comparison
        while lines and not lines[-1]:
            lines.pop()

        expected_lines = [
            "DOCUMENTATION SUMMARY REPORT",
            "============================",
            "Total markdown files: 5",
            "Total action items: 4",
            "Total config entries: 5",
            "Report generated: COMPLETE"
        ]

        assert lines == expected_lines, (
            f"Content of {path} does not match expected format.\n"
            f"Expected:\n{chr(10).join(expected_lines)}\n"
            f"Found:\n{chr(10).join(lines)}"
        )


class TestOriginalFilesPreserved:
    """Test that original source files are still present."""

    def test_raw_notes_still_exists(self):
        """The original raw_notes.txt should still exist."""
        path = "/home/user/docs_project/raw_notes.txt"
        assert os.path.isfile(path), f"Original file {path} should still exist"

    def test_settings_conf_still_exists(self):
        """The original settings.conf should still exist."""
        path = "/home/user/docs_project/config/settings.conf"
        assert os.path.isfile(path), f"Original file {path} should still exist"

    def test_markdown_files_still_exist(self):
        """All original markdown files should still exist."""
        md_files = [
            "/home/user/docs_project/readme.md",
            "/home/user/docs_project/api/api.md",
            "/home/user/docs_project/api/endpoints.md",
            "/home/user/docs_project/guides/installation.md",
            "/home/user/docs_project/guides/quickstart.md"
        ]
        for path in md_files:
            assert os.path.isfile(path), f"Original markdown file {path} should still exist"