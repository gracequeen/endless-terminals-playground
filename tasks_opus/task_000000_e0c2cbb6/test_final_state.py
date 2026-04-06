# test_final_state.py
"""
Tests to validate the final state of the filesystem after the student has
completed the iOS build log processing task.
"""

import os
import csv
import pytest


class TestBuildReportsDirectoryExists:
    """Tests to verify the build_reports directory was created."""

    def test_build_reports_directory_exists(self):
        """Verify that the build_reports directory exists."""
        build_reports_dir = "/home/user/build_reports"
        assert os.path.isdir(build_reports_dir), (
            f"Directory '{build_reports_dir}' does not exist. "
            "The agent should have created this directory."
        )


class TestWarningsFile:
    """Tests for the warnings.txt file."""

    def test_warnings_file_exists(self):
        """Verify that warnings.txt exists."""
        warnings_file = "/home/user/build_reports/warnings.txt"
        assert os.path.isfile(warnings_file), (
            f"File '{warnings_file}' does not exist. "
            "The agent should have created this file with extracted warnings."
        )

    def test_warnings_file_has_correct_line_count(self):
        """Verify that warnings.txt has exactly 6 warning lines."""
        warnings_file = "/home/user/build_reports/warnings.txt"
        with open(warnings_file, 'r') as f:
            lines = [line for line in f.read().strip().split('\n') if line]
        assert len(lines) == 6, (
            f"Expected 6 warning lines in '{warnings_file}', but found {len(lines)}. "
            "All lines containing 'warning:' (case-insensitive) should be extracted."
        )

    def test_warnings_file_contains_expected_warnings(self):
        """Verify that warnings.txt contains the expected warning messages."""
        warnings_file = "/home/user/build_reports/warnings.txt"
        with open(warnings_file, 'r') as f:
            content = f.read()

        expected_warnings = [
            "NetworkManager.swift:45:12:",
            "LoginViewController.swift:123:8:",
            "DataParser.swift:67:15:",
            "NetworkManager.swift:89:3:",
            "UserModel.swift:22:10:",
            "LoginViewController.swift:200:14:",
        ]

        for warning in expected_warnings:
            assert warning in content, (
                f"Expected warning containing '{warning}' not found in '{warnings_file}'."
            )

    def test_warnings_file_ends_with_newline(self):
        """Verify that warnings.txt ends with a newline."""
        warnings_file = "/home/user/build_reports/warnings.txt"
        with open(warnings_file, 'r') as f:
            content = f.read()
        assert content.endswith('\n'), (
            f"File '{warnings_file}' does not end with a newline."
        )


class TestErrorsFile:
    """Tests for the errors.txt file."""

    def test_errors_file_exists(self):
        """Verify that errors.txt exists."""
        errors_file = "/home/user/build_reports/errors.txt"
        assert os.path.isfile(errors_file), (
            f"File '{errors_file}' does not exist. "
            "The agent should have created this file with extracted errors."
        )

    def test_errors_file_has_correct_line_count(self):
        """Verify that errors.txt has exactly 2 error lines."""
        errors_file = "/home/user/build_reports/errors.txt"
        with open(errors_file, 'r') as f:
            lines = [line for line in f.read().strip().split('\n') if line]
        assert len(lines) == 2, (
            f"Expected 2 error lines in '{errors_file}', but found {len(lines)}. "
            "All lines containing 'error:' (case-insensitive) should be extracted."
        )

    def test_errors_file_contains_expected_errors(self):
        """Verify that errors.txt contains the expected error messages."""
        errors_file = "/home/user/build_reports/errors.txt"
        with open(errors_file, 'r') as f:
            content = f.read()

        expected_errors = [
            "CacheManager.swift:34:20:",
            "AppDelegate.swift:15:5:",
        ]

        for error in expected_errors:
            assert error in content, (
                f"Expected error containing '{error}' not found in '{errors_file}'."
            )

    def test_errors_file_ends_with_newline(self):
        """Verify that errors.txt ends with a newline."""
        errors_file = "/home/user/build_reports/errors.txt"
        with open(errors_file, 'r') as f:
            content = f.read()
        assert content.endswith('\n'), (
            f"File '{errors_file}' does not end with a newline."
        )


class TestBuildTimesCSV:
    """Tests for the build_times.csv file."""

    def test_build_times_file_exists(self):
        """Verify that build_times.csv exists."""
        build_times_file = "/home/user/build_reports/build_times.csv"
        assert os.path.isfile(build_times_file), (
            f"File '{build_times_file}' does not exist. "
            "The agent should have created this file with build timing information."
        )

    def test_build_times_has_correct_header(self):
        """Verify that build_times.csv has the correct CSV header."""
        build_times_file = "/home/user/build_reports/build_times.csv"
        with open(build_times_file, 'r') as f:
            first_line = f.readline().strip()
        assert first_line == "phase,duration_seconds", (
            f"Expected header 'phase,duration_seconds' in '{build_times_file}', "
            f"but found '{first_line}'."
        )

    def test_build_times_has_correct_data(self):
        """Verify that build_times.csv contains the correct build phase data."""
        build_times_file = "/home/user/build_reports/build_times.csv"
        with open(build_times_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        expected_phases = {
            "Compile Sources": "45",
            "Link Binary": "12",
            "Copy Resources": "8",
            "Code Signing": "23",
        }

        assert len(rows) == 4, (
            f"Expected 4 build phases in '{build_times_file}', but found {len(rows)}."
        )

        for row in rows:
            phase = row.get('phase', '').strip()
            duration = row.get('duration_seconds', '').strip()
            assert phase in expected_phases, (
                f"Unexpected phase '{phase}' found in '{build_times_file}'."
            )
            assert duration == expected_phases[phase], (
                f"Expected duration '{expected_phases[phase]}' for phase '{phase}', "
                f"but found '{duration}'."
            )

    def test_build_times_file_ends_with_newline(self):
        """Verify that build_times.csv ends with a newline."""
        build_times_file = "/home/user/build_reports/build_times.csv"
        with open(build_times_file, 'r') as f:
            content = f.read()
        assert content.endswith('\n'), (
            f"File '{build_times_file}' does not end with a newline."
        )


class TestSummaryFile:
    """Tests for the summary.txt file."""

    def test_summary_file_exists(self):
        """Verify that summary.txt exists."""
        summary_file = "/home/user/build_reports/summary.txt"
        assert os.path.isfile(summary_file), (
            f"File '{summary_file}' does not exist. "
            "The agent should have created this file with the build summary."
        )

    def test_summary_has_correct_warnings_count(self):
        """Verify that summary.txt shows correct total warnings count."""
        summary_file = "/home/user/build_reports/summary.txt"
        with open(summary_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 1, f"File '{summary_file}' is empty or has no lines."
        first_line = lines[0].strip()
        assert first_line == "Total Warnings: 6", (
            f"Expected 'Total Warnings: 6' on line 1, but found '{first_line}'."
        )

    def test_summary_has_correct_errors_count(self):
        """Verify that summary.txt shows correct total errors count."""
        summary_file = "/home/user/build_reports/summary.txt"
        with open(summary_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 2, f"File '{summary_file}' has fewer than 2 lines."
        second_line = lines[1].strip()
        assert second_line == "Total Errors: 2", (
            f"Expected 'Total Errors: 2' on line 2, but found '{second_line}'."
        )

    def test_summary_has_correct_total_build_time(self):
        """Verify that summary.txt shows correct total build time."""
        summary_file = "/home/user/build_reports/summary.txt"
        with open(summary_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 3, f"File '{summary_file}' has fewer than 3 lines."
        third_line = lines[2].strip()
        assert third_line == "Total Build Time: 88 seconds", (
            f"Expected 'Total Build Time: 88 seconds' on line 3, but found '{third_line}'."
        )

    def test_summary_has_correct_longest_phase(self):
        """Verify that summary.txt shows correct longest phase."""
        summary_file = "/home/user/build_reports/summary.txt"
        with open(summary_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) >= 4, f"File '{summary_file}' has fewer than 4 lines."
        fourth_line = lines[3].strip()
        assert fourth_line == "Longest Phase: Compile Sources (45 seconds)", (
            f"Expected 'Longest Phase: Compile Sources (45 seconds)' on line 4, "
            f"but found '{fourth_line}'."
        )

    def test_summary_file_ends_with_newline(self):
        """Verify that summary.txt ends with a newline."""
        summary_file = "/home/user/build_reports/summary.txt"
        with open(summary_file, 'r') as f:
            content = f.read()
        assert content.endswith('\n'), (
            f"File '{summary_file}' does not end with a newline."
        )


class TestFilesWithWarningsFile:
    """Tests for the files_with_warnings.txt file."""

    def test_files_with_warnings_exists(self):
        """Verify that files_with_warnings.txt exists."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        assert os.path.isfile(files_file), (
            f"File '{files_file}' does not exist. "
            "The agent should have created this file with unique Swift filenames."
        )

    def test_files_with_warnings_has_correct_count(self):
        """Verify that files_with_warnings.txt has exactly 4 unique filenames."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        with open(files_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        assert len(lines) == 4, (
            f"Expected 4 unique Swift filenames in '{files_file}', but found {len(lines)}."
        )

    def test_files_with_warnings_contains_expected_files(self):
        """Verify that files_with_warnings.txt contains the expected filenames."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        with open(files_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        expected_files = [
            "DataParser.swift",
            "LoginViewController.swift",
            "NetworkManager.swift",
            "UserModel.swift",
        ]

        assert lines == expected_files, (
            f"Expected filenames {expected_files} in alphabetical order, "
            f"but found {lines}."
        )

    def test_files_with_warnings_is_sorted_alphabetically(self):
        """Verify that files_with_warnings.txt is sorted alphabetically."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        with open(files_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        sorted_lines = sorted(lines)
        assert lines == sorted_lines, (
            f"Filenames in '{files_file}' are not sorted alphabetically. "
            f"Found: {lines}, Expected: {sorted_lines}."
        )

    def test_files_with_warnings_ends_with_newline(self):
        """Verify that files_with_warnings.txt ends with a newline."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        with open(files_file, 'r') as f:
            content = f.read()
        assert content.endswith('\n'), (
            f"File '{files_file}' does not end with a newline."
        )

    def test_files_with_warnings_only_contains_swift_files(self):
        """Verify that all entries in files_with_warnings.txt are .swift files."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        with open(files_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for filename in lines:
            assert filename.endswith('.swift'), (
                f"Expected only .swift files in '{files_file}', "
                f"but found '{filename}'."
            )

    def test_files_with_warnings_contains_only_filenames(self):
        """Verify that files_with_warnings.txt contains only filenames, not paths."""
        files_file = "/home/user/build_reports/files_with_warnings.txt"
        with open(files_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        for filename in lines:
            assert '/' not in filename, (
                f"Expected only filenames (no paths) in '{files_file}', "
                f"but found '{filename}' which contains a path separator."
            )