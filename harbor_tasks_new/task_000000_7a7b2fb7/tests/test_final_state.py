# test_final_state.py
"""
Tests to validate the final state of the operating system/filesystem
after the student has completed the container image audit task.
"""

import json
import os
import stat
import subprocess
import pytest


class TestOutputFilesExist:
    """Test that required output files exist."""

    def test_removal_report_exists(self):
        """The removal_report.json file must exist after task completion."""
        report_file = "/home/user/migration/removal_report.json"
        assert os.path.isfile(report_file), (
            f"File '{report_file}' does not exist. "
            "The task requires generating this JSON report file."
        )

    def test_remove_packages_script_exists(self):
        """The remove_packages.sh script must exist after task completion."""
        script_file = "/home/user/migration/remove_packages.sh"
        assert os.path.isfile(script_file), (
            f"File '{script_file}' does not exist. "
            "The task requires generating this uninstall script."
        )


class TestRemovalReportValidJson:
    """Test that removal_report.json is valid JSON with correct structure."""

    @pytest.fixture
    def report_data(self):
        """Load and parse the removal report JSON."""
        report_file = "/home/user/migration/removal_report.json"
        if not os.path.isfile(report_file):
            pytest.fail(f"Report file '{report_file}' does not exist.")

        with open(report_file, 'r') as f:
            content = f.read()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"removal_report.json is not valid JSON: {e}")

    def test_json_is_valid(self):
        """The removal_report.json must be valid JSON."""
        report_file = "/home/user/migration/removal_report.json"
        with open(report_file, 'r') as f:
            content = f.read()

        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"removal_report.json is not valid JSON: {e}")

    def test_has_summary_key(self, report_data):
        """The JSON must have a 'summary' key."""
        assert "summary" in report_data, (
            "removal_report.json is missing the 'summary' key at the top level."
        )

    def test_has_removable_packages_key(self, report_data):
        """The JSON must have a 'removable_packages' key."""
        assert "removable_packages" in report_data, (
            "removal_report.json is missing the 'removable_packages' key at the top level."
        )

    def test_has_dependency_protected_key(self, report_data):
        """The JSON must have a 'dependency_protected' key."""
        assert "dependency_protected" in report_data, (
            "removal_report.json is missing the 'dependency_protected' key at the top level."
        )


class TestSummarySection:
    """Test the summary section of the removal report."""

    @pytest.fixture
    def summary(self):
        """Load the summary section from the report."""
        report_file = "/home/user/migration/removal_report.json"
        with open(report_file, 'r') as f:
            data = json.load(f)
        return data.get("summary", {})

    def test_summary_has_total_installed(self, summary):
        """Summary must have 'total_installed' key."""
        assert "total_installed" in summary, (
            "Summary is missing 'total_installed' key."
        )

    def test_summary_has_total_required(self, summary):
        """Summary must have 'total_required' key."""
        assert "total_required" in summary, (
            "Summary is missing 'total_required' key."
        )

    def test_summary_has_removable_count(self, summary):
        """Summary must have 'removable_count' key."""
        assert "removable_count" in summary, (
            "Summary is missing 'removable_count' key."
        )

    def test_summary_has_kept_as_dependencies(self, summary):
        """Summary must have 'kept_as_dependencies' key."""
        assert "kept_as_dependencies" in summary, (
            "Summary is missing 'kept_as_dependencies' key."
        )

    def test_summary_has_total_space_savings_kb(self, summary):
        """Summary must have 'total_space_savings_kb' key."""
        assert "total_space_savings_kb" in summary, (
            "Summary is missing 'total_space_savings_kb' key."
        )

    def test_total_installed_equals_31(self, summary):
        """summary.total_installed must equal 31."""
        assert summary.get("total_installed") == 31, (
            f"summary.total_installed should be 31, got {summary.get('total_installed')}. "
            "The installed_packages.txt contains exactly 31 packages."
        )

    def test_total_required_equals_9(self, summary):
        """summary.total_required must equal 9."""
        assert summary.get("total_required") == 9, (
            f"summary.total_required should be 9, got {summary.get('total_required')}. "
            "The required_packages.txt contains exactly 9 packages."
        )

    def test_removable_count_is_positive_integer(self, summary):
        """summary.removable_count must be a positive integer."""
        removable_count = summary.get("removable_count")
        assert isinstance(removable_count, int), (
            f"summary.removable_count must be an integer, got {type(removable_count).__name__}."
        )
        assert removable_count > 0, (
            f"summary.removable_count should be positive, got {removable_count}. "
            "There should be packages that can be removed."
        )

    def test_removable_count_in_reasonable_range(self, summary):
        """summary.removable_count should be between 10 and 20."""
        removable_count = summary.get("removable_count")
        assert 10 <= removable_count <= 22, (
            f"summary.removable_count should be between 10 and 22, got {removable_count}. "
            "This suggests the dependency analysis may be incorrect."
        )

    def test_kept_as_dependencies_is_non_negative_integer(self, summary):
        """summary.kept_as_dependencies must be a non-negative integer."""
        kept = summary.get("kept_as_dependencies")
        assert isinstance(kept, int), (
            f"summary.kept_as_dependencies must be an integer, got {type(kept).__name__}."
        )
        assert kept >= 0, (
            f"summary.kept_as_dependencies should be non-negative, got {kept}."
        )

    def test_total_space_savings_kb_is_positive_integer(self, summary):
        """summary.total_space_savings_kb must be a positive integer."""
        space_savings = summary.get("total_space_savings_kb")
        assert isinstance(space_savings, int), (
            f"summary.total_space_savings_kb must be an integer, got {type(space_savings).__name__}."
        )
        assert space_savings > 0, (
            f"summary.total_space_savings_kb should be positive, got {space_savings}. "
            "Removing packages should save some space."
        )


class TestRemovablePackagesArray:
    """Test the removable_packages array in the removal report."""

    @pytest.fixture
    def removable_packages(self):
        """Load the removable_packages array from the report."""
        report_file = "/home/user/migration/removal_report.json"
        with open(report_file, 'r') as f:
            data = json.load(f)
        return data.get("removable_packages", [])

    def test_removable_packages_is_list(self, removable_packages):
        """removable_packages must be a list."""
        assert isinstance(removable_packages, list), (
            f"removable_packages must be a list, got {type(removable_packages).__name__}."
        )

    def test_removable_packages_not_empty(self, removable_packages):
        """removable_packages must not be empty."""
        assert len(removable_packages) > 0, (
            "removable_packages array is empty. There should be packages to remove."
        )

    def test_removable_packages_sorted_alphabetically(self, removable_packages):
        """removable_packages must be sorted alphabetically by name."""
        if len(removable_packages) == 0:
            pytest.skip("No removable packages to check sorting.")

        names = [pkg.get("name", "") for pkg in removable_packages]
        sorted_names = sorted(names)
        assert names == sorted_names, (
            f"removable_packages is not sorted alphabetically by name. "
            f"Got order: {names}, expected: {sorted_names}"
        )

    def test_each_package_has_required_keys(self, removable_packages):
        """Each package in removable_packages must have exactly the required keys."""
        required_keys = {"name", "installed_version", "size_kb", "has_security_update"}

        for i, pkg in enumerate(removable_packages):
            pkg_keys = set(pkg.keys())
            missing = required_keys - pkg_keys
            extra = pkg_keys - required_keys

            error_parts = []
            if missing:
                error_parts.append(f"missing keys: {missing}")
            if extra:
                error_parts.append(f"extra keys: {extra}")

            assert pkg_keys == required_keys, (
                f"Package at index {i} (name: {pkg.get('name', 'unknown')}) has incorrect keys. "
                f"{', '.join(error_parts)}"
            )

    def test_size_kb_values_are_integers(self, removable_packages):
        """size_kb values must be integers, not strings."""
        for pkg in removable_packages:
            size_kb = pkg.get("size_kb")
            assert isinstance(size_kb, int), (
                f"Package '{pkg.get('name')}' has size_kb as {type(size_kb).__name__}, "
                f"expected int. Value: {size_kb}"
            )

    def test_has_security_update_values_are_booleans(self, removable_packages):
        """has_security_update values must be booleans, not strings."""
        for pkg in removable_packages:
            has_update = pkg.get("has_security_update")
            assert isinstance(has_update, bool), (
                f"Package '{pkg.get('name')}' has has_security_update as {type(has_update).__name__}, "
                f"expected bool. Value: {has_update}"
            )

    def test_expected_removable_packages_present(self, removable_packages):
        """Packages like vim, nano, htop, tree, ncdu, git, apache2 should be removable."""
        removable_names = {pkg.get("name") for pkg in removable_packages}

        # These packages should definitely be removable (not dependencies of required packages)
        expected_removable = {"vim", "nano", "htop", "tree", "ncdu", "git", "apache2"}

        missing_expected = expected_removable - removable_names
        # Allow some flexibility - at least most of these should be present
        assert len(missing_expected) <= 2, (
            f"Expected these packages to be in removable_packages but they are missing: {missing_expected}. "
            "These packages are not dependencies of the required packages."
        )

    def test_required_packages_not_in_removable(self, removable_packages):
        """Required packages must NOT appear in removable_packages."""
        required = {"curl", "python3", "python3-pip", "jq", "nginx", 
                   "ca-certificates", "openssl", "bash", "coreutils"}
        removable_names = {pkg.get("name") for pkg in removable_packages}

        incorrectly_removable = required & removable_names
        assert len(incorrectly_removable) == 0, (
            f"These required packages incorrectly appear in removable_packages: {incorrectly_removable}"
        )


class TestDependencyProtectedArray:
    """Test the dependency_protected array in the removal report."""

    @pytest.fixture
    def report_data(self):
        """Load the full report data."""
        report_file = "/home/user/migration/removal_report.json"
        with open(report_file, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def dependency_protected(self, report_data):
        """Load the dependency_protected array from the report."""
        return report_data.get("dependency_protected", [])

    def test_dependency_protected_is_list(self, dependency_protected):
        """dependency_protected must be a list."""
        assert isinstance(dependency_protected, list), (
            f"dependency_protected must be a list, got {type(dependency_protected).__name__}."
        )

    def test_dependency_protected_sorted_if_not_empty(self, dependency_protected):
        """If dependency_protected is non-empty, it must be sorted alphabetically by name."""
        if len(dependency_protected) == 0:
            pytest.skip("dependency_protected is empty, skipping sort check.")

        names = [pkg.get("name", "") for pkg in dependency_protected]
        sorted_names = sorted(names)
        assert names == sorted_names, (
            f"dependency_protected is not sorted alphabetically by name. "
            f"Got order: {names}, expected: {sorted_names}"
        )

    def test_dependency_protected_has_correct_structure(self, dependency_protected):
        """Each item in dependency_protected must have 'name' and 'required_by' keys."""
        for i, pkg in enumerate(dependency_protected):
            assert "name" in pkg, (
                f"Item at index {i} in dependency_protected is missing 'name' key."
            )
            assert "required_by" in pkg, (
                f"Item at index {i} (name: {pkg.get('name', 'unknown')}) in dependency_protected "
                "is missing 'required_by' key."
            )
            assert isinstance(pkg.get("required_by"), list), (
                f"Item '{pkg.get('name')}' in dependency_protected has 'required_by' "
                f"as {type(pkg.get('required_by')).__name__}, expected list."
            )

    def test_core_libraries_likely_protected(self, report_data):
        """Core libraries like libssl3, zlib1g, libc6 should likely be dependency-protected."""
        dependency_protected = report_data.get("dependency_protected", [])
        removable_packages = report_data.get("removable_packages", [])

        protected_names = {pkg.get("name") for pkg in dependency_protected}
        removable_names = {pkg.get("name") for pkg in removable_packages}

        # These are core libraries that are likely dependencies of required packages
        core_libs = {"libssl3", "zlib1g", "libc6"}

        # Check that these are either in dependency_protected or not in removable
        # (they shouldn't be marked as removable)
        for lib in core_libs:
            # The library should NOT be in removable_packages
            assert lib not in removable_names, (
                f"Core library '{lib}' should not be in removable_packages as it's "
                "likely a dependency of required packages like openssl, curl, or python3."
            )


class TestRemovePackagesScript:
    """Test the remove_packages.sh script."""

    def test_script_is_executable(self):
        """The remove_packages.sh script must be executable."""
        script_file = "/home/user/migration/remove_packages.sh"
        assert os.path.isfile(script_file), f"Script '{script_file}' does not exist."

        file_stat = os.stat(script_file)
        is_executable = bool(file_stat.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        assert is_executable, (
            f"Script '{script_file}' is not executable. "
            "It should have been created with chmod +x."
        )

    def test_script_has_shebang(self):
        """The remove_packages.sh script must start with a shebang."""
        script_file = "/home/user/migration/remove_packages.sh"
        with open(script_file, 'r') as f:
            first_line = f.readline().strip()

        valid_shebangs = ["#!/bin/bash", "#!/bin/sh", "#!/usr/bin/env bash", "#!/usr/bin/env sh"]
        assert any(first_line.startswith(shebang) for shebang in valid_shebangs), (
            f"Script does not start with a valid shebang. "
            f"First line is: '{first_line}'. "
            f"Expected one of: {valid_shebangs}"
        )

    def test_script_contains_apt_remove_command(self):
        """The script must contain an apt-get remove or apt remove command."""
        script_file = "/home/user/migration/remove_packages.sh"
        with open(script_file, 'r') as f:
            content = f.read()

        has_apt_remove = ("apt-get remove" in content or 
                         "apt remove" in content or
                         "apt-get purge" in content or
                         "apt purge" in content)
        assert has_apt_remove, (
            "Script does not contain an 'apt-get remove', 'apt remove', "
            "'apt-get purge', or 'apt purge' command."
        )

    def test_script_contains_echo_or_dry_run(self):
        """The script should contain an echo statement (for dry-run info)."""
        script_file = "/home/user/migration/remove_packages.sh"
        with open(script_file, 'r') as f:
            content = f.read()

        has_echo = "echo" in content.lower()
        assert has_echo, (
            "Script does not contain an 'echo' statement. "
            "The task requires a dry-run echo statement before the actual removal command."
        )

    def test_script_references_removable_packages(self):
        """The script should reference the packages from removable_packages."""
        script_file = "/home/user/migration/remove_packages.sh"
        report_file = "/home/user/migration/removal_report.json"

        with open(script_file, 'r') as f:
            script_content = f.read()

        with open(report_file, 'r') as f:
            report_data = json.load(f)

        removable_packages = report_data.get("removable_packages", [])
        if not removable_packages:
            pytest.skip("No removable packages to check in script.")

        # Check that at least some of the removable package names appear in the script
        package_names = [pkg.get("name") for pkg in removable_packages]
        found_packages = [name for name in package_names if name in script_content]

        # At least half of the packages should be mentioned in the script
        assert len(found_packages) >= len(package_names) // 2, (
            f"Script should reference the removable packages. "
            f"Found {len(found_packages)} of {len(package_names)} package names in script. "
            f"Missing: {set(package_names) - set(found_packages)}"
        )


class TestDataConsistency:
    """Test consistency between different parts of the report."""

    @pytest.fixture
    def report_data(self):
        """Load the full report data."""
        report_file = "/home/user/migration/removal_report.json"
        with open(report_file, 'r') as f:
            return json.load(f)

    def test_removable_count_matches_array_length(self, report_data):
        """summary.removable_count must match the length of removable_packages array."""
        summary = report_data.get("summary", {})
        removable_packages = report_data.get("removable_packages", [])

        assert summary.get("removable_count") == len(removable_packages), (
            f"summary.removable_count ({summary.get('removable_count')}) does not match "
            f"the length of removable_packages array ({len(removable_packages)})."
        )

    def test_kept_as_dependencies_matches_array_length(self, report_data):
        """summary.kept_as_dependencies must match the length of dependency_protected array."""
        summary = report_data.get("summary", {})
        dependency_protected = report_data.get("dependency_protected", [])

        assert summary.get("kept_as_dependencies") == len(dependency_protected), (
            f"summary.kept_as_dependencies ({summary.get('kept_as_dependencies')}) does not match "
            f"the length of dependency_protected array ({len(dependency_protected)})."
        )

    def test_total_space_matches_sum_of_sizes(self, report_data):
        """summary.total_space_savings_kb must equal sum of all size_kb values."""
        summary = report_data.get("summary", {})
        removable_packages = report_data.get("removable_packages", [])

        calculated_total = sum(pkg.get("size_kb", 0) for pkg in removable_packages)
        reported_total = summary.get("total_space_savings_kb", 0)

        assert reported_total == calculated_total, (
            f"summary.total_space_savings_kb ({reported_total}) does not match "
            f"the sum of size_kb values in removable_packages ({calculated_total})."
        )

    def test_no_overlap_between_removable_and_protected(self, report_data):
        """No package should appear in both removable_packages and dependency_protected."""
        removable_packages = report_data.get("removable_packages", [])
        dependency_protected = report_data.get("dependency_protected", [])

        removable_names = {pkg.get("name") for pkg in removable_packages}
        protected_names = {pkg.get("name") for pkg in dependency_protected}

        overlap = removable_names & protected_names
        assert len(overlap) == 0, (
            f"These packages appear in both removable_packages and dependency_protected: {overlap}. "
            "A package cannot be both removable and protected."
        )

    def test_counts_add_up_correctly(self, report_data):
        """The counts should add up: installed = required + removable + protected + others."""
        summary = report_data.get("summary", {})

        total_installed = summary.get("total_installed", 0)
        total_required = summary.get("total_required", 0)
        removable_count = summary.get("removable_count", 0)
        kept_as_deps = summary.get("kept_as_dependencies", 0)

        # Total accounted for should not exceed total installed
        accounted = total_required + removable_count + kept_as_deps

        # Note: Some packages might be both required AND dependencies, so we allow some flexibility
        # But the sum should be close to total_installed
        assert accounted <= total_installed + 5, (
            f"Counts don't add up correctly. "
            f"total_installed={total_installed}, total_required={total_required}, "
            f"removable_count={removable_count}, kept_as_dependencies={kept_as_deps}. "
            f"Sum of required+removable+protected ({accounted}) exceeds total_installed."
        )
